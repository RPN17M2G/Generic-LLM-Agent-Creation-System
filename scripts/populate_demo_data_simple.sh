#!/bin/bash
# Simple script to populate ClickHouse with demo data using SQL commands
# Usage: ./populate_demo_data_simple.sh

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-8123}"
CLICKHOUSE_DB="${CLICKHOUSE_DB:-default}"
CLICKHOUSE_USER="${CLICKHOUSE_USER:-default}"

echo "Populating ClickHouse with demo data..."

# Create and populate users table
clickhouse-client --host=$CLICKHOUSE_HOST --port=$CLICKHOUSE_PORT --database=$CLICKHOUSE_DB --user=$CLICKHOUSE_USER <<EOF
CREATE TABLE IF NOT EXISTS users (
    id UInt32,
    name String,
    email String,
    age UInt8,
    created_at DateTime,
    status String
) ENGINE = MergeTree() ORDER BY id;

INSERT INTO users VALUES
(1, 'Alice Smith', 'alice@example.com', 30, now(), 'active'),
(2, 'Bob Johnson', 'bob@example.com', 25, now(), 'active'),
(3, 'Charlie Brown', 'charlie@example.com', 35, now(), 'inactive');

CREATE TABLE IF NOT EXISTS orders (
    id UInt32,
    user_id UInt32,
    product_id UInt32,
    quantity UInt16,
    price Decimal(10, 2),
    order_date DateTime,
    status String
) ENGINE = MergeTree() ORDER BY (order_date, id);

INSERT INTO orders VALUES
(1, 1, 1, 2, 99.99, now(), 'completed'),
(2, 2, 2, 1, 149.50, now(), 'pending'),
(3, 1, 3, 3, 49.99, now(), 'shipped');

CREATE TABLE IF NOT EXISTS products (
    id UInt32,
    name String,
    category String,
    price Decimal(10, 2),
    stock_quantity UInt16,
    created_at DateTime
) ENGINE = MergeTree() ORDER BY id;

INSERT INTO products VALUES
(1, 'Laptop Pro', 'Electronics', 999.99, 50, now()),
(2, 'Smartphone X', 'Electronics', 699.99, 100, now()),
(3, 'Wireless Headphones', 'Electronics', 199.99, 75, now());

CREATE TABLE IF NOT EXISTS logs (
    id UInt64,
    timestamp DateTime,
    level String,
    source String,
    message String,
    metadata String
) ENGINE = MergeTree() ORDER BY (timestamp, level);

INSERT INTO logs VALUES
(1, now(), 'INFO', 'api', 'User login successful', '{"user_id": 1}'),
(2, now(), 'ERROR', 'database', 'Connection timeout', '{"retry_count": 3}'),
(3, now(), 'WARNING', 'auth', 'Failed login attempt', '{"ip": "192.168.1.1"}');

CREATE TABLE IF NOT EXISTS trading_logs (
    id UInt64,
    timestamp DateTime,
    symbol String,
    price Decimal(10, 2),
    volume UInt32,
    message String,
    trade_type String
) ENGINE = MergeTree() ORDER BY (timestamp, symbol);

INSERT INTO trading_logs VALUES
(1, now(), 'AAPL', 150.25, 100, 'BUY order for AAPL at $150.25', 'BUY'),
(2, now(), 'GOOGL', 2800.50, 50, 'SELL order for GOOGL at $2800.50', 'SELL'),
(3, now(), 'MSFT', 350.75, 200, 'BUY order for MSFT at $350.75', 'BUY');

EOF

echo "Demo data populated successfully!"

