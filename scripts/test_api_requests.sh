#!/bin/bash
# Demo API requests for testing all agents
# Usage: ./test_api_requests.sh [base_url]
# Example: ./test_api_requests.sh http://localhost:5000

BASE_URL="${1:-http://localhost:5000}"

echo "=========================================="
echo "Testing Multi-Agent LLM Framework API"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo ""

# Health check
echo "1. Health Check"
echo "----------------------------------------"
curl -X GET "$BASE_URL/health" -H "Content-Type: application/json"
echo -e "\n\n"

# List agents
echo "2. List All Agents"
echo "----------------------------------------"
curl -X GET "$BASE_URL/agents" -H "Content-Type: application/json"
echo -e "\n\n"

# ClickHouse Analyst - Simple query
echo "3. ClickHouse Analyst - Simple Count Query"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/clickhouse_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many users are in the database?"
  }'
echo -e "\n\n"

# ClickHouse Analyst - Complex query
echo "4. ClickHouse Analyst - Complex Query"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/clickhouse_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 5 products by total sales amount?"
  }'
echo -e "\n\n"

# ClickHouse Chat - Conversational
echo "5. ClickHouse Chat - Conversational Query"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/clickhouse_chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about the users in the database. How many are active?"
  }'
echo -e "\n\n"

# Log Analyst - Error analysis
echo "6. Log Analyst - Error Analysis"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/log_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze the error logs from the last 24 hours. What patterns do you see?"
  }'
echo -e "\n\n"

# Log Analyst - Pattern detection
echo "7. Log Analyst - Pattern Detection"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/log_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the most common errors in the application logs?"
  }'
echo -e "\n\n"

# Financial Extractor - Stock data
echo "8. Financial Extractor - Stock Data Extraction"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/financial_extractor/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Extract all financial fields from the trading_logs table"
  }'
echo -e "\n\n"

# Financial Extractor - Transaction data
echo "9. Financial Extractor - Transaction Data"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/financial_extractor/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Extract all numerical financial fields from the transactions table"
  }'
echo -e "\n\n"

# Field Bucketing Analyst - Market data
echo "10. Field Bucketing Analyst - Market Data Bucketing"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/field_bucketing_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Extract interesting fields from market_data and create bucketing strategies for each field"
  }'
echo -e "\n\n"

# Field Bucketing Analyst - Trading data
echo "11. Field Bucketing Analyst - Trading Data Analysis"
echo "----------------------------------------"
curl -X POST "$BASE_URL/agents/field_bucketing_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Extract fields from trading_logs and suggest how to bucket the price and volume data"
  }'
echo -e "\n\n"

echo "=========================================="
echo "All test requests completed!"
echo "=========================================="

