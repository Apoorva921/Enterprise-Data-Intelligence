WITH source AS (
    SELECT * FROM read_parquet('data/lake/silver/products/*.parquet')
)
SELECT
    product_id,
    sku,
    name AS product_name,
    category,
    CAST(price AS DECIMAL(10, 2)) AS unit_price,
    CAST(cost AS DECIMAL(10, 2)) AS unit_cost,
    CAST(gross_margin_pct AS DECIMAL(5, 2)) AS gross_margin_pct,
    supplier_id,
    is_active
FROM source
WHERE price > 0
