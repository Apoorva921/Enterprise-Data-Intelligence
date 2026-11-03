"""
Checkpoint Manager for Incremental Batch Ingestion.
Maintains state of last extracted watermark / timestamp / cursor per pipeline.
"""
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class CheckpointManager:
    def __init__(self, db_path: str = "data/checkpoints.sqlite"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                pipeline_id TEXT PRIMARY KEY,
                last_checkpoint TEXT NOT NULL,
                records_processed INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def get_checkpoint(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pipeline_id, last_checkpoint, records_processed, status, updated_at FROM checkpoints WHERE pipeline_id = ?",
            (pipeline_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "pipeline_id": row[0],
                "last_checkpoint": row[1],
                "records_processed": row[2],
                "status": row[3],
                "updated_at": row[4],
            }
        return None

    def set_checkpoint(self, pipeline_id: str, last_checkpoint: str, records_count: int, status: str = "SUCCESS"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO checkpoints (pipeline_id, last_checkpoint, records_processed, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(pipeline_id) DO UPDATE SET
                last_checkpoint = excluded.last_checkpoint,
                records_processed = excluded.records_processed,
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (pipeline_id, last_checkpoint, records_count, status, now))
        conn.commit()
        conn.close()

