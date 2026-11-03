WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
payments AS (
    SELECT * FROM {{ ref('stg_payments') }}
)
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_gross_revenue,
    ROUND(AVG(o.total_amount), 2) AS overall_avg_order_value,
    COUNT(DISTINCT o.customer_id) AS total_purchasing_customers,
    ROUND(SUM(CASE WHEN p.is_successful THEN 1 ELSE 0 END) * 100.0 / COUNT(p.payment_id), 2) AS payment_success_rate
FROM orders o
LEFT JOIN payments p ON o.order_id = p.order_id
