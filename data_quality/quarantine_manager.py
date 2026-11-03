"""
Automated Data Quality Quarantine Manager.
Isolates anomalous, malformed, or orphaned records with detailed diagnostic failure metadata,
maintains audit history, and enables safe reprocessing and quarantine inspection.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from storage.lake_storage import LakeStorage

logger = logging.getLogger("QuarantineManager")


class QuarantineManager:
    def __init__(self, lake_storage: Optional[LakeStorage] = None):
        self.lake = lake_storage or LakeStorage()

    def quarantine_records(self, entity: str, bad_df: pd.DataFrame, error_reasons: List[str]) -> str:
        """Quarantines malformed records with failure diagnostic reasons."""
        if bad_df.empty:
            return ""
        path = self.lake.write_quarantine(entity, bad_df, error_reasons)
        logger.warning(f"Quarantined {len(bad_df):,} records for entity '{entity}' -> {path}")
        return path

    def get_quarantined_summary(self) -> Dict[str, Any]:
        """Provides summary of all quarantined records across entities."""
        entities = ["customers", "products", "orders", "order_items", "payments"]
        summary = {}
        total_quarantined = 0

        for ent in entities:
            try:
                df = self.lake.read_quarantine(ent)
                count = len(df)
                total_quarantined += count
                sample_reasons = df["_rejection_reason"].value_counts().head(3).to_dict() if "_rejection_reason" in df.columns and not df.empty else {}
                summary[ent] = {
                    "count": count,
                    "top_rejection_reasons": sample_reasons,
                }
            except Exception:
                summary[ent] = {"count": 0, "top_rejection_reasons": {}}

        return {
            "total_quarantined_records": total_quarantined,
            "entities": summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def inspect_quarantined_entity(self, entity: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns sample quarantined records for dashboard inspection."""
        try:
            df = self.lake.read_quarantine(entity)
            if df.empty:
                return []
            return df.head(limit).to_dict(orient="records")
        except Exception:
            return []

