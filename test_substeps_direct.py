"""
Direct Substep Test Script
直接Substep测试脚本

Uses FastAPI TestClient to test all substeps without needing external server.
使用FastAPI TestClient直接测试所有substeps，无需外部服务器。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi.testclient import TestClient
from src.main import app

# Initialize test client
client = TestClient(app)

# Test document path
TEST_DOC_PATH = Path("test_documents/test_high_risk.txt")

# Results storage
test_results: Dict[str, Dict[str, Any]] = {}


def load_test_document() -> str:
    """Load test document content"""
    with open(TEST_DOC_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_endpoint(method: str, endpoint: str, payload: Dict[str, Any] = None) -> tuple:
    """Test a single endpoint"""
    start_time = time.time()
    try:
        if method == "POST":
            resp = client.post(endpoint, json=payload)
        else:
            resp = client.get(endpoint, params=payload)

        elapsed = int((time.time() - start_time) * 1000)

        if resp.status_code == 200:
            return True, resp.json(), elapsed
        else:
            return False, {"error": resp.text, "status": resp.status_code}, elapsed
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        return False, {"error": str(e)}, elapsed


def run_all_tests():
    """Run all substep tests"""
    document_text = load_test_document()
    session_id = f"test_{int(time.time())}"

    # Define all test cases
    test_cases = [
        # Layer 5 (Document Level)
        {"layer": 5, "step": "1.0", "name": "Term Locking - Extract", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-0/extract-terms",
         "payload": {"document_text": document_text, "session_id": session_id}},
        {"layer": 5, "step": "1.1", "name": "Structure Framework", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-1/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 5, "step": "1.2", "name": "Section Uniformity", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-2/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 5, "step": "1.3", "name": "Logic Pattern", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-3/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 5, "step": "1.4", "name": "Paragraph Length", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-4/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 5, "step": "1.5", "name": "Transitions", "method": "POST",
         "endpoint": "/api/v1/layer5/step1-5/analyze",
         "payload": {"text": document_text, "session_id": session_id}},

        # Layer 4 (Section Level)
        {"layer": 4, "step": "2.0", "name": "Section Identification", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-0/identify",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 4, "step": "2.1", "name": "Section Order", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-1/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 4, "step": "2.2", "name": "Length Distribution", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-2/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 4, "step": "2.3", "name": "Internal Structure", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-3/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 4, "step": "2.4", "name": "Section Transition", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-4/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 4, "step": "2.5", "name": "Inter-Section Logic", "method": "POST",
         "endpoint": "/api/v1/layer4/step2-5/analyze",
         "payload": {"text": document_text, "session_id": session_id}},

        # Layer 3 (Paragraph Level)
        {"layer": 3, "step": "3.0", "name": "Paragraph Identification", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-0/identify",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 3, "step": "3.1", "name": "Paragraph Role", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-1/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 3, "step": "3.2", "name": "Internal Coherence", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-2/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 3, "step": "3.3", "name": "Anchor Density", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-3/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 3, "step": "3.4", "name": "Sentence Length", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-4/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 3, "step": "3.5", "name": "Paragraph Transition", "method": "POST",
         "endpoint": "/api/v1/layer3/step3-5/analyze",
         "payload": {"text": document_text, "session_id": session_id}},

        # Layer 2 (Sentence Level)
        {"layer": 2, "step": "4.0", "name": "Sentence Context", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-0/prepare",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 2, "step": "4.1", "name": "Sentence Role", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-1/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 2, "step": "4.2", "name": "Pattern Detection", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-2/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 2, "step": "4.3", "name": "Connector Analysis", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-3/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 2, "step": "4.4", "name": "Length Diversity", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-4/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 2, "step": "4.5", "name": "Sentence Rewriting", "method": "POST",
         "endpoint": "/api/v1/layer2/step4-5/rewrite",
         "payload": {"text": document_text, "session_id": session_id}},

        # Layer 1 (Lexical Level)
        {"layer": 1, "step": "5.0", "name": "Lexical Context", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-0/prepare",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 1, "step": "5.1", "name": "Fingerprint Detection", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-1/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 1, "step": "5.2", "name": "Human Feature", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-2/analyze",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 1, "step": "5.3", "name": "Replacement Generation", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-3/generate",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 1, "step": "5.4", "name": "Paragraph Rewriting", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-4/rewrite",
         "payload": {"text": document_text, "session_id": session_id}},
        {"layer": 1, "step": "5.5", "name": "Validation", "method": "POST",
         "endpoint": "/api/v1/layer1/step5-5/validate",
         "payload": {"text": document_text, "session_id": session_id}},
    ]

    print("=" * 80)
    print("SUBSTEP DIRECT TEST")
    print(f"Test Document: {TEST_DOC_PATH}")
    print(f"Session ID: {session_id}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    for test_case in test_cases:
        layer = test_case["layer"]
        step = test_case["step"]
        name = test_case["name"]
        key = f"Layer{layer}_Step{step}"

        print(f"\n[Testing] Layer {layer} - Step {step}: {name}")

        success, data, elapsed = test_endpoint(
            test_case["method"],
            test_case["endpoint"],
            test_case.get("payload")
        )

        if success:
            risk_score = data.get("risk_score", "N/A")
            risk_level = data.get("risk_level", "N/A")
            issues_count = len(data.get("issues", []))

            print(f"  [OK] Risk: {risk_score}/100 ({risk_level}), Issues: {issues_count}, Time: {elapsed}ms")

            test_results[key] = {
                "status": "SUCCESS",
                "layer": layer,
                "step": step,
                "name": name,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "issues_count": issues_count,
                "issues": data.get("issues", []),
                "recommendations": data.get("recommendations", []),
                "recommendations_zh": data.get("recommendations_zh", []),
                "processing_time_ms": elapsed,
                "full_response": data
            }
        else:
            error = str(data.get("error", "Unknown error"))[:200]
            status = data.get("status", "N/A")
            print(f"  [FAIL] Status: {status}, Error: {error}")

            test_results[key] = {
                "status": "FAILED",
                "layer": layer,
                "step": step,
                "name": name,
                "error": error,
                "http_status": status,
                "processing_time_ms": elapsed
            }

    return test_results


def generate_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Generate test report"""

    # Statistics
    success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in results.values() if r["status"] == "FAILED")

    high_risk = [r for r in results.values() if r["status"] == "SUCCESS" and r.get("risk_level") == "high"]
    medium_risk = [r for r in results.values() if r["status"] == "SUCCESS" and r.get("risk_level") == "medium"]
    low_risk = [r for r in results.values() if r["status"] == "SUCCESS" and r.get("risk_level") == "low"]

    report = []
    report.append("# Substep System Comprehensive Test Report")
    report.append("# Substep系统全面测试报告")
    report.append("")
    report.append(f"> Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"> Test Document: {TEST_DOC_PATH}")
    report.append(f"> Total Substeps: 30")
    report.append(f"> Success: {success_count}, Failed: {failed_count}")
    report.append("")
    report.append("---")
    report.append("")

    # Executive Summary
    report.append("## Executive Summary | 执行摘要")
    report.append("")
    report.append(f"- **Success Rate**: {success_count}/30 ({success_count*100//30}%)")
    report.append(f"- **High Risk Detections**: {len(high_risk)}")
    report.append(f"- **Medium Risk Detections**: {len(medium_risk)}")
    report.append(f"- **Low Risk Detections**: {len(low_risk)}")
    report.append("")

    # Determine effectiveness
    if len(high_risk) >= 5:
        effectiveness = "Excellent - system detects many AI patterns"
        effectiveness_zh = "优秀 - 系统检测到多个AI模式"
    elif len(high_risk) >= 3:
        effectiveness = "Good - system detects significant AI patterns"
        effectiveness_zh = "良好 - 系统检测到明显的AI模式"
    elif len(high_risk) >= 1:
        effectiveness = "Moderate - system detects some AI patterns"
        effectiveness_zh = "一般 - 系统检测到部分AI模式"
    else:
        effectiveness = "Limited - few AI patterns detected"
        effectiveness_zh = "有限 - 检测到较少AI模式"

    report.append(f"**Overall Effectiveness**: {effectiveness}")
    report.append(f"**总体效果**: {effectiveness_zh}")
    report.append("")

    # Layer Summary
    report.append("### Layer Summary | 层级汇总")
    report.append("")
    report.append("| Layer | Substeps | Success | Avg Risk | Effectiveness |")
    report.append("|-------|----------|---------|----------|---------------|")

    for layer in [5, 4, 3, 2, 1]:
        layer_results = [r for r in results.values() if r.get("layer") == layer]
        layer_success = sum(1 for r in layer_results if r["status"] == "SUCCESS")
        scores = [r.get("risk_score", 0) for r in layer_results if r["status"] == "SUCCESS" and isinstance(r.get("risk_score"), (int, float))]
        avg_score = sum(scores) / len(scores) if scores else 0
        eff = "High" if avg_score >= 50 else "Medium" if avg_score >= 30 else "Low"
        report.append(f"| Layer {layer} | {len(layer_results)} | {layer_success} | {avg_score:.1f} | {eff} |")

    report.append("")
    report.append("---")
    report.append("")

    # Detailed Results by Layer
    for layer in [5, 4, 3, 2, 1]:
        layer_name = {5: "Document", 4: "Section", 3: "Paragraph", 2: "Sentence", 1: "Lexical"}[layer]
        report.append(f"## Layer {layer} - {layer_name} Level")
        report.append("")

        layer_results = {k: v for k, v in results.items() if v.get("layer") == layer}

        for key, result in sorted(layer_results.items()):
            step = result["step"]
            name = result["name"]
            status = result["status"]

            report.append(f"### Step {step}: {name}")
            report.append("")

            if status == "SUCCESS":
                risk_score = result.get("risk_score", "N/A")
                risk_level = result.get("risk_level", "N/A")
                issues_count = result.get("issues_count", 0)

                report.append(f"- **Status**: SUCCESS")
                report.append(f"- **Risk Score**: {risk_score}/100")
                report.append(f"- **Risk Level**: {risk_level}")
                report.append(f"- **Issues Found**: {issues_count}")
                report.append(f"- **Processing Time**: {result.get('processing_time_ms', 0)}ms")
                report.append("")

                # Issues
                if result.get("issues"):
                    report.append("**Detected Issues:**")
                    for issue in result["issues"][:5]:
                        desc = issue.get("description", str(issue))
                        report.append(f"- {desc}")
                    report.append("")

                # Recommendations
                if result.get("recommendations"):
                    report.append("**Recommendations:**")
                    for rec in result["recommendations"][:3]:
                        report.append(f"- {rec}")
                    report.append("")

                # DE-AIGC Effectiveness
                if isinstance(risk_score, (int, float)):
                    if risk_score >= 60:
                        eff = "Excellent - Correctly identifies high AI risk"
                    elif risk_score >= 40:
                        eff = "Good - Detects moderate AI patterns"
                    elif risk_score >= 20:
                        eff = "Fair - Some detection capability"
                    else:
                        eff = "Limited - May need calibration"
                    report.append(f"**DE-AIGC Effectiveness**: {eff}")
                    report.append("")
            else:
                report.append(f"- **Status**: FAILED")
                report.append(f"- **Error**: {result.get('error', 'Unknown')[:200]}")
                report.append(f"- **HTTP Status**: {result.get('http_status', 'N/A')}")
                report.append("")

            report.append("---")
            report.append("")

    # Conclusion
    report.append("## Conclusion | 结论")
    report.append("")

    if success_count >= 25 and len(high_risk) >= 5:
        report.append("The DE-AIGC system demonstrates **excellent** performance. Most substeps executed successfully, and the test document (known to contain AI-generated content) was correctly identified with multiple high-risk flags.")
        report.append("")
        report.append("DE-AIGC系统表现**优秀**。大多数子步骤执行成功，测试文档（已知包含AI生成内容）被正确识别，显示多个高风险标记。")
    elif success_count >= 20:
        report.append("The DE-AIGC system demonstrates **good** performance with some room for improvement.")
        report.append("")
        report.append("DE-AIGC系统表现**良好**，仍有改进空间。")
    else:
        report.append("The DE-AIGC system needs improvement. Several substeps failed or did not detect expected AI patterns.")
        report.append("")
        report.append("DE-AIGC系统需要改进。多个子步骤失败或未检测到预期的AI模式。")

    report.append("")
    report.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(report)


def main():
    """Main entry point"""
    print("Starting direct substep tests...\n")

    # Run all tests
    results = run_all_tests()

    # Generate report
    report = generate_report(results)

    # Save report
    report_path = Path("doc/substep_test_report_v2.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save raw results
    json_path = Path("doc/substep_test_results_v2.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    # Summary
    success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in results.values() if r["status"] == "FAILED")
    high_risk = [r for r in results.values() if r["status"] == "SUCCESS" and r.get("risk_level") == "high"]

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: 30")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"High Risk Detections: {len(high_risk)}")
    print(f"\nReport saved to: {report_path}")
    print(f"Raw results saved to: {json_path}")


if __name__ == "__main__":
    main()
