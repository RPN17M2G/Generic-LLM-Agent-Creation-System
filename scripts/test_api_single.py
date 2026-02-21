"""
Quick single-request tester for API.
Usage: python scripts/test_api_single.py <agent_name> "<query>"
Example: python scripts/test_api_single.py clickhouse_analyst "How many users are in the database?"
"""
import sys
import json
import requests
from typing import Optional

def test_agent_query(agent_name: str, query: str, base_url: str = "http://localhost:5000"):
    """Test a single agent query."""
    url = f"{base_url}/agents/{agent_name}/query"
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    
    print(f"Testing Agent: {agent_name}")
    print(f"Query: {query}")
    print(f"URL: {url}")
    print("\nSending request...\n")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python test_api_single.py <agent_name> \"<query>\" [base_url]")
        print("\nExamples:")
        print('  python test_api_single.py clickhouse_analyst "How many users are in the database?"')
        print('  python test_api_single.py log_analyst "Analyze error logs"')
        print('  python test_api_single.py financial_extractor "Extract financial fields" http://localhost:5000')
        sys.exit(1)
    
    agent_name = sys.argv[1]
    query = sys.argv[2]
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:5000"
    
    result = test_agent_query(agent_name, query, base_url)
    
    if result:
        print("\n✓ Request completed successfully")
        return 0
    else:
        print("\n✗ Request failed")
        return 1

if __name__ == "__main__":
    exit(main())

