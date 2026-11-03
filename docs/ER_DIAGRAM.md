# Entity-Relationship & Star Schema Documentation

## 1. Operational Relational Schema (PostgreSQL)

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    CUSTOMERS ||--o{ CUSTOMER_SESSIONS : initiates
    CUSTOMERS {
        string customer_id PK
        string first_name
        string last_name
        string email
        string region
        string segment
        string account_status
        timestamp created_at
    }

    PRODUCTS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ INVENTORY : stocked_in
    PRODUCTS {
        string product_id PK
        string sku
        string name
        string category
        decimal price
        decimal cost
        string supplier_id
    }

    ORDERS ||--|{ ORDER_ITEMS : includes
    ORDERS ||--o{ PAYMENTS : pays_for
    ORDERS ||--o{ REFUNDS : refunded_by
    ORDERS {
        string order_id PK
        string customer_id FK
        timestamp order_date
        string status
        decimal subtotal
        decimal shipping_fee
        decimal tax_amount
        decimal total_amount
        string shipping_region
        string channel
    }

    ORDER_ITEMS {
        string order_item_id PK
        string order_id FK
        string product_id FK
        integer quantity
        decimal unit_price
        decimal discount_amount
        decimal total_price
    }

    PAYMENTS {
        string payment_id PK
        string order_id FK
        string customer_id
        string payment_method
        string payment_status
        string transaction_id
        decimal amount
        timestamp payment_date
    }

    REFUNDS {
        string refund_id PK
        string order_id FK
        string payment_id
        decimal refund_amount
        string refund_reason
        string status
        timestamp refund_date
    }

    INVENTORY {
        string inventory_id PK
        string product_id FK
        string warehouse_id
        integer stock_level
        integer reserved_stock
        decimal unit_cost
        timestamp last_restocked_at
    }
```

---

## 2. Analytical Warehouse Star Schema (Kimball Model)

```
                 +-------------------+
                 |    dim_dates      |
                 +-------------------+
                 | date_key (PK)     |
                 | full_date         |
                 | month_name        |
                 | quarter           |
                 | year              |
                 +---------+---------+
                           |
                           v
+-------------------+    +--------------------+    +--------------------+
|   dim_customers   |--->|    fact_orders     |<---|    dim_products    |
+-------------------+    +--------------------+    +--------------------+
| customer_key (PK) |    | order_key (PK)     |    | product_key (PK)   |
| customer_id       |    | order_id           |    | product_id         |
| full_name         |    | customer_id (FK)   |    | sku                |
| email             |    | date_key (FK)      |    | name               |
| segment           |    | status             |    | category           |
| region            |    | total_amount       |    | unit_price         |
| effective_date    |    | shipping_fee       |    | unit_cost          |
| end_date          |    | tax_amount         |    | gross_margin_pct   |
| is_current        |    | shipping_region    |    +---------+----------+
+-------------------+    +---------+----------+              |
                                   |                         |
                                   v                         v
                         +--------------------+    +---------+----------+
                         |   fact_payments    |    |  fact_order_items  |
                         +--------------------+    +--------------------+
                         | payment_key (PK)   |    | order_item_key(PK) |
                         | order_id (FK)      |    | order_id (FK)      |
                         | date_key (FK)      |    | product_id (FK)    |
                         | payment_method     |    | quantity           |
                         | amount             |    | total_price        |
                         | is_successful      |    | total_cost         |
                         +--------------------+    | gross_profit       |
                                                   +--------------------+
```

