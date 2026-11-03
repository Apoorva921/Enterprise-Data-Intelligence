"""
Unit Tests for Synthetic Data Generator.
"""
import pytest
from data_generator.config import GeneratorConfig
from data_generator.generator import ECommerceDataGenerator


def test_generator_config():
    config = GeneratorConfig(num_orders=500, num_customers=50)
    assert config.num_orders == 500
    assert config.num_customers == 50
    assert len(config.customer_segments) == 4
    assert len(config.product_categories) == 6


def test_generate_customers():
    config = GeneratorConfig(num_customers=100)
    gen = ECommerceDataGenerator(config=config, seed=42)
    df = gen.generate_customers()
    assert len(df) == 100
    assert "customer_id" in df.columns
    assert "segment" in df.columns
    assert "region" in df.columns
    assert df["is_simulated"].all()


def test_generate_orders_and_anomalies():
    config = GeneratorConfig(num_orders=200, num_customers=30, duplicate_rate=0.05, negative_price_rate=0.05)
    gen = ECommerceDataGenerator(config=config, seed=42)
    orders_df, items_df = gen.generate_orders_and_items()
    
    # Verify orders and duplicates
    assert len(orders_df) >= 200
    assert len(items_df) >= 200
    
    # Verify presence of injected intentional anomalies
    has_duplicates = orders_df["order_id"].duplicated().any()
    assert has_duplicates, "Expected intentional duplicates in orders"

    has_negatives = (orders_df["total_amount"] < 0).any()
    assert has_negatives, "Expected intentional negative order values for DQ testing"

