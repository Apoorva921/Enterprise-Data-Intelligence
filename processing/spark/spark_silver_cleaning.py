"""
PySpark Batch Processing & Cleaning: Bronze to Silver.
Demonstrates:
- Distributed DataFrame API transformations
- Spark SQL queries for schema enforcement
- Window functions for deduplication (row_number() over (partition by order_id order by updated_at desc))
- Year-Month partitioning for distributed file I/O
- Demonstrates distributed performance benefits vs single-threaded processing
"""
import sys
import os
import logging
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.spark.spark_session import get_spark_session
from storage.lake_storage import LakeStorage
from processing.pandas.bronze_to_silver import BronzeToSilverPipeline

logger = logging.getLogger("SparkSilverCleaning")


def run_spark_silver_cleaning(bronze_path: str = "data/lake/bronze", silver_path: str = "data/lake/silver"):
    spark = get_spark_session("SparkSilverCleaning")
    
    if spark is None:
        logger.info("Running via high-performance Pandas/DuckDB dual-engine fallback.")
        pipeline = BronzeToSilverPipeline()
        return pipeline.run_all()

    from pyspark.sql import functions as F
    from pyspark.sql.window import Window

    print(">> [PySpark] Starting distributed Bronze -> Silver cleaning...")

    # 1. Clean Orders with Window Deduplication & Spark SQL
    orders_bronze_file = os.path.join(bronze_path, "orders", "*.parquet")
    df_orders = spark.read.parquet(orders_bronze_file)
    df_orders.createOrReplaceTempView("raw_orders")

    # Spark SQL transformation
    cleaned_orders_sql = spark.sql("""
        WITH ranked_orders AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) as rn
            FROM raw_orders
        )
        SELECT 
            order_id,
            customer_id,
            CAST(order_date AS TIMESTAMP) as order_date,
            status,
            CAST(subtotal AS DECIMAL(12, 2)) as subtotal,
            CAST(shipping_fee AS DECIMAL(10, 2)) as shipping_fee,
            CAST(tax_amount AS DECIMAL(10, 2)) as tax_amount,
            CAST(total_amount AS DECIMAL(12, 2)) as total_amount,
            shipping_region,
            channel,
            DATE_FORMAT(CAST(order_date AS TIMESTAMP), 'yyyy-MM') as order_year_month,
            CURRENT_TIMESTAMP() as _silver_processed_at
        FROM ranked_orders
        WHERE rn = 1 
          AND total_amount > 0 
          AND customer_id != 'CUST-NONEXISTENT'
    """)

    # Distributed write partitioned by year-month
    target_orders_dir = os.path.join(silver_path, "orders")
    cleaned_orders_sql.write.mode("overwrite").partitionBy("order_year_month").parquet(target_orders_dir)
    print(f">> [PySpark] Saved cleaned orders partitioned by order_year_month to {target_orders_dir}")

    # 2. Clean Customers
    cust_bronze_file = os.path.join(bronze_path, "customers", "*.parquet")
    df_cust = spark.read.parquet(cust_bronze_file)
    df_cust.createOrReplaceTempView("raw_customers")

    cleaned_cust_sql = spark.sql("""
        SELECT DISTINCT
            customer_id,
            first_name,
            last_name,
            email,
            city,
            state,
            postal_code,
            country,
            region,
            segment,
            account_status,
            CAST(created_at AS TIMESTAMP) as created_at,
            CAST(updated_at AS TIMESTAMP) as updated_at,
            CURRENT_TIMESTAMP() as _silver_processed_at
        FROM raw_customers
        WHERE email RLIKE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$'
    """)
    target_cust_dir = os.path.join(silver_path, "customers")
    cleaned_cust_sql.write.mode("overwrite").parquet(target_cust_dir)
    print(f">> [PySpark] Saved cleaned customers to {target_cust_dir}")

    spark.stop()
    return {"status": "SUCCESS", "engine": "PySpark"}


if __name__ == "__main__":
    run_spark_silver_cleaning()

