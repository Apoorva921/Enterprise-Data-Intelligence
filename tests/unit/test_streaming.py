"""
Unit Tests for Streaming Ingestion & Dead-Letter Queue.
"""
import os
import pytest
from ingestion.streaming.kafka_producer import ECommerceStreamProducer
from ingestion.streaming.kafka_consumer import ECommerceStreamConsumer
from ingestion.streaming.dead_letter_queue import DeadLetterQueue


def test_streaming_producer_and_consumer(tmp_path):
    dlq = DeadLetterQueue(dlq_dir=os.path.join(tmp_path, "dlq"))
    producer = ECommerceStreamProducer()
    test_topic = f"test_orders_{os.urandom(4).hex()}"
    consumer = ECommerceStreamConsumer(topic=test_topic, dlq=dlq)

    # 1. Produce valid event
    valid_order = {
        "order_id": "TEST-ORD-001",
        "customer_id": "TEST-CUST-001",
        "order_date": "2024-01-01T00:00:00Z",
        "status": "COMPLETED",
        "total_amount": 99.50,
        "shipping_region": "North America",
        "channel": "Web"
    }
    producer.produce(test_topic, key="TEST-ORD-001", value=valid_order)

    # 2. Produce duplicate event
    producer.produce(test_topic, key="TEST-ORD-001", value=valid_order)

    # 3. Produce invalid poison-pill event
    poison_order = {
        "order_id": "POISON-001",
        "customer_id": "TEST-CUST-001",
        "order_date": "2024-01-01",
        "status": "INVALID",
        "total_amount": -50.00,  # Negative amount rejected by schema validator
        "shipping_region": "NA",
        "channel": "App"
    }
    producer.produce(test_topic, key="POISON-001", value=poison_order)

    # Consume batch
    res = consumer.consume_batch(max_messages=10)
    assert res["consumed_count"] >= 3
    assert res["valid_count"] >= 1
    assert res["duplicate_count"] >= 1
    assert res["dlq_count"] >= 1

    # Check DLQ storage
    dlq_messages = dlq.get_dlq_messages()
    assert len(dlq_messages) >= 1
    assert "Schema Validation Error" in dlq_messages[-1]["error_reason"]
