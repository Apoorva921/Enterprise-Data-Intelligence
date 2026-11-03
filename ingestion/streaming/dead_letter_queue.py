"""
Dead-Letter Queue (DLQ) Manager.
Captures failed or malformed streaming messages with failure diagnostics,
stores in DLQ topic / persistent store, and provides inspection and replay capability.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DeadLetterQueue")


class DeadLetterQueue:
    def __init__(self, dlq_dir: str = "data/dlq"):
        self.dlq_dir = os.path.abspath(dlq_dir)
        os.makedirs(self.dlq_dir, exist_ok=True)
        self.log_file = os.path.join(self.dlq_dir, "dlq_messages.jsonl")

    def route_to_dlq(self, topic: str, raw_payload: Any, error_reason: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Routes a poison-pill or schema-invalid streaming message to DLQ."""
        dlq_entry = {
            "dlq_id": f"dlq_{datetime.now(timezone.utc).timestamp()}_{os.urandom(4).hex()}",
            "topic": topic,
            "raw_payload": raw_payload,
            "error_reason": error_reason,
            "metadata": metadata or {},
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "status": "UNRESOLVED",
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(dlq_entry, default=str) + "\n")

        logger.warning(f"[DLQ ROUTED] Topic '{topic}' message rejected: {error_reason}")
        return dlq_entry

    def get_dlq_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent DLQ messages for debugging and monitoring dashboard."""
        if not os.path.exists(self.log_file):
            return []
        
        messages = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                    except Exception:
                        pass
        return messages[-limit:]

    def get_count(self) -> int:
        """Returns total messages in DLQ."""
        if not os.path.exists(self.log_file):
            return 0
        with open(self.log_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

