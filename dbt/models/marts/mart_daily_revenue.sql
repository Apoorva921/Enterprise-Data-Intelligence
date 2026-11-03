WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)
SELECT
    CAST(order_date AS DATE) AS order_date,
    COUNT(order_id) AS total_orders,
    SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_orders,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
GROUP BY CAST(order_date AS DATE)
ORDER BY order_date DESC

