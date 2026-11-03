-- Test asserts referential integrity: every payment must link to a valid order.
-- Returns orphaned payments (0 rows = test passed)
SELECT 
    p.payment_id,
    p.order_id
FROM {{ ref('stg_payments') }} p
LEFT JOIN {{ ref('stg_orders') }} o ON p.order_id = o.order_id
WHERE o.order_id IS NULL
