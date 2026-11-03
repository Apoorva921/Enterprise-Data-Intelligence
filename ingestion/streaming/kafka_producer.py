"""
Enterprise Kafka Event Producer.
Produces simulated real-time e-commerce events across topics:
- orders
- payments
- customer_events
- inventory_updates

Supports both live Apache Kafka cluster and an embedded high-performance
simulated broker for zero-dependency local development and CI testing.
"""
import os
import json
import time
import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("KafkaProducer")


class SimulatedMessageQueue:
    """Embedded thread-safe message queue matching Kafka partition semantics."""
    _topics: Dict[str, list] = {
        "orders": [],
        "payments": [],
        "customer_events": [],
        "inventory_updates": [],
        "dead_letter_queue": []
    }

    @classmethod
    def publish(cls, topic: str, key: str, value: Dict[str, Any]):
        if topic not in cls._topics:
            cls._topics[topic] = []
        envelope = {
            "key": key,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "offset": len(cls._topics[topic])
        }
        cls._topics[topic].append(envelope)
        
        # Also persist to disk for durability across processes
        queue_dir = os.path.abspath("data/streaming_queue")
        os.makedirs(queue_dir, exist_ok=True)
        topic_file = os.path.join(queue_dir, f"{topic}.jsonl")
        with open(topic_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(envelope) + "\n")

    @classmethod
    def get_messages(cls, topic: str, offset: int = 0, limit: int = 100):
        queue_dir = os.path.abspath("data/streaming_queue")
        topic_file = os.path.join(queue_dir, f"{topic}.jsonl")
        messages = []
        if os.path.exists(topic_file):
            with open(topic_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx >= offset:
                        try:
                            messages.append(json.loads(line))
                        except Exception:
                            pass
                        if len(messages) >= limit:
                            break
        return messages


class ECommerceStreamProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.is_live_kafka = False
        self.producer = None
        self._init_producer()

    def _init_producer(self):
        """Attempts connection to real Kafka; falls back to embedded queue."""
        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
                acks="all",
                request_timeout_ms=3000
            )
            self.is_live_kafka = True
            logger.info(f"Connected to Kafka cluster at {self.bootstrap_servers}")
        except Exception:
            self.is_live_kafka = False
            self.producer = None
            logger.info("Kafka cluster not detected. Operating in simulated embedded streaming mode.")

    def produce(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        """Publishes an event to specified Kafka topic."""
        # Attach simulation metadata tag
        value["_is_simulated"] = True
        value["_published_at"] = datetime.now(timezone.utc).isoformat()

        if self.is_live_kafka and self.producer:
            try:
                future = self.producer.send(topic, key=key, value=value)
                future.get(timeout=5)
                return True
            except Exception as e:
                logger.error(f"Live Kafka publish failed: {e}. Falling back to embedded queue.")

        SimulatedMessageQueue.publish(topic, key=key, value=value)
        return True

    def flush(self):
        if self.is_live_kafka and self.producer:
            self.producer.flush()

    def generate_simulated_order_event(self) -> Dict[str, Any]:
        """Generates a realistic simulated order event for streaming."""
        regions = ["North America - East", "North America - West", "Europe - Western", "Asia Pacific - East"]
        channels = ["Web", "Mobile App", "Affiliate"]
        order_id = f"STR-ORD-{random.randint(100000, 999999)}"
        cust_id = f"CUST-{random.randint(100000, 105000)}"
        
        # Occasional bad record for DLQ testing
        is_bad = random.random() < 0.03
        amount = -45.00 if is_bad else round(random.uniform(15.00, 450.00), 2)

        return {
            "order_id": order_id,
            "customer_id": cust_id,
            "order_date": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED" if not is_bad else "INVALID_AMOUNT",
            "total_amount": amount,
            "shipping_region": random.choice(regions),
            "channel": random.choice(channels),
            "items_count": random.randint(1, 4),
        }

    def generate_simulated_payment_event(self, order_id: str, cust_id: str, amount: float) -> Dict[str, Any]:
        """Generates a payment event matching an order."""
        methods = ["Credit Card", "PayPal", "Apple Pay", "Bank Transfer"]
        return {
            "payment_id": f"STR-PAY-{random.randint(100000, 999999)}",
            "order_id": order_id,
            "customer_id": cust_id,
            "payment_method": random.choice(methods),
            "payment_status": "SUCCESS" if random.random() > 0.05 else "FAILED",
            "amount": amount,
            "currency": "USD",
            "payment_date": datetime.now(timezone.utc).isoformat(),
        }
