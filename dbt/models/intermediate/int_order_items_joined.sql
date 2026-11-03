WITH items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),
products AS (
    SELECT * FROM {{ ref('stg_products') }}
)
SELECT
    i.order_item_id,
    i.order_id,
    i.product_id,
    p.product_name,
    p.category,
    i.quantity,
    i.unit_price,
    p.unit_cost,
    i.discount_amount,
    i.total_price,
    ROUND(i.quantity * p.unit_cost, 2) AS total_cost,
    ROUND(i.total_price - (i.quantity * p.unit_cost), 2) AS gross_profit
FROM items i
JOIN products p ON i.product_id = p.product_id

