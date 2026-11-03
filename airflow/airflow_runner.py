"""
Airflow CLI & Standalone Pipeline Orchestration Runner.
Executes Airflow DAGs, tracks execution duration, maintains pipeline run history,
and serves execution metrics to FastAPI and React dashboards.
"""
import os
import sys
import time
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airflow.dags.daily_batch_ingestion_dag import (
    ingest_customers_task,
    ingest_products_task,
    ingest_orders_task,
    ingest_payments_and_refunds_task,
)
from airflow.dags.customer_processing_dag import clean_customers_silver, update_customer_scd2
from airflow.dags.order_processing_dag import clean_orders_and_items, materialize_gold_orders
from airflow.dags.payment_processing_dag import clean_payments_and_refunds, materialize_gold_payments
from airflow.dags.inventory_sync_dag import sync_inventory_silver
from airflow.dags.warehouse_transformation_dag import run_dbt_models_task, run_dbt_tests_task
from airflow.dags.data_quality_validation_dag import run_full_dq_validation


class AirflowRunner:
    def __init__(self, db_path: str = "data/airflow_history.sqlite"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_history_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        return conn

    def _init_history_db(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS dag_runs (
                    run_id TEXT PRIMARY KEY,
                    dag_id TEXT NOT NULL,
                    execution_date TEXT NOT NULL,
                    state TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    tasks_executed INTEGER NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()

    def record_run(self, dag_id: str, state: str, duration: float, tasks: int, details: str = "") -> str:
        run_id = f"manual__{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}_{dag_id[:10]}_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        
        for attempt in range(5):
            try:
                with self._get_connection() as conn:
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO dag_runs (run_id, dag_id, execution_date, state, duration_seconds, tasks_executed, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, dag_id, now, state, duration, tasks, details))
                    conn.commit()
                return run_id
            except sqlite3.OperationalError as e:
                if attempt < 4:
                    time.sleep(0.2 * (attempt + 1))
                else:
                    print(f"Warning: Failed to record dag run after 5 attempts: {e}")
                    return run_id
        return run_id

    def get_dag_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        for attempt in range(5):
            try:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    c.execute("SELECT * FROM dag_runs ORDER BY execution_date DESC LIMIT ?", (limit,))
                    return [dict(r) for r in c.fetchall()]
            except sqlite3.OperationalError:
                if attempt < 4:
                    time.sleep(0.1 * (attempt + 1))
                else:
                    return []
        return []

    def run_dag(self, dag_id: str) -> Dict[str, Any]:
        """Runs the specified Airflow DAG workflow."""
        start_time = time.time()
        print(f"\n>> Executing Airflow DAG: '{dag_id}'...")

        try:
            if dag_id == "daily_batch_ingestion_dag":
                ingest_customers_task()
                ingest_products_task()
                ingest_orders_task()
                ingest_payments_and_refunds_task()
                tasks_count = 4

            elif dag_id == "customer_processing_dag":
                clean_customers_silver()
                update_customer_scd2()
                tasks_count = 2

            elif dag_id == "order_processing_dag":
                clean_orders_and_items()
                materialize_gold_orders()
                tasks_count = 2

            elif dag_id == "payment_processing_dag":
                clean_payments_and_refunds()
                materialize_gold_payments()
                tasks_count = 2

            elif dag_id == "inventory_sync_dag":
                sync_inventory_silver()
                tasks_count = 1

            elif dag_id == "warehouse_transformation_dag":
                run_dbt_models_task()
                run_dbt_tests_task()
                tasks_count = 2

            elif dag_id == "data_quality_validation_dag":
                run_full_dq_validation()
                tasks_count = 1

            else:
                raise ValueError(f"Unknown DAG ID: {dag_id}")

            duration = round(time.time() - start_time, 2)
            run_id = self.record_run(dag_id, "SUCCESS", duration, tasks_count, "Executed cleanly")
            print(f">> [SUCCESS] DAG '{dag_id}' completed in {duration}s. Run ID: {run_id}")
            return {"dag_id": dag_id, "run_id": run_id, "state": "SUCCESS", "duration_seconds": duration}

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            run_id = self.record_run(dag_id, "FAILED", duration, 0, str(e))
            print(f">> [FAILED] DAG '{dag_id}' failed: {e}")
            return {"dag_id": dag_id, "run_id": run_id, "state": "FAILED", "duration_seconds": duration, "error": str(e)}

    def run_all_dags(self) -> List[Dict[str, Any]]:
        """Executes all 7 DAGs in sequence to populate the entire Medallion architecture and Warehouse."""
        dags = [
            "daily_batch_ingestion_dag",
            "customer_processing_dag",
            "order_processing_dag",
            "payment_processing_dag",
            "inventory_sync_dag",
            "warehouse_transformation_dag",
            "data_quality_validation_dag",
        ]
        results = []
        for d in dags:
            res = self.run_dag(d)
            results.append(res)
        return results


def main():
    runner = AirflowRunner()
    runner.run_all_dags()


if __name__ == "__main__":
    main()
