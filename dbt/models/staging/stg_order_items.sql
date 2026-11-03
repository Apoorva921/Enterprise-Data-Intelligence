WITH source AS (
    SELECT * FROM read_parquet('data/lake/silver/order_items/*.parquet')
)
SELECT
    order_item_id,
    order_id,
    product_id,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DECIMAL(10, 2)) AS unit_price,
    CAST(discount_amount AS DECIMAL(10, 2)) AS discount_amount,
    CAST(total_price AS DECIMAL(12, 2)) AS total_price
FROM source
WHERE quantity > 0

