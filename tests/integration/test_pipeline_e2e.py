"""
End-to-End Integration Tests for Medallion Pipelines & Warehouse.
"""
import pytest
from warehouse.warehouse_manager import WarehouseManager
from dbt.dbt_runner import DBTRunner


def test_warehouse_kpis_and_views(warehouse):
    kpis = warehouse.get_kpi_summary()
    assert kpis["total_orders"] > 0
    assert kpis["total_revenue"] > 0
    assert kpis["active_customers"] > 0
    assert kpis["payment_success_rate"] > 0


def test_dbt_models_and_tests_pass(warehouse):
    runner = DBTRunner(warehouse=warehouse)
    run_res = runner.run_models()
    assert run_res["status"] == "SUCCESS"
    assert run_res["models_run"] >= 5

    test_res = runner.run_tests()
    assert test_res["passed"] == 5
    assert test_res["failed"] == 0
