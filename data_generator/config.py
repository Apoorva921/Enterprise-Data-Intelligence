"""
Configuration for Synthetic E-Commerce Data Generation.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class GeneratorConfig:
    num_customers: int = 5000
    num_products: int = 500
    num_orders: int = 100000
    num_sessions: int = 25000
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    
    # Anomaly / Quality Issue Injection Rates (for testing Great Expectations & Quarantine)
    anomaly_rate: float = 0.02  # 2% deliberate anomalies
    duplicate_rate: float = 0.01  # 1% duplicate order records
    null_customer_rate: float = 0.005  # 0.5% orphaned customer IDs
    negative_price_rate: float = 0.005  # 0.5% negative prices
    malformed_email_rate: float = 0.01  # 1% bad email syntax

    # Business Dimensions
    customer_segments: List[str] = field(
        default_factory=lambda: ["Consumer", "Small Business", "Enterprise", "VIP"]
    )
    product_categories: List[str] = field(
        default_factory=lambda: [
            "Electronics",
            "Fashion & Apparel",
            "Home & Living",
            "Beauty & Personal Care",
            "Sports & Outdoors",
            "Books & Digital Media",
        ]
    )
    geographical_regions: List[str] = field(
        default_factory=lambda: [
            "North America - East",
            "North America - West",
            "Europe - Western",
            "Europe - Northern",
            "Asia Pacific - East",
            "Asia Pacific - South",
            "Latin America",
        ]
    )
    payment_methods: List[str] = field(
        default_factory=lambda: [
            "Credit Card",
            "PayPal",
            "Apple Pay",
            "Bank Transfer",
            "Cryptocurrency",
        ]
    )
    order_statuses: List[str] = field(
        default_factory=lambda: [
            "COMPLETED",
            "COMPLETED",
            "COMPLETED",  # weighted completed
            "PENDING",
            "PROCESSING",
            "SHIPPED",
            "CANCELLED",
            "REFUNDED",
        ]
    )
    event_types: List[str] = field(
        default_factory=lambda: [
            "page_view",
            "product_view",
            "add_to_cart",
            "remove_from_cart",
            "search",
            "checkout_start",
            "checkout_complete",
        ]
    )
    device_types: List[str] = field(
        default_factory=lambda: ["desktop", "mobile_ios", "mobile_android", "tablet"]
    )

