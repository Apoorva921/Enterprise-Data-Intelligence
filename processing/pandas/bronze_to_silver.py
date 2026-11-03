"""
Medallion Architecture: Bronze to Silver Pipeline.
Cleans, normalizes, validates schemas, enforces UTC timestamps,
deduplicates records, and routes invalid records to the Quarantine Manager.
"""
import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import pandas as pd

from storage.lake_storage import LakeStorage

logger = logging.getLogger("BronzeToSilver")


class BronzeToSilverPipeline:
    def __init__(self, lake_storage: LakeStorage = None):
        self.lake = lake_storage or LakeStorage()
        self.summary_stats: Dict[str, Any] = {}

    def process_customers(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans customers, validates email format, and quarantines malformed records."""
        df = self.lake.read_bronze("customers")
        initial_count = len(df)

        # Email regex validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        valid_email_mask = df["email"].str.match(email_regex, na=False)
        
        # Valid records
        clean_df = df[valid_email_mask].copy()
        clean_df = clean_df.drop_duplicates(subset=["customer_id"])
        
        # Quarantine invalid emails
        bad_df = df[~valid_email_mask].copy()
        if not bad_df.empty:
            self.lake.write_quarantine("customers", bad_df, ["Malformed email address syntax"] * len(bad_df))

        # Standardize timestamps
        clean_df["created_at"] = pd.to_datetime(clean_df["created_at"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        clean_df["updated_at"] = pd.to_datetime(clean_df["updated_at"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()

        self.lake.write_silver("customers", clean_df)
        self.summary_stats["customers"] = {
            "initial": initial_count,
            "silver": len(clean_df),
            "quarantined": len(bad_df),
        }
        return clean_df, bad_df

    def process_products(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans products, enforces non-negative price/cost, and calculates initial margin."""
        df = self.lake.read_bronze("products")
        initial_count = len(df)

        valid_mask = (df["price"] > 0) & (df["cost"] > 0) & (df["price"] >= df["cost"])
        clean_df = df[valid_mask].copy()
        clean_df = clean_df.drop_duplicates(subset=["product_id"])

        bad_df = df[~valid_mask].copy()
        if not bad_df.empty:
            self.lake.write_quarantine("products", bad_df, ["Invalid price or cost <= 0 or cost > price"] * len(bad_df))

        clean_df["gross_margin_pct"] = ((clean_df["price"] - clean_df["cost"]) / clean_df["price"] * 100).round(2)
        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()

        self.lake.write_silver("products", clean_df)
        self.summary_stats["products"] = {
            "initial": initial_count,
            "silver": len(clean_df),
            "quarantined": len(bad_df),
        }
        return clean_df, bad_df

    def process_orders(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Cleans orders:
        - Deduplicates by order_id
        - Quarantines negative total_amounts
        - Quarantines orphaned customer_ids
        - Standardizes order_date to UTC and extracts year_month partition
        """
        df = self.lake.read_bronze("orders")
        initial_count = len(df)

        # 1. Deduplication
        dedup_df = df.drop_duplicates(subset=["order_id"], keep="first")
        duplicate_count = initial_count - len(dedup_df)

        # 2. Check customer referential integrity
        customers_df = self.lake.read_silver("customers")
        valid_cust_ids = set(customers_df["customer_id"].unique())
        
        valid_amount_mask = dedup_df["total_amount"] > 0
        valid_cust_mask = dedup_df["customer_id"].isin(valid_cust_ids)

        clean_mask = valid_amount_mask & valid_cust_mask
        clean_df = dedup_df[clean_mask].copy()
        bad_df = dedup_df[~clean_mask].copy()

        if not bad_df.empty:
            reasons = []
            for _, r in bad_df.iterrows():
                r_reasons = []
                if r["total_amount"] <= 0:
                    r_reasons.append("Negative or zero total_amount")
                if r["customer_id"] not in valid_cust_ids:
                    r_reasons.append(f"Orphaned customer_id '{r['customer_id']}'")
                reasons.append("; ".join(r_reasons))
            self.lake.write_quarantine("orders", bad_df, reasons)

        # Normalization and partition column
        clean_df["order_date"] = pd.to_datetime(clean_df["order_date"], utc=True)
        clean_df["order_year_month"] = clean_df["order_date"].dt.strftime("%Y-%m")
        clean_df["order_date"] = clean_df["order_date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()

        self.lake.write_silver("orders", clean_df, partition_col="order_year_month")
        self.summary_stats["orders"] = {
            "initial": initial_count,
            "duplicates_removed": duplicate_count,
            "silver": len(clean_df),
            "quarantined": len(bad_df),
        }
        return clean_df, bad_df

    def process_order_items(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans and validates order items."""
        df = self.lake.read_bronze("order_items")
        initial_count = len(df)

        valid_mask = (df["quantity"] > 0) & (df["unit_price"] >= 0) & (df["total_price"] >= 0)
        clean_df = df[valid_mask].copy()
        clean_df = clean_df.drop_duplicates(subset=["order_item_id"])

        bad_df = df[~valid_mask].copy()
        if not bad_df.empty:
            self.lake.write_quarantine("order_items", bad_df, ["Invalid item quantity or price"] * len(bad_df))

        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()
        self.lake.write_silver("order_items", clean_df)
        self.summary_stats["order_items"] = {
            "initial": initial_count,
            "silver": len(clean_df),
            "quarantined": len(bad_df),
        }
        return clean_df, bad_df

    def process_payments(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans payment transactions."""
        df = self.lake.read_bronze("payments")
        initial_count = len(df)

        clean_df = df.drop_duplicates(subset=["payment_id"]).copy()
        clean_df["payment_date"] = pd.to_datetime(clean_df["payment_date"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()

        self.lake.write_silver("payments", clean_df)
        self.summary_stats["payments"] = {
            "initial": initial_count,
            "silver": len(clean_df),
            "quarantined": 0,
        }
        return clean_df, pd.DataFrame()

    def process_inventory(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cleans inventory snapshots."""
        df = self.lake.read_bronze("inventory")
        clean_df = df.drop_duplicates(subset=["inventory_id"]).copy()
        clean_df["_silver_processed_at"] = datetime.now(timezone.utc).isoformat()
        self.lake.write_silver("inventory", clean_df)
        self.summary_stats["inventory"] = {
            "initial": len(df),
            "silver": len(clean_df),
            "quarantined": 0,
        }
        return clean_df, pd.DataFrame()

    def run_all(self) -> Dict[str, Any]:
        """Runs complete Bronze to Silver Medallion ETL."""
        logger.info("Executing Bronze -> Silver Medallion pipeline...")
        self.process_customers()
        self.process_products()
        self.process_orders()
        self.process_order_items()
        self.process_payments()
        self.process_inventory()
        logger.info("Bronze -> Silver pipeline completed successfully.")
        return self.summary_stats

