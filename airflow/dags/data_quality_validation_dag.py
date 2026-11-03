"""
Airflow DAG 7: Data Quality & Reliability Validation (Great Expectations).
Executes quality test suites across Bronze and Silver, calculates DQ score,
verifies quarantine isolation, and alerts if quality thresholds degrade.
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_quality.validation_runner import DataQualityValidationRunner


def run_full_dq_validation():
    runner = DataQualityValidationRunner()
    report = runner.run_complete_validation()
    silver_score = report["silver_audit"]["quality_score_pct"]
    print(f">> Data Quality Validation: Silver Conformance Score = {silver_score}%")
    if silver_score < 95.0:
        raise ValueError(f"Data Quality alert! Silver score {silver_score}% is below 95% SLA.")
    return report


default_args = {
    "owner": "data_reliability_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="data_quality_validation_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["data_quality", "great_expectations", "monitoring"],
) as dag:

    start = EmptyOperator(task_id="start_dq_audit")

    validate_task = PythonOperator(
        task_id="execute_great_expectations_audit",
        python_callable=run_full_dq_validation,
    )

    end = EmptyOperator(task_id="end_dq_audit")

    start >> validate_task >> end
