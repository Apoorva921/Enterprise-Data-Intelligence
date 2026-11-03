"""
Airflow DAG 3: Order Processing Pipeline.
Deduplicates orders, quarantines orphaned customers and negative totals,
partitions by year_month, and materializes fact_orders and fact_order_items.
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.pandas.bronze_to_silver import BronzeToSilverPipeline
from processing.pandas.silver_to_gold import SilverToGoldPipeline


def clean_orders_and_items():
    p = BronzeToSilverPipeline()
    p.process_orders()
    p.process_order_items()


def materialize_gold_orders():
    p = SilverToGoldPipeline()
    p.build_fact_orders()
    p.build_fact_order_items()


default_args = {
    "owner": "data_engineering_team",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="order_processing_dag",
    default_args=default_args,
    schedule_interval="0 * * * *",  # Hourly
    catchup=False,
    tags=["silver", "gold", "orders", "facts"],
) as dag:

    start = EmptyOperator(task_id="start_order_processing")

    clean_step = PythonOperator(
        task_id="clean_and_deduplicate_orders",
        python_callable=clean_orders_and_items,
    )

    gold_step = PythonOperator(
        task_id="materialize_fact_orders_and_items",
        python_callable=materialize_gold_orders,
    )

    end = EmptyOperator(task_id="end_order_processing")

    start >> clean_step >> gold_step >> end
