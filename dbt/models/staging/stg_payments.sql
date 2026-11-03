WITH source AS (
    SELECT * FROM read_parquet('data/lake/silver/payments/*.parquet')
)
SELECT
    payment_id,
    order_id,
    customer_id,
    payment_method,
    payment_status,
    transaction_id,
    CAST(amount AS DECIMAL(12, 2)) AS amount,
    currency,
    CAST(payment_date AS TIMESTAMP) AS payment_date,
    CASE WHEN payment_status = 'SUCCESS' THEN TRUE ELSE FALSE END AS is_successful
FROM source
