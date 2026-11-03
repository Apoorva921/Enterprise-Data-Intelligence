-- Power BI Product Dimension View
CREATE OR REPLACE VIEW view_powerbi_dim_product AS
SELECT 
    p.product_key,
    p.product_id,
    p.sku,
    p.name AS product_name,
    p.category,
    p.unit_price,
    p.unit_cost,
    p.gross_margin_pct,
    p.supplier_id
FROM dim_products p;

