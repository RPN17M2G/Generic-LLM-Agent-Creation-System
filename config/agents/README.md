# Agent Configurations

This directory contains YAML configuration files for different agent types.
Here are some example agents:

## Available Agents

### 1. `clickhouse_analyst.yaml`
General-purpose ClickHouse database analyst agent. Can generate and execute SQL queries.

**Use Cases:**
- Answer questions about database contents
- Generate SQL queries from natural language
- Execute and validate SQL queries

### 2. `clickhouse_chat.yaml`
Chat-oriented agent for ClickHouse database interactions.

**Use Cases:**
- Conversational database queries
- Interactive data exploration

### 3. `log_analyst.yaml` 
Specialized agent for analyzing log messages from databases.

**Capabilities:**
- Query log messages from database tables
- Parse log entries in various formats (JSON, CSV, text)
- Detect patterns, errors, and anomalies
- Provide insights about log meaning and significance
- Analyze trends and identify issues

**Use Cases:**
- "What errors occurred in the logs today?"
- "Analyze the application logs for anomalies"
- "What patterns do you see in the system logs?"
- "Summarize the error logs from the last hour"

**Required Database Tables:**
- `logs`, `log_entries`, `application_logs`, `system_logs`, `error_logs`

**Example Queries:**
- "Query the error logs from the last 24 hours and analyze them"
- "What are the most common errors in the application logs?"
- "Detect any anomalies in the system logs"

### 4. `financial_extractor.yaml` 
Specialized agent for extracting numerical fields from log messages for stock and finance analysis.

**Capabilities:**
- Query messages from database tables
- Parse message content
- Extract financial metrics (prices, volumes, percentages, etc.)
- Identify numerical fields relevant to financial analysis
- Extract stock-related data from messages

**Use Cases:**
- "Extract stock prices from the trading logs"
- "What financial metrics are in these messages?"
- "Find all numerical values related to finance in the logs"
- "Extract volume and price data from market messages"

**Required Database Tables:**
- `messages`, `log_messages`, `financial_logs`, `trading_logs`, `market_data`, `transactions`

**Example Queries:**
- "Query messages from the trading_logs table and extract all financial numerical fields"
- "Extract stock prices and volumes from the market_data table"
- "What numerical financial data is in these transaction logs?"

### 5. `field_bucketing_analyst.yaml` ⭐ NEW
Generic agent that extracts interesting fields from log messages and creates domain-aware bucketing strategies for each field.

**Capabilities:**
- Query messages/logs from database tables
- Parse message content
- Extract interesting fields of any type:
  - **Numeric fields**: integers, floats, percentages, ratios
  - **Financial fields**: amounts, currencies, stock prices, volumes
  - **Temporal fields**: dates, timestamps, durations
  - **Categorical fields**: status codes, types, categories
  - **Identifiers**: IDs, account numbers, reference codes
- Analyze each extracted field (statistics, distribution)
- Generate domain-aware bucketing strategies for each field
- Validate bucketing strategies
- Create meaningful data segments for analysis

**Use Cases:**
- "Extract interesting fields from trading logs and create bucketing strategies for each"
- "Analyze all numeric fields in the data and suggest how to bucket them"
- "Extract fields from messages and create domain-aware buckets for analysis"
- "What are the best ways to segment this data?"
- Works for any domain: financial, technical, business, etc.

**Workflow:**
1. Query data from database
2. Extract interesting fields from messages (numeric, categorical, temporal, etc.)
3. For each extracted field:
   - Analyze field distribution and statistics
   - Generate domain-aware bucketing strategy
   - Validate the strategy
4. Return bucketing strategies for all fields

**Required Database Tables:**
- `messages`, `log_messages`, `financial_logs`, `trading_logs`, `market_data`, `transactions`, `logs`, `log_entries`, `application_logs`

**Example Queries:**
- "Extract interesting fields from trading_logs and create bucketing strategies for each field"
- "Analyze all numeric fields in market_data and suggest how to bucket them"
- "Extract fields from messages and create domain-aware bucketing strategies"
- "What are the best ways to segment the data in this table?"

**Tools:**
- SQL generation/execution for data retrieval
- Message parsing
- **Generic field extraction** (supports multiple field types)
- Field validation
- Field analysis (statistics, distribution)
- Bucketing strategy generation (LLM-powered, domain-aware)
- Strategy validation

## Configuration Structure

Each agent configuration follows this structure:

```yaml
agent:
  name: "agent_name"
  description: "Agent description"
  
  llm:
    provider: "ollama"
    orchestrator_model: "model_name"
    host: "http://localhost:11434"
    temperature: 0.0
  
  database:
    type: "clickhouse"
    connection:
      host: "localhost"
      port: 8123
      database: "default"
    allowed_tables:
      - "table1"
      - "table2"
  
  tools:
    - name: "tool_name"
      type: "tool_type"
      config:
        model: "model_name"
  
  security:
    pii_masking: true
    query_validation: true
    allowed_operations:
      - "SELECT"
  
  behavior:
    max_iterations: 10
    enable_self_correction: true
    response_format: "json"
```

## Environment Variables

You can use environment variables in YAML files:
- `${VAR_NAME}` - Required variable
- `${VAR_NAME:default_value}` - Variable with default

Common variables:
- `CLICKHOUSE_HOST` - ClickHouse server host
- `CLICKHOUSE_DB` - ClickHouse database name
- `CLICKHOUSE_USER` - ClickHouse username
- `CLICKHOUSE_PASSWORD` - ClickHouse password
- `OLLAMA_HOST` - Ollama server URL

## Usage

### Via API

```bash
# Query the log analyst
curl -X POST http://localhost:5000/agents/log_analyst/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze the error logs from the last hour"}'

# Query the financial extractor
curl -X POST http://localhost:5000/agents/financial_extractor/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Extract financial fields from trading logs"}'

# Query the field bucketing analyst
curl -X POST http://localhost:5000/agents/field_bucketing_analyst/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Extract interesting fields from trading logs and create bucketing strategies for each"}'
```

### Via Python

```python
from agent_factory import AgentFactory
from core.orchestrator import AgentOrchestrator

# Create factory and orchestrator
factory = AgentFactory()
orchestrator = AgentOrchestrator(factory)

# Use log analyst
response = orchestrator.execute("log_analyst", "Analyze the error logs")
print(response)

# Use financial extractor
response = orchestrator.execute("financial_extractor", "Extract stock prices from messages")
print(response)

# Use field bucketing analyst
response = orchestrator.execute(
    "field_bucketing_analyst",
    "Extract interesting fields from trading_logs and create bucketing strategies for each field"
)
print(response)
```

## Adding New Agents

1. Create a new YAML file in this directory
2. Follow the configuration structure above
3. Register the agent name in your application
4. Test with sample queries
