# Enterprise-Scale Real-Time Data Intelligence Platform
[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React + TypeScript](https://img.shields.io/badge/Frontend-React%20%2B%20TS-61DAFB.svg)](https://react.dev/)
[![dbt](https://img.shields.io/badge/Transformation-dbt-FF694B.svg)](https://www.getdbt.com/)
[![Docker](https://img.shields.io/badge/Containers-Docker%20Compose-2496ED.svg)](docker-compose.yml)
[![Tests Passing](https://img.shields.io/badge/Pytest-21%20Passed-brightgreen.svg)](tests/)

> A production-grade, end-to-end Data Engineering and Intelligence platform for an enterprise e-commerce ecosystem. Ingests transactional batches and real-time Kafka event streams, cleanses and normalizes records via a Medallion Lakehouse Architecture, manages Slowly Changing Dimensions (SCD Type 2), validates data quality via Great Expectations with automated quarantine routing, transforms dimensional star schemas via dbt, and visualizes live intelligence through a React dashboard and Power BI.

---

## 1. Project Overview & Business Problem

Modern e-commerce platforms process millions of transactions daily across distributed microservices. Common enterprise data challenges include:
- **Disparate Ingestion**: Integrating high-velocity real-time clickstreams alongside periodic batch transactional feeds.
- **Data Quality Anomalies**: Handling negative prices, duplicate checkouts, and orphaned customer IDs without failing production pipelines.
- **Historical Attribution**: Tracking customer loyalty tier mutations over time without overwriting past revenue metrics.
- **Pipeline Observability**: Monitoring consumer lag, pipeline run durations, and data freshness with Prometheus and Grafana.

This platform resolves these challenges using an enterprise-grade **Medallion Lakehouse Architecture** (Bronze, Silver, Gold), Kimball Star Schema modeling, automated quarantine routing, and a modern React + FastAPI + Power BI interface.

---

## 2. Technology Stack & Architectural Roles

| Component | Technology | Architectural Role |
|---|---|---|
| **Data Generation** | Python 3.12+, Faker, NumPy | Generates >100,000 realistic e-commerce transactions across 9 entities with deliberate quality edge cases |
| **Batch Ingestion** | Python REST Client, Checkpoint Manager | Paginated extraction, exponential backoff, rate limiting (Token Bucket), persistent state tracking |
| **Streaming Ingestion** | Apache Kafka, Python Consumers | Event validation, consumer groups, duplicate detection, and Dead-Letter Queue (DLQ) poison routing |
| **Object Lake Storage** | MinIO / AWS S3 API | Immutable Bronze landing, partitioned Silver Parquet, and Gold dimensional tables |
| **Databases** | PostgreSQL & MongoDB | Relational transactional operational store; MongoDB document collection for flexible clickstream events |
| **Distributed Processing**| Apache Spark (PySpark) & Pandas | Distributed batch processing, schema enforcement, year-month partitioning, and SCD Type 2 merges |
| **Data Warehouse** | DuckDB (Local) & Google BigQuery | Local zero-credential analytical engine executing ANSI SQL against Parquet + BigQuery cloud DDL |
| **Data Transformation** | dbt (data build tool) | Staging views, intermediate joins, dimensional models, marts, and automated schema tests |
| **Orchestration** | Apache Airflow | 7 production DAGs: Daily batch, Customer SCD2, Orders, Payments, Inventory, dbt, and DQ validation |
| **Data Reliability** | Great Expectations | Multi-checkpoint validation, null/referential integrity checks, and automated quarantine manager |
| **Backend API** | FastAPI, Pydantic, JWT Auth | RESTful analytics API with 10+ endpoints, Prometheus metrics exporter, and Admin authentication |
| **Frontend Dashboard** | React 18, TypeScript, Tailwind CSS | Real-time monitoring: Executive Overview, Airflow Orchestration, Kafka Telemetry, DQ, and Analytics |
| **Business Intelligence** | Power BI, DAX | 25+ DAX financial/churn measures, pre-aggregated star schema views, and connection guide |
| **Observability** | Prometheus & Grafana | Custom metrics scraping, consumer lag tracking, pre-configured Grafana monitoring dashboards |
| **Infrastructure as Code**| Terraform & Docker Compose | 10-service Docker Compose deployment; Terraform AWS S3/IAM/Athena infrastructure templates |
| **Testing & CI/CD** | Pytest, GitHub Actions | 21 unit, integration, and data quality tests running on every pull request |

---

## 3. Medallion Data Architecture

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

## 4. Quick Start & Execution Guide

### Prerequisites
- Python 3.12+ (Python 3.13 supported)
- Node.js 20+ and npm
- Docker Desktop (optional for multi-container deployment)

### Step 1: Environment Setup
```bash
# Clone and enter workspace
git clone <repo-url>
cd enterprise-data-platform

# Install Python dependencies
pip install -r requirements.txt

# Configure environment secrets
cp .env.example .env
```

### Step 2: Generate Synthetic Historical Data (>100,000 Orders)
```bash
# Generates 100,000 orders + 9 entities (~450,000 records) with intentional anomalies
python scripts/generate_data.py --records 100000 --customers 5000
```

### Step 3: Execute End-to-End Medallion Pipeline
```bash
# Ingests Bronze -> Cleans Silver & Quarantines -> Models Gold Star Schema -> Executes dbt -> Runs Great Expectations
python scripts/run_all_pipelines.py
```

### Step 4: Run Real-Time Streaming Simulation
```bash
# Produces events, processes consumer group, filters duplicates, routes poison pills to DLQ
python scripts/run_streaming_simulation.py
```

### Step 5: Start Backend and Frontend Servers
```bash
# Terminal 1: Start FastAPI REST Backend (Port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start React + TypeScript Frontend (Port 3000)
cd frontend
npm run dev
```
Open **http://localhost:3000** in your browser to interact with the dashboard.  
Swagger API Docs are available at **http://localhost:8000/docs**.

---

## 5. Dockerized Multi-Service Deployment

To launch all 10 platform services in Docker containers:
```bash
docker compose up -d
```

| Service | Port | Description |
|---|---|---|
| **React Frontend** | `http://localhost:3000` | Real-time monitoring and BI interface |
| **FastAPI Backend** | `http://localhost:8000` | REST API and Prometheus metrics exporter |
| **PostgreSQL** | `localhost:5432` | Relational operational warehouse |
| **MongoDB** | `localhost:27017` | Unstructured clickstream document store |
| **Kafka & Zookeeper**| `localhost:9092` | Real-time streaming message bus |
| **MinIO Console** | `http://localhost:9001` | S3-compatible Object Lake browser |
| **Prometheus** | `http://localhost:9090` | Observability metrics scraper |
| **Grafana** | `http://localhost:3001` | Pre-provisioned operational dashboards |

---

## 6. Power BI Integration

The platform provides a complete integration layer for **Power BI Desktop**:
- **Connection Guide**: See [docs/POWERBI_CONNECTION_GUIDE.md](powerbi/POWERBI_CONNECTION_GUIDE.md) for step-by-step setup connecting via PostgreSQL DirectQuery or Parquet lake.
- **DAX Measures**: Over 25 pre-built production DAX formulas located in [powerbi/dax_measures.dax](powerbi/dax_measures.dax) (Gross Margin %, Revenue MoM Growth %, Customer Lifetime Value, Payment Success Rate %).
- **Analytical Views**: Ready-to-query SQL views located in `powerbi/views/`.

---

## 7. Automated Testing Suite

All tests can be executed with a single command:
```bash
pytest tests/ -v
```

**Test Coverage Summary (21 Passed)**:
- **Unit Tests**:
  - `test_generator.py`: Verifies customer segment distributions and intentional anomaly injection.
  - `test_batch_ingestion.py`: Verifies CheckpointManager state persistence and Bronze landing.
  - `test_streaming.py`: Verifies Kafka producer, consumer group deduplication, and DLQ routing.
  - `test_processing.py`: Verifies Silver deduplication, positive price bounds, and SCD Type 2 dimension versioning.
- **Integration Tests**:
  - `test_pipeline_e2e.py`: Executes warehouse aggregations and validates 5 dbt tests.
  - `test_api_endpoints.py`: Validates all FastAPI endpoints, pagination, and JWT admin security.
- **Data Quality Tests**:
  - `test_great_expectations.py`: Asserts that Bronze detects anomalies and Silver maintains 100% SLA conformance.

---

## 8. Repository Structure

```
enterprise-data-platform/
│
├── backend/                        # FastAPI REST API Backend
│   ├── app/
│   │   ├── api/routes.py           # REST endpoints
│   │   ├── core/                   # Security, JWT, settings
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── services/               # Data, pipeline, and streaming services
│   │   └── main.py                 # FastAPI application
│
├── frontend/                       # React 18 + TypeScript + Tailwind CSS UI
│   ├── src/
│   │   ├── components/             # Overview, Pipelines, Streaming, DQ, Analytics
│   │   ├── services/api.ts         # Backend API client with auto-polling
│   │   └── App.tsx                 # Master view router
│
├── data_generator/                 # High-performance synthetic data generator
│   ├── generator.py                # Generates >100,000 records across 9 entities
│   ├── config.py                   # Configurable anomaly injection rates
│   └── schemas.py                  # Pydantic entity schemas
│
├── ingestion/                      # Ingestion engines
│   ├── batch/                      # REST API client with backoff & checkpoints
│   └── streaming/                  # Kafka producer, consumer, DLQ manager
│
├── storage/                        # Storage layer clients
│   ├── lake_storage.py             # S3/MinIO & local Medallion filesystem lake
│   ├── postgres_client.py          # PostgreSQL client with connection pooling
│   └── mongo_client.py             # MongoDB client for clickstream events
│
├── processing/                     # Distributed & local data processing
│   ├── pandas/                     # Bronze-to-Silver & Silver-to-Gold pipelines
│   └── spark/                      # PySpark distributed batch cleaning & SCD2
│
├── warehouse/                      # Analytical Warehouse
│   ├── warehouse_manager.py        # DuckDB local warehouse engine
│   └── bigquery_schemas.sql        # Google BigQuery partitioned & clustered DDL
│
├── dbt/                            # dbt transformation models & tests
│   ├── models/staging/             # Cleaned staging views
│   ├── models/intermediate/        # Line item cost joins & customer metrics
│   ├── models/marts/               # Materialized fact and dimension tables
│   └── tests/                      # Custom schema assertions
│
├── airflow/                        # Apache Airflow orchestration
│   ├── dags/                       # 7 production DAGs
│   └── airflow_runner.py           # Standalone workflow runner & execution audit
│
├── data_quality/                   # Data reliability & quarantine
│   ├── expectations_suite.py       # Great Expectations assertions
│   ├── quarantine_manager.py       # Rejection isolation with diagnostic tags
│   └── validation_runner.py        # Audit runner producing health scores
│
├── monitoring/                     # Observability stack
│   ├── prometheus/                 # Scraping configuration
│   └── grafana/dashboards/         # Pre-configured monitoring dashboards
│
├── powerbi/                        # Power BI analytics integration
│   ├── dax_measures.dax            # 25+ DAX financial/operational measures
│   ├── views/                      # Star schema SQL views
│   └── POWERBI_CONNECTION_GUIDE.md # Connection handbook
│
├── infrastructure/                 # DevOps & Cloud provisioning
│   ├── docker/                     # Service Dockerfiles
│   └── terraform/                  # AWS S3, IAM, Athena, Glue IaC
│
├── tests/                          # Automated Pytest suite (21 tests)
├── docs/                           # Architecture, Data Flow, ERD, API specs
├── docker-compose.yml              # 10-service container orchestration
├── Makefile                        # Automation shortcuts
├── requirements.txt                # Python dependencies
└── README.md                       # Documentation
```

---

## 9. Security & Best Practices

- **Zero Hardcoded Secrets**: All credentials dynamically read from `.env` and environment variables.
- **Least Privilege Access**: Terraform IAM policies explicitly scope S3 and Glue permissions without wildcards.
- **Input Validation**: Pydantic models validate every inbound payload on streaming and API layers.
- **Administrative Protection**: Pipeline triggers and administrative actions require signed HMAC-SHA256 JWT tokens.

---

## 10. License
Distributed under the Apache 2.0 License.

