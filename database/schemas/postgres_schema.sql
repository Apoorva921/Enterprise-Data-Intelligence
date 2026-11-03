-- ============================================================================
-- Enterprise Real-Time Data Intelligence Platform
-- Operational Relational Schema (PostgreSQL DDL)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS operational;
SET search_path TO operational, public;

-- ----------------------------------------------------------------------------
-- 1. CUSTOMERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(32),
    city VARCHAR(64) NOT NULL,
    state VARCHAR(32) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(32) NOT NULL DEFAULT 'USA',
    region VARCHAR(64) NOT NULL,
    segment VARCHAR(32) NOT NULL CHECK (segment IN ('Consumer', 'Small Business', 'Enterprise', 'VIP')),
    account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (account_status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_customers_region ON customers(region);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- ----------------------------------------------------------------------------
-- 2. PRODUCTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) PRIMARY KEY,
    sku VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    cost NUMERIC(10, 2) NOT NULL CHECK (cost >= 0),
    supplier_id VARCHAR(32) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);

-- ----------------------------------------------------------------------------
-- 3. ORDERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('PENDING', 'PROCESSING', 'SHIPPED', 'COMPLETED', 'CANCELLED', 'REFUNDED')),
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0),
    shipping_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(12, 2) NOT NULL,
    shipping_region VARCHAR(64) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_region ON orders(shipping_region);

-- ----------------------------------------------------------------------------
-- 4. ORDER ITEMS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_price NUMERIC(12, 2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

-- ----------------------------------------------------------------------------
-- 5. PAYMENTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    customer_id VARCHAR(32) NOT NULL,
    payment_method VARCHAR(32) NOT NULL,
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('SUCCESS', 'FAILED', 'PENDING')),
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    payment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    error_message TEXT,
    is_simulated BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);

-- ----------------------------------------------------------------------------
-- 6. REFUNDS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refunds (
    refund_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    payment_id VARCHAR(32) NOT NULL,
    refund_amount NUMERIC(12, 2) NOT NULL CHECK (refund_amount >= 0),
    refund_reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PROCESSED', 'REJECTED')),
    refund_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_refunds_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refunds_order ON refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status);

-- ----------------------------------------------------------------------------
-- 7. INVENTORY TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id VARCHAR(32) PRIMARY KEY,
    product_id VARCHAR(32) NOT NULL,
    warehouse_id VARCHAR(32) NOT NULL,
    stock_level INTEGER NOT NULL CHECK (stock_level >= 0),
    reserved_stock INTEGER NOT NULL DEFAULT 0 CHECK (reserved_stock >= 0),
    reorder_point INTEGER NOT NULL DEFAULT 50,
    unit_cost NUMERIC(10, 2) NOT NULL,
    last_restocked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT uq_product_warehouse UNIQUE (product_id, warehouse_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id);

