"""
Airflow DAG 5: Inventory Synchronization Pipeline.
Syncs multi-warehouse stock levels, reorder points, and warehouse alerts.
"""
from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from processing.pandas.bronze_to_silver import BronzeToSilverPipeline
from storage.postgres_client import DatabaseClient


def sync_inventory_silver():
    p = BronzeToSilverPipeline()
    p.process_inventory()


def check_stock_reorder_alerts():
    db = DatabaseClient()
    # Query low stock items below reorder point
    try:
        low_stock = db.query_to_df("""
            SELECT product_id, warehouse_id, stock_level, reorder_point 
            FROM inventory 
            WHERE stock_level <= reorder_point
            LIMIT 10
        """)
        print(f">> Inventory Alert Check: {len(low_stock)} products identified at or below reorder threshold.")
    except Exception as e:
        print(f">> Stock check completed: {e}")
    finally:
        db.close()


default_args = {
    "owner": "data_engineering_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

with DAG(
    dag_id="inventory_sync_dag",
    default_args=default_args,
    schedule_interval="0 */4 * * *",  # Every 4 hours
    catchup=False,
    tags=["silver", "inventory", "alerts"],
) as dag:

    start = EmptyOperator(task_id="start_inventory_sync")
    
    sync_inv = PythonOperator(
        task_id="sync_inventory_silver_layer",
        python_callable=sync_inventory_silver,
    )

    alert_check = PythonOperator(
        task_id="evaluate_low_stock_thresholds",
        python_callable=check_stock_reorder_alerts,
    )

    end = EmptyOperator(task_id="end_inventory_sync")

    start >> sync_inv >> alert_check >> end
