"""
Airflow DAG 1: Daily Batch Ingestion.
Extracts daily transactional batches from REST APIs and raw feeds,
attaches audit metadata, and persists to Bronze Lake Storage.
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.batch.batch_ingestor import BatchIngestor


def ingest_customers_task():
    ingestor = BatchIngestor()
    return ingestor.ingest_entity_from_file("customers", "data/raw/customers.parquet")


def ingest_products_task():
    ingestor = BatchIngestor()
    return ingestor.ingest_entity_from_file("products", "data/raw/products.parquet")


def ingest_orders_task():
    ingestor = BatchIngestor()
    res1 = ingestor.ingest_entity_from_file("orders", "data/raw/orders.parquet")
    res2 = ingestor.ingest_entity_from_file("order_items", "data/raw/order_items.parquet")
    return [res1, res2]


def ingest_payments_and_refunds_task():
    ingestor = BatchIngestor()
    res1 = ingestor.ingest_entity_from_file("payments", "data/raw/payments.parquet")
    res2 = ingestor.ingest_entity_from_file("refunds", "data/raw/refunds.parquet")
    return [res1, res2]


default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": True,
    "email": ["alerts-data@enterprise-company.com"],
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="daily_batch_ingestion_dag",
    default_args=default_args,
    description="Daily ingestion of transactional data into Bronze lake layer",
    schedule_interval="@daily",
    catchup=False,
    tags=["bronze", "ingestion", "batch"],
) as dag:

    start_task = EmptyOperator(task_id="start_batch_ingestion")

    ingest_cust = PythonOperator(
        task_id="ingest_customers_bronze",
        python_callable=ingest_customers_task,
    )

    ingest_prod = PythonOperator(
        task_id="ingest_products_bronze",
        python_callable=ingest_products_task,
    )

    ingest_ord = PythonOperator(
        task_id="ingest_orders_and_items_bronze",
        python_callable=ingest_orders_task,
    )

    ingest_pay = PythonOperator(
        task_id="ingest_payments_refunds_bronze",
        python_callable=ingest_payments_and_refunds_task,
    )

    end_task = EmptyOperator(task_id="end_batch_ingestion")

    # Workflow DAG task dependencies
    start_task >> [ingest_cust, ingest_prod]
    [ingest_cust, ingest_prod] >> ingest_ord
    ingest_ord >> ingest_pay
    ingest_pay >> end_task
