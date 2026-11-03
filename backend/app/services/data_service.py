"""
Data Service Layer for Analytical Warehouse Queries.
Directly interfaces with DuckDB analytical warehouse and Gold Parquet layer.
"""
import os
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from warehouse.warehouse_manager import WarehouseManager


class DataService:
    def __init__(self, warehouse: Optional[WarehouseManager] = None):
        self.warehouse = warehouse or WarehouseManager()

    def get_kpis(self) -> Dict[str, Any]:
        return self.warehouse.get_kpi_summary()

    def get_orders_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        where_clauses = []
        if status and isinstance(status, str):
            where_clauses.append(f"status = '{status}'")
        if region and isinstance(region, str):
            where_clauses.append(f"shipping_region = '{region}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        count_sql = f"SELECT COUNT(*) FROM fact_orders {where_sql};"
        total = self.warehouse.conn.execute(count_sql).fetchone()[0]

        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT 
                order_id,
                customer_id,
                CAST(order_date AS VARCHAR) as order_date,
                status,
                total_amount,
                shipping_region,
                channel
            FROM fact_orders
            {where_sql}
            ORDER BY order_date DESC
            LIMIT {page_size} OFFSET {offset};
        """
        rows = self.warehouse.conn.execute(query_sql).df().to_dict(orient="records")
        return rows, total

    def get_customers_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        segment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        where_sql = f"WHERE segment = '{segment}' AND is_current = TRUE" if (segment and isinstance(segment, str)) else "WHERE is_current = TRUE"
        count_sql = f"SELECT COUNT(*) FROM dim_customers {where_sql};"
        total = self.warehouse.conn.execute(count_sql).fetchone()[0]

        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT 
                customer_id,
                full_name,
                email,
                segment,
                region,
                city,
                state
            FROM dim_customers
            {where_sql}
            LIMIT {page_size} OFFSET {offset};
        """
        rows = self.warehouse.conn.execute(query_sql).df().to_dict(orient="records")
        return rows, total

    def get_products_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        where_sql = f"WHERE category = '{category}'" if (category and isinstance(category, str)) else ""
        count_sql = f"SELECT COUNT(*) FROM dim_products {where_sql};"
        total = self.warehouse.conn.execute(count_sql).fetchone()[0]

        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT 
                product_id,
                sku,
                name,
                category,
                unit_price,
                unit_cost,
                gross_margin_pct
            FROM dim_products
            {where_sql}
            LIMIT {page_size} OFFSET {offset};
        """
        rows = self.warehouse.conn.execute(query_sql).df().to_dict(orient="records")
        return rows, total

    def get_revenue_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        sql = f"""
            SELECT 
                order_day,
                total_orders,
                completed_orders,
                total_gross_revenue,
                avg_order_value
            FROM mart_daily_revenue
            ORDER BY order_day DESC
            LIMIT {days};
        """
        try:
            return self.warehouse.conn.execute(sql).df().to_dict(orient="records")
        except Exception:
            return []

    def get_regional_performance(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                shipping_region as region,
                COUNT(order_id) as total_orders,
                ROUND(SUM(total_amount), 2) as total_revenue
            FROM fact_orders
            GROUP BY shipping_region
            ORDER BY total_revenue DESC;
        """
        try:
            return self.warehouse.conn.execute(sql).df().to_dict(orient="records")
        except Exception:
            return []

    def get_category_performance(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                category,
                COUNT(product_id) as product_count,
                ROUND(AVG(gross_margin_pct), 2) as avg_margin_pct
            FROM dim_products
            GROUP BY category
            ORDER BY avg_margin_pct DESC;
        """
        try:
            return self.warehouse.conn.execute(sql).df().to_dict(orient="records")
        except Exception:
            return []
