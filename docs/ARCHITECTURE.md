# Architecture Specification: Enterprise Real-Time Data Intelligence Platform

## 1. System Architecture Overview

The platform implements a cloud-native **Medallion Lakehouse Architecture** capable of ingesting high-volume transactional e-commerce data via both batch REST endpoints and low-latency Apache Kafka event streams.

```
+----------------------------------------------------------------------------------------------------+
|                                    INGESTION LAYER                                                 |
|  - Batch REST API Extractor (Pagination, Token Bucket Rate Limiting, Exponential Backoff)           |
|  - Apache Kafka Stream Producer (Topics: orders, payments, customer_events, inventory_updates)     |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                      BRONZE LAYER (RAW LAKE)                                       |
|  - Preserves immutable raw source payloads with _ingestion_timestamp, _batch_id, _source_file      |
|  - S3 / MinIO Object Storage (Parquet/JSON) + MongoDB (Raw Clickstream Documents)                  |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                  SILVER LAYER (CLEANSED & VALIDATED)                               |
|  - Schema enforcement, UTC normalization, primary key deduplication                                |
|  - Automated Great Expectations Quality Suite                                                      |
|  - Automated Quarantine Manager for malformed/anomalous records                                    |
|  - Storage: Partitioned Parquet (by order_year_month) & PostgreSQL Relational Store                |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                     GOLD LAYER (ANALYTICS & BI)                                    |
|  - Dimensional Modeling (Kimball Star Schema):                                                     |
|      * Fact: fact_orders, fact_order_items, fact_payments                                          |
|      * Dimensions: dim_customers (SCD Type 2), dim_products, dim_dates                             |
|  - dbt Transformation Layer (Staging views, Intermediate joins, Materialized Marts)                |
|  - Local Analytical Warehouse (DuckDB) / Google BigQuery Cloud Warehouse                           |
+------------------------+---------------------------------------------------+-----------------------+
                         |                                                   |
                         v                                                   v
+------------------------------------+             +-------------------------------------------------+
|          FASTAPI BACKEND           |             |                POWER BI DESKTOP                 |
|  - 10+ REST API Endpoints          |             |  - DirectQuery / Import Star Schema             |
|  - Prometheus Instrumentation      |             |  - 25+ DAX Measures (Gross Margin, CLV, Growth) |
+-----------------+------------------+             +-------------------------------------------------+
                  |
                  v
+------------------------------------+
|       REACT + TYPESCRIPT UI        |
|  - Tailwind CSS Responsive Design  |
|  - 5 Operational & BI Tabs         |
+------------------------------------+
```

---

## 2. Medallion Layer Design

### 2.1 Bronze Layer (Raw)
- **Design Philosophy**: Append-only, format-agnostic, raw fidelity. No business transformations are applied.
- **Storage**: MinIO / S3 bucket `s3://ecommerce-lake/bronze/<entity>/`. Clickstream unstructured JSON logs are captured in MongoDB `ecommerce_events.raw_customer_events`.
- **Metadata**: Ingestion audit fields `_ingestion_timestamp`, `_batch_id`, and `_source_file` are appended to every record.

### 2.2 Silver Layer (Cleansed, Normalized, Partitioned)
- **Deduplication**: Window functions identify and drop duplicates by primary key (`order_id`, `customer_id`, etc.).
- **Quarantine Engine**: Records failing structural or business validity rules (e.g., negative order total, invalid email syntax, orphaned foreign key) are quarantined to `s3://ecommerce-lake/quarantine/<entity>/` with diagnostic rejection tags.
- **Timestamp Normalization**: All timestamps converted to ISO-8601 UTC.
- **Partitioning**: Orders are partitioned by `order_year_month` (e.g., `orders/order_year_month=2024-05/`) to prune partition scans.

### 2.3 Gold Layer (Star Schema & Business Marts)
- **Fact Tables**:
  - `fact_orders`: Granularity of 1 row per order. Key metrics: `subtotal`, `tax_amount`, `shipping_fee`, `total_amount`.
  - `fact_order_items`: Granularity of 1 row per line item. Includes `unit_cost`, `total_cost`, `gross_profit`.
  - `fact_payments`: Reconciles transaction status with order status.
- **Dimension Tables**:
  - `dim_customers`: Implements Slowly Changing Dimensions (SCD Type 2) tracking segment migrations with `customer_key`, `effective_date`, `end_date`, and `is_current`.
  - `dim_products`: Catalog hierarchy, costs, unit prices, supplier mapping.
  - `dim_dates`: Fiscal and calendar dates, day of week, quarter, weekend indicators.
- **Marts**:
  - `mart_daily_revenue`: Pre-aggregated daily total revenue, completed order volume, and Average Order Value (AOV).
  - `mart_customer_lifetime_value`: Total lifetime spend, order frequency, churn risk.
  - `mart_product_performance`: Sales volume and gross profit margin by SKU.

---

## 3. Streaming Architecture (Apache Kafka)

- **Topics**:
  - `orders`: Transactional checkout events.
  - `payments`: Payment authorization records.
  - `customer_events`: Clickstream event stream.
  - `inventory_updates`: Multi-warehouse stock level mutations.
  - `dead_letter_queue`: Poison message isolation queue.
- **Reliability & Idempotency**:
  - Sliding deduplication window in the consumer group prevents duplicate event processing.
  - Schema validation catches schema drift or invalid types; failing messages are routed to DLQ with stacktrace headers.
