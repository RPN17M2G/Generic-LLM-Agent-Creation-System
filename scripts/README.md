# Demo Data Population Scripts

This directory contains scripts for populating ClickHouse with demo data for testing agents.

## Quick Start

### Prerequisites

1. ClickHouse must be running and accessible
2. Install required Python package:
   ```bash
   pip install clickhouse-connect
   ```

3. Set environment variables (optional, defaults shown):
   ```bash
   export CLICKHOUSE_HOST=localhost
   export CLICKHOUSE_PORT=8123
   export CLICKHOUSE_DB=default
   export CLICKHOUSE_USER=default
   export CLICKHOUSE_PASSWORD=
   ```

### Running the Script

```bash
python scripts/populate_demo_data.py
```

## What Gets Created

The script creates and populates the following tables:

### Core Tables
- **users** (100 records): User data with names, emails, ages, statuses
- **orders** (200 records): Order data with user/product relationships
- **products** (50 records): Product catalog with categories and prices

### Log Tables
- **logs** (500 records): General application logs with levels and sources
- **log_entries** (300 records): Structured log entries with services and error codes
- **application_logs** (400 records): Application logs with performance metrics

### Financial/Trading Tables
- **messages** (200 records): Generic messages from various sources
- **financial_logs** (300 records): Financial transaction logs with amounts and currencies
- **trading_logs** (500 records): Stock trading logs with symbols, prices, volumes
- **market_data** (1000 records): Market data with OHLC prices and volumes
- **transactions** (250 records): Financial transactions with accounts and amounts

## Data Characteristics

- **Temporal Data**: All tables include timestamps spanning the last 7-365 days
- **Realistic Values**: Data uses realistic names, prices, amounts, and patterns
- **Relationships**: Foreign key relationships (e.g., orders reference users and products)
- **Variety**: Multiple categories, statuses, levels, and types for testing

## Testing Agents

After populating data, you can test agents with queries like:

### ClickHouse Analyst
```bash
curl -X POST http://localhost:5000/agents/clickhouse_analyst/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many users are in the database?"}'
```

### Log Analyst
```bash
curl -X POST http://localhost:5000/agents/log_analyst/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze the error logs from the last 24 hours"}'
```

### Financial Extractor
```bash
curl -X POST http://localhost:5000/agents/financial_extractor/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Extract financial fields from trading logs"}'
```

### Field Bucketing Analyst
```bash
curl -X POST http://localhost:5000/agents/field_bucketing_analyst/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Extract interesting fields from market_data and create bucketing strategies"}'
```

## Customization

You can modify the script to:
- Change record counts (adjust `count` parameters)
- Add more tables
- Modify data patterns
- Add more realistic data distributions

## Troubleshooting

### Connection Issues
- Verify ClickHouse is running: `curl http://localhost:8123`
- Check environment variables match your ClickHouse configuration
- Ensure the database exists

### Table Already Exists
- The script uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run multiple times
- To start fresh, drop tables first:
  ```sql
  DROP TABLE IF EXISTS users;
  DROP TABLE IF EXISTS orders;
  -- etc.
  ```

### Data Not Appearing
- Check ClickHouse logs for errors
- Verify the database name is correct
- Ensure you have write permissions

