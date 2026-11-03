"""
PySpark Gold Aggregations & Star Schema Builder.
Demonstrates distributed joins across Fact and Dimension tables,
and rollup aggregations for executive reporting.
"""
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.spark.spark_session import get_spark_session
from processing.pandas.silver_to_gold import SilverToGoldPipeline

logger = logging.getLogger("SparkGoldAggregation")


def run_spark_gold_aggregation(silver_path: str = "data/lake/silver", gold_path: str = "data/lake/gold"):
    spark = get_spark_session("SparkGoldAggregation")
    if spark is None:
        logger.info("PySpark absent; executing via Pandas/DuckDB Gold Pipeline.")
        pipeline = SilverToGoldPipeline()
        return pipeline.run_all()

    print(">> [PySpark] Executing distributed Fact/Dim joins and mart aggregations...")
    df_orders = spark.read.parquet(os.path.join(silver_path, "orders"))
    df_items = spark.read.parquet(os.path.join(silver_path, "order_items"))
    df_prods = spark.read.parquet(os.path.join(silver_path, "products"))

    df_orders.createOrReplaceTempView("silver_orders")
    df_items.createOrReplaceTempView("silver_items")
    df_prods.createOrReplaceTempView("silver_products")

    # Distributed daily revenue aggregation
    daily_revenue_mart = spark.sql("""
        SELECT 
            TO_DATE(order_date) as order_day,
            COUNT(order_id) as total_orders,
            SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_orders,
            ROUND(SUM(total_amount), 2) as total_gross_revenue,
            ROUND(AVG(total_amount), 2) as avg_order_value
        FROM silver_orders
        GROUP BY TO_DATE(order_date)
        ORDER BY order_day
    """)
    daily_revenue_mart.write.mode("overwrite").parquet(os.path.join(gold_path, "mart_daily_revenue"))

    # Distributed product profitability join
    product_profit_mart = spark.sql("""
        SELECT 
            p.product_id,
            p.name as product_name,
            p.category,
            SUM(i.quantity) as units_sold,
            ROUND(SUM(i.total_price), 2) as gross_revenue,
            ROUND(SUM(i.quantity * p.cost), 2) as total_cogs,
            ROUND(SUM(i.total_price) - SUM(i.quantity * p.cost), 2) as gross_profit
        FROM silver_items i
        JOIN silver_products p ON i.product_id = p.product_id
        GROUP BY p.product_id, p.name, p.category
    """)
    product_profit_mart.write.mode("overwrite").parquet(os.path.join(gold_path, "mart_product_performance"))

    print(">> [PySpark] Gold analytics marts written successfully.")
    spark.stop()
    return {"status": "SUCCESS", "engine": "PySpark"}


if __name__ == "__main__":
    run_spark_gold_aggregation()

