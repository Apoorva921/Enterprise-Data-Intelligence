-- Power BI Customer Dimension View with SCD2 Current Flag
CREATE OR REPLACE VIEW view_powerbi_dim_customer AS
SELECT 
    c.customer_key,
    c.customer_id,
    c.full_name,
    c.email,
    c.segment,
    c.region,
    c.city,
    c.state,
    c.effective_date,
    c.end_date,
    c.is_current
FROM dim_customers c;

