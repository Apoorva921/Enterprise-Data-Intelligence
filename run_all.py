"""
Single All-in-One Platform Launcher.
Orchestrates:
1. Synthetic Data Generation (100k+ records)
2. Database Schema Initialization
3. Medallion ETL Pipelines (Bronze -> Silver -> Gold)
4. dbt Transformations and SQL Quality Assertions
5. Great Expectations Data Reliability Audit
6. Real-Time Kafka Streaming Simulation
7. Starts the unified server hosting both the React Dashboard and REST API at:
   >>> http://localhost:8000 <<<
"""
import os
import sys
import time
import webbrowser
import threading

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def open_browser(url: str, delay_sec: float = 1.5):
    time.sleep(delay_sec)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    print("=" * 70)
    print("  ENTERPRISE REAL-TIME DATA INTELLIGENCE PLATFORM")
    print("  ALL-IN-ONE AUTOMATED RUNNER & UNIFIED APPLICATION")
    print("=" * 70)

    # 1. Check or generate synthetic data
    raw_orders = os.path.join(BASE_DIR, "data", "raw", "orders.parquet")
    if not os.path.exists(raw_orders):
        print("\n[1/4] Generating 100,000+ historical synthetic records...")
        from data_generator.config import GeneratorConfig
        from data_generator.generator import ECommerceDataGenerator
        gen = ECommerceDataGenerator(config=GeneratorConfig(num_orders=100000, num_customers=5000))
        gen.generate_all(output_dir="data/raw")
    else:
        print("\n[1/4] Historical raw datasets found in data/raw (100k+ records ready).")

    # 2. Run master Medallion ETL & dbt & Great Expectations
    print("\n[2/4] Executing Medallion Lakehouse Pipeline (Bronze -> Silver -> Gold)...")
    from scripts.run_all_pipelines import main as run_pipelines
    run_pipelines()

    # 3. Run streaming simulation
    print("\n[3/4] Running Real-Time Streaming Simulation (Kafka + DLQ)...")
    from scripts.run_streaming_simulation import main as run_streaming
    run_streaming()

    # 4. Start Unified Server (serves React Dashboard + FastAPI Backend + Docs)
    url = "http://localhost:8000"
    print("\n" + "=" * 70)
    print(f"  PLATFORM IS READY! OPEN THIS SINGLE LINK IN YOUR BROWSER:")
    print(f"  >>> {url} <<<")
    print("=" * 70)
    print("  * Unified React Dashboard:  http://localhost:8000")
    print("  * Interactive Swagger Docs: http://localhost:8000/docs")
    print("  * Prometheus Metrics:       http://localhost:8000/api/metrics")
    print("  * Health Check:             http://localhost:8000/api/health")
    print("=" * 70 + "\n")

    # Auto-open browser in background thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Launch server
    import uvicorn
    from backend.app.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()

