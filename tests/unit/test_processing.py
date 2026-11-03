"""
Unit Tests for Medallion Processing & SCD Type 2 Modeling.
"""
import pytest
import pandas as pd
from storage.lake_storage import LakeStorage
from processing.pandas.bronze_to_silver import BronzeToSilverPipeline
from processing.pandas.silver_to_gold import SilverToGoldPipeline


def test_medallion_cleansing_and_quarantine(lake_storage):
    # Verify Bronze to Silver cleans orders and isolates anomalies
    p = BronzeToSilverPipeline(lake_storage=lake_storage)
    clean_orders, bad_orders = p.process_orders()

    assert not clean_orders.empty
    assert (clean_orders["total_amount"] > 0).all(), "Silver orders must not have negative totals"
    assert clean_orders["order_id"].is_unique, "Silver orders must be deduplicated"


def test_scd2_customer_dimension(lake_storage):
    # Verify SCD Type 2 logic
    gold_pipe = SilverToGoldPipeline(lake_storage=lake_storage)
    dim_cust = gold_pipe.build_dim_customers_scd2()

    assert "customer_key" in dim_cust.columns
    assert "effective_date" in dim_cust.columns
    assert "end_date" in dim_cust.columns
    assert "is_current" in dim_cust.columns

    # Verify that retired records have is_current == False
    retired = dim_cust[dim_cust["is_current"] == False]
    assert len(retired) > 0, "Expected historical SCD2 retired versions"
    assert (retired["end_date"] != "9999-12-31").all()
