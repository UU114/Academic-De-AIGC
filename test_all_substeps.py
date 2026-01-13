"""
Comprehensive Substep Testing Script
综合substep测试脚本

Tests all substeps across 5 layers and generates detailed test report
"""

import sys
import json
import time
import asyncio
import httpx
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENT = Path("test_documents/test_high_risk.txt")
REPORT_FILE = Path("doc/substep_test_report.md")

# Load test document
print(f"Loading test document: {TEST_DOCUMENT}")
with open(TEST_DOCUMENT, 'r', encoding='utf-8') as f:
    TEST_TEXT = f.read()

print(f"Test document loaded: {len(TEST_TEXT)} characters\n")

# Test results storage
test_results = []

class SubstepTest:
    def __init__(self, layer, step, name, endpoint):
        self.layer = layer
        self.step = step
        self.name = name
        self.endpoint = endpoint
        self.status = "pending"
        self.execution_time_ms = 0
        self.error = None
        self.response = None
        self.detections = []
        self.risk_level = None

async def test_substep(client, test):
    """Test a single substep"""
    print(f"\n{'='*70}")
    print(f"Testing: Layer {test.layer} - Step {test.step} - {test.name}")
    print(f"Endpoint: {test.endpoint}")
    print(f"{'='*70}")

    start_time = time.time()

    try:
        # Prepare payload
        payload = {
            "text": TEST_TEXT,
            "session_id": "test_session_001"
        }

        # Make API request
        response = await client.post(f"{BASE_URL}{test.endpoint}", json=payload, timeout=60.0)

        test.execution_time_ms = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            test.response = response.json()
            test.status = "success"
            print(f"[SUCCESS] ({test.execution_time_ms}ms)")

            # Extract key information
            if "issues" in test.response:
                test.detections = test.response["issues"]
                print(f"   Detections: {len(test.detections)} issues found")

            if "risk_level" in test.response:
                test.risk_level = test.response["risk_level"]
                print(f"   Risk Level: {test.risk_level}")

            # Print sample detections
            if test.detections:
                print(f"   Sample Issues:")
                for i, issue in enumerate(test.detections[:3]):
                    issue_type = issue.get('type', 'unknown')
                    description = issue.get('description', issue.get('message', 'No description'))
                    print(f"     {i+1}. {issue_type}: {description[:80]}...")

        elif response.status_code == 404:
            test.status = "not_implemented"
            test.error = "Endpoint not found - substep may not be implemented yet"
            print(f"[NOT_IMPLEMENTED] {test.error}")

        else:
            test.status = "failed"
            test.error = f"HTTP {response.status_code}: {response.text[:200]}"
            print(f"[FAILED] {test.error}")

    except httpx.ConnectError:
        test.status = "failed"
        test.error = "Connection error - server may not be running"
        print(f"[FAILED] {test.error}")

    except httpx.ReadTimeout:
        test.status = "timeout"
        test.error = "Request timeout after 60s"
        print(f"[TIMEOUT] {test.error}")

    except Exception as e:
        test.status = "failed"
        test.error = str(e)
        print(f"[FAILED] {test.error}")

    return test


def append_test_result_to_report(test):
    """Append test result to report file"""
    with open(REPORT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## Layer {test.layer} - Step {test.step}: {test.name}\n\n")
        f.write(f"**Status**: {test.status.upper()}\n\n")
        f.write(f"**Execution Time**: {test.execution_time_ms}ms\n\n")
        f.write(f"**API Endpoint**: `{test.endpoint}`\n\n")

        if test.status == "success":
            f.write(f"### Detection Results\n\n")
            f.write(f"- **Issues Detected**: {len(test.detections)}\n")
            if test.risk_level:
                f.write(f"- **Risk Level**: {test.risk_level}\n")
            f.write(f"\n")

            if test.detections:
                f.write(f"**Sample Issues**:\n\n")
                for i, issue in enumerate(test.detections[:5]):
                    issue_type = issue.get('type', 'unknown')
                    description = issue.get('description', issue.get('message', 'No description'))
                    f.write(f"{i+1}. **{issue_type}**: {description}\n")
                f.write(f"\n")

            f.write(f"**Full Response Keys**: {', '.join(test.response.keys())}\n\n")

        elif test.status == "not_implemented":
            f.write(f"### Status\n\n")
            f.write(f"⚠️ This substep is not yet implemented in the backend.\n\n")
            f.write(f"**Note**: {test.error}\n\n")

        elif test.status in ["failed", "timeout"]:
            f.write(f"### Error Details\n\n")
            f.write(f"```\n{test.error}\n```\n\n")

        f.write(f"---\n")


async def run_all_tests():
    """Run all substep tests"""

    # Define all substeps to test based on design documents
    substeps = [
        # Layer 5 - Document Level
        SubstepTest(5, "1.0", "Term Locking", "/api/v1/layer5/step1-0/extract-terms"),
        SubstepTest(5, "1.1", "Section Structure & Order", "/api/v1/layer5/step1-1/analyze"),
        SubstepTest(5, "1.2", "Section Uniformity", "/api/v1/layer5/step1-2/analyze"),
        SubstepTest(5, "1.3", "Logic Pattern & Closure", "/api/v1/layer5/step1-3/analyze"),
        SubstepTest(5, "1.4", "Paragraph Length Uniformity", "/api/v1/layer5/step1-4/analyze"),
        SubstepTest(5, "1.5", "Transitions & Connectors", "/api/v1/layer5/step1-5/analyze"),

        # Layer 4 - Section Level
        SubstepTest(4, "2.0", "Section Identification", "/api/v1/layer4/step2-0/identify"),
        SubstepTest(4, "2.1", "Section Order & Structure", "/api/v1/layer4/step2-1/analyze"),
        SubstepTest(4, "2.2", "Length Distribution", "/api/v1/layer4/step2-2/analyze"),
        SubstepTest(4, "2.3", "Internal Structure Similarity", "/api/v1/layer4/step2-3/analyze"),
        SubstepTest(4, "2.4", "Section Transition", "/api/v1/layer4/step2-4/analyze"),
        SubstepTest(4, "2.5", "Inter-Section Logic", "/api/v1/layer4/step2-5/analyze"),

        # Layer 3 - Paragraph Level
        SubstepTest(3, "3.0", "Paragraph Identification", "/api/v1/layer3/step3-0/identify"),
        SubstepTest(3, "3.1", "Paragraph Role Detection", "/api/v1/layer3/step3-1/analyze"),
        SubstepTest(3, "3.2", "Internal Coherence", "/api/v1/layer3/step3-2/analyze"),
        SubstepTest(3, "3.3", "Anchor Density", "/api/v1/layer3/step3-3/analyze"),
        SubstepTest(3, "3.4", "Sentence Length Distribution", "/api/v1/layer3/step3-4/analyze"),
        SubstepTest(3, "3.5", "Paragraph Transition", "/api/v1/layer3/step3-5/analyze"),

        # Layer 2 - Sentence Level
        SubstepTest(2, "4.0", "Sentence Context Preparation", "/api/v1/layer2/step4-0/prepare"),
        SubstepTest(2, "4.1", "Sentence Role Detection", "/api/v1/layer2/step4-1/analyze"),
        SubstepTest(2, "4.2", "Pattern Detection", "/api/v1/layer2/step4-2/analyze"),
        SubstepTest(2, "4.3", "Connector Analysis", "/api/v1/layer2/step4-3/analyze"),
        SubstepTest(2, "4.4", "Length Diversity", "/api/v1/layer2/step4-4/analyze"),
        SubstepTest(2, "4.5", "Sentence Rewriting", "/api/v1/layer2/step4-5/rewrite"),

        # Layer 1 - Lexical Level
        SubstepTest(1, "5.0", "Lexical Context Preparation", "/api/v1/layer1/step5-0/prepare"),
        SubstepTest(1, "5.1", "Fingerprint Detection", "/api/v1/layer1/step5-1/detect"),
        SubstepTest(1, "5.2", "Human Feature Analysis", "/api/v1/layer1/step5-2/analyze"),
        SubstepTest(1, "5.3", "Replacement Generation", "/api/v1/layer1/step5-3/generate"),
        SubstepTest(1, "5.4", "Paragraph Rewriting", "/api/v1/layer1/step5-4/rewrite"),
        SubstepTest(1, "5.5", "Validation", "/api/v1/layer1/step5-5/validate"),
    ]

    print(f"\n{'#'*70}")
    print(f"# SUBSTEP COMPREHENSIVE TESTING")
    print(f"# Total Substeps: {len(substeps)}")
    print(f"# Test Document: {TEST_DOCUMENT}")
    print(f"# Report File: {REPORT_FILE}")
    print(f"{'#'*70}\n")

    # Create HTTP client
    async with httpx.AsyncClient() as client:
        # Test each substep
        for test in substeps:
            result = await test_substep(client, test)
            test_results.append(result)

            # Append result to report immediately
            append_test_result_to_report(result)

            # Small delay between tests
            await asyncio.sleep(0.5)

    # Generate summary
    generate_summary()


def generate_summary():
    """Generate test summary"""
    print(f"\n\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}\n")

    total = len(test_results)
    success = sum(1 for t in test_results if t.status == "success")
    not_impl = sum(1 for t in test_results if t.status == "not_implemented")
    failed = sum(1 for t in test_results if t.status == "failed")
    timeout = sum(1 for t in test_results if t.status == "timeout")

    print(f"Total Substeps Tested: {total}")
    print(f"  [SUCCESS] Success: {success} ({success/total*100:.1f}%)")
    print(f"  [NOT_IMPL] Not Implemented: {not_impl} ({not_impl/total*100:.1f}%)")
    print(f"  [FAILED] Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"  [TIMEOUT] Timeout: {timeout} ({timeout/total*100:.1f}%)")
    print()

    # Summary by layer
    print(f"Summary by Layer:")
    for layer in [5, 4, 3, 2, 1]:
        layer_tests = [t for t in test_results if t.layer == layer]
        layer_success = sum(1 for t in layer_tests if t.status == "success")
        print(f"  Layer {layer}: {layer_success}/{len(layer_tests)} successful")
    print()

    # Append summary to report
    with open(REPORT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n\n---\n\n")
        f.write(f"## Overall Test Summary | 总体测试摘要\n\n")
        f.write(f"**Test Completion Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"### Statistics | 统计数据\n\n")
        f.write(f"- **Total Substeps**: {total}\n")
        f.write(f"- **✅ Success**: {success} ({success/total*100:.1f}%)\n")
        f.write(f"- **⚠️ Not Implemented**: {not_impl} ({not_impl/total*100:.1f}%)\n")
        f.write(f"- **❌ Failed**: {failed} ({failed/total*100:.1f}%)\n")
        f.write(f"- **⏱️ Timeout**: {timeout} ({timeout/total*100:.1f}%)\n\n")

        f.write(f"### Summary by Layer | 按层级汇总\n\n")
        f.write(f"| Layer | Success | Not Impl | Failed | Timeout | Total |\n")
        f.write(f"|-------|---------|----------|--------|---------|-------|\n")
        for layer in [5, 4, 3, 2, 1]:
            layer_tests = [t for t in test_results if t.layer == layer]
            layer_success = sum(1 for t in layer_tests if t.status == "success")
            layer_not_impl = sum(1 for t in layer_tests if t.status == "not_implemented")
            layer_failed = sum(1 for t in layer_tests if t.status == "failed")
            layer_timeout = sum(1 for t in layer_tests if t.status == "timeout")
            f.write(f"| Layer {layer} | {layer_success} | {layer_not_impl} | {layer_failed} | {layer_timeout} | {len(layer_tests)} |\n")
        f.write(f"\n")

        f.write(f"### Recommendations | 建议\n\n")
        if not_impl > 0:
            f.write(f"1. **Implement Missing Substeps**: {not_impl} substeps are not yet implemented. These should be prioritized based on the design documents.\n")
        if failed > 0:
            f.write(f"2. **Fix Failed Substeps**: {failed} substeps failed during testing. Review error logs and fix issues.\n")
        if success == total:
            f.write(f"1. **Excellent Coverage**: All substeps are implemented and working correctly!\n")
            f.write(f"2. **Next Steps**: Proceed with Playwright UI testing and DEAIGC effectiveness evaluation.\n")
        f.write(f"\n")

        f.write(f"---\n\n")
        f.write(f"*Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")


if __name__ == "__main__":
    print(f"Starting comprehensive substep testing...")
    print(f"Report will be written to: {REPORT_FILE}\n")

    # Run async tests
    asyncio.run(run_all_tests())

    print(f"\n{'='*70}")
    print(f"Testing complete! Full report written to: {REPORT_FILE}")
    print(f"{'='*70}\n")
