"""
Pipeline Service for Airflow DAG status and execution control.
"""
from typing import List, Dict, Any, Optional
from airflow.airflow_runner import AirflowRunner


class PipelineService:
    def __init__(self):
        self.runner = AirflowRunner()

    def get_all_pipelines(self) -> List[Dict[str, Any]]:
        """Returns catalog of known Airflow DAG pipelines and their latest run state."""
        catalog = [
            {"id": "daily_batch_ingestion_dag", "name": "Daily Batch Ingestion", "schedule": "@daily", "layer": "Bronze"},
            {"id": "customer_processing_dag", "name": "Customer SCD2 Processing", "schedule": "@daily", "layer": "Silver/Gold"},
            {"id": "order_processing_dag", "name": "Order Processing & Partitioning", "schedule": "Hourly", "layer": "Silver/Gold"},
            {"id": "payment_processing_dag", "name": "Payment & Reconciliation", "schedule": "Every 30m", "layer": "Silver/Gold"},
            {"id": "inventory_sync_dag", "name": "Inventory Synchronization", "schedule": "Every 4h", "layer": "Silver"},
            {"id": "warehouse_transformation_dag", "name": "dbt Warehouse Transformations", "schedule": "Daily 2 AM", "layer": "Marts"},
            {"id": "data_quality_validation_dag", "name": "Great Expectations DQ Audit", "schedule": "@daily", "layer": "Quality"},
        ]
        
        runs = {r["dag_id"]: r for r in self.runner.get_dag_runs(limit=100)}
        for p in catalog:
            latest = runs.get(p["id"])
            p["last_status"] = latest["state"] if latest else "IDLE"
            p["last_run_date"] = latest["execution_date"] if latest else "Never"
            p["last_duration_seconds"] = latest["duration_seconds"] if latest else 0.0
        return catalog

    def get_pipeline_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.runner.get_dag_runs(limit=limit)

    def trigger_pipeline(self, dag_id: str) -> Dict[str, Any]:
        return self.runner.run_dag(dag_id)

