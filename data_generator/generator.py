"""
High-Performance Synthetic E-Commerce Data Generator.
Produces realistic historical datasets across 9 business entities with
deliberate anomalies for data quality testing.
"""
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from faker import Faker

from .config import GeneratorConfig


class ECommerceDataGenerator:
    def __init__(self, config: GeneratorConfig = None, seed: int = 42):
        self.config = config or GeneratorConfig()
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        
        self.customers_df: pd.DataFrame = None
        self.products_df: pd.DataFrame = None
        self.orders_df: pd.DataFrame = None
        self.order_items_df: pd.DataFrame = None
        self.payments_df: pd.DataFrame = None
        self.refunds_df: pd.DataFrame = None
        self.inventory_df: pd.DataFrame = None
        self.sessions_df: pd.DataFrame = None
        self.events_df: pd.DataFrame = None

    def _random_dates(self, start_date_str: str, end_date_str: str, n: int) -> np.ndarray:
        start_ts = pd.Timestamp(start_date_str).value // 10**9
        end_ts = pd.Timestamp(end_date_str).value // 10**9
        random_ts = np.random.randint(start_ts, end_ts, size=n)
        return pd.to_datetime(random_ts, unit="s")

    def generate_customers(self) -> pd.DataFrame:
        """Generates synthetic customer records with segment distribution and realistic regions."""
        n = self.config.num_customers
        customer_ids = [f"CUST-{100000 + i}" for i in range(n)]
        
        segments = np.random.choice(
            self.config.customer_segments,
            size=n,
            p=[0.60, 0.25, 0.10, 0.05],  # Consumer 60%, Small Biz 25%, Enterprise 10%, VIP 5%
        )
        regions = np.random.choice(self.config.geographical_regions, size=n)
        created_dates = self._random_dates(self.config.start_date, "2023-06-30", n)
        
        first_names = [self.fake.first_name() for _ in range(n)]
        last_names = [self.fake.last_name() for _ in range(n)]
        emails = [f"{fn.lower()}.{ln.lower()}_{i}@{self.fake.free_email_domain()}" for i, (fn, ln) in enumerate(zip(first_names, last_names))]
        
        # Inject deliberate malformed emails for DQ testing
        malformed_count = int(n * self.config.malformed_email_rate)
        for idx in np.random.choice(n, malformed_count, replace=False):
            emails[idx] = f"invalid-email-no-at-sign_{idx}.com"

        df = pd.DataFrame({
            "customer_id": customer_ids,
            "first_name": first_names,
            "last_name": last_names,
            "email": emails,
            "phone": [self.fake.phone_number() for _ in range(n)],
            "city": [self.fake.city() for _ in range(n)],
            "state": [self.fake.state_abbr() for _ in range(n)],
            "postal_code": [self.fake.postcode() for _ in range(n)],
            "country": "USA",
            "region": regions,
            "segment": segments,
            "account_status": np.random.choice(["ACTIVE", "SUSPENDED", "INACTIVE"], size=n, p=[0.92, 0.05, 0.03]),
            "created_at": created_dates,
            "updated_at": created_dates + pd.to_timedelta(np.random.randint(1, 100, size=n), unit="D"),
            "is_simulated": True,
        })
        self.customers_df = df
        return df

    def generate_products(self) -> pd.DataFrame:
        """Generates realistic catalog products with pricing margins."""
        n = self.config.num_products
        product_ids = [f"PROD-{20000 + i}" for i in range(n)]
        categories = np.random.choice(self.config.product_categories, size=n)
        
        base_prices = {
            "Electronics": (49.99, 1299.99),
            "Fashion & Apparel": (14.99, 299.99),
            "Home & Living": (19.99, 599.99),
            "Beauty & Personal Care": (9.99, 149.99),
            "Sports & Outdoors": (24.99, 499.99),
            "Books & Digital Media": (7.99, 79.99),
        }
        
        prices = []
        costs = []
        for cat in categories:
            min_p, max_p = base_prices[cat]
            price = round(random.uniform(min_p, max_p), 2)
            cost = round(price * random.uniform(0.40, 0.75), 2)
            prices.append(price)
            costs.append(cost)

        product_names = [f"{self.fake.word().capitalize()} {self.fake.bs().split()[0].capitalize()} Edition" for _ in range(n)]
        skus = [f"SKU-{cat[:3].upper()}-{1000 + i}" for i, cat in enumerate(categories)]
        supplier_ids = [f"SUPP-{random.randint(100, 150)}" for _ in range(n)]

        df = pd.DataFrame({
            "product_id": product_ids,
            "sku": skus,
            "name": product_names,
            "category": categories,
            "price": prices,
            "cost": costs,
            "supplier_id": supplier_ids,
            "is_active": True,
            "created_at": pd.Timestamp(self.config.start_date),
            "is_simulated": True,
        })
        self.products_df = df
        return df

    def generate_orders_and_items(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates orders and detailed order items with intentional anomalies."""
        if self.customers_df is None:
            self.generate_customers()
        if self.products_df is None:
            self.generate_products()

        n_orders = self.config.num_orders
        order_ids = [f"ORD-{500000 + i}" for i in range(n_orders)]
        order_dates = self._random_dates(self.config.start_date, self.config.end_date, n_orders)
        
        # Select customer IDs (with some orphaned customer IDs injected for DQ checks)
        cust_pool = self.customers_df["customer_id"].tolist()
        cust_choices = np.random.choice(cust_pool, size=n_orders)
        
        # Inject orphaned customer IDs
        null_cust_count = int(n_orders * self.config.null_customer_rate)
        for idx in np.random.choice(n_orders, null_cust_count, replace=False):
            cust_choices[idx] = "CUST-NONEXISTENT"

        statuses = np.random.choice(self.config.order_statuses, size=n_orders)
        shipping_regions = np.random.choice(self.config.geographical_regions, size=n_orders)
        channels = np.random.choice(["Web", "Mobile App", "Affiliate", "Direct Marketing"], size=n_orders, p=[0.45, 0.40, 0.10, 0.05])

        # Generate order items
        # Average 1 to 4 items per order
        items_per_order = np.random.choice([1, 2, 3, 4], size=n_orders, p=[0.55, 0.25, 0.15, 0.05])
        total_items = int(np.sum(items_per_order))
        
        prod_pool = self.products_df["product_id"].tolist()
        prod_price_map = dict(zip(self.products_df["product_id"], self.products_df["price"]))
        
        order_item_ids = [f"ITEM-{800000 + j}" for j in range(total_items)]
        item_order_ids = []
        item_product_ids = []
        item_quantities = []
        item_unit_prices = []
        item_totals = []
        item_discounts = []
        item_dates = []

        cur_item_idx = 0
        order_subtotals = np.zeros(n_orders)
        
        for i in range(n_orders):
            n_items = items_per_order[i]
            o_id = order_ids[i]
            o_date = order_dates[i]
            chosen_prods = random.sample(prod_pool, min(n_items, len(prod_pool)))
            
            subtotal = 0.0
            for prod_id in chosen_prods:
                qty = random.choices([1, 2, 3, 5], weights=[0.75, 0.18, 0.05, 0.02])[0]
                unit_price = prod_price_map[prod_id]
                discount = round(unit_price * qty * (0.1 if random.random() < 0.15 else 0.0), 2)
                item_total = round(unit_price * qty - discount, 2)
                
                item_order_ids.append(o_id)
                item_product_ids.append(prod_id)
                item_quantities.append(qty)
                item_unit_prices.append(unit_price)
                item_discounts.append(discount)
                item_totals.append(item_total)
                item_dates.append(o_date)
                
                subtotal += item_total
                cur_item_idx += 1
            
            order_subtotals[i] = round(subtotal, 2)

        # Shipping fee and tax
        shipping_fees = np.where(order_subtotals > 75.0, 0.0, 9.99)
        tax_amounts = np.round(order_subtotals * 0.0825, 2)
        discount_amounts = np.zeros(n_orders)
        total_amounts = np.round(order_subtotals + shipping_fees + tax_amounts - discount_amounts, 2)

        # Inject deliberate negative / malformed totals for DQ quarantine
        neg_count = int(n_orders * self.config.negative_price_rate)
        for idx in np.random.choice(n_orders, neg_count, replace=False):
            total_amounts[idx] = -round(abs(total_amounts[idx]), 2)

        orders_df = pd.DataFrame({
            "order_id": order_ids,
            "customer_id": cust_choices,
            "order_date": order_dates,
            "status": statuses,
            "subtotal": order_subtotals,
            "shipping_fee": shipping_fees,
            "tax_amount": tax_amounts,
            "discount_amount": discount_amounts,
            "total_amount": total_amounts,
            "shipping_region": shipping_regions,
            "channel": channels,
            "created_at": order_dates,
            "updated_at": order_dates + pd.to_timedelta(np.random.randint(0, 48, size=n_orders), unit="h"),
            "is_simulated": True,
        })

        # Inject duplicate order records
        dup_count = int(n_orders * self.config.duplicate_rate)
        if dup_count > 0:
            dup_indices = np.random.choice(n_orders, dup_count, replace=False)
            duplicates = orders_df.iloc[dup_indices].copy()
            orders_df = pd.concat([orders_df, duplicates], ignore_index=True)

        items_df = pd.DataFrame({
            "order_item_id": order_item_ids,
            "order_id": item_order_ids,
            "product_id": item_product_ids,
            "quantity": item_quantities,
            "unit_price": item_unit_prices,
            "discount_amount": item_discounts,
            "total_price": item_totals,
            "created_at": item_dates,
            "is_simulated": True,
        })

        self.orders_df = orders_df
        self.order_items_df = items_df
        return orders_df, items_df

    def generate_payments(self) -> pd.DataFrame:
        """Generates payment transaction records corresponding to orders."""
        if self.orders_df is None:
            self.generate_orders_and_items()

        n = len(self.orders_df)
        payment_ids = [f"PAY-{700000 + i}" for i in range(n)]
        order_ids = self.orders_df["order_id"].tolist()
        cust_ids = self.orders_df["customer_id"].tolist()
        amounts = self.orders_df["total_amount"].tolist()
        order_dates = self.orders_df["order_date"].tolist()
        order_statuses = self.orders_df["status"].tolist()

        methods = np.random.choice(
            self.config.payment_methods,
            size=n,
            p=[0.50, 0.25, 0.15, 0.07, 0.03],  # Credit Card 50%, PayPal 25%, Apple Pay 15%
        )

        statuses = []
        error_messages = []
        for o_status in order_statuses:
            if o_status in ["CANCELLED", "REFUNDED"]:
                if random.random() < 0.4:
                    statuses.append("FAILED")
                    error_messages.append("Card authorization declined - insufficient funds")
                else:
                    statuses.append("SUCCESS")
                    error_messages.append(None)
            elif o_status == "COMPLETED" or o_status == "SHIPPED":
                statuses.append("SUCCESS")
                error_messages.append(None)
            else:
                if random.random() < 0.08:
                    statuses.append("FAILED")
                    error_messages.append("Payment gateway timeout")
                else:
                    statuses.append("SUCCESS")
                    error_messages.append(None)

        tx_ids = [f"TXN-{uuid.uuid4().hex[:12].upper()}" for _ in range(n)]
        payment_dates = [od + timedelta(seconds=random.randint(5, 120)) for od in order_dates]

        df = pd.DataFrame({
            "payment_id": payment_ids,
            "order_id": order_ids,
            "customer_id": cust_ids,
            "payment_method": methods,
            "payment_status": statuses,
            "transaction_id": tx_ids,
            "amount": amounts,
            "currency": "USD",
            "payment_date": payment_dates,
            "error_message": error_messages,
            "is_simulated": True,
        })
        self.payments_df = df
        return df

    def generate_refunds(self) -> pd.DataFrame:
        """Generates refund records for returned or cancelled orders."""
        if self.payments_df is None:
            self.generate_payments()

        # Target orders with REFUNDED or CANCELLED status
        refunded_orders = self.orders_df[self.orders_df["status"].isin(["REFUNDED", "CANCELLED"])]
        n = len(refunded_orders)
        if n == 0:
            n = 100
            refunded_orders = self.orders_df.head(100)

        refund_ids = [f"REF-{900000 + i}" for i in range(n)]
        order_ids = refunded_orders["order_id"].tolist()
        amounts = refunded_orders["total_amount"].abs().tolist()
        order_dates = refunded_orders["order_date"].tolist()

        reasons = [
            "Customer returned item - defective",
            "Customer returned item - wrong size",
            "Customer cancelled before shipping",
            "Package lost in transit",
            "Disputed transaction",
        ]
        
        refund_reasons = np.random.choice(reasons, size=n)
        refund_statuses = np.random.choice(["PROCESSED", "REJECTED"], size=n, p=[0.92, 0.08])
        refund_dates = [od + timedelta(days=random.randint(1, 14)) for od in order_dates]

        df = pd.DataFrame({
            "refund_id": refund_ids,
            "order_id": order_ids,
            "payment_id": [f"PAY-{700000 + random.randint(0, len(self.payments_df)-1)}" for _ in range(n)],
            "refund_amount": amounts,
            "refund_reason": refund_reasons,
            "status": refund_statuses,
            "refund_date": refund_dates,
            "is_simulated": True,
        })
        self.refunds_df = df
        return df

    def generate_inventory(self) -> pd.DataFrame:
        """Generates inventory snapshots across multiple distribution fulfillment centers."""
        if self.products_df is None:
            self.generate_products()

        warehouses = ["WH-EAST-1", "WH-EAST-2", "WH-WEST-1", "WH-CENTRAL-1", "WH-EU-1"]
        records = []
        inv_id = 1000

        for _, prod in self.products_df.iterrows():
            prod_id = prod["product_id"]
            cost = prod["cost"]
            for wh in warehouses:
                stock = random.randint(15, 800)
                reserved = random.randint(0, min(20, stock))
                records.append({
                    "inventory_id": f"INV-{inv_id}",
                    "product_id": prod_id,
                    "warehouse_id": wh,
                    "stock_level": stock,
                    "reserved_stock": reserved,
                    "reorder_point": random.randint(50, 100),
                    "unit_cost": cost,
                    "last_restocked_at": self._random_dates("2024-01-01", "2024-12-31", 1)[0],
                    "is_simulated": True,
                })
                inv_id += 1

        df = pd.DataFrame(records)
        self.inventory_df = df
        return df

    def generate_sessions_and_events(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates clickstream sessions and web events for MongoDB raw event ingestion."""
        if self.customers_df is None:
            self.generate_customers()

        n_sessions = self.config.num_sessions
        session_ids = [f"SESS-{uuid.uuid4().hex[:12]}" for _ in range(n_sessions)]
        cust_pool = self.customers_df["customer_id"].tolist() + [None] * int(n_sessions * 0.3)
        cust_choices = random.choices(cust_pool, k=n_sessions)
        
        session_starts = self._random_dates(self.config.start_date, self.config.end_date, n_sessions)
        durations = np.random.exponential(scale=300, size=n_sessions).astype(int) + 15
        session_ends = session_starts + pd.to_timedelta(durations, unit="s")
        
        platforms = np.random.choice(["Web", "iOS", "Android"], size=n_sessions, p=[0.55, 0.28, 0.17])
        device_types = np.random.choice(self.config.device_types, size=n_sessions)
        referrers = np.random.choice(
            ["google_search", "direct", "facebook_ads", "instagram", "affiliate_partner", "email_newsletter"],
            size=n_sessions,
            p=[0.40, 0.25, 0.15, 0.10, 0.06, 0.04],
        )

        sessions_df = pd.DataFrame({
            "session_id": session_ids,
            "customer_id": cust_choices,
            "session_start": session_starts,
            "session_end": session_ends,
            "duration_seconds": durations,
            "platform": platforms,
            "device_type": device_types,
            "ip_address": [self.fake.ipv4() for _ in range(n_sessions)],
            "referrer": referrers,
            "is_simulated": True,
        })

        # Generate clickstream events per session (2 to 6 events per session)
        events = []
        event_counter = 1
        for i in range(min(n_sessions, 5000)):  # sample sessions for detailed clickstream
            s_id = session_ids[i]
            c_id = cust_choices[i]
            d_type = device_types[i]
            s_time = session_starts[i]
            
            # Sequence: page_view -> search -> product_view -> add_to_cart -> checkout_complete
            flow = ["page_view", "search", "product_view", "add_to_cart"]
            if random.random() < 0.25:
                flow.append("checkout_complete")

            cur_time = s_time
            for ev_type in flow:
                events.append({
                    "event_id": f"EVT-{event_counter:07d}",
                    "session_id": s_id,
                    "customer_id": c_id,
                    "event_type": ev_type,
                    "page_url": f"https://shop.enterprise-store.com/{ev_type}",
                    "timestamp": cur_time.isoformat(),
                    "device_type": d_type,
                    "metadata": {
                        "browser": "Chrome",
                        "viewport": "1920x1080",
                        "load_time_ms": random.randint(120, 1800),
                        "simulated": True,
                    },
                    "is_simulated": True,
                })
                event_counter += 1
                cur_time += timedelta(seconds=random.randint(10, 90))

        events_df = pd.DataFrame(events)
        self.sessions_df = sessions_df
        self.events_df = events_df
        return sessions_df, events_df

    def generate_all(self, output_dir: str = "data/raw") -> Dict[str, pd.DataFrame]:
        """Generates all 9 entities and saves them to the specified raw storage directory."""
        os.makedirs(output_dir, exist_ok=True)
        print(">> Generating Customers...")
        self.generate_customers()
        print(">> Generating Catalog Products...")
        self.generate_products()
        print(f">> Generating {self.config.num_orders} Orders and Order Items...")
        self.generate_orders_and_items()
        print(">> Generating Payments...")
        self.generate_payments()
        print(">> Generating Refunds...")
        self.generate_refunds()
        print(">> Generating Inventory Snapshots...")
        self.generate_inventory()
        print(">> Generating Customer Sessions & Clickstream Events...")
        self.generate_sessions_and_events()

        datasets = {
            "customers": self.customers_df,
            "products": self.products_df,
            "orders": self.orders_df,
            "order_items": self.order_items_df,
            "payments": self.payments_df,
            "refunds": self.refunds_df,
            "inventory": self.inventory_df,
            "sessions": self.sessions_df,
            "events": self.events_df,
        }

        for name, df in datasets.items():
            csv_path = os.path.join(output_dir, f"{name}.csv")
            parquet_path = os.path.join(output_dir, f"{name}.parquet")
            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)
            print(f"   [OK] Saved {name}: {len(df):,} records -> {parquet_path}")

        return datasets
