"""
Unit Tests for Batch Ingestion & Checkpoint Manager.
"""
import os
import pytest
import pandas as pd
from ingestion.batch.checkpoint_manager import CheckpointManager
from ingestion.batch.batch_ingestor import BatchIngestor
from storage.lake_storage import LakeStorage


def test_checkpoint_manager(tmp_path):
    db_file = os.path.join(tmp_path, "test_checkpoints.sqlite")
    mgr = CheckpointManager(db_path=db_file)
    
    # Initial state
    assert mgr.get_checkpoint("test_pipeline") is None
    
    # Set and retrieve
    mgr.set_checkpoint("test_pipeline", "2024-01-01T00:00:00Z", 150, "SUCCESS")
    cp = mgr.get_checkpoint("test_pipeline")
    assert cp is not None
    assert cp["records_processed"] == 150
    assert cp["status"] == "SUCCESS"


def test_batch_ingestor_bronze_write(tmp_path):
    lake = LakeStorage(base_dir=os.path.join(tmp_path, "lake"))
    ingestor = BatchIngestor(lake_storage=lake)
    
    # Create sample raw parquet
    sample_raw = os.path.join(tmp_path, "sample.parquet")
    df = pd.DataFrame({"id": ["A1", "A2"], "val": [10, 20]})
    df.to_parquet(sample_raw)

    res = ingestor.ingest_entity_from_file("sample", sample_raw)
    assert res["status"] == "COMPLETED"
    assert res["records_ingested"] == 2
    
    # Read back from Bronze
    bronze_df = lake.read_bronze("sample")
    assert len(bronze_df) == 2
    assert "_ingestion_timestamp" in bronze_df.columns
    assert "_batch_id" in bronze_df.columns
