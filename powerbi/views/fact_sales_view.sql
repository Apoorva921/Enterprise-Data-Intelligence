-- Power BI Fact Sales DirectQuery / Import View
CREATE OR REPLACE VIEW view_powerbi_fact_sales AS
SELECT 
    f.order_id,
    f.customer_id,
    f.date_key,
    CAST(f.order_date AS DATE) AS order_date,
    f.status AS order_status,
    f.subtotal,
    f.shipping_fee,
    f.tax_amount,
    f.discount_amount,
    f.total_amount AS gross_amount,
    (f.total_amount - f.tax_amount - f.shipping_fee) AS net_amount,
    f.shipping_region,
    f.channel
FROM fact_orders f;

