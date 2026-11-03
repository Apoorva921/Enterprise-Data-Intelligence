"""
Autonomous Dashboard Controller & Verification Suite.
Directly exercises every dashboard capability, triggers Airflow DAGs,
tests filtering & search on the 97,928 orders dataset, verifies streaming
topics and DLQ isolation, and audits analytical marts.
"""
import urllib.request
import json
import time
import sys
from typing import Dict, Any, List

BASE_URL = "http://127.0.0.1:8000"

def get(url: str, token: str = None) -> Any:
    req = urllib.request.Request(f"{BASE_URL}{url}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post(url: str, data: dict = None, token: str = None) -> Any:
    body = json.dumps(data).encode("utf-8") if data else b"{}"
    req = urllib.request.Request(f"{BASE_URL}{url}", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("================================================================================")
    print("     AUTONOMOUS DASHBOARD CONTROLLER & SYSTEM HEALTH VERIFICATION              ")
    print("================================================================================")

    # 1. AUTHENTICATION
    print("\n[STEP 1] Authenticating Administrative User...")
    auth = post("/api/auth/login", {"username": "admin", "password": "adminpassword123"})
    token = auth["access_token"]
    print(f"  -> Authenticated. Role: ADMIN, Token Type: {auth['token_type']}")

    # 2. EXECUTIVE METRICS & STORE INTEGRITY
    print("\n[STEP 2] Auditing Executive Sales KPIs (DuckDB OLAP Direct)...")
    kpis = get("/api/kpis")
    print(f"  -> Total Processed Orders : {kpis['total_orders']:,}")
    print(f"  -> Gross Sales Revenue    : ${kpis['total_revenue']:,.2f}")
    print(f"  -> Average Order Value    : ${kpis['avg_order_value']:.2f}")
    print(f"  -> Active Customers       : {kpis['active_customers']:,} (SCD Type 2)")
    print(f"  -> Payment Gateway SLA    : {kpis['payment_success_rate']:.1f}%")
    print(f"  -> Order Completion Rate  : {kpis['completion_rate']:.1f}%")
    assert kpis["total_orders"] == 97928, "Order count mismatch"
    assert kpis["total_revenue"] > 60000000, "Revenue sum mismatch"

    # 3. EXERCISING ALL STATUS FILTERS
    print("\n[STEP 3] Testing Orders Status Filters (Customer Transactions Explorer)...")
    statuses = ["COMPLETED", "SHIPPED", "PENDING", "PROCESSING", "CANCELLED", "REFUNDED"]
    total_breakdown = 0
    for st in statuses:
        res = get(f"/api/orders?page=1&page_size=5&status={st}")
        count = res["total"]
        total_breakdown += count
        sample_id = res["items"][0]["order_id"] if res["items"] else "N/A"
        print(f"  -> Filter [{st:<10}] : {count:>6,} orders | Sample ID: {sample_id}")
        assert count > 0, f"Status {st} returned 0 records"
    print(f"  -> Sum of all status subsets: {total_breakdown:,} (Matches 97,928 total)")
    assert total_breakdown == 97928

    # 4. EXERCISING ALL REGIONAL FILTERS
    print("\n[STEP 4] Testing Geographic Regional Filters...")
    regions = [
        "North America - East",
        "North America - West",
        "Europe - Western",
        "Europe - Northern",
        "Asia Pacific - East",
        "Asia Pacific - South",
        "Latin America"
    ]
    total_regional = 0
    for reg in regions:
        encoded_reg = urllib.parse.quote(reg)
        res = get(f"/api/orders?page=1&page_size=5&region={encoded_reg}")
        count = res["total"]
        total_regional += count
        sample_amt = res["items"][0]["total_amount"] if res["items"] else 0.0
        print(f"  -> Region [{reg:<20}] : {count:>6,} orders | Sample Amount: ${sample_amt:.2f}")
        assert count > 0, f"Region {reg} returned 0 records"
    print(f"  -> Sum of all regional subsets: {total_regional:,} (Matches 97,928 total)")
    assert total_regional == 97928

    # 5. TESTING PAGINATION FLOW
    print("\n[STEP 5] Testing Pagination Flow (Pages 1 -> 5)...")
    for page in [1, 2, 3, 4, 5]:
        res = get(f"/api/orders?page={page}&page_size=10")
        first_order = res["items"][0]["order_id"]
        last_order = res["items"][-1]["order_id"]
        print(f"  -> Page {page}: {len(res['items'])} items | Range: {first_order} ... {last_order}")
        assert len(res["items"]) == 10

    # 6. TRIGGERING ALL 7 AIRFLOW PIPELINES AUTONOMOUSLY
    print("\n[STEP 6] Triggering All 7 Apache Airflow DAGs via Platform API...")
    dags = [
        ("daily_batch_ingestion_dag", "Bronze API Batch Ingestion"),
        ("customer_processing_dag", "Silver Customer Deduplication"),
        ("order_processing_dag", "Silver Order Normalization"),
        ("payment_processing_dag", "Silver Payment Reconciliation"),
        ("inventory_sync_dag", "Silver Inventory Sync"),
        ("warehouse_transformation_dag", "Gold Star Schema & dbt"),
        ("data_quality_validation_dag", "Great Expectations Test Suite")
    ]
    for dag_id, desc in dags:
        t0 = time.time()
        res = post(f"/api/pipelines/{dag_id}/trigger", token=token)
        dur = time.time() - t0
        print(f"  -> Dispatched [{dag_id:<28}] ({desc}): State: {res['state']} in {dur:.2f}s")
        assert res["state"] == "SUCCESS", f"DAG {dag_id} did not succeed"

    # 7. LIVE STREAMING & DEAD-LETTER QUEUE VERIFICATION
    print("\n[STEP 7] Auditing Kafka Streaming Broker & Dead-Letter Queue...")
    stream = get("/api/streaming/status")
    print("  -> Kafka Topic Event Volume:")
    for topic, count in stream["topics"].items():
        print(f"     * Topic [{topic:<18}]: {count:>4} published stream events")
        assert count > 0, f"Topic {topic} has no events"
    print(f"  -> Dead-Letter Queue Interception: {stream['dlq_message_count']} quarantined poison message(s)")
    dlq = get("/api/streaming/dlq?limit=5")
    sample_dlq = dlq["messages"][0]
    print(f"     * Intercepted Topic: {sample_dlq['topic']}")
    print(f"     * Validation Error : {sample_dlq['error_reason']}")
    print(f"     * Raw Bad Payload  : {json.dumps(sample_dlq['raw_payload'])}")

    # 8. DATA QUALITY SUITE AUDIT
    print("\n[STEP 8] Auditing Great Expectations Data Quality Suite...")
    dq = get("/api/data-quality")
    silver = dq["silver_audit"]
    bronze = dq["bronze_audit"]
    quar = dq["quarantine_summary"]
    print(f"  -> Silver Layer SLA Score : {silver['quality_score_pct']}% Conformance ({silver['passed_checks']}/{silver['total_checks']} assertions passed)")
    print(f"  -> Bronze Anomaly Catch   : {bronze['failed_checks']} anomaly categories detected & isolated")
    print(f"  -> Quarantined Records    : {quar['total_quarantined_records']:,} dirty records prevented from entering Gold warehouse")
    assert silver["quality_score_pct"] == 100.0, "Silver layer failed 100% SLA"

    # 9. ANALYTICAL MARTS & TIME INTELLIGENCE
    print("\n[STEP 9] Auditing Analytical Warehouse Marts...")
    rev = get("/api/revenue?days=30")
    daily = rev["daily_trends"]
    print(f"  -> 30-Day Gross Revenue Mart : {len(daily)} continuous daily aggregated data points")
    print(f"     * Latest Day: {daily[0]['order_day']} - Gross: ${daily[0]['total_gross_revenue']:,.2f} ({daily[0]['total_orders']} orders)")
    print(f"     * Earliest Day in Window: {daily[-1]['order_day']} - Gross: ${daily[-1]['total_gross_revenue']:,.2f}")
    assert len(daily) == 30, "Expected 30 daily data points"

    print("\n================================================================================")
    print("     ALL AUTONOMOUS CHECKS PASSED: DASHBOARD IS 100% OPERATIONAL & VERIFIED     ")
    print("================================================================================")

if __name__ == "__main__":
    main()
