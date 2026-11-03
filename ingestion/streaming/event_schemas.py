"""
Streaming Event Schemas for Kafka Ingestion.
Enforces strict schema validation for orders, payments, customer clickstream, and inventory updates.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class StreamOrderEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_ord_{datetime.now(timezone.utc).timestamp()}")
    order_id: str
    customer_id: str
    order_date: str
    status: str
    total_amount: float
    shipping_region: str
    channel: str
    items_count: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("total_amount")
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError(f"Order total_amount cannot be negative: {v}")
        return v


class StreamPaymentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_pay_{datetime.now(timezone.utc).timestamp()}")
    payment_id: str
    order_id: str
    customer_id: str
    payment_method: str
    payment_status: str  # SUCCESS, FAILED, PENDING
    amount: float
    currency: str = "USD"
    payment_date: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("payment_status")
    def validate_status(cls, v):
        if v not in ["SUCCESS", "FAILED", "PENDING"]:
            raise ValueError(f"Invalid payment status: {v}")
        return v


class StreamCustomerEvent(BaseModel):
    event_id: str
    session_id: str
    customer_id: Optional[str] = None
    event_type: str
    page_url: str
    device_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StreamInventoryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_inv_{datetime.now(timezone.utc).timestamp()}")
    product_id: str
    warehouse_id: str
    change_type: str  # RESTOCK, PURCHASE_DEDUCTION, RETURN_RESTOCK
    quantity_changed: int
    stock_level_after: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

