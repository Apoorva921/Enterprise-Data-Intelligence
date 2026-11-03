"""
Data Quality & Reliability Tests using Great Expectations Suite.
"""
import pytest
from data_quality.validation_runner import DataQualityValidationRunner


def test_data_quality_validation_suite():
    runner = DataQualityValidationRunner()
    report = runner.run_complete_validation()

    # 1. Verify Bronze correctly detected injected deliberate anomalies
    bronze = report["bronze_audit"]
    assert bronze["failed_checks"] > 0, "Bronze must detect deliberate duplicates and negative amounts"

    # 2. Verify Silver is 100% conforming and production-ready
    silver = report["silver_audit"]
    assert silver["quality_score_pct"] == 100.0, "Silver layer must have 100% conformance score"
    assert silver["failed_checks"] == 0

    # 3. Verify Quarantine Manager populated
    quarantine = report["quarantine_summary"]
    assert quarantine["total_quarantined_records"] > 0
    assert "orders" in quarantine["entities"]
    assert "customers" in quarantine["entities"]
