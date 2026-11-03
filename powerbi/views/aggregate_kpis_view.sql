-- Power BI Aggregate Executive KPI View
CREATE OR REPLACE VIEW view_powerbi_aggregate_kpis AS
SELECT 
    d.order_day AS report_date,
    d.total_orders,
    d.completed_orders,
    d.total_gross_revenue,
    d.avg_order_value,
    ROUND((d.completed_orders * 100.0 / NULLIF(d.total_orders, 0)), 2) AS completion_rate_pct
FROM mart_daily_revenue d;
