WITH source AS (
    SELECT * FROM read_parquet('data/lake/silver/customers/*.parquet')
)
SELECT
    customer_id,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name,
    LOWER(TRIM(email)) AS email,
    phone,
    city,
    state,
    postal_code,
    country,
    region,
    segment,
    account_status,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CAST(updated_at AS TIMESTAMP) AS updated_at
FROM source
WHERE email IS NOT NULL AND customer_id IS NOT NULL

