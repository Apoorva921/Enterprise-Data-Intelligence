WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
)
SELECT
    CONCAT(customer_id, '_V1') AS customer_key,
    customer_id,
    full_name,
    email,
    segment,
    region,
    city,
    state,
    postal_code,
    country,
    account_status,
    DATE '2023-01-01' AS effective_date,
    DATE '9999-12-31' AS end_date,
    TRUE AS is_current
FROM customers

