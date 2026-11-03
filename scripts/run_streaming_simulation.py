"""
Streaming Simulation Script.
Produces simulated e-commerce events to Kafka topics, runs consumers,
demonstrates DLQ routing for invalid events and deduplication.
"""
import sys
import os
import time

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.streaming.kafka_producer import ECommerceStreamProducer
from ingestion.streaming.kafka_consumer import ECommerceStreamConsumer
from ingestion.streaming.dead_letter_queue import DeadLetterQueue


def main():
    print("============================================================")
    print(">> Starting Real-Time Streaming Simulation")
    print("============================================================")

    producer = ECommerceStreamProducer()
    dlq = DeadLetterQueue()
    order_consumer = ECommerceStreamConsumer(topic="orders", dlq=dlq)

    # 1. Produce 20 simulated order events
    print(">> Producing 20 simulated order events...")
    generated_orders = []
    for _ in range(20):
        order = producer.generate_simulated_order_event()
        producer.produce(topic="orders", key=order["order_id"], value=order)
        generated_orders.append(order)

    # Inject an intentional duplicate event
    dup_order = generated_orders[0]
    print(f">> Injecting intentional duplicate order: {dup_order['order_id']}")
    producer.produce(topic="orders", key=dup_order["order_id"], value=dup_order)

    # Inject an intentional poison-pill (schema-invalid) event
    poison_order = {
        "order_id": "POISON-999",
        "customer_id": "CUST-999",
        "order_date": "2024-01-01",
        "status": "INVALID",
        "total_amount": -150.00,  # Negative amount violates schema validator
        "shipping_region": "Unknown",
        "channel": "Web"
    }
    print(f">> Injecting intentional poison-pill event with negative total: ${poison_order['total_amount']}")
    producer.produce(topic="orders", key="POISON-999", value=poison_order)

    # 2. Consume events
    print("\n>> Consuming streamed events with Consumer Group...")
    result = order_consumer.consume_batch(max_messages=50)

    print(f"\n>> Streaming Processing Results:")
    print(f"   Total Messages Consumed: {result['consumed_count']}")
    print(f"   Valid Events Accepted:   {result['valid_count']}")
    print(f"   Duplicates Filtered:     {result['duplicate_count']}")
    print(f"   Poison Messages to DLQ:  {result['dlq_count']}")

    dlq_messages = dlq.get_dlq_messages(limit=3)
    if dlq_messages:
        print(f"\n>> Last DLQ Rejection Diagnostic:")
        last = dlq_messages[-1]
        print(f"   DLQ ID:       {last['dlq_id']}")
        print(f"   Error Reason: {last['error_reason']}")

    print("\n[SUCCESS] Streaming simulation completed successfully!")


if __name__ == "__main__":
    main()
