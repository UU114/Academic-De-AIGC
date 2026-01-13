"""
Test all 30 Substep Endpoints
测试所有30个子步骤端点
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001/api/v1"

# Test text
TEST_TEXT = """
This comprehensive study delves into the multifaceted realm of artificial intelligence and its pivotal role in transforming the landscape of academic research. The intricate tapestry of methodologies employed underscores the paramount importance of robust and seamless integration.

In conclusion, our findings suggest that innovative approaches can facilitate transformative outcomes. Furthermore, it is worth noting that the ever-evolving nature of this field requires continuous adaptation. The results indicate a significant association between the variables examined.
"""

TEST_DATA = {
    "text": TEST_TEXT,
    "session_id": "test-session-001",
    "locked_terms": ["artificial intelligence", "academic research"]
}

# All endpoints to test (updated with correct paths for special cases)
ENDPOINTS = [
    # Layer 5 (Document)
    ("POST", "/layer5/step1-0/extract-terms", {"document_text": TEST_TEXT, "session_id": "test-session-001"}),
    ("POST", "/layer5/step1-1/analyze", TEST_DATA),
    ("POST", "/layer5/step1-2/analyze", TEST_DATA),
    ("POST", "/layer5/step1-3/analyze", TEST_DATA),
    ("POST", "/layer5/step1-4/analyze", TEST_DATA),
    ("POST", "/layer5/step1-5/analyze", TEST_DATA),
    
    # Layer 4 (Section)
    ("POST", "/layer4/step2-0/analyze", TEST_DATA),
    ("POST", "/layer4/step2-1/analyze", TEST_DATA),
    ("POST", "/layer4/step2-2/analyze", TEST_DATA),
    ("POST", "/layer4/step2-3/analyze", TEST_DATA),
    ("POST", "/layer4/step2-4/analyze", TEST_DATA),
    ("POST", "/layer4/step2-5/analyze", TEST_DATA),
    
    # Layer 3 (Paragraph)
    ("POST", "/layer3/step3-0/analyze", TEST_DATA),
    ("POST", "/layer3/step3-1/analyze", TEST_DATA),
    ("POST", "/layer3/step3-2/analyze", TEST_DATA),
    ("POST", "/layer3/step3-3/analyze", TEST_DATA),
    ("POST", "/layer3/step3-4/analyze", TEST_DATA),
    ("POST", "/layer3/step3-5/analyze", TEST_DATA),
    
    # Layer 2 (Sentence)
    ("POST", "/layer2/step4-0/analyze", TEST_DATA),
    ("POST", "/layer2/step4-1/analyze", TEST_DATA),
    ("POST", "/layer2/step4-2/analyze", TEST_DATA),
    ("POST", "/layer2/step4-3/analyze", TEST_DATA),
    ("POST", "/layer2/step4-4/analyze", TEST_DATA),
    ("POST", "/layer2/step4-5/analyze", TEST_DATA),
    
    # Layer 1 (Lexical)
    ("POST", "/layer1/step5-0/analyze", TEST_DATA),
    ("POST", "/layer1/step5-1/analyze", TEST_DATA),
    ("POST", "/layer1/step5-2/analyze", TEST_DATA),
    ("POST", "/layer1/step5-3/analyze", TEST_DATA),
    ("POST", "/layer1/step5-4/analyze", TEST_DATA),
    ("POST", "/layer1/step5-5/validate", TEST_DATA),
]

def test_endpoint(method, endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            resp = requests.post(url, json=data, timeout=10)
        else:
            resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            risk_score = result.get("risk_score", "N/A")
            risk_level = result.get("risk_level", "N/A")
            return True, f"risk_score={risk_score}, risk_level={risk_level}"
        else:
            return False, f"Status {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("Testing 30 Substep Endpoints")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for method, endpoint, data in ENDPOINTS:
        success, msg = test_endpoint(method, endpoint, data)
        status = "PASS" if success else "FAIL"
        if success:
            passed += 1
            print(f"[{status}] {endpoint}: {msg}")
        else:
            failed += 1
            print(f"[{status}] {endpoint}: {msg}")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
