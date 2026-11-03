"""
FastAPI REST API Routes.
Exposes analytical warehouse models, pipeline orchestration,
data quality reports, and streaming telemetry to frontend dashboard.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, verify_admin_token
from backend.app.schemas.schemas import (
    HealthResponse,
    KPISummaryResponse,
    PaginatedResponse,
    PipelineRunResponse,
    StreamingStatusResponse,
    LoginRequest,
    LoginResponse,
)
from backend.app.services.data_service import DataService
from backend.app.services.pipeline_service import PipelineService
from backend.app.services.streaming_service import StreamingService
from data_quality.validation_runner import DataQualityValidationRunner

router = APIRouter(prefix="/api", tags=["Enterprise Data Platform"])

data_service = DataService()
pipeline_service = PipelineService()
streaming_service = StreamingService()


# ----------------------------------------------------------------------------
# 1. SYSTEM HEALTH & PROMETHEUS METRICS
# ----------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "UP",
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "warehouse": "HEALTHY",
            "storage_lake": "HEALTHY",
            "streaming_queue": "HEALTHY",
            "airflow_scheduler": "ACTIVE",
        },
    }


@router.get("/metrics")
def get_metrics(format: Optional[str] = Query("prometheus", description="'prometheus' or 'json'")):
    """Returns platform observability metrics in Prometheus exposition or JSON format."""
    kpis = data_service.get_kpis()
    streaming = streaming_service.get_status()
    total_stream_msgs = sum(streaming.get("topics", {}).values())

    if format == "json":
        return {
            "kpis": kpis,
            "streaming": streaming,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Prometheus exposition format
    metrics_text = f"""# HELP platform_total_orders Total orders processed in analytical warehouse
# TYPE platform_total_orders counter
platform_total_orders {kpis.get('total_orders', 0)}

# HELP platform_total_revenue Total gross revenue in USD
# TYPE platform_total_revenue gauge
platform_total_revenue {kpis.get('total_revenue', 0.0)}

# HELP platform_avg_order_value Average order value in USD
# TYPE platform_avg_order_value gauge
platform_avg_order_value {kpis.get('avg_order_value', 0.0)}

# HELP platform_active_customers Unique purchasing customers
# TYPE platform_active_customers gauge
platform_active_customers {kpis.get('active_customers', 0)}

# HELP platform_payment_success_rate Percentage of successful payments
# TYPE platform_payment_success_rate gauge
platform_payment_success_rate {kpis.get('payment_success_rate', 0.0)}

# HELP kafka_stream_total_messages Total messages in Kafka streaming topics
# TYPE kafka_stream_total_messages counter
kafka_stream_total_messages {total_stream_msgs}

# HELP kafka_dlq_messages Total poison messages routed to dead-letter queue
# TYPE kafka_dlq_messages counter
kafka_dlq_messages {streaming.get('dlq_message_count', 0)}
"""
    return PlainTextResponse(content=metrics_text)


# ----------------------------------------------------------------------------
# 2. AUTHENTICATION
# ----------------------------------------------------------------------------
@router.post("/auth/login", response_model=LoginResponse)
def login(creds: LoginRequest):
    """Generates an administrative JWT token for pipeline triggers."""
    if creds.username == settings.admin_username and creds.password == settings.admin_password:
        token = create_access_token({"sub": creds.username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer", "expires_in": 86400}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials. Use admin / adminpassword123",
    )


# ----------------------------------------------------------------------------
# 3. EXECUTIVE KPIS & REVENUE ANALYTICS
# ----------------------------------------------------------------------------
@router.get("/kpis", response_model=KPISummaryResponse)
def get_kpis():
    """Returns high-level business KPIs."""
    return data_service.get_kpis()


@router.get("/revenue")
def get_revenue(days: int = Query(30, ge=1, le=365)):
    """Returns daily revenue trends, order counts, and AOV for charting."""
    trends = data_service.get_revenue_trends(days=days)
    regional = data_service.get_regional_performance()
    category = data_service.get_category_performance()
    return {
        "daily_trends": trends,
        "regional_breakdown": regional,
        "category_breakdown": category,
    }


# ----------------------------------------------------------------------------
# 4. DATA CATALOG: ORDERS, CUSTOMERS, PRODUCTS
# ----------------------------------------------------------------------------
@router.get("/orders", response_model=PaginatedResponse)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
):
    """Paginated list of orders from Gold warehouse fact table."""
    items, total = data_service.get_orders_paginated(page=page, page_size=page_size, status=status, region=region)
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_more": page < total_pages,
    }


@router.get("/customers", response_model=PaginatedResponse)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    segment: Optional[str] = Query(None),
):
    """Paginated list of customers from SCD Type 2 dimension."""
    items, total = data_service.get_customers_paginated(page=page, page_size=page_size, segment=segment)
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_more": page < total_pages,
    }


@router.get("/products", response_model=PaginatedResponse)
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    category: Optional[str] = Query(None),
):
    """Paginated product catalog with pricing and margin metrics."""
    items, total = data_service.get_products_paginated(page=page, page_size=page_size, category=category)
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_more": page < total_pages,
    }


# ----------------------------------------------------------------------------
# 5. DATA PIPELINES (AIRFLOW MONITORING & TRIGGER)
# ----------------------------------------------------------------------------
@router.get("/pipelines")
def get_pipelines():
    """Lists all data pipelines, their schedules, and latest execution states."""
    return {
        "pipelines": pipeline_service.get_all_pipelines(),
        "recent_runs": pipeline_service.get_pipeline_runs(limit=20),
    }


@router.get("/pipelines/{dag_id}")
def get_pipeline_by_id(dag_id: str):
    """Returns details and history for a specific pipeline."""
    runs = [r for r in pipeline_service.get_pipeline_runs(limit=50) if r["dag_id"] == dag_id]
    return {
        "dag_id": dag_id,
        "total_runs": len(runs),
        "history": runs,
    }


@router.post("/pipelines/{dag_id}/trigger")
def trigger_pipeline(dag_id: str, admin: Dict[str, Any] = Depends(verify_admin_token)):
    """Triggers an Airflow DAG execution. Protected by admin JWT token."""
    res = pipeline_service.trigger_pipeline(dag_id)
    return res


# ----------------------------------------------------------------------------
# 6. STREAMING & KAFKA TELEMETRY
# ----------------------------------------------------------------------------
@router.get("/streaming/status", response_model=StreamingStatusResponse)
def get_streaming_status():
    """Real-time Kafka streaming statistics, topics, and consumer lag."""
    return streaming_service.get_status()


@router.get("/streaming/dlq")
def get_dlq_messages(limit: int = Query(20, ge=1, le=100)):
    """Retrieves rejected poison messages in Dead-Letter Queue."""
    return {
        "count": streaming_service.dlq.get_count(),
        "messages": streaming_service.get_dlq_sample(limit=limit),
    }


# ----------------------------------------------------------------------------
# 7. DATA QUALITY & QUARANTINE (GREAT EXPECTATIONS)
# ----------------------------------------------------------------------------
@router.get("/data-quality")
def get_data_quality():
    """Returns latest Great Expectations validation reports and quarantine audit."""
    report_file = os.path.abspath("data/data_quality/reports/latest_validation_report.json")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # If report file doesn't exist yet, run validation on-demand
    dq = DataQualityValidationRunner()
    return dq.run_complete_validation()
