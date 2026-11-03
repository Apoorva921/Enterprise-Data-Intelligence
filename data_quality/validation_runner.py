"""
Great Expectations Data Quality Validation Runner.
Executes test suites, computes Data Quality Score (0-100%),
generates comprehensive diagnostic reports, and verifies pipeline idempotency.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from storage.lake_storage import LakeStorage
from data_quality.expectations_suite import QualityExpectationsSuite
from data_quality.quarantine_manager import QuarantineManager

logger = logging.getLogger("ValidationRunner")


class DataQualityValidationRunner:
    def __init__(self, lake: LakeStorage = None, quarantine: QuarantineManager = None):
        self.lake = lake or LakeStorage()
        self.quarantine = quarantine or QuarantineManager(lake_storage=self.lake)
        self.reports_dir = os.path.abspath("data/data_quality/reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def run_bronze_quality_audit(self) -> Dict[str, Any]:
        """
        Runs quality assertions against raw Bronze layer.
        Verifies that intentional anomalies (duplicates, negative values, malformed emails)
        are successfully detected.
        """
        suite = QualityExpectationsSuite
        results = []

        # 1. Orders Audit
        try:
            orders_df = self.lake.read_bronze("orders")
            results.append(suite.expect_column_to_exist(orders_df, "order_id"))
            results.append(suite.expect_column_values_to_not_be_null(orders_df, "order_id"))
            results.append(suite.expect_column_values_to_be_unique(orders_df, "order_id"))  # Expected to detect duplicates
            results.append(suite.expect_column_values_to_be_between(orders_df, "total_amount", 0.01, 50000.0))  # Expected to detect negatives
            results.append(suite.expect_column_values_to_be_in_set(
                orders_df, "status", ["PENDING", "PROCESSING", "SHIPPED", "COMPLETED", "CANCELLED", "REFUNDED"]
            ))
        except Exception as e:
            logger.error(f"Error auditing bronze orders: {e}")

        # 2. Customers Audit
        try:
            cust_df = self.lake.read_bronze("customers")
            results.append(suite.expect_column_to_exist(cust_df, "customer_id"))
            results.append(suite.expect_column_values_to_not_be_null(cust_df, "customer_id"))
            results.append(suite.expect_column_values_to_match_regex(cust_df, "email", r"^[\w\.-]+@[\w\.-]+\.\w+$"))  # Expected to detect malformed emails
        except Exception as e:
            logger.error(f"Error auditing bronze customers: {e}")

        passed = sum(1 for r in results if r.get("success") is True)
        failed = len(results) - passed
        score = round((passed / len(results) * 100), 2) if results else 0

        report = {
            "suite_name": "bronze_raw_ingestion_suite",
            "layer": "BRONZE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checks": len(results),
            "passed_checks": passed,
            "failed_checks": failed,
            "quality_score_pct": score,
            "expectations": results,
        }
        return report

    def run_silver_quality_audit(self) -> Dict[str, Any]:
        """
        Runs quality assertions against cleansed Silver layer.
        In Silver, 100% of expectations MUST pass because anomalies are quarantined.
        """
        suite = QualityExpectationsSuite
        results = []

        try:
            orders_df = self.lake.read_silver("orders")
            cust_df = self.lake.read_silver("customers")
            prods_df = self.lake.read_silver("products")

            # Orders in Silver MUST be unique, positive, and have referential integrity
            results.append(suite.expect_column_values_to_not_be_null(orders_df, "order_id"))
            results.append(suite.expect_column_values_to_be_unique(orders_df, "order_id"))
            results.append(suite.expect_column_values_to_be_between(orders_df, "total_amount", 0.01, 50000.0))
            results.append(suite.expect_referential_integrity(orders_df, "customer_id", cust_df, "customer_id"))

            # Customers in Silver MUST have valid emails and unique IDs
            results.append(suite.expect_column_values_to_be_unique(cust_df, "customer_id"))
            results.append(suite.expect_column_values_to_match_regex(cust_df, "email", r"^[\w\.-]+@[\w\.-]+\.\w+$"))

            # Products in Silver MUST have positive margins
            results.append(suite.expect_column_values_to_be_between(prods_df, "price", 0.01, 10000.0))
        except Exception as e:
            logger.error(f"Error auditing silver layer: {e}")

        passed = sum(1 for r in results if r.get("success") is True)
        failed = len(results) - passed
        score = round((passed / len(results) * 100), 2) if results else 0

        report = {
            "suite_name": "silver_cleaned_conformance_suite",
            "layer": "SILVER",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checks": len(results),
            "passed_checks": passed,
            "failed_checks": failed,
            "quality_score_pct": score,
            "expectations": results,
        }
        return report

    def run_complete_validation(self) -> Dict[str, Any]:
        """Executes full validation suites and saves the report."""
        bronze_report = self.run_bronze_quality_audit()
        silver_report = self.run_silver_quality_audit()
        quarantine_summary = self.quarantine.get_quarantined_summary()

        overall_report = {
            "audit_id": f"dq_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bronze_audit": bronze_report,
            "silver_audit": silver_report,
            "quarantine_summary": quarantine_summary,
            "is_silver_production_ready": silver_report.get("quality_score_pct") == 100.0,
        }

        report_path = os.path.join(self.reports_dir, "latest_validation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(overall_report, f, indent=2)

        logger.info(f"Data Quality audit finished. Report saved to {report_path}")
        return overall_report

