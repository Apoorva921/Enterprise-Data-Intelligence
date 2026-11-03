"""
Master End-to-End Pipeline Runner.
Orchestrates:
1. Bronze Batch Ingestion
2. Silver Cleaning, Normalization & Quarantine
3. Gold Star Schema Modeling & SCD Type 2
4. dbt Transformations and SQL Assertions
5. Great Expectations Data Quality Suite
6. Operational Database Population
"""
import sys
import os
import time

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.batch.batch_ingestor import BatchIngestor
from processing.pandas.bronze_to_silver import BronzeToSilverPipeline
from processing.pandas.silver_to_gold import SilverToGoldPipeline
from dbt.dbt_runner import DBTRunner
from data_quality.validation_runner import DataQualityValidationRunner
from warehouse.warehouse_manager import WarehouseManager
from storage.postgres_client import DatabaseClient
from airflow.airflow_runner import AirflowRunner


def main():
    print("============================================================")
    print(">> Launching Enterprise Real-Time Data Intelligence Platform")
    print("   Master End-to-End Medallion Pipeline Execution")
    print("============================================================")
    
    total_start = time.time()

    # Step 1: Batch Ingestion -> Bronze
    print("\n[STEP 1/6] Ingesting Raw Data into Bronze Lake Layer...")
    ingestor = BatchIngestor()
    bronze_results = ingestor.ingest_all_raw_entities("data/raw")
    print(f"   [OK] Ingested {len(bronze_results)} entities into Bronze.")

    # Step 2: Bronze -> Silver (Cleaning & Quarantine)
    print("\n[STEP 2/6] Processing Silver Layer (Cleansing, Schema & Quarantine)...")
    silver_pipe = BronzeToSilverPipeline()
    silver_stats = silver_pipe.run_all()
    print("   [OK] Silver layer processing stats:")
    for ent, stats in silver_stats.items():
        print(f"        - {ent}: {stats.get('silver', 0):,} clean, {stats.get('quarantined', 0):,} quarantined")

    # Step 3: Silver -> Gold (Star Schema, SCD2 & Aggregated Marts)
    print("\n[STEP 3/6] Modeling Gold Star Schema & Curated Marts...")
    gold_pipe = SilverToGoldPipeline()
    gold_pipe.run_all()
    print("   [OK] Gold dimensional models and fact tables materialized.")

    # Step 4: Analytical Data Warehouse (DuckDB / BigQuery) & dbt
    print("\n[STEP 4/6] Initializing Data Warehouse & Running dbt Transformations...")
    warehouse = WarehouseManager()
    dbt_runner = DBTRunner(warehouse=warehouse)
    dbt_runner.run_models()
    dbt_runner.run_tests()

    # Step 5: Load Operational Database (PostgreSQL / SQLite)
    print("\n[STEP 5/6] Synchronizing Operational Relational Database...")
    db_client = DatabaseClient()
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "schemas", "postgres_schema.sql")
    db_client.execute_script(schema_path)
    
    # Load sample records into operational store
    orders_clean = silver_pipe.lake.read_silver("orders").drop(columns=["order_year_month", "_silver_processed_at"], errors="ignore").head(5000)
    db_client.load_dataframe("orders", orders_clean, if_exists="replace")
    cust_clean = silver_pipe.lake.read_silver("customers").drop(columns=["_silver_processed_at"], errors="ignore").head(1000)
    db_client.load_dataframe("customers", cust_clean, if_exists="replace")
    print("   [OK] Operational relational tables updated.")

    # Step 6: Data Quality Validation (Great Expectations)
    print("\n[STEP 6/6] Executing Great Expectations Data Quality Audit...")
    dq_runner = DataQualityValidationRunner()
    dq_report = dq_runner.run_complete_validation()
    silver_score = dq_report["silver_audit"]["quality_score_pct"]
    quarantined_total = dq_report["quarantine_summary"]["total_quarantined_records"]
    print(f"   [OK] Data Quality Audit Complete!")
    print(f"        Silver Conformance Score: {silver_score}%")
    print(f"        Quarantined Anomalies:    {quarantined_total:,} records")

    # Record DAG execution history in Airflow Runner
    airflow = AirflowRunner()
    airflow.record_run("master_e2e_pipeline", "SUCCESS", round(time.time() - total_start, 2), 6, "All 6 stages passed")

    total_duration = round(time.time() - total_start, 2)
    print(f"\n============================================================")
    print(f"[SUCCESS] All Medallion Data Pipelines Completed in {total_duration}s!")
    print(f"============================================================")


if __name__ == "__main__":
    main()
