WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)
SELECT
    order_id AS order_key,
    order_id,
    customer_id,
    CAST(strftime(order_date, '%Y%m%d') AS INTEGER) AS date_key,
    order_date,
    order_status,
    subtotal,
    shipping_fee,
    tax_amount,
    discount_amount,
    total_amount,
    shipping_region,
    channel
FROM orders
