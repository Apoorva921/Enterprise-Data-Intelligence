WITH source AS (
    SELECT * FROM read_parquet('data/lake/silver/orders/**/*.parquet')
)
SELECT
    order_id,
    customer_id,
    CAST(order_date AS TIMESTAMP) AS order_date,
    status AS order_status,
    CAST(subtotal AS DECIMAL(12, 2)) AS subtotal,
    CAST(shipping_fee AS DECIMAL(10, 2)) AS shipping_fee,
    CAST(tax_amount AS DECIMAL(10, 2)) AS tax_amount,
    CAST(discount_amount AS DECIMAL(10, 2)) AS discount_amount,
    CAST(total_amount AS DECIMAL(12, 2)) AS total_amount,
    shipping_region,
    channel,
    order_year_month
FROM source
WHERE total_amount > 0 AND customer_id != 'CUST-NONEXISTENT'
