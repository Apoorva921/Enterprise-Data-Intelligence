"""
Pydantic Schemas for Synthetic E-Commerce Entities.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CustomerSchema(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    region: str
    segment: str
    account_status: str = "ACTIVE"
    created_at: str
    updated_at: str
    is_simulated: bool = True


class ProductSchema(BaseModel):
    product_id: str
    sku: str
    name: str
    category: str
    price: float
    cost: float
    supplier_id: str
    is_active: bool = True
    created_at: str
    is_simulated: bool = True


class OrderItemSchema(BaseModel):
    order_item_id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    total_price: float
    discount_amount: float = 0.0
    created_at: str
    is_simulated: bool = True


class OrderSchema(BaseModel):
    order_id: str
    customer_id: str
    order_date: str
    status: str
    subtotal: float
    shipping_fee: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    shipping_region: str
    channel: str
    created_at: str
    updated_at: str
    is_simulated: bool = True


class PaymentSchema(BaseModel):
    payment_id: str
    order_id: str
    customer_id: str
    payment_method: str
    payment_status: str  # SUCCESS, FAILED, PENDING
    transaction_id: str
    amount: float
    currency: str = "USD"
    payment_date: str
    error_message: Optional[str] = None
    is_simulated: bool = True


class RefundSchema(BaseModel):
    refund_id: str
    order_id: str
    payment_id: str
    refund_amount: float
    refund_reason: str
    status: str  # PROCESSED, REJECTED
    refund_date: str
    is_simulated: bool = True


class InventorySchema(BaseModel):
    inventory_id: str
    product_id: str
    warehouse_id: str
    stock_level: int
    reserved_stock: int
    reorder_point: int
    unit_cost: float
    last_restocked_at: str
    is_simulated: bool = True


class CustomerSessionSchema(BaseModel):
    session_id: str
    customer_id: Optional[str]
    session_start: str
    session_end: str
    duration_seconds: int
    platform: str
    device_type: str
    ip_address: str
    referrer: str
    is_simulated: bool = True


class WebsiteEventSchema(BaseModel):
    event_id: str
    session_id: str
    customer_id: Optional[str]
    event_type: str
    page_url: str
    timestamp: str
    device_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True
