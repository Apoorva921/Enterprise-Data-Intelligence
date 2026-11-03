-- ============================================================================
-- Google BigQuery Production Analytical Warehouse DDL
-- Dataset: enterprise_dw
-- Optimized with Partitioning by DATE(order_date) and Clustering
-- ============================================================================

-- 1. STAGING / SILVER ORDERS
CREATE TABLE IF NOT EXISTS `enterprise_dw.silver_orders` (
    order_id STRING NOT NULL,
    customer_id STRING NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status STRING NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    shipping_fee NUMERIC(10, 2) NOT NULL,
    tax_amount NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    shipping_region STRING NOT NULL,
    channel STRING NOT NULL,
    _silver_processed_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(order_date)
CLUSTER BY customer_id, status, shipping_region
OPTIONS(
    description="Cleaned and validated orders partitioned by order date for cost-effective scanning."
);

-- 2. DIMENSION CUSTOMERS (SCD TYPE 2)
CREATE TABLE IF NOT EXISTS `enterprise_dw.dim_customers` (
    customer_key STRING NOT NULL,
    customer_id STRING NOT NULL,
    full_name STRING NOT NULL,
    email STRING NOT NULL,
    segment STRING NOT NULL,
    region STRING NOT NULL,
    city STRING NOT NULL,
    state STRING NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOL NOT NULL
)
CLUSTER BY customer_id, segment, region
OPTIONS(
    description="SCD Type 2 Customer dimension tracking segment and regional tier migrations over time."
);

-- 3. DIMENSION PRODUCTS
CREATE TABLE IF NOT EXISTS `enterprise_dw.dim_products` (
    product_key STRING NOT NULL,
    product_id STRING NOT NULL,
    sku STRING NOT NULL,
    name STRING NOT NULL,
    category STRING NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    gross_margin_pct FLOAT64 NOT NULL,
    supplier_id STRING NOT NULL
)
CLUSTER BY category, supplier_id;

-- 4. FACT ORDERS
CREATE TABLE IF NOT EXISTS `enterprise_dw.fact_orders` (
    order_key STRING NOT NULL,
    order_id STRING NOT NULL,
    customer_id STRING NOT NULL,
    date_key INT64 NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status STRING NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    shipping_fee NUMERIC(10, 2) NOT NULL,
    tax_amount NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    shipping_region STRING NOT NULL,
    channel STRING NOT NULL
)
PARTITION BY DATE(order_date)
CLUSTER BY status, shipping_region;

-- 5. EXECUTIVE REVENUE MART
CREATE OR REPLACE VIEW `enterprise_dw.view_executive_daily_revenue` AS
SELECT 
    DATE(order_date) as report_date,
    COUNT(order_id) as total_orders,
    COUNTIF(status = 'COMPLETED') as completed_orders,
    ROUND(SUM(total_amount), 2) as gross_revenue,
    ROUND(SAFE_DIVIDE(SUM(total_amount), COUNT(order_id)), 2) as average_order_value,
    ROUND(SAFE_DIVIDE(COUNTIF(status = 'COMPLETED'), COUNT(order_id)) * 100, 2) as order_completion_rate
FROM `enterprise_dw.fact_orders`
GROUP BY report_date
ORDER BY report_date DESC;

