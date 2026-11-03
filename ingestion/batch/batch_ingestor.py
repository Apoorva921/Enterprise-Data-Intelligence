"""
Batch Ingestor Service.
Extracts data from raw datasets or REST feeds, injects audit metadata,
writes to Bronze layer, and records state in CheckpointManager.
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from storage.lake_storage import LakeStorage
from ingestion.batch.checkpoint_manager import CheckpointManager

logger = logging.getLogger("BatchIngestor")


class BatchIngestor:
    def __init__(self, lake_storage: Optional[LakeStorage] = None, checkpoint_mgr: Optional[CheckpointManager] = None):
        self.lake = lake_storage or LakeStorage()
        self.checkpoints = checkpoint_mgr or CheckpointManager()

    def ingest_entity_from_file(self, entity: str, source_file_path: str) -> Dict[str, Any]:
        """
        Ingests a raw data file (CSV or Parquet) into the Bronze lake layer with full audit metadata.
        """
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Source file not found: {source_file_path}")

        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger.info(f"Starting batch ingestion for entity '{entity}' (Batch ID: {batch_id})")

        if source_file_path.endswith(".parquet"):
            df = pd.read_parquet(source_file_path)
        else:
            df = pd.read_csv(source_file_path)

        record_count = len(df)
        bronze_path = self.lake.write_bronze(entity=entity, df=df, batch_id=batch_id)

        # Update persistent checkpoint
        self.checkpoints.set_checkpoint(
            pipeline_id=f"batch_{entity}",
            last_checkpoint=datetime.now(timezone.utc).isoformat(),
            records_count=record_count,
            status="SUCCESS"
        )

        logger.info(f"Successfully ingested {record_count:,} records for '{entity}' into Bronze -> {bronze_path}")
        return {
            "entity": entity,
            "batch_id": batch_id,
            "records_ingested": record_count,
            "bronze_path": bronze_path,
            "status": "COMPLETED",
        }

    def ingest_all_raw_entities(self, raw_dir: str = "data/raw") -> List[Dict[str, Any]]:
        """Ingests all available raw files into Bronze storage."""
        entities = ["customers", "products", "orders", "order_items", "payments", "refunds", "inventory", "sessions", "events"]
        results = []
        for ent in entities:
            parquet_path = os.path.join(raw_dir, f"{ent}.parquet")
            csv_path = os.path.join(raw_dir, f"{ent}.csv")
            source = parquet_path if os.path.exists(parquet_path) else csv_path
            if os.path.exists(source):
                res = self.ingest_entity_from_file(entity=ent, source_file_path=source)
                results.append(res)
            else:
                logger.warning(f"No source data file found for entity '{ent}' in {raw_dir}")
        return results

