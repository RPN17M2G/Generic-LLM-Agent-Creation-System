"""
Python script for testing API endpoints with demo requests.
Usage: python scripts/test_api_requests.py [base_url]
"""
import sys
import json
import requests
from typing import Dict, Any, Optional
import time

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_request(name: str, method: str, endpoint: str, data: Optional[Dict] = None):
    """Print request details."""
    print(f"\n[{name}]")
    print(f"  Method: {method}")
    print(f"  Endpoint: {endpoint}")
    if data:
        print(f"  Payload: {json.dumps(data, indent=2)}")

def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make an API request and return the response."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=120)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=120)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else {}
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "error": str(e)
        }

def test_health_check():
    """Test health check endpoint."""
    print_section("1. Health Check")
    print_request("Health Check", "GET", "/health")
    result = make_request("GET", "/health")
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    return result

def test_list_agents():
    """Test list agents endpoint."""
    print_section("2. List All Agents")
    print_request("List Agents", "GET", "/agents")
    result = make_request("GET", "/agents")
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    return result

def test_clickhouse_analyst():
    """Test ClickHouse Analyst agent."""
    print_section("3. ClickHouse Analyst - Simple Query")
    query = "How many users are in the database?"
    print_request("ClickHouse Analyst", "POST", "/agents/clickhouse_analyst/query", {"query": query})
    result = make_request("POST", "/agents/clickhouse_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    print_section("4. ClickHouse Analyst - Complex Query")
    query = "What are the top 5 products by total sales amount?"
    print_request("ClickHouse Analyst", "POST", "/agents/clickhouse_analyst/query", {"query": query})
    result = make_request("POST", "/agents/clickhouse_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    return result

def test_clickhouse_chat():
    """Test ClickHouse Chat agent."""
    print_section("5. ClickHouse Chat - Conversational")
    query = "Tell me about the users in the database. How many are active?"
    print_request("ClickHouse Chat", "POST", "/agents/clickhouse_chat/query", {"query": query})
    result = make_request("POST", "/agents/clickhouse_chat/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    return result

def test_log_analyst():
    """Test Log Analyst agent."""
    print_section("6. Log Analyst - Error Analysis")
    query = "Analyze the error logs from the last 24 hours. What patterns do you see?"
    print_request("Log Analyst", "POST", "/agents/log_analyst/query", {"query": query})
    result = make_request("POST", "/agents/log_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    print_section("7. Log Analyst - Pattern Detection")
    query = "What are the most common errors in the application logs?"
    print_request("Log Analyst", "POST", "/agents/log_analyst/query", {"query": query})
    result = make_request("POST", "/agents/log_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    return result

def test_financial_extractor():
    """Test Financial Extractor agent."""
    print_section("8. Financial Extractor - Stock Data")
    query = "Extract all financial fields from the trading_logs table"
    print_request("Financial Extractor", "POST", "/agents/financial_extractor/query", {"query": query})
    result = make_request("POST", "/agents/financial_extractor/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    print_section("9. Financial Extractor - Transaction Data")
    query = "Extract all numerical financial fields from the transactions table"
    print_request("Financial Extractor", "POST", "/agents/financial_extractor/query", {"query": query})
    result = make_request("POST", "/agents/financial_extractor/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    return result

def test_field_bucketing_analyst():
    """Test Field Bucketing Analyst agent."""
    print_section("10. Field Bucketing Analyst - Market Data")
    query = "Extract interesting fields from market_data and create bucketing strategies for each field"
    print_request("Field Bucketing Analyst", "POST", "/agents/field_bucketing_analyst/query", {"query": query})
    result = make_request("POST", "/agents/field_bucketing_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    print_section("11. Field Bucketing Analyst - Trading Data")
    query = "Extract fields from trading_logs and suggest how to bucket the price and volume data"
    print_request("Field Bucketing Analyst", "POST", "/agents/field_bucketing_analyst/query", {"query": query})
    result = make_request("POST", "/agents/field_bucketing_analyst/query", {"query": query})
    print(f"  Status: {result.get('status_code')}")
    print(f"  Response: {json.dumps(result.get('response', {}), indent=2)}")
    
    return result

def main():
    """Run all test requests."""
    print("=" * 60)
    print("  Multi-Agent LLM Framework - API Test Suite")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Starting tests at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    try:
        # Basic endpoints
        results["health"] = test_health_check()
        time.sleep(1)
        
        results["list_agents"] = test_list_agents()
        time.sleep(1)
        
        # Agent queries
        results["clickhouse_analyst"] = test_clickhouse_analyst()
        time.sleep(2)
        
        results["clickhouse_chat"] = test_clickhouse_chat()
        time.sleep(2)
        
        results["log_analyst"] = test_log_analyst()
        time.sleep(2)
        
        results["financial_extractor"] = test_financial_extractor()
        time.sleep(2)
        
        results["field_bucketing_analyst"] = test_field_bucketing_analyst()
        
        # Summary
        print_section("Test Summary")
        print("\nResults:")
        for test_name, result in results.items():
            status = result.get('status_code', 'N/A')
            status_icon = "✓" if status == 200 else "✗"
            print(f"  {status_icon} {test_name}: {status}")
        
        print("\n" + "=" * 60)
        print("  All tests completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

