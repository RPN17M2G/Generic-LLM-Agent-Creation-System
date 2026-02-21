"""
Script to populate ClickHouse with demo data for testing agents.
"""
import os
from clickhouse_connect import get_client
from datetime import datetime, timedelta
import random
import json

# Configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "default")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "example_password")

def get_clickhouse_client():
    """Get ClickHouse client connection."""
    return get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DB,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD
    )

def create_tables(client):
    """Create all necessary tables."""
    print("Creating tables...")
    
    # Users table
    client.command("""
    CREATE TABLE IF NOT EXISTS users (
        id UInt32,
        name String,
        email String,
        age UInt8,
        created_at DateTime,
        status String
    ) ENGINE = MergeTree()
    ORDER BY id
    """)
    print("✓ Created users table")
    
    # Orders table
    client.command("""
    CREATE TABLE IF NOT EXISTS orders (
        id UInt32,
        user_id UInt32,
        product_id UInt32,
        quantity UInt16,
        price Decimal(10, 2),
        order_date DateTime,
        status String
    ) ENGINE = MergeTree()
    ORDER BY (order_date, id)
    """)
    print("✓ Created orders table")
    
    # Products table
    client.command("""
    CREATE TABLE IF NOT EXISTS products (
        id UInt32,
        name String,
        category String,
        price Decimal(10, 2),
        stock_quantity UInt16,
        created_at DateTime
    ) ENGINE = MergeTree()
    ORDER BY id
    """)
    print("✓ Created products table")
    
    # Logs table
    client.command("""
    CREATE TABLE IF NOT EXISTS logs (
        id UInt64,
        timestamp DateTime,
        level String,
        source String,
        message String,
        metadata String
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, level)
    """)
    print("✓ Created logs table")
    
    # Log entries table
    # Drop and recreate to ensure correct schema (error_code is nullable)
    client.command("DROP TABLE IF EXISTS log_entries")
    client.command("""
    CREATE TABLE log_entries (
        id UInt64,
        timestamp DateTime,
        level String,
        service String,
        message String,
        error_code Nullable(String),
        user_id UInt32
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """)
    print("✓ Created log_entries table")
    
    # Application logs table
    client.command("""
    CREATE TABLE IF NOT EXISTS application_logs (
        id UInt64,
        timestamp DateTime,
        level String,
        component String,
        message String,
        duration_ms UInt32,
        status_code UInt16
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """)
    print("✓ Created application_logs table")
    
    # Messages table
    client.command("""
    CREATE TABLE IF NOT EXISTS messages (
        id UInt64,
        timestamp DateTime,
        source String,
        message_text String,
        metadata String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """)
    print("✓ Created messages table")
    
    # Financial logs table
    client.command("""
    CREATE TABLE IF NOT EXISTS financial_logs (
        id UInt64,
        timestamp DateTime,
        transaction_type String,
        message String,
        amount Decimal(12, 2),
        currency String,
        account_id String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """)
    print("✓ Created financial_logs table")
    
    # Trading logs table
    client.command("""
    CREATE TABLE IF NOT EXISTS trading_logs (
        id UInt64,
        timestamp DateTime,
        symbol String,
        price Decimal(10, 2),
        volume UInt32,
        message String,
        trade_type String
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, symbol)
    """)
    print("✓ Created trading_logs table")
    
    # Market data table
    client.command("""
    CREATE TABLE IF NOT EXISTS market_data (
        id UInt64,
        timestamp DateTime,
        symbol String,
        open_price Decimal(10, 2),
        high_price Decimal(10, 2),
        low_price Decimal(10, 2),
        close_price Decimal(10, 2),
        volume UInt64,
        message String
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, symbol)
    """)
    print("✓ Created market_data table")
    
    # Transactions table
    client.command("""
    CREATE TABLE IF NOT EXISTS transactions (
        id UInt64,
        timestamp DateTime,
        transaction_id String,
        account_from String,
        account_to String,
        amount Decimal(12, 2),
        currency String,
        description String
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """)
    print("✓ Created transactions table")

def populate_users(client, count=100):
    """Populate users table with demo data."""
    print(f"\nPopulating users table with {count} records...")
    
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    statuses = ["active", "inactive", "pending", "suspended"]
    
    data = []
    base_time = datetime.now() - timedelta(days=365)
    
    for i in range(1, count + 1):
        data.append([
            i,
            f"{random.choice(first_names)} {random.choice(last_names)}",
            f"user{i}@example.com",
            random.randint(18, 80),
            base_time + timedelta(days=random.randint(0, 365)),
            random.choice(statuses)
        ])
    
    client.insert("users", data, column_names=["id", "name", "email", "age", "created_at", "status"])
    print(f"✓ Inserted {count} users")

def populate_products(client, count=50):
    """Populate products table with demo data."""
    print(f"\nPopulating products table with {count} records...")
    
    categories = ["Electronics", "Clothing", "Books", "Food", "Toys", "Furniture", "Sports", "Beauty"]
    product_names = {
        "Electronics": ["Laptop", "Smartphone", "Tablet", "Headphones", "Camera"],
        "Clothing": ["T-Shirt", "Jeans", "Jacket", "Shoes", "Hat"],
        "Books": ["Novel", "Textbook", "Guide", "Biography", "Dictionary"],
        "Food": ["Snacks", "Beverages", "Candy", "Chips", "Cookies"],
        "Toys": ["Action Figure", "Puzzle", "Board Game", "Doll", "Car"],
        "Furniture": ["Chair", "Table", "Sofa", "Desk", "Bed"],
        "Sports": ["Ball", "Racket", "Bike", "Helmet", "Shoes"],
        "Beauty": ["Shampoo", "Lotion", "Perfume", "Makeup", "Cream"]
    }
    
    data = []
    base_time = datetime.now() - timedelta(days=180)
    
    for i in range(1, count + 1):
        category = random.choice(categories)
        product_name = random.choice(product_names[category])
        data.append([
            i,
            f"{product_name} {i}",
            category,
            round(random.uniform(10.0, 500.0), 2),
            random.randint(0, 1000),
            base_time + timedelta(days=random.randint(0, 180))
        ])
    
    client.insert("products", data, column_names=["id", "name", "category", "price", "stock_quantity", "created_at"])
    print(f"✓ Inserted {count} products")

def populate_orders(client, count=200):
    """Populate orders table with demo data."""
    print(f"\nPopulating orders table with {count} records...")
    
    statuses = ["pending", "completed", "cancelled", "shipped"]
    base_time = datetime.now() - timedelta(days=90)
    
    data = []
    for i in range(1, count + 1):
        data.append([
            i,
            random.randint(1, 100),  # user_id
            random.randint(1, 50),   # product_id
            random.randint(1, 5),    # quantity
            round(random.uniform(20.0, 500.0), 2),  # price
            base_time + timedelta(days=random.randint(0, 90)),
            random.choice(statuses)
        ])
    
    client.insert("orders", data, column_names=["id", "user_id", "product_id", "quantity", "price", "order_date", "status"])
    print(f"✓ Inserted {count} orders")

def populate_logs(client, count=500):
    """Populate logs table with demo data."""
    print(f"\nPopulating logs table with {count} records...")
    
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    sources = ["api", "database", "auth", "payment", "notification", "scheduler"]
    base_time = datetime.now() - timedelta(days=7)
    
    messages = [
        "User login successful",
        "Database query executed",
        "Payment processed",
        "Email sent",
        "Cache updated",
        "Session expired",
        "Rate limit exceeded",
        "Invalid credentials",
        "File uploaded",
        "Configuration changed"
    ]
    
    data = []
    for i in range(1, count + 1):
        level = random.choice(levels)
        source = random.choice(sources)
        message = random.choice(messages)
        metadata = json.dumps({
            "request_id": f"req_{random.randint(1000, 9999)}",
            "ip": f"192.168.1.{random.randint(1, 255)}",
            "user_agent": "Mozilla/5.0"
        })
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 168)),
            level,
            source,
            message,
            metadata
        ])
    
    client.insert("logs", data, column_names=["id", "timestamp", "level", "source", "message", "metadata"])
    print(f"✓ Inserted {count} log entries")

def populate_log_entries(client, count=300):
    """Populate log_entries table with demo data."""
    print(f"\nPopulating log_entries table with {count} records...")
    
    levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    services = ["user-service", "order-service", "payment-service", "inventory-service", "notification-service"]
    error_codes = ["E001", "E002", "E003", "E404", "E500", "", "", ""]  # Some entries have no error (use empty string)
    
    messages = [
        "Processing request",
        "Request completed successfully",
        "Failed to connect to database",
        "Invalid input parameters",
        "Service unavailable",
        "Timeout occurred",
        "Resource not found",
        "Authentication failed"
    ]
    
    data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(1, count + 1):
        error_code = random.choice(error_codes)
        # Ensure error_code is never None (shouldn't happen with current list, but defensive)
        if error_code is None:
            error_code = ""
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 168)),
            random.choice(levels),
            random.choice(services),
            random.choice(messages),
            error_code,
            random.randint(1, 100) if random.random() > 0.3 else 0
        ])
    
    client.insert("log_entries", data, column_names=["id", "timestamp", "level", "service", "message", "error_code", "user_id"])
    print(f"✓ Inserted {count} log entries")

def populate_application_logs(client, count=400):
    """Populate application_logs table with demo data."""
    print(f"\nPopulating application_logs table with {count} records...")
    
    levels = ["INFO", "WARNING", "ERROR"]
    components = ["api", "database", "cache", "queue", "worker", "scheduler"]
    status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503]
    
    messages = [
        "API request received",
        "Database connection established",
        "Cache hit",
        "Cache miss",
        "Queue job processed",
        "Worker started",
        "Scheduled task executed",
        "Request validation failed",
        "Response sent"
    ]
    
    data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(1, count + 1):
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 168)),
            random.choice(levels),
            random.choice(components),
            random.choice(messages),
            random.randint(10, 5000),  # duration_ms
            random.choice(status_codes)
        ])
    
    client.insert("application_logs", data, column_names=["id", "timestamp", "level", "component", "message", "duration_ms", "status_code"])
    print(f"✓ Inserted {count} application logs")

def populate_messages(client, count=200):
    """Populate messages table with demo data."""
    print(f"\nPopulating messages table with {count} records...")
    
    sources = ["email", "sms", "push", "webhook", "api"]
    
    message_templates = [
        "Order #{} has been shipped",
        "Payment of ${} received",
        "User {} logged in",
        "Stock price: ${}",
        "Transaction {} completed",
        "Alert: {}",
        "Notification: {}",
        "Update: {}"
    ]
    
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(1, count + 1):
        template = random.choice(message_templates)
        message_text = template.format(
            random.randint(1000, 9999),
            round(random.uniform(10, 1000), 2),
            f"user{random.randint(1, 100)}",
            round(random.uniform(50, 200), 2)
        )
        
        metadata = json.dumps({
            "source_id": f"src_{i}",
            "priority": random.choice(["low", "medium", "high"])
        })
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 720)),
            random.choice(sources),
            message_text,
            metadata
        ])
    
    client.insert("messages", data, column_names=["id", "timestamp", "source", "message_text", "metadata"])
    print(f"✓ Inserted {count} messages")

def populate_financial_logs(client, count=300):
    """Populate financial_logs table with demo data."""
    print(f"\nPopulating financial_logs table with {count} records...")
    
    transaction_types = ["payment", "refund", "transfer", "deposit", "withdrawal", "fee"]
    currencies = ["USD", "EUR", "GBP", "JPY"]
    
    messages = [
        "Payment processed successfully",
        "Refund issued",
        "Transfer completed",
        "Deposit received",
        "Withdrawal processed",
        "Transaction fee applied",
        "Payment failed",
        "Account balance updated"
    ]
    
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(1, count + 1):
        currency = random.choice(currencies)
        amount = round(random.uniform(10.0, 10000.0), 2)
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 720)),
            random.choice(transaction_types),
            random.choice(messages),
            amount,
            currency,
            f"ACC{random.randint(100000, 999999)}"
        ])
    
    client.insert("financial_logs", data, column_names=["id", "timestamp", "transaction_type", "message", "amount", "currency", "account_id"])
    print(f"✓ Inserted {count} financial logs")

def populate_trading_logs(client, count=500):
    """Populate trading_logs table with demo data."""
    print(f"\nPopulating trading_logs table with {count} records...")
    
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
    trade_types = ["BUY", "SELL", "LIMIT", "MARKET"]
    
    data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(1, count + 1):
        symbol = random.choice(symbols)
        price = round(random.uniform(50.0, 500.0), 2)
        volume = random.randint(10, 10000)
        
        data.append([
            i,
            base_time + timedelta(minutes=random.randint(0, 10080)),
            symbol,
            price,
            volume,
            f"{trade_types[0]} order for {symbol} at ${price}",
            random.choice(trade_types)
        ])
    
    client.insert("trading_logs", data, column_names=["id", "timestamp", "symbol", "price", "volume", "message", "trade_type"])
    print(f"✓ Inserted {count} trading logs")

def populate_market_data(client, count=1000):
    """Populate market_data table with demo data."""
    print(f"\nPopulating market_data table with {count} records...")
    
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "SPY", "QQQ"]
    
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(1, count + 1):
        symbol = random.choice(symbols)
        base_price = random.uniform(50.0, 500.0)
        high = base_price + random.uniform(0, 10)
        low = base_price - random.uniform(0, 10)
        open_price = round(base_price + random.uniform(-5, 5), 2)
        close_price = round(base_price + random.uniform(-5, 5), 2)
        volume = random.randint(1000, 1000000)
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 720)),
            symbol,
            open_price,
            round(high, 2),
            round(low, 2),
            close_price,
            volume,
            f"Market data for {symbol}: Open=${open_price}, Close=${close_price}, Volume={volume}"
        ])
    
    client.insert("market_data", data, column_names=["id", "timestamp", "symbol", "open_price", "high_price", "low_price", "close_price", "volume", "message"])
    print(f"✓ Inserted {count} market data records")

def populate_transactions(client, count=250):
    """Populate transactions table with demo data."""
    print(f"\nPopulating transactions table with {count} records...")
    
    currencies = ["USD", "EUR", "GBP"]
    
    descriptions = [
        "Payment for order",
        "Refund processed",
        "Account transfer",
        "Monthly subscription",
        "Service fee",
        "Interest payment",
        "Dividend payment",
        "Salary deposit"
    ]
    
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(1, count + 1):
        currency = random.choice(currencies)
        amount = round(random.uniform(10.0, 5000.0), 2)
        
        data.append([
            i,
            base_time + timedelta(hours=random.randint(0, 720)),
            f"TXN{random.randint(100000, 999999)}",
            f"ACC{random.randint(100000, 999999)}",
            f"ACC{random.randint(100000, 999999)}",
            amount,
            currency,
            random.choice(descriptions)
        ])
    
    client.insert("transactions", data, column_names=["id", "timestamp", "transaction_id", "account_from", "account_to", "amount", "currency", "description"])
    print(f"✓ Inserted {count} transactions")

def main():
    """Main function to populate all demo data."""
    print("=" * 60)
    print("ClickHouse Demo Data Population Script")
    print("=" * 60)
    
    try:
        client = get_clickhouse_client()
        print(f"\n✓ Connected to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
        print(f"✓ Using database: {CLICKHOUSE_DB}\n")
        
        # Create tables
        create_tables(client)
        
        # Populate data
        populate_users(client, count=100)
        populate_products(client, count=50)
        populate_orders(client, count=200)
        populate_logs(client, count=500)
        populate_log_entries(client, count=300)
        populate_application_logs(client, count=400)
        populate_messages(client, count=200)
        populate_financial_logs(client, count=300)
        populate_trading_logs(client, count=500)
        populate_market_data(client, count=1000)
        populate_transactions(client, count=250)
        
        print("\n" + "=" * 60)
        print("✓ Demo data population completed successfully!")
        print("=" * 60)
        print("\nYou can now test the agents with queries like:")
        print("  - 'How many users are in the database?'")
        print("  - 'Analyze the error logs from the last 24 hours'")
        print("  - 'Extract financial fields from trading logs'")
        print("  - 'What are the top 5 products by sales?'")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

