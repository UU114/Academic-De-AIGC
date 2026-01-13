"""
Comprehensive Substep Test Script V2
全面的Substep测试脚本 V2

Tests all 30 substeps across 5 layers:
- Layer 5: Document Level (Step 1.0 - 1.5)
- Layer 4: Section Level (Step 2.0 - 2.5)
- Layer 3: Paragraph Level (Step 3.0 - 3.5)
- Layer 2: Sentence Level (Step 4.0 - 4.5)
- Layer 1: Lexical Level (Step 5.0 - 5.5)
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

BASE_URL = "http://localhost:8000/api/v1"

# Test document path
TEST_DOC_PATH = Path("test_documents/test_high_risk.txt")

# Test results storage
test_results: Dict[str, Dict[str, Any]] = {}


def load_test_document() -> str:
    """Load test document content"""
    with open(TEST_DOC_PATH, "r", encoding="utf-8") as f:
        return f.read()


async def test_endpoint(
    session: aiohttp.ClientSession,
    method: str,
    endpoint: str,
    payload: Dict[str, Any] = None,
    name: str = ""
) -> Tuple[bool, Dict[str, Any], int]:
    """Test a single endpoint and return result"""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()

    try:
        if method == "POST":
            async with session.post(url, json=payload) as resp:
                elapsed = int((time.time() - start_time) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    return True, data, elapsed
                else:
                    error_text = await resp.text()
                    return False, {"error": error_text, "status": resp.status}, elapsed
        elif method == "GET":
            async with session.get(url, params=payload) as resp:
                elapsed = int((time.time() - start_time) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    return True, data, elapsed
                else:
                    error_text = await resp.text()
                    return False, {"error": error_text, "status": resp.status}, elapsed
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        return False, {"error": str(e)}, elapsed


async def run_all_tests():
    """Run all substep tests"""
    document_text = load_test_document()
    session_id = f"test_{int(time.time())}"

    # Define all test cases
    test_cases = [
        # Layer 5 (Document Level)
        {
            "layer": 5, "step": "1.0", "name": "Term Locking - Extract",
            "method": "POST", "endpoint": "/layer5/step1-0/extract-terms",
            "payload": {"document_text": document_text, "session_id": session_id}
        },
        {
            "layer": 5, "step": "1.1", "name": "Structure Framework",
            "method": "POST", "endpoint": "/layer5/step1-1/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 5, "step": "1.2", "name": "Section Uniformity",
            "method": "POST", "endpoint": "/layer5/step1-2/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 5, "step": "1.3", "name": "Logic Pattern",
            "method": "POST", "endpoint": "/layer5/step1-3/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 5, "step": "1.4", "name": "Paragraph Length",
            "method": "POST", "endpoint": "/layer5/step1-4/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 5, "step": "1.5", "name": "Transitions",
            "method": "POST", "endpoint": "/layer5/step1-5/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        # Layer 4 (Section Level)
        {
            "layer": 4, "step": "2.0", "name": "Section Identification",
            "method": "POST", "endpoint": "/layer4/step2-0/identify",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 4, "step": "2.1", "name": "Section Order",
            "method": "POST", "endpoint": "/layer4/step2-1/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 4, "step": "2.2", "name": "Length Distribution",
            "method": "POST", "endpoint": "/layer4/step2-2/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 4, "step": "2.3", "name": "Internal Structure",
            "method": "POST", "endpoint": "/layer4/step2-3/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 4, "step": "2.4", "name": "Section Transition",
            "method": "POST", "endpoint": "/layer4/step2-4/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 4, "step": "2.5", "name": "Inter-Section Logic",
            "method": "POST", "endpoint": "/layer4/step2-5/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        # Layer 3 (Paragraph Level)
        {
            "layer": 3, "step": "3.0", "name": "Paragraph Identification",
            "method": "POST", "endpoint": "/layer3/step3-0/identify",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 3, "step": "3.1", "name": "Paragraph Role",
            "method": "POST", "endpoint": "/layer3/step3-1/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 3, "step": "3.2", "name": "Internal Coherence",
            "method": "POST", "endpoint": "/layer3/step3-2/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 3, "step": "3.3", "name": "Anchor Density",
            "method": "POST", "endpoint": "/layer3/step3-3/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 3, "step": "3.4", "name": "Sentence Length",
            "method": "POST", "endpoint": "/layer3/step3-4/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 3, "step": "3.5", "name": "Paragraph Transition",
            "method": "POST", "endpoint": "/layer3/step3-5/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        # Layer 2 (Sentence Level)
        {
            "layer": 2, "step": "4.0", "name": "Sentence Context",
            "method": "POST", "endpoint": "/layer2/step4-0/prepare",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 2, "step": "4.1", "name": "Sentence Role",
            "method": "POST", "endpoint": "/layer2/step4-1/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 2, "step": "4.2", "name": "Pattern Detection",
            "method": "POST", "endpoint": "/layer2/step4-2/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 2, "step": "4.3", "name": "Connector Analysis",
            "method": "POST", "endpoint": "/layer2/step4-3/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 2, "step": "4.4", "name": "Length Diversity",
            "method": "POST", "endpoint": "/layer2/step4-4/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 2, "step": "4.5", "name": "Sentence Rewriting",
            "method": "POST", "endpoint": "/layer2/step4-5/rewrite",
            "payload": {"text": document_text, "session_id": session_id}
        },
        # Layer 1 (Lexical Level)
        {
            "layer": 1, "step": "5.0", "name": "Lexical Context",
            "method": "POST", "endpoint": "/layer1/step5-0/prepare",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 1, "step": "5.1", "name": "Fingerprint Detection",
            "method": "POST", "endpoint": "/layer1/step5-1/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 1, "step": "5.2", "name": "Human Feature",
            "method": "POST", "endpoint": "/layer1/step5-2/analyze",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 1, "step": "5.3", "name": "Replacement Generation",
            "method": "POST", "endpoint": "/layer1/step5-3/generate",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 1, "step": "5.4", "name": "Paragraph Rewriting",
            "method": "POST", "endpoint": "/layer1/step5-4/rewrite",
            "payload": {"text": document_text, "session_id": session_id}
        },
        {
            "layer": 1, "step": "5.5", "name": "Validation",
            "method": "POST", "endpoint": "/layer1/step5-5/validate",
            "payload": {"text": document_text, "session_id": session_id}
        },
    ]

    print("=" * 80)
    print("SUBSTEP COMPREHENSIVE TEST V2")
    print(f"Test Document: {TEST_DOC_PATH}")
    print(f"Session ID: {session_id}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            layer = test_case["layer"]
            step = test_case["step"]
            name = test_case["name"]
            key = f"Layer{layer}_Step{step}"

            print(f"\n[Testing] Layer {layer} - Step {step}: {name}")

            success, data, elapsed = await test_endpoint(
                session,
                test_case["method"],
                test_case["endpoint"],
                test_case.get("payload")
            )

            if success:
                # Extract key metrics
                risk_score = data.get("risk_score", "N/A")
                risk_level = data.get("risk_level", "N/A")
                issues_count = len(data.get("issues", []))

                print(f"  [OK] Risk: {risk_score}/100 ({risk_level}), Issues: {issues_count}, Time: {elapsed}ms")

                # Store detailed results
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
                error = data.get("error", "Unknown error")
                status = data.get("status", "N/A")
                print(f"  [FAIL] Status: {status}, Error: {error[:100]}...")

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


def evaluate_deaigc_effectiveness(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate DE-AIGC effectiveness based on test results"""

    evaluation = {
        "total_substeps": 30,
        "success_count": 0,
        "failed_count": 0,
        "high_risk_detections": [],
        "medium_risk_detections": [],
        "low_risk_detections": [],
        "layer_summary": {},
        "key_findings": [],
        "overall_effectiveness": "N/A"
    }

    layer_stats = {1: [], 2: [], 3: [], 4: [], 5: []}

    for key, result in results.items():
        if result["status"] == "SUCCESS":
            evaluation["success_count"] += 1
            layer = result["layer"]
            risk_score = result.get("risk_score", 0)
            risk_level = result.get("risk_level", "low")

            if isinstance(risk_score, (int, float)):
                layer_stats[layer].append(risk_score)

            if risk_level == "high":
                evaluation["high_risk_detections"].append({
                    "step": f"Step {result['step']}",
                    "name": result["name"],
                    "risk_score": risk_score,
                    "issues": result.get("issues_count", 0)
                })
            elif risk_level == "medium":
                evaluation["medium_risk_detections"].append({
                    "step": f"Step {result['step']}",
                    "name": result["name"],
                    "risk_score": risk_score,
                    "issues": result.get("issues_count", 0)
                })
            else:
                evaluation["low_risk_detections"].append({
                    "step": f"Step {result['step']}",
                    "name": result["name"],
                    "risk_score": risk_score,
                    "issues": result.get("issues_count", 0)
                })
        else:
            evaluation["failed_count"] += 1

    # Calculate layer averages
    for layer, scores in layer_stats.items():
        if scores:
            avg = sum(scores) / len(scores)
            evaluation["layer_summary"][f"Layer {layer}"] = {
                "avg_risk_score": round(avg, 1),
                "substeps_tested": len(scores),
                "effectiveness": "High" if avg >= 50 else "Medium" if avg >= 30 else "Low"
            }

    # Key findings
    if len(evaluation["high_risk_detections"]) >= 3:
        evaluation["key_findings"].append("Multiple high-risk AI patterns detected - document needs significant revision")
    if evaluation["success_count"] == 30:
        evaluation["key_findings"].append("All 30 substeps executed successfully")
    if evaluation["failed_count"] > 0:
        evaluation["key_findings"].append(f"{evaluation['failed_count']} substeps failed - check implementation")

    # Overall effectiveness
    total_high = len(evaluation["high_risk_detections"])
    if total_high >= 5:
        evaluation["overall_effectiveness"] = "Excellent - system detects many AI patterns"
    elif total_high >= 3:
        evaluation["overall_effectiveness"] = "Good - system detects significant AI patterns"
    elif total_high >= 1:
        evaluation["overall_effectiveness"] = "Moderate - system detects some AI patterns"
    else:
        evaluation["overall_effectiveness"] = "Limited - few AI patterns detected"

    return evaluation


def generate_report(results: Dict[str, Dict[str, Any]], evaluation: Dict[str, Any]) -> str:
    """Generate comprehensive test report"""

    report = []
    report.append("# Substep System Comprehensive Test Report V2")
    report.append("# Substep系统全面测试报告 V2")
    report.append("")
    report.append(f"> Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"> Test Document: {TEST_DOC_PATH}")
    report.append(f"> Total Substeps: {evaluation['total_substeps']}")
    report.append(f"> Success: {evaluation['success_count']}, Failed: {evaluation['failed_count']}")
    report.append("")
    report.append("---")
    report.append("")

    # Executive Summary
    report.append("## Executive Summary | 执行摘要")
    report.append("")
    report.append(f"**Overall Effectiveness**: {evaluation['overall_effectiveness']}")
    report.append("")
    report.append("### Key Findings | 关键发现")
    for finding in evaluation["key_findings"]:
        report.append(f"- {finding}")
    report.append("")

    # Layer Summary
    report.append("### Layer Summary | 层级汇总")
    report.append("")
    report.append("| Layer | Avg Risk Score | Substeps | Detection Effectiveness |")
    report.append("|-------|----------------|----------|-------------------------|")
    for layer_name, stats in evaluation["layer_summary"].items():
        report.append(f"| {layer_name} | {stats['avg_risk_score']} | {stats['substeps_tested']} | {stats['effectiveness']} |")
    report.append("")

    # High Risk Detections
    report.append("### High Risk Detections | 高风险检测")
    report.append("")
    if evaluation["high_risk_detections"]:
        for det in evaluation["high_risk_detections"]:
            report.append(f"- **{det['step']}: {det['name']}** - Risk: {det['risk_score']}, Issues: {det['issues']}")
    else:
        report.append("- No high-risk patterns detected")
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
                report.append(f"**Status**: SUCCESS")
                report.append(f"**Risk Score**: {result.get('risk_score', 'N/A')}/100")
                report.append(f"**Risk Level**: {result.get('risk_level', 'N/A')}")
                report.append(f"**Issues Found**: {result.get('issues_count', 0)}")
                report.append(f"**Processing Time**: {result.get('processing_time_ms', 0)}ms")
                report.append("")

                # Issues
                if result.get("issues"):
                    report.append("**Detected Issues:**")
                    for issue in result["issues"][:5]:  # Limit to 5 issues
                        desc = issue.get("description", str(issue))
                        report.append(f"- {desc}")
                    report.append("")

                # Recommendations
                if result.get("recommendations"):
                    report.append("**Recommendations:**")
                    for rec in result["recommendations"][:3]:
                        report.append(f"- {rec}")
                    report.append("")

                # DE-AIGC Effectiveness Evaluation
                risk_score = result.get("risk_score", 0)
                if isinstance(risk_score, (int, float)):
                    if risk_score >= 60:
                        effectiveness = "Excellent - Correctly identifies high AI risk"
                    elif risk_score >= 40:
                        effectiveness = "Good - Detects moderate AI patterns"
                    elif risk_score >= 20:
                        effectiveness = "Fair - Some detection capability"
                    else:
                        effectiveness = "Limited - May need calibration"
                    report.append(f"**DE-AIGC Effectiveness**: {effectiveness}")
                    report.append("")
            else:
                report.append(f"**Status**: FAILED")
                report.append(f"**Error**: {result.get('error', 'Unknown')[:200]}")
                report.append(f"**HTTP Status**: {result.get('http_status', 'N/A')}")
                report.append("")

            report.append("---")
            report.append("")

    # Overall Evaluation
    report.append("## Overall DE-AIGC Effectiveness Evaluation")
    report.append("")
    report.append("### Detection Capability Assessment | 检测能力评估")
    report.append("")

    # Count by risk level
    high_count = len(evaluation["high_risk_detections"])
    med_count = len(evaluation["medium_risk_detections"])
    low_count = len(evaluation["low_risk_detections"])

    report.append(f"- **High Risk Detections**: {high_count}")
    report.append(f"- **Medium Risk Detections**: {med_count}")
    report.append(f"- **Low Risk Detections**: {low_count}")
    report.append("")

    # Final Verdict
    report.append("### Final Verdict | 最终结论")
    report.append("")

    if high_count >= 5:
        report.append("The DE-AIGC system demonstrates **excellent** detection capability. The test document (known to be AI-generated) was correctly identified with multiple high-risk flags across various analytical dimensions.")
        report.append("")
        report.append("DE-AIGC系统展现了**优秀**的检测能力。测试文档（已知为AI生成）被正确识别，在多个分析维度上都标记为高风险。")
    elif high_count >= 3:
        report.append("The DE-AIGC system demonstrates **good** detection capability. Several key AI patterns were successfully identified in the test document.")
        report.append("")
        report.append("DE-AIGC系统展现了**良好**的检测能力。测试文档中的多个关键AI模式被成功识别。")
    else:
        report.append("The DE-AIGC system shows **moderate** detection capability. Consider adjusting detection thresholds or adding more detection rules.")
        report.append("")
        report.append("DE-AIGC系统展现了**一般**的检测能力。建议调整检测阈值或添加更多检测规则。")

    report.append("")
    report.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(report)


async def main():
    """Main entry point"""
    print("Starting comprehensive substep tests...\n")

    # Run all tests
    results = await run_all_tests()

    # Evaluate effectiveness
    evaluation = evaluate_deaigc_effectiveness(results)

    # Generate report
    report = generate_report(results, evaluation)

    # Save report
    report_path = Path("doc/substep_test_report_v2.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save raw results as JSON
    json_path = Path("doc/substep_test_results_v2.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "evaluation": evaluation}, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {evaluation['total_substeps']}")
    print(f"Success: {evaluation['success_count']}")
    print(f"Failed: {evaluation['failed_count']}")
    print(f"High Risk Detections: {len(evaluation['high_risk_detections'])}")
    print(f"Overall Effectiveness: {evaluation['overall_effectiveness']}")
    print(f"\nReport saved to: {report_path}")
    print(f"Raw results saved to: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
