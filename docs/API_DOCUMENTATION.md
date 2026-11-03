# FastAPI Analytics REST API Specification

Base URL: `http://localhost:8000/api`  
Interactive Swagger UI: `http://localhost:8000/docs`

---

## 1. Authentication

Administrative endpoints (such as triggering an Airflow pipeline) require a JWT Bearer token in the `Authorization` header.

### `POST /api/auth/login`
Authenticates administrative users.

**Request Body**:
```json
{
  "username": "admin",
  "password": "adminpassword123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

## 2. Health & Monitoring

### `GET /api/health`
System health check endpoint for container orchestrators and load balancers.

**Response (200 OK)**:
```json
{
  "status": "UP",
  "environment": "development",
  "timestamp": "2024-05-18T10:00:00Z",
  "components": {
    "warehouse": "HEALTHY",
    "storage_lake": "HEALTHY",
    "streaming_queue": "HEALTHY",
    "airflow_scheduler": "ACTIVE"
  }
}
```

### `GET /api/metrics`
Observability metrics in Prometheus exposition format (default) or JSON (`?format=json`).

---

## 3. Executive Business Intelligence

### `GET /api/kpis`
Summary of high-level performance indicators computed directly from the Gold analytical warehouse.

**Response (200 OK)**:
```json
{
  "total_orders": 97928,
  "total_revenue": 63619498.94,
  "avg_order_value": 649.66,
  "active_customers": 4950,
  "completion_rate": 37.55,
  "payment_success_rate": 88.15
}
```

### `GET /api/revenue?days=30`
Daily revenue time-series trends, regional sales distribution, and category profit margins.

---

## 4. Analytical Data Catalog

### `GET /api/orders`
Paginated and filterable orders fact table.

**Query Parameters**:
- `page` (int, default: 1): Page number.
- `page_size` (int, default: 25, max: 100): Records per page.
- `status` (string, optional): Order status (`COMPLETED`, `PENDING`, `CANCELLED`, etc.).
- `region` (string, optional): Geographical region filter.

### `GET /api/customers`
Paginated customer dimension with SCD Type 2 active record filtration.

### `GET /api/products`
Paginated product catalog with pricing, unit costs, and profit margin percentages.

---

## 5. Orchestration & Streaming

### `GET /api/pipelines`
Lists all 7 Airflow DAGs with their schedules and latest execution run states.

### `POST /api/pipelines/{dag_id}/trigger`
Triggers immediate execution of an Airflow DAG workflow. Protected by Admin JWT token.

### `GET /api/streaming/status`
Real-time Kafka streaming statistics, published event volume per topic, and consumer lag.

### `GET /api/streaming/dlq?limit=20`
Lists poison messages isolated in the Dead-Letter Queue with detailed diagnostic error messages.

### `GET /api/data-quality`
Returns latest Great Expectations validation audit, Silver conformance score, and quarantined entity counts.
