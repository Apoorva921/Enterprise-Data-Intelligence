// ============================================================================
// MongoDB Initialization Script for Raw Event Ingestion
// Database: ecommerce_events
// ============================================================================

const db = db.getSiblingDB('ecommerce_events');

// Create collections
db.createCollection('raw_customer_events');
db.createCollection('raw_sessions');
db.createCollection('dead_letter_events');

// Indexes for raw_customer_events
db.raw_customer_events.createIndex({ "event_id": 1 }, { unique: true });
db.raw_customer_events.createIndex({ "session_id": 1 });
db.raw_customer_events.createIndex({ "customer_id": 1 });
db.raw_customer_events.createIndex({ "timestamp": -1 });
db.raw_customer_events.createIndex({ "event_type": 1 });

// Indexes for raw_sessions
db.raw_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.raw_sessions.createIndex({ "customer_id": 1 });
db.raw_sessions.createIndex({ "session_start": -1 });

// Indexes for dead_letter_events
db.dead_letter_events.createIndex({ "message_id": 1 }, { unique: true });
db.dead_letter_events.createIndex({ "failed_at": -1 });
db.dead_letter_events.createIndex({ "topic": 1 });

print("MongoDB collections and indexes initialized successfully for ecommerce_events.");

