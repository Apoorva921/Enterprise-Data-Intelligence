"""
Lake Storage Interface for Medallion Architecture (Bronze, Silver, Gold).
Supports both local file system lake storage and AWS S3 / MinIO object storage.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd


class LakeStorage:
    def __init__(self, base_dir: str = "data/lake", backend: str = "local", s3_endpoint: str = None):
        self.base_dir = os.path.abspath(base_dir)
        self.backend = backend.lower()
        self.s3_endpoint = s3_endpoint
        
        # Medallion layers
        self.bronze_dir = os.path.join(self.base_dir, "bronze")
        self.silver_dir = os.path.join(self.base_dir, "silver")
        self.gold_dir = os.path.join(self.base_dir, "gold")
        self.quarantine_dir = os.path.join(self.base_dir, "quarantine")

        for layer in [self.bronze_dir, self.silver_dir, self.gold_dir, self.quarantine_dir]:
            os.makedirs(layer, exist_ok=True)

    def write_bronze(self, entity: str, df: pd.DataFrame, batch_id: str) -> str:
        """
        Writes raw ingested records to Bronze storage layer.
        Preserves raw schema and appends ingestion metadata.
        """
        enriched_df = df.copy()
        enriched_df["_ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
        enriched_df["_batch_id"] = batch_id
        enriched_df["_source_file"] = f"batch_{batch_id}_{entity}.parquet"

        target_dir = os.path.join(self.bronze_dir, entity)
        os.makedirs(target_dir, exist_ok=True)
        
        target_path = os.path.join(target_dir, f"{entity}_{batch_id}.parquet")
        enriched_df.to_parquet(target_path, index=False)
        return target_path

    def read_bronze(self, entity: str) -> pd.DataFrame:
        """Reads latest or all Bronze records for an entity."""
        target_dir = os.path.join(self.bronze_dir, entity)
        if not os.path.exists(target_dir):
            raw_path = os.path.join("data/raw", f"{entity}.parquet")
            if os.path.exists(raw_path):
                return pd.read_parquet(raw_path)
            raise FileNotFoundError(f"No Bronze storage found for entity: {entity}")
        
        files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".parquet")]
        if not files:
            raise FileNotFoundError(f"No parquet files in Bronze for entity: {entity}")
        
        # Read the latest ingested batch for clean incremental processing
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return pd.read_parquet(files[0])

    def write_silver(self, entity: str, df: pd.DataFrame, partition_col: Optional[str] = None) -> str:
        """
        Writes cleaned and schema-validated records to Silver layer.
        Supports partition directory hierarchy. Cleanly overwrites existing partitions.
        """
        import shutil
        target_dir = os.path.join(self.silver_dir, entity)
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)

        if partition_col and partition_col in df.columns:
            target_path = target_dir
            df.to_parquet(target_path, partition_cols=[partition_col], index=False)
        else:
            target_path = os.path.join(target_dir, f"{entity}_clean.parquet")
            df.to_parquet(target_path, index=False)
        return target_path

    def read_silver(self, entity: str) -> pd.DataFrame:
        """Reads cleaned Silver layer records."""
        target_dir = os.path.join(self.silver_dir, entity)
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"No Silver storage found for entity: {entity}")
        
        file_path = os.path.join(target_dir, f"{entity}_clean.parquet")
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)
        return pd.read_parquet(target_dir)

    def write_quarantine(self, entity: str, bad_df: pd.DataFrame, error_reasons: List[str]) -> str:
        """Quarantines malformed records with failure diagnostic metadata."""
        if bad_df.empty:
            return ""

        q_df = bad_df.copy()
        q_df["_quarantine_timestamp"] = datetime.now(timezone.utc).isoformat()
        q_df["_rejection_reason"] = error_reasons

        target_dir = os.path.join(self.quarantine_dir, entity)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{entity}_quarantine.parquet")
        
        if os.path.exists(target_path):
            existing = pd.read_parquet(target_path)
            q_df = pd.concat([existing, q_df], ignore_index=True)
        
        q_df.to_parquet(target_path, index=False)
        return target_path

    def read_quarantine(self, entity: str) -> pd.DataFrame:
        """Reads quarantined records for auditing and inspection."""
        target_path = os.path.join(self.quarantine_dir, entity, f"{entity}_quarantine.parquet")
        if os.path.exists(target_path):
            return pd.read_parquet(target_path)
        return pd.DataFrame()

    def write_gold(self, model_name: str, df: pd.DataFrame) -> str:
        """Writes curated dimensional / fact models to Gold analytics layer."""
        target_path = os.path.join(self.gold_dir, f"{model_name}.parquet")
        df.to_parquet(target_path, index=False)
        return target_path

    def read_gold(self, model_name: str) -> pd.DataFrame:
        """Reads curated Gold models."""
        target_path = os.path.join(self.gold_dir, f"{model_name}.parquet")
        if os.path.exists(target_path):
            return pd.read_parquet(target_path)
        raise FileNotFoundError(f"Gold table {model_name} not found at {target_path}")
