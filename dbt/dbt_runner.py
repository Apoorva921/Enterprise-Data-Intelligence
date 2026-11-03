"""
dbt Runner & Test Validator.
Executes dbt transformation models, staging views, marts, and schema test assertions
using DuckDB / PostgreSQL warehouse.
"""
import os
import sys
import time
import logging
from typing import Dict, Any, List

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from warehouse.warehouse_manager import WarehouseManager

logger = logging.getLogger("dbtRunner")


class DBTRunner:
    def __init__(self, warehouse: WarehouseManager = None):
        self.warehouse = warehouse or WarehouseManager()

    def run_models(self) -> Dict[str, Any]:
        """Compiles and executes dbt staging and mart models."""
        print("============================================================")
        print(">> Running dbt Models (Staging -> Intermediate -> Marts)")
        print("============================================================")

        start_time = time.time()
        results = []

        # 1. Staging Views
        staging_models = [
            ("stg_customers", "SELECT customer_id, full_name, email, segment, region, city, state FROM dim_customers WHERE is_current = TRUE;"),
            ("stg_products", "SELECT product_id, sku, name AS product_name, category, unit_price, unit_cost, gross_margin_pct FROM dim_products;"),
            ("stg_orders", "SELECT order_id, customer_id, order_date, status AS order_status, total_amount, shipping_region, channel FROM fact_orders WHERE total_amount > 0;"),
            ("stg_payments", "SELECT payment_key AS payment_id, order_id, customer_id, payment_method, payment_status, amount, is_successful FROM fact_payments;"),
        ]

        for model_name, sql in staging_models:
            self.warehouse.conn.execute(f"CREATE OR REPLACE VIEW {model_name} AS {sql}")
            print(f"   [OK] Compiled and created staging model: {model_name}")
            results.append({"model": model_name, "type": "view", "status": "SUCCESS"})

        # 2. Intermediate Models
        self.warehouse.conn.execute("""
            CREATE OR REPLACE VIEW int_order_items_joined AS
            SELECT 
                i.order_item_key,
                i.order_id,
                i.product_id,
                p.product_name,
                p.category,
                i.quantity,
                i.unit_price,
                i.total_price,
                i.gross_profit
            FROM fact_order_items i
            JOIN stg_products p ON i.product_id = p.product_id;
        """)
        print("   [OK] Compiled and created intermediate model: int_order_items_joined")
        results.append({"model": "int_order_items_joined", "type": "view", "status": "SUCCESS"})

        # 3. Analytics Marts
        self.warehouse.conn.execute("""
            CREATE OR REPLACE TABLE dbt_mart_daily_revenue AS
            SELECT 
                CAST(order_date AS DATE) as report_date,
                COUNT(order_id) as total_orders,
                SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_orders,
                ROUND(SUM(total_amount), 2) as total_revenue,
                ROUND(AVG(total_amount), 2) as avg_order_value
            FROM stg_orders
            GROUP BY CAST(order_date AS DATE)
            ORDER BY report_date DESC;
        """)
        print("   [OK] Compiled and materialized table: dbt_mart_daily_revenue")
        results.append({"model": "dbt_mart_daily_revenue", "type": "table", "status": "SUCCESS"})

        elapsed = time.time() - start_time
        print(f"\n>> Finished running {len(results)} dbt models in {elapsed:.2f}s.")
        return {"status": "SUCCESS", "models_run": len(results), "duration_seconds": elapsed}

    def run_tests(self) -> Dict[str, Any]:
        """Runs dbt assertion tests: unique, not-null, referential integrity, and business logic."""
        print("\n============================================================")
        print(">> Running dbt Tests & Quality Assertions")
        print("============================================================")

        tests = [
            ("unique_stg_customers_customer_id", "SELECT customer_id, COUNT(*) FROM stg_customers GROUP BY customer_id HAVING COUNT(*) > 1;"),
            ("not_null_stg_customers_email", "SELECT * FROM stg_customers WHERE email IS NULL;"),
            ("unique_stg_orders_order_id", "SELECT order_id, COUNT(*) FROM stg_orders GROUP BY order_id HAVING COUNT(*) > 1;"),
            ("assert_positive_order_amounts", "SELECT order_id, total_amount FROM stg_orders WHERE total_amount <= 0;"),
            ("assert_payment_matching", "SELECT p.payment_id, p.order_id FROM stg_payments p LEFT JOIN stg_orders o ON p.order_id = o.order_id WHERE o.order_id IS NULL;"),
        ]

        passed = 0
        failed = 0
        test_details = []

        for test_name, sql in tests:
            try:
                res = self.warehouse.conn.execute(sql).fetchall()
                if len(res) == 0:
                    print(f"   [PASS] {test_name}")
                    passed += 1
                    test_details.append({"test": test_name, "status": "PASS", "failing_rows": 0})
                else:
                    print(f"   [FAIL] {test_name} - Found {len(res)} failing rows")
                    failed += 1
                    test_details.append({"test": test_name, "status": "FAIL", "failing_rows": len(res)})
            except Exception as e:
                print(f"   [ERROR] {test_name}: {e}")
                failed += 1
                test_details.append({"test": test_name, "status": "ERROR", "error": str(e)})

        print(f"\n>> dbt Test Results: {passed} PASSED, {failed} FAILED out of {len(tests)} tests.")
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "tests": test_details,
        }


def main():
    runner = DBTRunner()
    runner.run_models()
    runner.run_tests()


if __name__ == "__main__":
    main()
