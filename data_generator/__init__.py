"""
Data Generator Package for Enterprise E-Commerce Data Platform.
Simulates realistic e-commerce transactions across customers, products, orders,
payments, refunds, inventory, and clickstream events.
"""
from .generator import ECommerceDataGenerator
from .config import GeneratorConfig

__all__ = ["ECommerceDataGenerator", "GeneratorConfig"]

