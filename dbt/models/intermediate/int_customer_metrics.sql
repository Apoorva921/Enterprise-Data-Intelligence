WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)
SELECT
    customer_id,
    COUNT(order_id) AS total_orders,
    ROUND(SUM(total_amount), 2) AS lifetime_spend,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
FROM orders
GROUP BY customer_id

