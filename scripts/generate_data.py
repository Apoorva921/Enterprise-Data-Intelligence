"""
CLI entry point to execute synthetic data generation.
Usage:
    python scripts/generate_data.py --records 100000 --output data/raw
"""
import argparse
import sys
import os

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.config import GeneratorConfig
from data_generator.generator import ECommerceDataGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce data.")
    parser.add_argument("--records", type=int, default=100000, help="Number of orders to generate (default: 100000)")
    parser.add_argument("--customers", type=int, default=5000, help="Number of customers to generate (default: 5000)")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory (default: data/raw)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    print("============================================================")
    print(">> Launching Enterprise Synthetic Data Generator")
    print(f"   Target Orders: {args.records:,}")
    print(f"   Target Customers: {args.customers:,}")
    print(f"   Destination: {args.output}")
    print("============================================================")

    config = GeneratorConfig(
        num_orders=args.records,
        num_customers=args.customers,
        num_products=500,
        num_sessions=min(25000, max(1000, args.records // 4))
    )

    generator = ECommerceDataGenerator(config=config, seed=args.seed)
    datasets = generator.generate_all(output_dir=args.output)

    total_records = sum(len(df) for df in datasets.values())
    print("\n[SUCCESS] Data Generation Complete!")
    print(f"   Total entities generated across 9 tables: {total_records:,} records.")


if __name__ == "__main__":
    main()
