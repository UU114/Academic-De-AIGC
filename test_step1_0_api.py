"""
Test Step 1.0 API endpoint to verify it can call LLM successfully
测试Step 1.0 API端点以验证其能否成功调用LLM
"""
import requests
import json

# Test text
test_text = """
Machine learning is a subset of artificial intelligence that enables computers to learn from data.
Neural networks are computational models inspired by biological neural systems. The Transformer
architecture, introduced by Vaswani et al. (2017), revolutionized natural language processing.
The BERT model uses bidirectional training to understand context better.
"""

# API endpoint
url = "http://localhost:8000/api/v1/layer5/step1-0/extract-terms"

# Request payload
payload = {
    "document_text": test_text,
    "session_id": "test-session-123"
}

print("Testing Step 1.0 Term Extraction API...")
print(f"URL: {url}")
print(f"Text length: {len(test_text)} chars\n")

try:
    response = requests.post(url, json=payload, timeout=30)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n--- Extraction Results ---")
        print(f"Total Terms: {result.get('total_count')}")
        print(f"By Type: {result.get('by_type')}")
        print(f"Processing Time: {result.get('processing_time_ms')} ms")
    else:
        print(f"Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to server. Is it running on port 8000?")
except requests.exceptions.Timeout:
    print("ERROR: Request timeout (>30s)")
except Exception as e:
    print(f"ERROR: {e}")
