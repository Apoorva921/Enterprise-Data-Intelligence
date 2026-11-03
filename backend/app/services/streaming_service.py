"""
Streaming Service for Kafka Topic and Consumer Status Telemetry.
"""
import os
import glob
from typing import Dict, Any, List

from ingestion.streaming.dead_letter_queue import DeadLetterQueue
from ingestion.streaming.kafka_producer import ECommerceStreamProducer


class StreamingService:
    def __init__(self):
        self.dlq = DeadLetterQueue()
        self.producer = ECommerceStreamProducer()

    def get_status(self) -> Dict[str, Any]:
        """Returns message counts per streaming topic and DLQ count."""
        topics = ["orders", "payments", "customer_events", "inventory_updates"]
        topic_counts = {}

        queue_dir = os.path.abspath("data/streaming_queue")
        for t in topics:
            t_file = os.path.join(queue_dir, f"{t}.jsonl")
            if os.path.exists(t_file):
                with open(t_file, "r", encoding="utf-8") as f:
                    count = sum(1 for line in f if line.strip())
            else:
                count = 0
            topic_counts[t] = count

        return {
            "status": "HEALTHY",
            "live_kafka_active": self.producer.is_live_kafka,
            "bootstrap_servers": self.producer.bootstrap_servers,
            "topics": topic_counts,
            "consumer_groups": {
                "ecommerce_consumer_group": {
                    "state": "STABLE",
                    "lag": 0,
                    "partitions_assigned": 4,
                }
            },
            "dlq_message_count": self.dlq.get_count(),
        }

    def get_dlq_sample(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.dlq.get_dlq_messages(limit=limit)

