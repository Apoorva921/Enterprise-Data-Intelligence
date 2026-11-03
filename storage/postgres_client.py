"""
Database Client with PostgreSQL & SQLite Seamless Adapter.
Provides connection pooling, DDL execution, data insertion, and query execution.
"""
import os
import sqlite3
from typing import List, Dict, Any, Optional
import pandas as pd


class DatabaseClient:
    def __init__(self, connection_string: Optional[str] = None):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", 5432))
        self.db = os.getenv("POSTGRES_DB", "ecommerce_dw")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
        
        self.sqlite_fallback_path = os.path.abspath("data/ecommerce_dw.sqlite")
        os.makedirs(os.path.dirname(self.sqlite_fallback_path), exist_ok=True)
        self.is_postgres = False
        self._init_connection()

    def _init_connection(self):
        """Attempts connection to PostgreSQL; seamlessly falls back to SQLite."""
        try:
            import psycopg2
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.db,
                user=self.user,
                password=self.password,
                connect_timeout=2
            )
            self.is_postgres = True
            print(">> Connected to PostgreSQL operational warehouse.")
        except Exception:
            self.is_postgres = False
            self.conn = sqlite3.connect(self.sqlite_fallback_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Enable foreign key constraints in SQLite
            self.conn.execute("PRAGMA foreign_keys = ON;")

    def execute(self, query: str, params: Optional[tuple] = None):
        """Executes a SQL statement."""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor
        except Exception as e:
            self.conn.rollback()
            raise e

    def execute_script(self, script_path: str):
        """Executes a multi-statement SQL script file."""
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not self.is_postgres:
            # Clean PostgreSQL specific syntax for SQLite compatibility
            clean_sql = content.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
            clean_sql = clean_sql.replace("NUMERIC(10, 2)", "REAL")
            clean_sql = clean_sql.replace("NUMERIC(12, 2)", "REAL")
            clean_sql = clean_sql.replace("CREATE SCHEMA IF NOT EXISTS operational;", "")
            clean_sql = clean_sql.replace("SET search_path TO operational, public;", "")
            cursor = self.conn.cursor()
            cursor.executescript(clean_sql)
            self.conn.commit()
        else:
            cursor = self.conn.cursor()
            cursor.execute(content)
            self.conn.commit()

    def load_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "append"):
        """Loads a pandas DataFrame into database table."""
        # Clean datetime columns to string format for reliable ingestion
        clean_df = df.copy()
        for col in clean_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            clean_df[col] = clean_df[col].astype(str)
        
        clean_df.to_sql(table_name, con=self.conn, if_exists=if_exists, index=False)
        self.conn.commit()

    def query_to_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Runs a SELECT query and returns the results as a pandas DataFrame."""
        return pd.read_sql_query(query, con=self.conn, params=params)

    def close(self):
        if self.conn:
            self.conn.close()

