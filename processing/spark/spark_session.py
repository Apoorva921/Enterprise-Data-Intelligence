"""
PySpark Session Factory with Graceful Fallback.
Configures Spark application with optimal partition shuffle settings,
memory limits, and Parquet/Delta compatibility.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("SparkSession")


def get_spark_session(app_name: str = "EnterpriseDataPlatform") -> Optional[Any]:
    """
    Initializes and returns a configured SparkSession.
    If PySpark or Java is unavailable in the environment, returns None.
    """
    try:
        from pyspark.sql import SparkSession
        builder = (
            SparkSession.builder.appName(app_name)
            .master("local[*]")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.default.parallelism", "8")
            .config("spark.driver.memory", "2g")
            .config("spark.sql.parquet.compression.codec", "snappy")
        )
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"PySpark session initialized successfully: {spark.version}")
        return spark
    except Exception as e:
        logger.warning(f"PySpark not available in local host environment: {e}. PySpark scripts will use dual-engine fallback.")
        return None
