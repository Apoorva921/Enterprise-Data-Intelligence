"""
Pydantic API Request & Response Schemas.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    environment: str
    timestamp: str
    components: Dict[str, str]


class KPISummaryResponse(BaseModel):
    total_orders: int
    total_revenue: float
    avg_order_value: float
    active_customers: int
    completion_rate: float
    payment_success_rate: float


class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_more: bool


class PipelineRunResponse(BaseModel):
    run_id: str
    dag_id: str
    execution_date: str
    state: str
    duration_seconds: float
    tasks_executed: int
    details: Optional[str] = None


class StreamingStatusResponse(BaseModel):
    status: str
    topics: Dict[str, int]
    consumer_groups: Dict[str, Any]
    dlq_message_count: int
    live_kafka_active: bool


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

