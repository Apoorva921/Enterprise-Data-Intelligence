-- Test asserts that no orders have non-positive total amounts.
-- Returns failing rows (should return 0 rows for test to pass)
SELECT 
    order_id,
    total_amount
FROM {{ ref('stg_orders') }}
WHERE total_amount <= 0
