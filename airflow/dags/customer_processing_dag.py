"""
Airflow DAG 2: Customer Data Processing.
Cleans customer records, enforces schema, quarantines malformed emails,
and updates SCD Type 2 dim_customers.
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


def clean_customers_silver():
    pipeline = BronzeToSilverPipeline()
    return pipeline.process_customers()


def update_customer_scd2():
    pipeline = SilverToGoldPipeline()
    return pipeline.build_dim_customers_scd2()


default_args = {
    "owner": "data_engineering_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="customer_processing_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["silver", "gold", "scd2", "customers"],
) as dag:

    start = EmptyOperator(task_id="start_customer_processing")
    
    clean_cust = PythonOperator(
        task_id="clean_customers_bronze_to_silver",
        python_callable=clean_customers_silver,
    )

    scd2_update = PythonOperator(
        task_id="update_dim_customers_scd2",
        python_callable=update_customer_scd2,
    )

    end = EmptyOperator(task_id="end_customer_processing")

    start >> clean_cust >> scd2_update >> end
