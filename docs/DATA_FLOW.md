# Data Flow Specification: Enterprise Real-Time Data Intelligence Platform

## 1. End-to-End Data Lifecycle

```
[Raw Sources: REST APIs / CSV / JSON / Kafka]
                     |
                     v
             (Batch Ingestion)
                     |
                     +---> [Bronze Parquet Lake (MinIO/S3)]
                     |        - Raw payloads + Ingestion Timestamps
                     |
                     v
             (Silver Cleansing Pipeline)
                     |
                     +---> [Data Quality Checks (Great Expectations)]
                     |        |
                     |        +--- [Pass] ---> [Silver Partitioned Parquet & PostgreSQL]
                     |        |
                     |        +--- [Fail] ---> [Quarantine Manager (S3 / Table)]
                     |
                     v
             (Gold Star Schema Pipeline & dbt Transformations)
                     |
                     +---> [Dimension Modeling (SCD Type 2 Customers, Products, Dates)]
                     |
                     +---> [Fact Tables (fact_orders, fact_order_items, fact_payments)]
                     |
                     +---> [Curated Marts (Daily Revenue, Customer CLV, Product Margins)]
                     |
                     v
             [Analytical Warehouse: DuckDB / Google BigQuery]
                     |
                     +----------------------------+
                     |                            |
                     v                            v
          [FastAPI Analytics Engine]     [Power BI DirectQuery / Import]
                     |                            |
                     v                            v
         [React TypeScript Dashboard]    [Executive Power BI Dashboard]
```

---

## 2. Batch Data Flow Stages

1. **Extraction**:
   - `BatchAPIClient` queries external endpoints using cursor-based pagination.
   - Enforces a Token Bucket rate limiter (30 token capacity, refill rate 15 req/sec).
   - In the event of network disruption or HTTP 5xx responses, exponential backoff with random jitter retries up to 4 attempts.
2. **Bronze Landing**:
   - Raw records are written to `data/lake/bronze/<entity>/<entity>_<batch_id>.parquet`.
   - `CheckpointManager` records the batch ID, timestamp, and row count into SQLite state storage.
3. **Silver Transformation**:
   - Cleansing: Email regex validation, null check on primary keys.
   - Quarantine: Malformed records are diverted into `data/lake/quarantine/<entity>/`.
   - Normalization: String dates parsed to UTC timestamps.
   - Partitioning: Saved partitioned by `order_year_month`.
4. **Gold Dimensional Modeling**:
   - SCD Type 2 dimension merge preserves customer historical tiers.
   - Analytical star schema joins order items with product costs to materialize gross profit.
5. **dbt Warehouse Compilation**:
   - Staging models (`stg_customers`, `stg_orders`, `stg_products`, `stg_payments`) are compiled into relational views.
   - Marts (`dbt_mart_daily_revenue`, `int_order_items_joined`) are materialized into persistent tables.
   - 5 dbt assertions execute to guarantee zero negative amounts and foreign key referential integrity.

---

## 3. Streaming Data Flow Stages

1. **Event Publication**:
   - `ECommerceStreamProducer` validates schemas via Pydantic (`StreamOrderEvent`, `StreamPaymentEvent`).
   - Tags payloads with `_is_simulated = True` and published timestamp.
2. **Kafka Bus**:
   - Real Kafka cluster on port `9092` / embedded high-performance streaming engine.
3. **Consumer Group Processing**:
   - `ECommerceStreamConsumer` continuously polls partitions.
   - Checks in-memory deduplication cache.
   - Evaluates payload constraints.
4. **Dead-Letter Queue (DLQ)**:
   - Malformed events (e.g. negative prices, malformed JSON) are caught by Pydantic validators and routed to `dead_letter_queue`.
   - Saved to persistent log with diagnostic failure reason and original payload for operator review.
