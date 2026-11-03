# Enterprise-Scale Real-Time Data Intelligence Platform

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TS-61DAFB.svg)](https://react.dev/)
[![DuckDB](https://img.shields.io/badge/OLAP-DuckDB-FFF000.svg)](https://duckdb.org/)
[![dbt](https://img.shields.io/badge/Transformation-dbt-FF694B.svg)](https://www.getdbt.com/)
[![Docker](https://img.shields.io/badge/Containers-Docker%20Compose-2496ED.svg)](docker-compose.yml)
[![Tests Passing](https://img.shields.io/badge/Pytest-21%2F21%20Passed-brightgreen.svg)](tests/)

A production-grade, distributed Data Engineering and Analytics platform architected for high-scale enterprise e-commerce environments. Ingests transactional batches and streaming Kafka event streams, cleanses and normalizes records across a Medallion Lakehouse Architecture (Bronze, Silver, Gold), tracks Slowly Changing Dimensions (SCD Type 2), validates data quality via Great Expectations with automated quarantine isolation, models Kimball dimensional star schemas and marts using dbt, and serves sub-second analytics through an embedded React + TypeScript dashboard and FastAPI REST engine.

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Technology Stack & Core Responsibilities](#3-technology-stack--core-responsibilities)
4. [Medallion Lakehouse Data Flow](#4-medallion-lakehouse-data-flow)
5. [Core Engineering Subsystems](#5-core-engineering-subsystems)
   - [Synthetic High-Scale Data Generator](#51-synthetic-high-scale-data-generator)
   - [Dual Ingestion Layer: Batch & Streaming](#52-dual-ingestion-layer-batch--streaming)
   - [Dead-Letter Queue (DLQ) & Quarantine Isolation](#53-dead-letter-queue-dlq--quarantine-isolation)
   - [Distributed Processing & SCD Type 2 Dimensions](#54-distributed-processing--scd-type-2-dimensions)
   - [Kimball Star Schema & Analytical Warehouse](#55-kimball-star-schema--analytical-warehouse)
   - [dbt Transformation & Semantic Modeling Layer](#56-dbt-transformation--semantic-modeling-layer)
   - [Pipeline Orchestration (7 Apache Airflow DAGs)](#57-pipeline-orchestration-7-apache-airflow-dags)
   - [Data Reliability & Quality Gates (Great Expectations)](#58-data-reliability--quality-gates-great-expectations)
   - [Unified Enterprise Dashboard & Analytics Engine](#59-unified-enterprise-dashboard--analytics-engine)
6. [Quick Start & Single-Command Launch](#6-quick-start--single-command-launch)
7. [Production Multi-Service Deployment (Docker Compose)](#7-production-multi-service-deployment-docker-compose)
8. [REST API Specification](#8-rest-api-specification)
9. [Automated Testing & Autonomous Verification](#9-automated-testing--autonomous-verification)
10. [Repository Structure](#10-repository-structure)
11. [Security, Governance & Operational Best Practices](#11-security-governance--operational-best-practices)
12. [License](#12-license)

---

## 1. Executive Summary & Problem Statement

Modern e-commerce organizations generate multi-terabyte datasets across independent transactional microservices, mobile applications, and warehouse fulfillment centers. Engineering teams face four fundamental bottlenecks:

1. **Disparate Ingestion Rates**: Managing high-frequency, real-time clickstreams alongside periodic bulk relational dumps without data skew or resource starvation.
2. **Contaminated Data Contagion**: Handling anomalies (negative transaction prices, duplicate checkout signals, orphaned foreign keys) without crashing downstream ELT pipelines or polluting executive reporting.
3. **Temporal History Drift**: Accurately reconstructing historical customer loyalty tiers, addresses, and purchase habits at any arbitrary point in time without destructive table overwrites.
4. **Latency vs. Cost Trade-offs**: Delivering sub-second interactive OLAP queries to business users without incurring massive cloud compute overhead on cold warehouse clusters.

This platform resolves these challenges by coupling an immutable Medallion Lakehouse (MinIO / S3 Parquet storage) with an in-process columnar warehouse (DuckDB), backed by enterprise dbt transformations, automated Great Expectations anomaly isolation gates, Apache Airflow workflow orchestration, and an operational React dashboard.

---

## 2. End-to-End System Architecture

```
====================================================================================================
                                      SOURCE & GENERATION LAYER
  - 100,000+ Orders across 9 Entities (Customers, Products, Orders, Items, Payments, Refunds, Inventory, Clicks)
  - Deliberate Quality Injections: Duplicate events, negative prices, orphaned keys, malformed emails
====================================================================================================
                     |                                              |
     (Periodic Batch REST Feeds)                      (Real-Time Event Streams)
                     v                                              v
+------------------------------------------+   +------------------------------------------+
|         BATCH INGESTION CLIENT           |   |           APACHE KAFKA BROKER            |
|  - Token Bucket Rate Limiting            |   |  - Topics: orders, payments,             |
|  - Exponential Backoff Retries           |   |           customer_events, inventory     |
|  - CheckpointManager State Persistence   |   |  - Sliding Deduplication Cache           |
+------------------------------------------+   +------------------------------------------+
                     |                                              |
                     |                                              v
                     |                                 +--------------------------+
                     |                                 | DEAD-LETTER QUEUE (DLQ)  |
                     |                                 | - Schema Rejections      |
                     |                                 | - Diagnostic Error Trace |
                     |                                 +--------------------------+
                     |                                              |
                     +----------------------+-----------------------+
                                            |
                                            v
====================================================================================================
                                  BRONZE LAYER (RAW OBJECT LAKE)
  - Immutable raw JSON and Parquet payloads stored in S3 / MinIO
  - Preserves system audit metadata: _ingestion_timestamp, _batch_id, _source_file
====================================================================================================
                                            |
                                            v
====================================================================================================
                            SILVER LAYER (CLEANSED, DEDUPLICATED, VALIDATED)
  - PySpark / Pandas Distributed Cleansing Engine
  - Strict Pydantic Schema Validation & Type Coercion
  - Anomaly Quarantine Isolation: Bad records diverted to data/quarantine/
  - Partitioned Parquet Storage: year=YYYY/month=MM partitioning
  - PostgreSQL Operational Store: Synchronized tables for live relational queries
====================================================================================================
                                            |
                                            v
====================================================================================================
                               GOLD LAYER (KIMBALL STAR SCHEMA & MARTS)
  - Fact Tables: fact_orders, fact_order_items, fact_payments
  - Dimension Tables: dim_customers (SCD Type 2), dim_products, dim_dates
  - Analytical Marts: mart_daily_revenue, mart_customer_lifetime_value, mart_product_performance
  - Transformations & Schema Assertions compiled via dbt
====================================================================================================
                                            |
                                            v
====================================================================================================
                                   ANALYTICAL SERVING LAYER
  - Embedded Columnar Engine: DuckDB high-speed vector execution on Gold Parquet
  - Cloud Warehouse DDL: Google BigQuery partitioned and clustered enterprise schemas
====================================================================================================
                     |                                              |
                     v                                              v
+------------------------------------------+   +------------------------------------------+
|          FASTAPI REST ENGINE             |   |        APACHE AIRFLOW RUNNER             |
|  - Analytical SQL Query API              |   |  - 7 Production DAG Workflows            |
|  - Prometheus Instrumentation            |   |  - Automated Retries & Backfills         |
|  - HMAC-SHA256 JWT Authentication        |   |  - WAL-Enabled Run History Audit         |
+------------------------------------------+   +------------------------------------------+
                     |
                     v
====================================================================================================
                      UNIFIED OPERATIONAL REACT + TYPESCRIPT DASHBOARD
  - Host: http://localhost:8000 (Served directly by FastAPI static runtime)
  - Executive Overview & Sales Performance  |  Customer Transactions Explorer with Drill-Down
  - Airflow Workflow Orchestrator (Manual Trigger & Audit Trail)
  - Apache Kafka Telemetry & DLQ Payload Inspector with Traffic Simulator
  - Great Expectations Quality Scorecard & Quarantine Entity Breakdown
  - Dimensional Warehouse Marts with 7d / 14d / 30d / 90d Dynamic Time Windows
====================================================================================================
```

---

## 3. Technology Stack & Core Responsibilities

| Subsystem | Technology | Version | Purpose in Architecture |
| :--- | :--- | :--- | :--- |
| **Data Generation** | Python, Faker, NumPy | 3.12+ | Synthesizes 100k+ enterprise e-commerce records across 9 relational schemas with realistic variance and boundary test cases. |
| **Streaming Broker** | Apache Kafka | 3.7 | Ingests real-time events across 4 partitioned topics with consumer group coordination. |
| **Dead-Letter Queue**| JSONL / Python DLQ Manager | Native | Isolates schema validation failures with diagnostic error traces for zero-loss quarantine. |
| **Object Lake Storage**| MinIO / AWS S3 API | Latest | Multi-tiered object storage for raw Bronze landing, partitioned Silver, and curated Gold Parquet files. |
| **Relational Database**| PostgreSQL | 16-alpine | Transactional operational store with connection pooling and schema constraints. |
| **Document Store** | MongoDB | 7.0 | High-velocity storage for raw semi-structured web clickstream events. |
| **Batch Processing** | Apache Spark (PySpark) & Pandas | 3.5.0 | Large-scale parallel transformations, duplicate pruning, partition writing, and SCD Type 2 dimension merging. |
| **Analytical OLAP** | DuckDB | 1.1+ | Zero-credential columnar analytical engine executing sub-second ANSI SQL on Parquet files. |
| **Cloud Warehouse** | Google BigQuery | Standard SQL | Enterprise cloud data warehouse DDL with partitioning on `order_date` and clustering on `status, shipping_region`. |
| **Data Modeling** | dbt (data build tool) | 1.8+ | Manages the semantic layer: compiles staging views, intermediate join tables, and dimensional business marts. |
| **Workflow Scheduler**| Apache Airflow | 2.8+ | Orchestrates 7 production workflows with automated dependency tracking, failure handling, and execution history. |
| **Data Reliability** | Great Expectations | 0.18+ | Automates multi-checkpoint quality suites, column assertions, and quarantine routing with SLA scoring. |
| **Backend Framework** | FastAPI | 0.110+ | Asynchronous REST backend exposing analytical query endpoints, JWT authentication, and Prometheus metrics. |
| **Frontend Runtime** | React 18, TypeScript, Tailwind CSS | 18.3 | High-density operational dashboard featuring multi-dimensional filtering, streaming controls, and marts visualizer. |
| **Observability** | Prometheus & Grafana | Latest | Custom metrics exporter, scraping intervals, consumer lag tracking, and operational dashboards. |
| **Infrastructure** | Docker Compose & Terraform | Latest | 10-service local containerized network and AWS IaC provisioning for S3, Glue, Athena, and IAM roles. |
| **Quality Assurance**| Pytest & AnyIO | 8.0+ | Automated test suite verifying data pipelines, API contracts, SCD2 mechanics, and Great Expectations checks. |

---

## 4. Medallion Lakehouse Data Flow

The platform applies the Databricks Medallion pattern to enforce structural integrity and auditability at every stage:

```
[Raw Sources: REST APIs, Microservice Dumps, Kafka Events]
                           |
                           v
+--------------------------------------------------------------------+
| 1. BRONZE LAYER (Raw Ingestion)                                    |
|    - Path: data/lake/bronze/{entity}/                              |
|    - Format: Raw JSON / Parquet with exact source fidelity         |
|    - Metadata: Ingestion timestamp, batch UUID, origin filename    |
|    - SLA: 100% ingestion completeness; zero data modification      |
+--------------------------------------------------------------------+
                           |
                           v
+--------------------------------------------------------------------+
| 2. SILVER LAYER (Cleansed, Validated & Quarantined)                |
|    - Path: data/lake/silver/{entity}/                              |
|    - Format: Snappy-compressed Parquet partitioned by year/month   |
|    - Processing: Deduplication by primary key, UTC normalization,  |
|      referential validation, schema enforcement                    |
|    - Quarantine Gate: Dirty records routed to data/quarantine/     |
|    - Great Expectations SLA: 100% assertions passed                |
+--------------------------------------------------------------------+
                           |
                           v
+--------------------------------------------------------------------+
| 3. GOLD LAYER (Curated Star Schema & Dimensional Marts)            |
|    - Path: data/lake/gold/                                         |
|    - Format: High-performance columnar Parquet                    |
|    - Modeling: Kimball Dimensional Star Schema                     |
|      * Fact Tables: fact_orders, fact_order_items, fact_payments   |
|      * Dimensions: dim_customers (SCD2), dim_products, dim_dates   |
|      * Curated Marts: mart_daily_revenue, mart_customer_ltv        |
+--------------------------------------------------------------------+
                           |
                           v
+--------------------------------------------------------------------+
| 4. SERVING & APPLICATION LAYER                                     |
|    - DuckDB Columnar Views -> FastAPI REST APIs -> React Dashboard |
+--------------------------------------------------------------------+
```

---

## 5. Core Engineering Subsystems

### 5.1 Synthetic High-Scale Data Generator
Located in [`data_generator/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/data_generator/).
- Generates over **100,000 orders** and approximately **450,000 total entity records** across 9 distinct datasets: `customers`, `products`, `orders`, `order_items`, `payments`, `refunds`, `inventory`, `promotions`, and `clickstream`.
- Features a deterministic random seed with realistic commercial distributions:
  - Order amounts modeled with log-normal curves reflecting real consumer checkout baskets ($20 to $5,000).
  - Geographical distribution balanced across 7 standard global operational regions: `North America - East`, `North America - West`, `Europe - Western`, `Europe - Northern`, `Asia Pacific - East`, `Asia Pacific - South`, and `Latin America`.
  - Realistic status state machine: `COMPLETED` (37.5%), `SHIPPED` (12.5%), `PENDING` (12.5%), `PROCESSING` (12.5%), `CANCELLED` (12.5%), and `REFUNDED` (12.5%).
- **Deliberate Anomaly Injection**: Injects known data flaws (negative pricing, malformed email patterns, duplicate event keys, and orphaned customer IDs) at strict configurable probabilities (0.5% to 2.0%) to test pipeline resilience.

### 5.2 Dual Ingestion Layer: Batch & Streaming
Located in [`ingestion/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/ingestion/).
- **Batch REST Ingestion Client** ([`ingestion/batch/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/ingestion/batch/)):
  - Implements a **Token Bucket Rate Limiter** to prevent overwhelming source API endpoints.
  - Implements an **Exponential Backoff and Jitter** retry handler for transient HTTP 429 and 503 errors.
  - Uses [`CheckpointManager`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/ingestion/batch/checkpoint_manager.py) with atomic JSON state commits to ensure idempotent, resume-capable batch loading.
- **Apache Kafka Streaming Pipeline** ([`ingestion/streaming/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/ingestion/streaming/)):
  - High-throughput producers publishing structured event payloads to 4 topics: `orders`, `payments`, `customer_events`, and `inventory_updates`.
  - Consumer groups utilizing sliding-window in-memory deduplication caches (`dedup_cache`) to drop duplicate event signals.
  - Strict Pydantic schema validation executing on every inbound event message before ingestion.

### 5.3 Dead-Letter Queue (DLQ) & Quarantine Isolation
Located in [`ingestion/streaming/dead_letter_queue.py`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/ingestion/streaming/dead_letter_queue.py) and [`data_quality/quarantine_manager.py`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/data_quality/quarantine_manager.py).
- Ensures contaminated data never reaches the Silver layer or corrupts production analytics.
- **Streaming DLQ**: Invalid Kafka payloads (e.g., negative order totals, missing required fields) are trapped by the consumer's Pydantic validation gate and immediately diverted to `data/dlq/dlq_messages.jsonl` with diagnostic metadata (failing schema constraint, offset, source topic, failure timestamp).
- **Batch Quarantine Manager**: During Silver layer processing, records failing relational checks (such as orphaned `customer_id` values or malformed email syntax) are isolated into `data/quarantine/{entity}_quarantine.parquet` with rejection reason tags. Production lakes remain 100% clean.

### 5.4 Distributed Processing & SCD Type 2 Dimensions
Located in [`processing/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/processing/).
- Offers dual execution engines: **Apache Spark (PySpark)** for multi-node cluster execution and **Pandas** for high-efficiency single-node execution.
- **Partitioning**: Silver and Gold transaction tables are partitioned by `order_year_month` (`year=YYYY/month=MM`), enabling instant partition pruning on historical date queries.
- **Slowly Changing Dimensions (SCD Type 2)**:
  - Implemented in [`processing/pandas/scd2_handler.py`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/processing/pandas/scd2_handler.py) and PySpark equivalent.
  - Tracks customer attribute mutations (loyalty tiers, segment upgrades, shipping addresses) over time.
  - Uses surrogate hashing keys, `valid_from`, `valid_to` timestamps, and an `is_current` boolean flag. Historical purchases remain anchored to the customer's state at the exact time of order placement.

### 5.5 Kimball Star Schema & Analytical Warehouse
Located in [`warehouse/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/warehouse/).
- Modeled strictly according to Kimball dimensional modeling principles:
  - **Fact Tables**: `fact_orders` (grain: one row per transaction), `fact_order_items` (grain: one row per line item), `fact_payments` (grain: one row per payment transaction).
  - **Dimension Tables**: `dim_customers` (SCD2 customer profile), `dim_products` (catalog pricing and margins), `dim_dates` (calendar dimension covering all transactional dates).
- **DuckDB Local Columnar Warehouse** ([`warehouse/warehouse_manager.py`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/warehouse/warehouse_manager.py)):
  - Mounts Gold Parquet files as zero-copy SQL views.
  - Executes analytical aggregations (grouping 97k+ rows across multiple dimensions) in single-digit milliseconds with zero external infrastructure dependencies.
- **Google BigQuery Production Schemas** ([`warehouse/bigquery_schemas.sql`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/warehouse/bigquery_schemas.sql)):
  - Production-ready DDL definitions featuring column clustering on `status, shipping_region` and time-based partitioning on `DATE(order_date)`.

### 5.6 dbt Transformation & Semantic Modeling Layer
Located in [`dbt/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/dbt/).
- Operates in three sequential compilation stages:
  1. **Staging Views (`stg_`)**: Standardizes column names, casts timestamps, and applies filter assertions (`WHERE total_amount > 0`).
  2. **Intermediate Models (`int_`)**: Joins order items with product catalog metadata to compute line-item margins, discounts, and item costs.
  3. **Curated Marts (`mart_`)**: Pre-aggregates executive metrics:
     - `mart_daily_revenue`: Daily aggregated volume, total gross sales, completed order count, and completion rate.
     - `mart_customer_lifetime_value`: Total orders per customer, lifetime gross spend, average order value, and recency.
     - `mart_product_performance`: Units sold, total margin dollars, and category share.
- Automated schema tests verify `unique`, `not_null`, `positive_total_amount`, and `accepted_values` for order statuses.

### 5.7 Pipeline Orchestration (7 Apache Airflow DAGs)
Located in [`airflow/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/airflow/).
- Managed by a standalone, zero-dependency runner ([`airflow/airflow_runner.py`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/airflow/airflow_runner.py)) equipped with Write-Ahead Logging (WAL) and automated busy-retry handling.
- **7 Production DAGs**:
  1. `daily_batch_ingestion_dag`: Ingests raw source entities into Bronze object storage.
  2. `customer_processing_dag`: Executes customer deduplication and updates SCD Type 2 dimension records.
  3. `order_processing_dag`: Cleanses transactions, removes dirty records to quarantine, and writes partitioned Parquet.
  4. `payment_processing_dag`: Reconciles payments and refunds, computing net revenue.
  5. `inventory_sync_dag`: Synchronizes warehouse stock changes with product catalog balances.
  6. `warehouse_transformation_dag`: Compiles dbt staging views, intermediate join models, and analytical marts.
  7. `data_quality_validation_dag`: Executes Great Expectations assertion suites and generates the latest audit scorecard.
- Features a **"Run All 7 Pipelines"** button and individual DAG manual dispatch buttons with sub-second execution duration recording.

### 5.8 Data Reliability & Quality Gates (Great Expectations)
Located in [`data_quality/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/data_quality/).
- Automates quality gates before promoting data between layers:
  - **Bronze Suite**: Intercepts structural anomalies (null keys, out-of-bound dates, corrupted emails) and verifies catch rates.
  - **Silver Suite**: Asserts 100% SLA conformance across 7 strict assertions (uniqueness of primary keys, positive prices, valid status enum values, foreign key integrity).
- Produces a machine-readable JSON health report in `data/data_quality/reports/latest_validation_report.json` detailing passed checks, failed checks, and entity quarantine counts.

### 5.9 Unified Enterprise Dashboard & Analytics Engine
Located in [`frontend/`](file:///c:/Users/sriva/OneDrive/Desktop/Data%20Engineer/frontend/).
- Built with **React 18**, **TypeScript**, and **Tailwind CSS**, styled in a crisp white canvas with rich saturated accents.
- Served directly by FastAPI on **`http://localhost:8000`** with zero CORS complexity.
- **5 Integrated Monitoring Tabs**:
  1. **Overview & Sales**: Real-time sales KPIs ($63.6M gross revenue, 97,928 orders), interactive "Sales Overview" vs. "How Data Moves" view switcher, and a Customer Transactions Explorer with multi-field search, region and status dropdowns, CSV export, and an order details modal.
  2. **Automated Pipelines**: Airflow orchestration control room displaying all 7 DAG schedules, execution states, durations, recent run audit trails, individual manual triggers, and a master sequential pipeline trigger.
  3. **Live Streaming**: Apache Kafka telemetry displaying live topic counts, consumer lag, DLQ poison message count, interactive event simulator, poison anomaly injector, and a full diagnostic payload inspector with JSON copy utility.
  4. **Data Quality & Checks**: Great Expectations scorecard showing Silver Layer SLA score (100%), bronze catch rate, quarantine summaries, interactive entity tabs (`customers`, `orders`, `order_items`), and an audit re-run button.
  5. **Analytics & Reports**: Kimball star schema daily revenue visualizer with dynamic timeframe buttons (**7d**, **14d**, **30d**, **90d**), regional fulfillment distribution, product category margin breakdown, and CSV data export.

---

## 6. Quick Start & Single-Command Launch

### Prerequisites
- **Python**: Version 3.12 or 3.13 installed
- **Node.js**: Version 20+ and npm installed
- **Operating System**: Windows, macOS, or Linux

### Single-Command All-in-One Execution
The repository includes an all-in-one launcher that generates data, runs all Medallion pipelines, executes dbt, runs quality audits, and starts the unified dashboard:

```bash
# 1. Clone the repository
git clone <repository-url>
cd enterprise-data-platform

# 2. Install dependencies
pip install -r requirements.txt
npm run build --prefix frontend

# 3. Launch platform
python run_all.py
```
*On Windows, you can also double-click `start.bat`.*

The launcher automatically:
- Checks for and generates historical datasets (100,000+ orders).
- Executes Bronze, Silver, Gold transformations and dbt models.
- Executes Great Expectations data validation.
- Launches the unified server on **`http://localhost:8000`** and opens your default browser.

### Direct Server Run (If Data is Already Generated)
To start the platform server directly:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- **Unified Dashboard**: `http://localhost:8000`
- **Interactive Swagger API Documentation**: `http://localhost:8000/docs`
- **Prometheus Metrics**: `http://localhost:8000/api/metrics`
- **System Health Endpoint**: `http://localhost:8000/api/health`

---

## 7. Production Multi-Service Deployment (Docker Compose)

For containerized cloud deployment across all 10 independent services:

```bash
# Launch entire containerized ecosystem
docker compose up -d

# Verify all containers are healthy
docker compose ps
```

### Containerized Network Topology

| Service | Port | Internal URL | Purpose |
| :--- | :--- | :--- | :--- |
| **Unified Web Platform** | `8000` | `http://localhost:8000` | Serves React Dashboard, REST API, and Swagger docs |
| **PostgreSQL** | `5432` | `postgres:5432` | Relational operational store |
| **MongoDB** | `27017` | `mongodb:27017` | Clickstream document store |
| **Apache Kafka** | `9092` | `kafka:9092` | Event streaming broker |
| **Zookeeper** | `2181` | `zookeeper:2181` | Kafka cluster metadata coordinator |
| **MinIO API** | `9000` | `minio:9000` | S3-compatible Object Lake endpoint |
| **MinIO Console** | `9001` | `http://localhost:9001` | Web-based object storage browser |
| **Prometheus** | `9090` | `http://localhost:9090` | Metrics scraper and time-series database |
| **Grafana** | `3001` | `http://localhost:3001` | Observability monitoring dashboards |

---

## 8. REST API Specification

All API endpoints are documented with OpenAPI / Swagger UI at `/docs`. Below is a reference of the core routes:

| Method | Endpoint | Query / Body Parameters | Response Model | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | None | `{"status": "UP"}` | Cluster health and subsystem status probe. |
| `GET` | `/api/metrics` | None | Prometheus Text Format | Operational metrics exporter for Prometheus scraping. |
| `GET` | `/api/kpis` | None | `KPISummaryResponse` | Executive sales KPIs calculated via fast DuckDB OLAP SQL. |
| `GET` | `/api/orders` | `page`, `page_size`, `status`, `region` | `PaginatedResponse` | Filtered, searchable, and paginated transaction records. |
| `GET` | `/api/customers` | `page`, `page_size`, `segment` | `PaginatedResponse` | Paginated SCD Type 2 customer records with active flags. |
| `GET` | `/api/products` | `page`, `page_size`, `category` | `PaginatedResponse` | Product catalog with prices, costs, and gross margins. |
| `GET` | `/api/revenue` | `days` (Default: 30) | `RevenueAnalyticsResponse` | Kimball daily revenue mart with category & regional breakdowns. |
| `GET` | `/api/pipelines` | None | `PipelineCatalogResponse` | Active Airflow DAGs, schedules, states, and execution history. |
| `POST`| `/api/pipelines/{dag_id}/trigger` | `Authorization: Bearer <JWT>` | `TriggerResponse` | Dispatches manual DAG execution (or `all` for full stack). |
| `GET` | `/api/streaming/status` | None | `StreamingStatusResponse` | Real-time Kafka topic event counters and consumer group lag. |
| `GET` | `/api/streaming/dlq` | `limit` (Default: 25) | `DLQResponse` | Quarantined Dead-Letter Queue messages with error diagnostics. |
| `POST`| `/api/streaming/simulate` | `count` (Default: 25) | `SimulationResponse` | Publishes live simulated transactions across Kafka topics. |
| `POST`| `/api/streaming/simulate-poison` | None | `DLQInjectionResponse` | Injects an intentional invalid order to trigger the DLQ gate. |
| `GET` | `/api/data-quality` | `refresh` (Default: false) | `DataQualityReport` | Great Expectations audit report and quarantine breakdown. |
| `POST`| `/api/data-quality/run` | None | `DataQualityReport` | Triggers a fresh Great Expectations test validation suite. |
| `POST`| `/api/auth/login` | `{"username": "...", "password": "..."}` | `TokenResponse` | Issues signed HMAC-SHA256 JWT bearer token for admin actions. |

---

## 9. Automated Testing & Autonomous Verification

### Pytest Test Suite (21 Tests)
The platform includes 21 comprehensive unit, integration, and data reliability tests:

```bash
pytest tests/ -v
```

```
tests/data_quality/test_great_expectations.py::test_data_quality_validation_suite PASSED
tests/integration/test_api_endpoints.py::test_health_endpoint PASSED
tests/integration/test_api_endpoints.py::test_metrics_prometheus_and_json PASSED
tests/integration/test_api_endpoints.py::test_kpi_summary_endpoint PASSED
tests/integration/test_api_endpoints.py::test_orders_paginated PASSED
tests/integration/test_api_endpoints.py::test_customers_paginated PASSED
tests/integration/test_api_endpoints.py::test_products_paginated PASSED
tests/integration/test_api_endpoints.py::test_pipelines_catalog PASSED
tests/integration/test_api_endpoints.py::test_streaming_status PASSED
tests/integration/test_api_endpoints.py::test_data_quality_report PASSED
tests/integration/test_api_endpoints.py::test_admin_auth_and_trigger PASSED
tests/integration/test_pipeline_e2e.py::test_warehouse_kpis_and_views PASSED
tests/integration/test_pipeline_e2e.py::test_dbt_models_and_tests_pass PASSED
tests/unit/test_batch_ingestion.py::test_checkpoint_manager PASSED
tests/unit/test_batch_ingestion.py::test_batch_ingestor_bronze_write PASSED
tests/unit/test_generator.py::test_generator_config PASSED
tests/unit/test_generator.py::test_generate_customers PASSED
tests/unit/test_generator.py::test_generate_orders_and_anomalies PASSED
tests/unit/test_processing.py::test_medallion_cleansing_and_quarantine PASSED
tests/unit/test_processing.py::test_scd2_customer_dimension PASSED
tests/unit/test_streaming.py::test_streaming_producer_and_consumer PASSED

============================= 21 passed in 3.26s ==============================
```

### Autonomous Dashboard Controller & Health Verification
A specialized end-to-end verification controller executes across all 9 subsystems, validating authentication, database aggregations, status filters, regional subsets, pagination, DAG execution, Kafka streaming, and Great Expectations gates:

```bash
python scripts/autonomous_control_runner.py
```

```
================================================================================
     AUTONOMOUS DASHBOARD CONTROLLER & SYSTEM HEALTH VERIFICATION              
================================================================================
[STEP 1] Authenticating Administrative User... (Role: ADMIN, Token: Bearer) -> PASSED
[STEP 2] Auditing Executive Sales KPIs (97,928 orders, $63.6M revenue) -> PASSED
[STEP 3] Testing Orders Status Filters (Completed: 36,770, Shipped: 12,245) -> PASSED
[STEP 4] Testing Geographic Regional Filters (All 7 zones reconciled) -> PASSED
[STEP 5] Testing Pagination Flow (Pages 1 -> 5 verified) -> PASSED
[STEP 6] Triggering All 7 Apache Airflow DAGs via Platform API -> PASSED (All SUCCESS)
[STEP 7] Auditing Kafka Streaming Broker & Dead-Letter Queue -> PASSED
[STEP 8] Auditing Great Expectations Data Quality Suite (100% SLA) -> PASSED
[STEP 9] Auditing Analytical Warehouse Marts (Daily aggregation verified) -> PASSED
================================================================================
     ALL AUTONOMOUS CHECKS PASSED: DASHBOARD IS 100% OPERATIONAL & VERIFIED     
================================================================================
```

---

## 10. Repository Structure

```
enterprise-data-platform/
│
├── backend/                             # FastAPI High-Performance REST Engine
│   ├── app/
│   │   ├── api/routes.py                # REST endpoints with input validation & auth
│   │   ├── core/config.py               # Pydantic BaseSettings & JWT security
│   │   ├── schemas/models.py            # Pydantic response models
│   │   ├── services/                    # DataService, PipelineService, StreamingService
│   │   └── main.py                      # FastAPI application with static mount
│
├── frontend/                            # Unified React 18 + TypeScript Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx               # Enterprise top navigation & live status
│   │   │   ├── OverviewTab.tsx          # Executive KPIs & Transactions Explorer
│   │   │   ├── PipelinesTab.tsx         # Airflow Orchestration & Manual DAG dispatch
│   │   │   ├── StreamingTab.tsx         # Kafka Broker Telemetry & DLQ Inspector
│   │   │   ├── DataQualityTab.tsx       # Great Expectations Quality Scorecard
│   │   │   └── AnalyticsTab.tsx         # Dimensional Marts & Revenue Trend Visualizer
│   │   ├── services/api.ts              # Type-safe API client with auto-refresh
│   │   ├── App.tsx                      # Root application layout
│   │   ├── types.ts                     # TypeScript interface definitions
│   │   └── index.css                    # Tailwind CSS with custom sleek scrollbar
│   ├── index.html                       # HTML5 entry point
│   └── package.json                     # Frontend dependencies and build scripts
│
├── data_generator/                      # High-Scale Synthetic Data Generator
│   ├── generator.py                     # Generates 100k+ records across 9 entities
│   ├── config.py                        # Anomaly injection rates & distributions
│   └── schemas.py                       # Pydantic entity schema validators
│
├── ingestion/                           # Ingestion Subsystems
│   ├── batch/
│   │   ├── batch_ingestor.py            # REST client with rate limiting & backoff
│   │   └── checkpoint_manager.py        # State persistence for idempotent batch runs
│   └── streaming/
│       ├── kafka_producer.py            # High-throughput multi-topic event producer
│       ├── kafka_consumer.py            # Consumer group with deduplication & DLQ routing
│       ├── event_schemas.py             # Streaming Pydantic models
│       └── dead_letter_queue.py         # Poison pill quarantine router & inspector
│
├── storage/                             # Storage Clients & Drivers
│   ├── lake_storage.py                  # S3/MinIO & local filesystem lake manager
│   ├── postgres_client.py               # PostgreSQL client with connection pooling
│   └── mongo_client.py                  # MongoDB driver for raw clickstream events
│
├── processing/                          # Distributed & Local Processing Engines
│   ├── pandas/
│   │   ├── bronze_to_silver.py          # Data cleansing, validation & quarantine
│   │   ├── silver_to_gold.py            # Star schema modeling & marts creation
│   │   └── scd2_handler.py              # Slowly Changing Dimension Type 2 engine
│   └── spark/
│       ├── batch_processor.py           # PySpark distributed ETL pipeline
│       └── scd2_spark.py                # PySpark SCD2 dimension merge
│
├── warehouse/                           # Analytical Serving Warehouse
│   ├── warehouse_manager.py             # DuckDB columnar engine executing on Gold Parquet
│   └── bigquery_schemas.sql             # Google BigQuery partitioned & clustered DDL
│
├── dbt/                                 # dbt Transformation Models & Tests
│   ├── models/staging/                  # Cleaned staging SQL views
│   ├── models/intermediate/             # Joined line items & customer metrics
│   ├── models/marts/                    # Materialized fact & dimension tables
│   ├── tests/                           # Schema integrity assertions
│   └── dbt_runner.py                    # Standalone dbt model compilation runner
│
├── airflow/                             # Pipeline Orchestration
│   ├── dags/                            # 7 production Medallion workflow DAGs
│   └── airflow_runner.py                # Standalone scheduler & WAL execution audit
│
├── data_quality/                        # Reliability & Anomaly Quarantine
│   ├── expectations_suite.py            # Great Expectations validation suites
│   ├── quarantine_manager.py            # Quarantine isolation with diagnostic tags
│   └── validation_runner.py             # Audit runner generating health scorecards
│
├── monitoring/                          # Observability Stack
│   ├── prometheus/prometheus.yml        # Prometheus scrape configurations
│   └── grafana/dashboards/              # Pre-configured Grafana monitoring dashboards
│
├── infrastructure/                      # DevOps & Cloud IaC
│   ├── docker/                          # Dockerfiles for services
│   └── terraform/                       # AWS S3, Glue, Athena, IAM provisioning
│
├── scripts/                             # Utility & Automation Scripts
│   ├── autonomous_control_runner.py     # Automated 9-step system verification suite
│   ├── run_all_pipelines.py             # Master end-to-end pipeline execution
│   └── run_streaming_simulation.py      # Kafka & DLQ traffic simulation
│
├── tests/                               # Automated Test Suite (21 Pytest tests)
├── docker-compose.yml                   # 10-service container orchestration
├── run_all.py                           # Single-command all-in-one launcher
├── start.bat                            # Windows one-click launcher
├── requirements.txt                     # Python dependencies
└── README.md                            # System Documentation
```

---

## 11. Security, Governance & Operational Best Practices

- **Zero Hardcoded Secrets**: All credentials, database URIs, API keys, and JWT secrets are dynamically loaded from environment variables and `.env` files via Pydantic `BaseSettings`.
- **HMAC-SHA256 JWT Authentication**: Administrative operations (such as triggering Airflow DAG workflows or purging data) require valid cryptographic bearer tokens issued by the auth service.
- **Strict Quarantine Isolation**: Defective, schema-invalid, or contaminated records are automatically diverted to isolated quarantine directories without interrupting production execution or contaminating analytical tables.
- **Concurrency & Resource Isolation**: Columnar queries and SQLite execution logs use cursor isolation and Write-Ahead Logging (`WAL`) to prevent database file locks during high-concurrency read and write cycles.
- **Least-Privilege Cloud IaC**: Terraform templates explicitly define granular AWS IAM policies restricted to required S3 bucket prefixes and Glue databases, strictly avoiding wildcard permissions.

---

## 12. License

This project is licensed under the Apache License, Version 2.0. See the `LICENSE` file for details.
