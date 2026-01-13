"""
Test Step 1.1 API endpoint to verify LLM integration
测试Step 1.1 API端点以验证LLM集成
"""
import requests
import json

# Test text with obvious AI-like structure
test_text = """
First, we need to understand the basic concept. This involves several key components.
Second, we should examine the implementation details. This requires careful analysis.
Third, we must consider the practical applications. This demonstrates the utility.
Finally, we can draw conclusions from our investigation. This completes our study.
"""

# API endpoint
url = "http://localhost:8000/api/v1/analysis/document/structure"

# Request payload
payload = {
    "text": test_text
}

print("Testing Step 1.1 Structure Analysis API...")
print(f"URL: {url}")
print(f"Text length: {len(test_text)} chars\n")

try:
    response = requests.post(url, json=payload, timeout=30)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n--- Analysis Results ---")
        print(f"Risk Score: {result.get('risk_score')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"Issues Found: {len(result.get('issues', []))}")

        for i, issue in enumerate(result.get('issues', []), 1):
            print(f"\nIssue {i}:")
            print(f"  Type: {issue.get('type')}")
            print(f"  Description: {issue.get('description_zh')}")
            print(f"  Severity: {issue.get('severity')}")
    else:
        print(f"Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to server. Is it running on port 8000?")
except requests.exceptions.Timeout:
    print("ERROR: Request timeout (>30s)")
except Exception as e:
    print(f"ERROR: {e}")
