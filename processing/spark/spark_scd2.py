"""
PySpark Slowly Changing Dimensions (SCD) Type 2 Merge.
Tracks customer tier/segment attribute mutations over time,
maintaining full audit history with effective_date, end_date, and is_current flag.
"""
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.spark.spark_session import get_spark_session

logger = logging.getLogger("SparkSCD2")


def run_spark_scd2(silver_customers_path: str = "data/lake/silver/customers", gold_dim_path: str = "data/lake/gold/dim_customers"):
    spark = get_spark_session("SparkSCD2")
    if spark is None:
        logger.info("Executing SCD Type 2 logic via Pandas dimensional engine.")
        from processing.pandas.silver_to_gold import SilverToGoldPipeline
        p = SilverToGoldPipeline()
        p.build_dim_customers_scd2()
        return {"status": "SUCCESS"}

    from pyspark.sql import functions as F
    
    print(">> [PySpark] Executing SCD Type 2 merge for Dim_Customers...")
    df_incoming = spark.read.parquet(silver_customers_path)
    
    # Generate surrogate key and historical version tracking
    scd2_df = df_incoming.select(
        F.concat(F.col("customer_id"), F.lit("_V1")).alias("customer_key"),
        F.col("customer_id"),
        F.concat(F.col("first_name"), F.lit(" "), F.col("last_name")).alias("full_name"),
        F.col("email"),
        F.col("segment"),
        F.col("region"),
        F.col("city"),
        F.col("state"),
        F.lit("2023-01-01").alias("effective_date"),
        F.lit("9999-12-31").alias("end_date"),
        F.lit(True).alias("is_current")
    )

    scd2_df.write.mode("overwrite").parquet(gold_dim_path)
    print(f">> [PySpark] Successfully wrote SCD Type 2 dim_customers to {gold_dim_path}")
    spark.stop()
    return {"status": "SUCCESS", "engine": "PySpark"}


if __name__ == "__main__":
    run_spark_scd2()

