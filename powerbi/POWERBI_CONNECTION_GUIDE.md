# Power BI Desktop Integration Handbook
## Enterprise Real-Time Data Intelligence Platform

This guide provides technical instructions for connecting **Power BI Desktop** to the analytics warehouse layer of the platform.

---

### 1. Connection Architecture

Power BI connects directly to the curated **Gold Layer** and analytical views:

```
+--------------------------------------------------------------------+
|                         POWER BI DESKTOP                           |
|  - Star Schema Model (1 Fact Table : 3 Dimension Tables)           |
|  - 25+ DAX Financial, Churn, and Operational KPI Measures         |
|  - DirectQuery or Import Mode with Scheduled Incremental Refresh   |
+--------------------------------------------------------------------+
                                 |
                                 v
        +--------------------------------------------------+
        |                ANALYTICAL STORAGE                |
        |  Option A: PostgreSQL Container / Cloud Database |
        |  Option B: DuckDB Analytical Parquet Warehouse   |
        |  Option C: Google BigQuery Cloud Warehouse       |
        +--------------------------------------------------+
```

---

### 2. Option A: Connecting to PostgreSQL Operational Warehouse

1. Open **Power BI Desktop**.
2. Click **Get Data** -> **PostgreSQL Database** -> **Connect**.
3. In the connection dialog, enter:
   - **Server**: `localhost:5432` (or your Docker container / AWS RDS endpoint)
   - **Database**: `ecommerce_dw`
   - **Data Connectivity mode**: Select **DirectQuery** for live streaming queries, or **Import** for in-memory modeling.
4. When prompted for credentials, select **Database** and supply:
   - **User name**: `postgres`
   - **Password**: `postgrespassword` (or the secret set in your `.env`)
5. In the Navigator pane, select the four analytical views:
   - `view_powerbi_fact_sales`
   - `view_powerbi_dim_customer`
   - `view_powerbi_dim_product`
   - `view_powerbi_aggregate_kpis`
6. Click **Load**.

---

### 3. Option B: Connecting to Local DuckDB / Parquet Warehouse

If running the zero-credential local development warehouse:

1. In Power BI Desktop, choose **Get Data** -> **Parquet** (or **Folder**).
2. Browse to the absolute path:
   `c:\Users\sriva\OneDrive\Desktop\Data Engineer\data\lake\gold\`
3. Select and load:
   - `fact_orders.parquet`
   - `dim_customers.parquet`
   - `dim_products.parquet`
   - `dim_dates.parquet`
   - `mart_daily_revenue.parquet`
4. Click **Transform Data** (Power Query) or **Load**.

---

### 4. Option C: Connecting to Google BigQuery

1. In Power BI Desktop, click **Get Data** -> **Google BigQuery**.
2. Sign in with your corporate Google Cloud OAuth credentials.
3. Select your Project ID (e.g., `enterprise-data-intelligence`) and dataset `enterprise_dw`.
4. Select the tables `fact_orders`, `dim_customers`, and `dim_products`.
5. Select **DirectQuery** mode.

---

### 5. Establishing Star Schema Relationships in Power BI

Navigate to the **Model View** tab in Power BI Desktop and configure the following 1-to-many single-directional relationships:

| From Table (Dimension) | From Column | To Table (Fact) | To Column | Cardinality | Cross filter direction |
|---|---|---|---|---|---|
| `dim_customers` | `customer_id` | `fact_orders` | `customer_id` | 1 to Many (1:*) | Single |
| `dim_products` | `product_id` | `fact_order_items` | `product_id` | 1 to Many (1:*) | Single |
| `dim_dates` | `date_key` | `fact_orders` | `date_key` | 1 to Many (1:*) | Single |

---

### 6. Applying DAX Measures

1. In Power BI Desktop, click **New Table** under Modeling:
   ```dax
   _KeyMeasures = ROW("Description", "Centralized DAX Measure Repository")
   ```
2. Open `powerbi/dax_measures.dax` in any text editor.
3. Create the DAX measures one by one (e.g. `[Total Gross Revenue]`, `[Average Order Value (AOV)]`, `[Payment Success Rate %]`, `[Customer Lifetime Value]`).
4. Format currency measures as `$#,##0.00` and percentage measures as `0.0%`.
