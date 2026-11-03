"""
Local Analytical Data Warehouse Manager.
Uses DuckDB to provide local analytical warehouse execution,
serving as the zero-credential drop-in alternative for Google BigQuery.
"""
import os
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional


class WarehouseManager:
    def __init__(self, db_path: str = "data/analytics_dw.duckdb"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        self._register_views()

    def _register_views(self):
        """Registers Gold and Silver Parquet layers as SQL views in DuckDB."""
        gold_dir = os.path.abspath("data/lake/gold")
        silver_dir = os.path.abspath("data/lake/silver")
        raw_dir = os.path.abspath("data/raw")

        views = {
            "dim_dates": os.path.join(gold_dir, "dim_dates.parquet"),
            "dim_customers": os.path.join(gold_dir, "dim_customers.parquet"),
            "dim_products": os.path.join(gold_dir, "dim_products.parquet"),
            "fact_orders": os.path.join(gold_dir, "fact_orders.parquet"),
            "fact_order_items": os.path.join(gold_dir, "fact_order_items.parquet"),
            "fact_payments": os.path.join(gold_dir, "fact_payments.parquet"),
            "mart_daily_revenue": os.path.join(gold_dir, "mart_daily_revenue.parquet"),
            "mart_customer_lifetime_value": os.path.join(gold_dir, "mart_customer_lifetime_value.parquet"),
            "mart_product_performance": os.path.join(gold_dir, "mart_product_performance.parquet"),
        }

        for view_name, file_path in views.items():
            if os.path.exists(file_path):
                norm_path = file_path.replace("\\", "/")
                self.conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{norm_path}');")

    def query(self, sql_query: str) -> pd.DataFrame:
        """Executes analytical SQL query and returns a pandas DataFrame."""
        return self.conn.execute(sql_query).df()

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Calculates executive KPI metrics directly via fast analytical SQL."""
        try:
            sql = """
                SELECT 
                    COUNT(order_id) as total_orders,
                    ROUND(SUM(total_amount), 2) as total_revenue,
                    ROUND(AVG(total_amount), 2) as avg_order_value,
                    COUNT(DISTINCT customer_id) as active_customers,
                    ROUND(SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(order_id), 2) as completion_rate
                FROM fact_orders;
            """
            res = self.conn.execute(sql).fetchone()
            
            pay_sql = """
                SELECT 
                    ROUND(SUM(CASE WHEN is_successful THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as payment_success_rate
                FROM fact_payments;
            """
            pay_res = self.conn.execute(pay_sql).fetchone()

            return {
                "total_orders": res[0] or 0,
                "total_revenue": res[1] or 0.0,
                "avg_order_value": res[2] or 0.0,
                "active_customers": res[3] or 0,
                "completion_rate": res[4] or 0.0,
                "payment_success_rate": pay_res[0] if pay_res else 95.0,
            }
        except Exception as e:
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "active_customers": 0,
                "completion_rate": 0.0,
                "payment_success_rate": 0.0,
                "error": str(e),
            }

    def close(self):
        self.conn.close()

