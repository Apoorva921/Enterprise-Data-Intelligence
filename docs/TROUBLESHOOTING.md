# Troubleshooting & Operations Guide

## 1. Quick Diagnostic Checklist

| Symptom | Probable Cause | Remediation Step |
|---|---|---|
| **FastAPI fails to start with port conflict** | Port 8000 already bound by another process | Check running processes via `netstat -ano \| findstr :8000` or change port in `.env` |
| **dbt models fail with table not found** | Gold layer Parquet files not yet materialized | Run `python scripts/run_all_pipelines.py` to populate Bronze, Silver, and Gold layers |
| **Great Expectations shows Silver score < 100%** | Malformed data was not properly quarantined | Inspect quarantine directory `data/lake/quarantine/` and re-run Silver cleaning |
| **Kafka consumer lag growing** | Processing bottleneck or unhandled consumer exception | Inspect DLQ via `GET /api/streaming/dlq` for poison messages stalling the stream |
| **Docker Compose container exits unexpectedly** | Insufficient memory allocated to Docker daemon | Increase Docker Desktop memory limit to at least 4 GB RAM |

---

## 2. Common Operations Tasks

### A. Reprocessing Corrupted Batches
If bad data was ingested, the Medallion pipeline is completely idempotent:
```bash
# 1. Clean the lake layers
rm -rf data/lake/silver/* data/lake/gold/* data/lake/quarantine/*

# 2. Re-execute the master pipeline
python scripts/run_all_pipelines.py
```

### B. Triggering Airflow DAGs via CLI
```bash
# Trigger customer SCD2 processing
python -c "from airflow.airflow_runner import AirflowRunner; AirflowRunner().run_dag('customer_processing_dag')"

# Trigger dbt transformations
python -c "from airflow.airflow_runner import AirflowRunner; AirflowRunner().run_dag('warehouse_transformation_dag')"
```

### C. Inspecting Dead-Letter Queue (DLQ)
Query the FastAPI endpoint:
```bash
curl -s http://localhost:8000/api/streaming/dlq?limit=5 | jq .
```
Or view the persisted JSONL file:
```bash
head -n 5 data/dlq/dlq_messages.jsonl
```
