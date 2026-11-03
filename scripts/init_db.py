"""
Database Initialization Script.
Creates tables, constraints, indexes and views for PostgreSQL and SQLite.
"""
import sys
import os

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.postgres_client import DatabaseClient


def main():
    print(">> Initializing operational database schemas and tables...")
    client = DatabaseClient()
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "schemas", "postgres_schema.sql")
    client.execute_script(schema_path)
    print(f">> [OK] Database schema initialized successfully on {'PostgreSQL' if client.is_postgres else 'SQLite fallback'}.")
    client.close()


if __name__ == "__main__":
    main()
