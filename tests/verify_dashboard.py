import urllib.request
import json
import sys

BASE_URL = 'http://127.0.0.1:8000'

def test_endpoint(name, url, method='GET', data=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            status = resp.status
            parsed = json.loads(body) if body.startswith(('{', '[')) else body
            return status, parsed
    except Exception as e:
        return 500, str(e)

def run_audit():
    print("=== 1. TESTING HEALTH & ROOT STATIC ASSETS ===")
    st, body = test_endpoint('Root HTML', f"{BASE_URL}/")
    print(f"  [PASS] Root HTML: HTTP {st}, Bundle Size: {len(body)} bytes")
    assert st == 200 and '<!doctype html>' in body.lower()

    st, health = test_endpoint('Health', f"{BASE_URL}/api/health")
    print(f"  [PASS] Health API: HTTP {st}, Service Status: {health.get('status')}")
    assert st == 200 and health.get('status') == 'UP'

    print("\n=== 2. TESTING OVERVIEW & SALES APIS ===")
    st, kpis = test_endpoint('KPIs', f"{BASE_URL}/api/kpis")
    print(f"  [PASS] KPIs: Total Orders: {kpis.get('total_orders')}, Gross Revenue: ${kpis.get('total_revenue'):,.2f}, AOV: ${kpis.get('avg_order_value'):.2f}")
    assert st == 200 and kpis.get('total_orders') == 97928
    assert kpis.get('total_revenue') > 60000000

    st, orders_p1 = test_endpoint('Orders Page 1', f"{BASE_URL}/api/orders?page=1&page_size=10")
    print(f"  [PASS] Orders Pagination (Page 1): {len(orders_p1.get('items'))} items returned, Total: {orders_p1.get('total')}")
    assert st == 200 and len(orders_p1.get('items')) == 10 and orders_p1.get('total') == 97928

    st, orders_filter = test_endpoint('Filter Status COMPLETED', f"{BASE_URL}/api/orders?page=1&page_size=10&status=COMPLETED")
    print(f"  [PASS] Filter by Status 'COMPLETED': {orders_filter.get('total')} orders found")
    assert st == 200 and orders_filter.get('total') > 0
    for item in orders_filter.get('items'):
        assert item['status'] == 'COMPLETED'

    st, orders_region = test_endpoint('Filter Region', f"{BASE_URL}/api/orders?page=1&page_size=10&region=Europe%20-%20Western")
    print(f"  [PASS] Filter by Region 'Europe - Western': {orders_region.get('total')} orders found")
    assert st == 200 and orders_region.get('total') > 0
    for item in orders_region.get('items'):
        assert item['shipping_region'] == 'Europe - Western'

    print("\n=== 3. TESTING AUTOMATED PIPELINES & DISPATCH ===")
    st, pipes = test_endpoint('Pipelines Catalog', f"{BASE_URL}/api/pipelines")
    print(f"  [PASS] Pipelines Catalog: {len(pipes.get('pipelines'))} DAGs registered, {len(pipes.get('recent_runs'))} historical run audits")
    assert st == 200 and len(pipes.get('pipelines')) == 7

    # Test login
    st, auth = test_endpoint('Admin Login', f"{BASE_URL}/api/auth/login", method='POST', data={'username': 'admin', 'password': 'adminpassword123'})
    print(f"  [PASS] Admin Authentication: Token acquired ({auth.get('token_type', 'bearer')})")
    assert st == 200 and 'access_token' in auth
    token = auth['access_token']

    # Trigger DAG
    st, trig = test_endpoint('Trigger DAG', f"{BASE_URL}/api/pipelines/daily_batch_ingestion_dag/trigger", method='POST', headers={'Authorization': f"Bearer {token}"})
    print(f"  [PASS] Trigger 'daily_batch_ingestion_dag': State: {trig.get('state')}, Duration: {trig.get('duration_seconds')}s")
    assert st == 200 and trig.get('state') == 'SUCCESS'

    print("\n=== 4. TESTING LIVE STREAMING & DLQ POISON ISOLATION ===")
    st, stream = test_endpoint('Streaming Status', f"{BASE_URL}/api/streaming/status")
    topics = stream.get('topics')
    print(f"  [PASS] Kafka Broker Topics Active:")
    for top, count in topics.items():
        print(f"         - {top}: {count} stream events")
    assert st == 200 and stream.get('status') == 'HEALTHY'
    assert topics.get('orders') > 0
    assert topics.get('payments') > 0
    assert topics.get('customer_events') > 0
    assert topics.get('inventory_updates') > 0

    st, dlq = test_endpoint('DLQ Messages', f"{BASE_URL}/api/streaming/dlq?limit=5")
    print(f"  [PASS] Dead-Letter Queue: {dlq.get('count')} quarantined poison event(s)")
    assert st == 200 and dlq.get('count') >= 1
    sample = dlq.get('messages')[0]
    print(f"         - Quarantined topic: {sample.get('topic')}")
    print(f"         - Schema validation failure: {sample.get('error_reason')[:70]}...")

    print("\n=== 5. TESTING DATA QUALITY & QUARANTINE ===")
    st, dq = test_endpoint('Data Quality Audit', f"{BASE_URL}/api/data-quality")
    silver = dq.get('silver_audit')
    quar = dq.get('quarantine_summary')
    print(f"  [PASS] Great Expectations Silver Conformance: {silver.get('quality_score_pct')}% SLA ({silver.get('passed_checks')}/{silver.get('total_checks')} checks)")
    print(f"  [PASS] Total Quarantined Dirty Records: {quar.get('total_quarantined_records')}")
    assert st == 200 and silver.get('quality_score_pct') == 100.0
    assert quar.get('total_quarantined_records') > 0

    print("\n=== 6. TESTING ANALYTICS & WAREHOUSE MARTS ===")
    st, rev = test_endpoint('Revenue Analytics', f"{BASE_URL}/api/revenue?days=30")
    daily = rev.get('daily_trends')
    regional = rev.get('regional_breakdown')
    cats = rev.get('category_breakdown')
    print(f"  [PASS] 30-Day Daily Gross Revenue Mart: {len(daily)} daily timeline points")
    print(f"  [PASS] Regional Breakdown: {len(regional)} geographic regions analyzed")
    print(f"  [PASS] Product Catalog: {len(cats)} categories with average gross margin")
    assert st == 200 and len(daily) > 0 and len(regional) > 0 and len(cats) > 0

    print("\n" + "=" * 50)
    print("AUDIT RESULT: 100% COMPLETE & VERIFIED PROPERLY!")
    print("=" * 50)

if __name__ == '__main__':
    run_audit()

