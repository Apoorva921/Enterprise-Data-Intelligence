WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
)
SELECT
    product_id AS product_key,
    product_id,
    sku,
    product_name,
    category,
    unit_price,
    unit_cost,
    gross_margin_pct,
    supplier_id,
    is_active
FROM products
