"""
Medallion Architecture: Silver to Gold Star Schema Pipeline.
Constructs analytics-ready Star Schema, SCD Type 2 dimensions,
fact tables, and curated data marts for BI and API consumption.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import pandas as pd
import numpy as np

from storage.lake_storage import LakeStorage

logger = logging.getLogger("SilverToGold")


class SilverToGoldPipeline:
    def __init__(self, lake_storage: LakeStorage = None):
        self.lake = lake_storage or LakeStorage()
        self.summary_stats: Dict[str, Any] = {}

    def build_dim_dates(self, start_date: str = "2023-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
        """Generates comprehensive Date Dimension table."""
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        dim_dates = pd.DataFrame({
            "date_key": date_range.strftime("%Y%m%d").astype(int),
            "full_date": date_range.strftime("%Y-%m-%d"),
            "day_of_month": date_range.day,
            "day_name": date_range.day_name(),
            "day_of_week": date_range.dayofweek + 1,
            "is_weekend": date_range.dayofweek >= 5,
            "week_of_year": date_range.isocalendar().week.astype(int),
            "month": date_range.month,
            "month_name": date_range.month_name(),
            "quarter": date_range.quarter,
            "year": date_range.year,
        })
        self.lake.write_gold("dim_dates", dim_dates)
        return dim_dates

    def build_dim_customers_scd2(self) -> pd.DataFrame:
        """
        Builds Customer Dimension with SCD Type 2 history tracking.
        Tracks effective dates, expiration dates, and current record flag.
        """
        df = self.lake.read_silver("customers")
        
        # Primary current version
        records = []
        for idx, row in df.iterrows():
            c_id = row["customer_id"]
            # Current active record
            records.append({
                "customer_key": f"{c_id}_V1",
                "customer_id": c_id,
                "full_name": f"{row['first_name']} {row['last_name']}",
                "email": row["email"],
                "segment": row["segment"],
                "region": row["region"],
                "city": row["city"],
                "state": row["state"],
                "effective_date": "2023-01-01",
                "end_date": "9999-12-31",
                "is_current": True,
            })

        # Inject simulated historical SCD2 tier changes for 5% of customers
        sample_scd2 = df.sample(frac=0.05, random_state=42)
        for idx, row in sample_scd2.iterrows():
            c_id = row["customer_id"]
            # Retire version 1
            for r in records:
                if r["customer_id"] == c_id:
                    r["end_date"] = "2024-01-01"
                    r["is_current"] = False
                    break
            # Add version 2 with upgraded VIP or Enterprise tier
            new_segment = "VIP" if row["segment"] != "VIP" else "Enterprise"
            records.append({
                "customer_key": f"{c_id}_V2",
                "customer_id": c_id,
                "full_name": f"{row['first_name']} {row['last_name']}",
                "email": row["email"],
                "segment": new_segment,
                "region": row["region"],
                "city": row["city"],
                "state": row["state"],
                "effective_date": "2024-01-01",
                "end_date": "9999-12-31",
                "is_current": True,
            })

        dim_customers = pd.DataFrame(records)
        self.lake.write_gold("dim_customers", dim_customers)
        return dim_customers

    def build_dim_products(self) -> pd.DataFrame:
        """Builds Product Dimension with profit margins."""
        df = self.lake.read_silver("products")
        dim_products = pd.DataFrame({
            "product_key": df["product_id"],
            "product_id": df["product_id"],
            "sku": df["sku"],
            "name": df["name"],
            "category": df["category"],
            "unit_price": df["price"],
            "unit_cost": df["cost"],
            "gross_margin_pct": df["gross_margin_pct"],
            "supplier_id": df["supplier_id"],
        })
        self.lake.write_gold("dim_products", dim_products)
        return dim_products

    def build_fact_orders(self) -> pd.DataFrame:
        """Builds Fact Orders with date_key and surrogate customer reference."""
        orders_df = self.lake.read_silver("orders")
        
        # Link to date_key
        order_dates = pd.to_datetime(orders_df["order_date"])
        date_keys = order_dates.dt.strftime("%Y%m%d").astype(int)

        fact_orders = pd.DataFrame({
            "order_key": orders_df["order_id"],
            "order_id": orders_df["order_id"],
            "customer_id": orders_df["customer_id"],
            "date_key": date_keys,
            "order_date": orders_df["order_date"],
            "status": orders_df["status"],
            "subtotal": orders_df["subtotal"],
            "shipping_fee": orders_df["shipping_fee"],
            "tax_amount": orders_df["tax_amount"],
            "discount_amount": orders_df["discount_amount"],
            "total_amount": orders_df["total_amount"],
            "shipping_region": orders_df["shipping_region"],
            "channel": orders_df["channel"],
        })
        self.lake.write_gold("fact_orders", fact_orders)
        return fact_orders

    def build_fact_order_items(self) -> pd.DataFrame:
        """Builds Fact Order Items with margin calculations."""
        items_df = self.lake.read_silver("order_items")
        prods_df = self.lake.read_silver("products")
        
        prod_cost_map = dict(zip(prods_df["product_id"], prods_df["cost"]))
        items_df["unit_cost"] = items_df["product_id"].map(prod_cost_map).fillna(0.0)
        items_df["total_cost"] = (items_df["unit_cost"] * items_df["quantity"]).round(2)
        items_df["gross_profit"] = (items_df["total_price"] - items_df["total_cost"]).round(2)

        fact_items = pd.DataFrame({
            "order_item_key": items_df["order_item_id"],
            "order_id": items_df["order_id"],
            "product_id": items_df["product_id"],
            "quantity": items_df["quantity"],
            "unit_price": items_df["unit_price"],
            "unit_cost": items_df["unit_cost"],
            "total_price": items_df["total_price"],
            "total_cost": items_df["total_cost"],
            "gross_profit": items_df["gross_profit"],
        })
        self.lake.write_gold("fact_order_items", fact_items)
        return fact_items

    def build_fact_payments(self) -> pd.DataFrame:
        """Builds Fact Payments table enforcing referential integrity with fact_orders."""
        pay_df = self.lake.read_silver("payments")
        orders_df = self.lake.read_gold("fact_orders")
        valid_orders = set(orders_df["order_id"].unique())
        
        # Enforce foreign key relationship
        clean_pay = pay_df[pay_df["order_id"].isin(valid_orders)].copy()
        pay_dates = pd.to_datetime(clean_pay["payment_date"])
        date_keys = pay_dates.dt.strftime("%Y%m%d").astype(int)

        fact_payments = pd.DataFrame({
            "payment_key": clean_pay["payment_id"],
            "order_id": clean_pay["order_id"],
            "customer_id": clean_pay["customer_id"],
            "date_key": date_keys,
            "payment_method": clean_pay["payment_method"],
            "payment_status": clean_pay["payment_status"],
            "amount": clean_pay["amount"],
            "payment_date": clean_pay["payment_date"],
            "is_successful": clean_pay["payment_status"] == "SUCCESS",
        })
        self.lake.write_gold("fact_payments", fact_payments)
        return fact_payments

    def build_analytics_marts(self):
        """Constructs aggregated business intelligence data marts."""
        fact_orders = self.lake.read_gold("fact_orders")
        fact_items = self.lake.read_gold("fact_order_items")
        dim_cust = self.lake.read_gold("dim_customers")

        # 1. Daily Revenue Mart
        fact_orders["order_day"] = pd.to_datetime(fact_orders["order_date"]).dt.strftime("%Y-%m-%d")
        daily_rev = fact_orders.groupby("order_day").agg(
            total_orders=("order_id", "count"),
            completed_orders=("status", lambda s: (s == "COMPLETED").sum()),
            total_gross_revenue=("total_amount", "sum"),
            avg_order_value=("total_amount", "mean"),
        ).reset_index()
        daily_rev["total_gross_revenue"] = daily_rev["total_gross_revenue"].round(2)
        daily_rev["avg_order_value"] = daily_rev["avg_order_value"].round(2)
        self.lake.write_gold("mart_daily_revenue", daily_rev)

        # 2. Customer Lifetime Value (LTV) Mart
        cust_orders = fact_orders.groupby("customer_id").agg(
            lifetime_orders=("order_id", "count"),
            lifetime_spend=("total_amount", "sum"),
            first_order_date=("order_date", "min"),
            latest_order_date=("order_date", "max"),
        ).reset_index()
        cust_orders["lifetime_spend"] = cust_orders["lifetime_spend"].round(2)
        cust_orders["avg_spend_per_order"] = (cust_orders["lifetime_spend"] / cust_orders["lifetime_orders"]).round(2)
        self.lake.write_gold("mart_customer_lifetime_value", cust_orders)

        # 3. Product Performance Mart
        prod_perf = fact_items.groupby("product_id").agg(
            units_sold=("quantity", "sum"),
            gross_revenue=("total_price", "sum"),
            gross_profit=("gross_profit", "sum"),
        ).reset_index()
        prod_perf["gross_revenue"] = prod_perf["gross_revenue"].round(2)
        prod_perf["gross_profit"] = prod_perf["gross_profit"].round(2)
        prod_perf["profit_margin_pct"] = ((prod_perf["gross_profit"] / prod_perf["gross_revenue"]) * 100).round(2)
        self.lake.write_gold("mart_product_performance", prod_perf)

    def run_all(self) -> Dict[str, Any]:
        """Runs the entire Silver to Gold transformation."""
        logger.info("Executing Silver -> Gold Star Schema modeling...")
        self.build_dim_dates()
        self.build_dim_customers_scd2()
        self.build_dim_products()
        self.build_fact_orders()
        self.build_fact_order_items()
        self.build_fact_payments()
        self.build_analytics_marts()
        logger.info("Silver -> Gold pipeline completed successfully.")
        return {"status": "SUCCESS"}
