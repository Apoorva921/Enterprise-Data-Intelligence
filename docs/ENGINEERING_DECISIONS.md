# Engineering Architecture Decisions Record (ADR)

## ADR-001: Medallion Architecture with Bronze, Silver, Gold Layers
- **Context**: The business requires both real-time event streaming and batch transaction processing across multiple source entities with differing schemas and quality guarantees.
- **Decision**: Adopt the Medallion Architecture. Bronze maintains raw source fidelity; Silver cleanses, normalizes, deduplicates, and quarantines bad records; Gold structures analytics into a Kimball Star Schema.
- **Trade-offs**: Requires intermediate storage overhead, but provides complete auditability, replayability, and isolates reporting queries from operational extraction locks.

---

## ADR-002: Dual-Engine Local & Cloud Warehousing (DuckDB & Google BigQuery)
- **Context**: Production workloads target Google BigQuery, but developers and CI/CD pipelines need a zero-credential, lightning-fast local execution environment.
- **Decision**: Provide drop-in dual-engine compatibility. Parquet files in the lake can be queried locally by DuckDB at millions of rows per second with identical SQL semantics, while BigQuery partitioned DDL and dbt profile targets are supplied for cloud deployment.
- **Benefits**: Local tests run in 3 seconds without incurring cloud compute costs or requiring IAM credentials.

---

## ADR-003: Automated Quarantine Pattern for Data Reliability
- **Context**: Transactional feeds often contain malformed records (negative pricing, malformed email strings, orphaned foreign keys). Dropping them silently hides data producer bugs; failing the entire pipeline halts operations.
- **Decision**: Implement the Automated Quarantine Manager. Records failing Great Expectations assertions are diverted into a quarantine bucket with rejection diagnostic metadata. Silver continues processing clean records with 100% SLA conformance.
- **Benefits**: Downstream analytics are never blocked, and data quality engineers have an auditable queue of bad data to remediate with producers.

---

## ADR-004: Slowly Changing Dimensions (SCD Type 2) for Customer History
- **Context**: E-commerce customers upgrade segments (Consumer -> Small Business -> VIP). Simple overwrites erase historical sales attribution.
- **Decision**: Implement Kimball SCD Type 2 on `dim_customers`. Each segment transition retires the prior record with an `end_date` and inserts a new active version with `is_current = True`.
- **Benefits**: Historical orders link to the customer's tier at the time of purchase, preserving accurate customer cohort analytics.

---

## ADR-005: Dead-Letter Queue (DLQ) in Kafka Streaming
- **Context**: Streaming consumers can encounter poison-pill messages (unparseable JSON, schema constraint violations) that crash the consumer loop or stall partition offsets.
- **Decision**: Wrap consumer message processing in validation blocks that divert unparseable messages to a dedicated `dead_letter_queue` topic and persistent store.
- **Benefits**: Consumer offsets continue advancing without manual intervention; operators can inspect and replay poison messages from the React dashboard.

