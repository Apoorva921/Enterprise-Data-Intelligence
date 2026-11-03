"""
Airflow DAG 4: Payment Processing & Reconciliation Pipeline.
Cleans payments and refunds, links with orders, and computes failure rates.
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


def clean_payments_and_refunds():
    p = BronzeToSilverPipeline()
    p.process_payments()


def materialize_gold_payments():
    p = SilverToGoldPipeline()
    p.build_fact_payments()


default_args = {
    "owner": "data_engineering_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="payment_processing_dag",
    default_args=default_args,
    schedule_interval="*/30 * * * *",  # Every 30 mins
    catchup=False,
    tags=["silver", "gold", "payments"],
) as dag:

    start = EmptyOperator(task_id="start_payment_pipeline")

    clean_pay = PythonOperator(
        task_id="clean_payments_silver",
        python_callable=clean_payments_and_refunds,
    )

    gold_pay = PythonOperator(
        task_id="materialize_fact_payments",
        python_callable=materialize_gold_payments,
    )

    end = EmptyOperator(task_id="end_payment_pipeline")

    start >> clean_pay >> gold_pay >> end
