#!/bin/bash
# Quick test script - runs essential tests only
# Usage: ./quick_test.sh [base_url]

BASE_URL="${1:-http://localhost:5000}"

echo "Quick API Test Suite"
echo "===================="
echo ""

# Health check
echo "1. Health Check..."
curl -s -X GET "$BASE_URL/health" | jq '.' || echo "Failed"
echo ""

# List agents
echo "2. List Agents..."
curl -s -X GET "$BASE_URL/agents" | jq '.agents' || echo "Failed"
echo ""

# Simple query
echo "3. ClickHouse Analyst - Simple Query..."
curl -s -X POST "$BASE_URL/agents/clickhouse_analyst/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many users are in the database?"}' | jq '.response' || echo "Failed"
echo ""

echo "Quick test completed!"

