"""
Airflow DAG 6: Data Warehouse Transformation (dbt Execution).
Triggers dbt compile, runs staging/marts models, and executes test assertions.
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dbt.dbt_runner import DBTRunner


def run_dbt_models_task():
    runner = DBTRunner()
    res = runner.run_models()
    if res["status"] != "SUCCESS":
        raise RuntimeError("dbt models compilation/run failed!")
    return res


def run_dbt_tests_task():
    runner = DBTRunner()
    res = runner.run_tests()
    if res["failed"] > 0:
        raise RuntimeError(f"dbt test assertions failed: {res['failed']} failures!")
    return res


default_args = {
    "owner": "analytics_engineering_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="warehouse_transformation_dag",
    default_args=default_args,
    schedule_interval="0 2 * * *",  # 2 AM daily
    catchup=False,
    tags=["dbt", "warehouse", "transformation", "marts"],
) as dag:

    start = EmptyOperator(task_id="start_dbt_pipeline")

    dbt_run = PythonOperator(
        task_id="dbt_run_models",
        python_callable=run_dbt_models_task,
    )

    dbt_test = PythonOperator(
        task_id="dbt_test_assertions",
        python_callable=run_dbt_tests_task,
    )

    end = EmptyOperator(task_id="end_dbt_pipeline")

    start >> dbt_run >> dbt_test >> end
