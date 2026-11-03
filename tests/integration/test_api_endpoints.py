"""
Integration Tests for FastAPI REST Endpoints & Route Handlers.
Validates schemas, responses, business logic, pagination, and security.
"""
import pytest
from backend.app.api import routes
from backend.app.schemas.schemas import LoginRequest


def test_health_endpoint():
    res = routes.get_health()
    assert res["status"] == "UP"
    assert "components" in res
    assert res["components"]["warehouse"] == "HEALTHY"


def test_metrics_prometheus_and_json():
    res_prom = routes.get_metrics(format="prometheus")
    assert "platform_total_orders" in res_prom.body.decode()

    res_json = routes.get_metrics(format="json")
    assert "kpis" in res_json
    assert res_json["kpis"]["total_orders"] > 0


def test_kpi_summary_endpoint():
    res = routes.get_kpis()
    assert res["total_orders"] > 0
    assert res["total_revenue"] > 0
    assert res["active_customers"] > 0
    assert res["payment_success_rate"] > 0


def test_orders_paginated():
    res = routes.get_orders(page=1, page_size=10)
    assert len(res["items"]) == 10
    assert res["total"] > 0
    assert res["page"] == 1
    assert res["page_size"] == 10


def test_customers_paginated():
    res = routes.get_customers(page=1, page_size=15)
    assert len(res["items"]) == 15
    assert res["total"] > 0


def test_products_paginated():
    res = routes.get_products(page=1, page_size=10)
    assert len(res["items"]) == 10
    assert res["total"] > 0


def test_pipelines_catalog():
    res = routes.get_pipelines()
    assert len(res["pipelines"]) == 7
    pipeline_ids = [p["id"] for p in res["pipelines"]]
    assert "daily_batch_ingestion_dag" in pipeline_ids
    assert "warehouse_transformation_dag" in pipeline_ids


def test_streaming_status():
    res = routes.get_streaming_status()
    assert res["status"] == "HEALTHY"
    assert "topics" in res
    assert "orders" in res["topics"]


def test_data_quality_report():
    res = routes.get_data_quality()
    assert "silver_audit" in res
    assert res["silver_audit"]["quality_score_pct"] == 100.0


def test_admin_auth_and_trigger():
    # Login to get JWT
    login_req = LoginRequest(username="admin", password="adminpassword123")
    login_res = routes.login(login_req)
    assert "access_token" in login_res
    assert login_res["token_type"] == "bearer"

    # Trigger with valid admin authentication context
    trig_res = routes.trigger_pipeline(
        dag_id="customer_processing_dag",
        admin={"sub": "admin", "role": "admin"}
    )
    assert trig_res["state"] == "SUCCESS"
    assert trig_res["dag_id"] == "customer_processing_dag"
