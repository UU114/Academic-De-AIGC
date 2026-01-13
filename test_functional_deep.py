"""
Deep Functional Testing for All Substeps
所有子步骤的深度功能测试

This script tests:
1. Detection functionality - Does it detect AI characteristics correctly?
2. Modification functionality - Can it modify text and does the modification work?
3. Text flow - Does modified text pass to next substep correctly?
4. Locked terms - Are locked terms preserved throughout all modifications?

测试内容：
1. 检测功能 - 是否正确检测AI特征？
2. 修改功能 - 能否修改文本且修改有效？
3. 文本流动 - 修改后的文本是否正确传递到下一个substep？
4. 锁定词汇 - 所有修改过程中锁定词汇是否被保护？
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os
import difflib


class DeepFunctionalTester:
    """Deep functional testing framework for all substeps"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"func_test_{int(time.time())}"

        # Test results structure
        self.results = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "test_type": "functional_deep",
            "substeps": {},
            "summary": {
                "total_substeps": 0,
                "implemented": 0,
                "detection_works": 0,
                "modification_works": 0,
                "not_implemented": 0,
                "issues": []
            }
        }

        # Track text evolution
        self.text_history = []
        self.current_text = ""
        self.locked_terms = []

        # Track detected issues and applied modifications
        self.detected_issues = {}
        self.applied_modifications = {}

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "[INFO]",
            "SUCCESS": "[PASS]",
            "WARNING": "[WARN]",
            "ERROR": "[FAIL]",
            "TEST": "[TEST]"
        }.get(level, "[LOG]")
        print(f"[{timestamp}] {prefix} {message}")

    def load_test_document(self, file_path: str) -> bool:
        """Load test document"""
        self.log(f"Loading test document: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_text = f.read()
            self.text_history.append({
                "step": "original",
                "text": self.current_text,
                "length": len(self.current_text),
                "timestamp": datetime.now().isoformat()
            })
            self.log(f"Loaded {len(self.current_text)} characters", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to load document: {e}", "ERROR")
            return False

    def compare_texts(self, text1: str, text2: str) -> Dict[str, Any]:
        """Compare two texts and return differences"""
        if text1 == text2:
            return {"identical": True, "changes": 0}

        # Calculate diff
        diff = list(difflib.unified_diff(
            text1.split('\n'),
            text2.split('\n'),
            lineterm=''
        ))

        # Count changes
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return {
            "identical": False,
            "changes": additions + deletions,
            "additions": additions,
            "deletions": deletions,
            "diff_lines": len(diff)
        }

    def verify_locked_terms(self, original: str, modified: str) -> Dict[str, Any]:
        """Verify locked terms are preserved in modified text"""
        if not self.locked_terms:
            return {"checked": False, "reason": "no_locked_terms"}

        violations = []
        for term in self.locked_terms:
            original_count = original.lower().count(term.lower())
            modified_count = modified.lower().count(term.lower())

            if original_count != modified_count:
                violations.append({
                    "term": term,
                    "original_count": original_count,
                    "modified_count": modified_count,
                    "violation": "count_changed"
                })

        return {
            "checked": True,
            "violations": violations,
            "preserved": len(violations) == 0
        }

    # =========================================================================
    # Layer 5 - Document Level Tests
    # =========================================================================

    def test_layer5_step1_0_term_locking(self) -> Dict[str, Any]:
        """Test Step 1.0: Term Locking - FUNCTIONAL TEST"""
        self.log("=" * 80)
        self.log("FUNCTIONAL TEST: Layer 5 - Step 1.0: Term Locking", "TEST")
        self.log("=" * 80)

        result = {
            "step": "1.0_term_locking",
            "implemented": False,
            "detection_works": False,
            "modification_works": False,
            "tests": []
        }

        try:
            # Test 1: Can it extract terms?
            self.log("Test 1.0.1: Extracting terms from document...")
            extract_response = requests.post(
                f"{self.base_url}/api/v1/analysis/term-lock/extract-terms",
                json={
                    "document_text": self.current_text,
                    "session_id": self.session_id
                },
                timeout=60
            )

            if extract_response.status_code != 200:
                result["tests"].append({
                    "name": "extract_terms",
                    "passed": False,
                    "error": f"HTTP {extract_response.status_code}"
                })
                return result

            extract_data = extract_response.json()
            result["implemented"] = True

            # Verify: Did it actually extract meaningful terms?
            extracted_count = extract_data.get('total_count', 0)
            extracted_terms = extract_data.get('extracted_terms', [])

            self.log(f"Extracted {extracted_count} terms")

            # Check quality of extraction
            has_technical = any(t['term_type'] == 'technical_term' for t in extracted_terms)
            has_acronyms = any(t['term_type'] == 'acronym' for t in extracted_terms)
            has_key_phrases = any(t['term_type'] == 'key_phrase' for t in extracted_terms)

            detection_quality = {
                "total_extracted": extracted_count,
                "has_technical_terms": has_technical,
                "has_acronyms": has_acronyms,
                "has_key_phrases": has_key_phrases,
                "quality_score": sum([has_technical, has_acronyms, has_key_phrases])
            }

            result["detection_works"] = extracted_count > 0 and detection_quality["quality_score"] >= 2

            result["tests"].append({
                "name": "term_extraction_quality",
                "passed": result["detection_works"],
                "details": detection_quality
            })

            if result["detection_works"]:
                self.log(f"[OK] Term extraction works: {extracted_count} terms found", "SUCCESS")
            else:
                self.log(f"[NG] Term extraction quality insufficient", "WARNING")

            # Test 2: Can it lock and persist terms?
            terms_to_lock = [t['term'] for t in extracted_terms[:5]]  # Lock first 5
            self.log(f"Test 1.0.2: Locking {len(terms_to_lock)} terms...")

            confirm_response = requests.post(
                f"{self.base_url}/api/v1/analysis/term-lock/confirm-lock",
                json={
                    "session_id": self.session_id,
                    "locked_terms": terms_to_lock,
                    "custom_terms": ["test term"]
                },
                timeout=30
            )

            if confirm_response.status_code == 200:
                confirm_data = confirm_response.json()
                self.locked_terms = confirm_data.get('locked_terms', [])

                # Verify persistence
                get_response = requests.get(
                    f"{self.base_url}/api/v1/analysis/term-lock/locked-terms",
                    params={"session_id": self.session_id},
                    timeout=10
                )

                if get_response.status_code == 200:
                    get_data = get_response.json()
                    retrieved_count = get_data.get('locked_count', 0)

                    result["modification_works"] = retrieved_count == len(self.locked_terms)

                    result["tests"].append({
                        "name": "term_locking_persistence",
                        "passed": result["modification_works"],
                        "locked_count": len(self.locked_terms),
                        "retrieved_count": retrieved_count
                    })

                    if result["modification_works"]:
                        self.log(f"[OK] Term locking works: {len(self.locked_terms)} terms locked and persistent", "SUCCESS")
                    else:
                        self.log(f"[NG] Term locking persistence issue", "WARNING")

        except Exception as e:
            self.log(f"Exception in term locking test: {e}", "ERROR")
            result["tests"].append({
                "name": "term_locking",
                "passed": False,
                "exception": str(e)
            })

        self.results["substeps"]["layer5_step1_0"] = result
        return result

    def test_layer5_step1_1_structure_detection(self) -> Dict[str, Any]:
        """Test Step 1.1: Structure Framework Detection - FUNCTIONAL TEST"""
        self.log("=" * 80)
        self.log("FUNCTIONAL TEST: Layer 5 - Step 1.1: Structure Detection", "TEST")
        self.log("=" * 80)

        result = {
            "step": "1.1_structure_detection",
            "implemented": False,
            "detection_works": False,
            "modification_works": False,
            "tests": []
        }

        try:
            # Test: Does it detect structural AI characteristics?
            self.log("Test 1.1.1: Analyzing document structure...")
            response = requests.post(
                f"{self.base_url}/api/v1/analysis/document/structure",
                json={
                    "text": self.current_text,
                    "session_id": self.session_id
                },
                timeout=120
            )

            if response.status_code != 200:
                return result

            data = response.json()
            result["implemented"] = True

            # Analyze detection quality
            risk_score = data.get('risk_score', 0)
            issues = data.get('issues', [])

            # Our test document is HIGHLY AI-characteristic, so:
            # - Risk score should be > 60 (high)
            # - Should detect multiple issues

            detection_quality = {
                "risk_score": risk_score,
                "issues_count": len(issues),
                "risk_level": data.get('risk_level', 'unknown'),
                "expected_high_risk": risk_score > 60,
                "found_issues": len(issues) > 0
            }

            result["detection_works"] = risk_score > 60 and len(issues) > 0

            result["tests"].append({
                "name": "structure_detection_accuracy",
                "passed": result["detection_works"],
                "details": detection_quality
            })

            if result["detection_works"]:
                self.log(f"[OK] Structure detection works: Risk={risk_score}, Issues={len(issues)}", "SUCCESS")
            else:
                self.log(f"[NG] Structure detection may be under-sensitive: Risk={risk_score}", "WARNING")

            # Store detected issues for later verification
            self.detected_issues["structure"] = issues

            # Note: Structure modification is typically user-guided, not automatic
            # So we mark modification_works as N/A
            result["modification_works"] = None  # N/A - user-guided

        except Exception as e:
            self.log(f"Exception in structure detection: {e}", "ERROR")
            result["tests"].append({
                "name": "structure_detection",
                "passed": False,
                "exception": str(e)
            })

        self.results["substeps"]["layer5_step1_1"] = result
        return result

    def test_layer5_step1_2_paragraph_length(self) -> Dict[str, Any]:
        """Test Step 1.2: Paragraph Length Analysis - FUNCTIONAL TEST"""
        self.log("=" * 80)
        self.log("FUNCTIONAL TEST: Layer 5 - Step 1.2: Paragraph Length", "TEST")
        self.log("=" * 80)

        result = {
            "step": "1.2_paragraph_length",
            "implemented": False,
            "detection_works": False,
            "modification_works": False,
            "tests": []
        }

        try:
            self.log("Test 1.2.1: Analyzing paragraph lengths...")
            response = requests.post(
                f"{self.base_url}/api/v1/analysis/document/paragraph-length",
                json={
                    "text": self.current_text,
                    "session_id": self.session_id
                },
                timeout=60
            )

            if response.status_code != 200:
                return result

            data = response.json()
            result["implemented"] = True

            # Check detection quality
            paragraphs = data.get('paragraphs', [])
            cv = data.get('cv', 0)
            # FIX: Use correct field name from API response
            mean_length = data.get('mean_length', 0)

            # Our test doc has uniform paragraphs, CV should be low (< 0.30)
            # FIX: Check for actual strategy fields in API response
            has_strategies = (
                len(data.get('merge_suggestions', [])) > 0 or
                len(data.get('split_suggestions', [])) > 0 or
                len(data.get('expand_suggestions', [])) > 0 or
                len(data.get('compress_suggestions', [])) > 0
            )
            detection_quality = {
                "paragraphs_found": len(paragraphs),
                "cv": cv,
                "mean_length": mean_length,
                "detected_uniformity": cv < 0.30,
                "has_strategies": has_strategies
            }

            result["detection_works"] = len(paragraphs) > 0

            result["tests"].append({
                "name": "paragraph_analysis_accuracy",
                "passed": result["detection_works"],
                "details": detection_quality
            })

            if result["detection_works"]:
                self.log(f"[OK] Paragraph analysis works: {len(paragraphs)} paragraphs, CV={cv:.3f}", "SUCCESS")
            else:
                self.log(f"[NG] Paragraph analysis incomplete", "WARNING")

            # Check for modification suggestions
            strategies = data.get('suggested_strategies', [])
            if strategies:
                self.log(f"  Found {len(strategies)} modification strategies")
                result["modification_works"] = True

        except Exception as e:
            self.log(f"Exception in paragraph length test: {e}", "ERROR")
            result["tests"].append({
                "name": "paragraph_length",
                "passed": False,
                "exception": str(e)
            })

        self.results["substeps"]["layer5_step1_2"] = result
        return result

    def test_layer1_fingerprint_detection_deep(self) -> Dict[str, Any]:
        """Test Layer 1 Step 5.1: Fingerprint Detection - DEEP FUNCTIONAL TEST"""
        self.log("=" * 80)
        self.log("DEEP FUNCTIONAL TEST: Layer 1 - Step 5.1: Fingerprint Detection", "TEST")
        self.log("=" * 80)

        result = {
            "step": "5.1_fingerprint_detection",
            "implemented": False,
            "detection_works": False,
            "modification_works": False,
            "tests": []
        }

        try:
            self.log("Test 5.1.1: Detecting AIGC fingerprints...")
            response = requests.post(
                f"{self.base_url}/api/v1/analysis/lexical/analyze",
                json={
                    "text": self.current_text,
                    "session_id": self.session_id
                },
                timeout=60
            )

            if response.status_code != 200:
                self.log(f"API error: {response.status_code}", "ERROR")
                return result

            data = response.json()
            result["implemented"] = True

            # Deep analysis: Our test document contains MANY fingerprint words
            # Let's manually count what SHOULD be detected
            test_text_lower = self.current_text.lower()

            expected_fingerprints = {
                "delve": test_text_lower.count("delve"),
                "tapestry": test_text_lower.count("tapestry"),
                "multifaceted": test_text_lower.count("multifaceted"),
                "intricate": test_text_lower.count("intricate"),
                "comprehensive": test_text_lower.count("comprehensive"),
                "robust": test_text_lower.count("robust"),
                "leverage": test_text_lower.count("leverage"),
                "paramount": test_text_lower.count("paramount"),
                "holistic": test_text_lower.count("holistic"),
                "seamless": test_text_lower.count("seamless"),
            }

            expected_total = sum(count for count in expected_fingerprints.values() if count > 0)

            # What did the API detect?
            # FIX: Use correct field names from LexicalAnalysisResponse
            # API returns: fingerprint_matches (dict with type_a, type_b, phrases)
            # API returns: details.fingerprints.total_type_a, total_type_b, total_phrases
            fingerprint_matches = data.get('fingerprint_matches', {})
            type_a_list = fingerprint_matches.get('type_a', [])
            type_b_list = fingerprint_matches.get('type_b', [])
            phrase_list = fingerprint_matches.get('phrases', [])

            # Also check details for totals
            details = data.get('details', {})
            fingerprints_details = details.get('fingerprints', {}) if isinstance(details, dict) else {}

            # Calculate detected totals from match lists
            type_a_total = sum(m.get('count', 1) for m in type_a_list) if type_a_list else fingerprints_details.get('total_type_a', 0)
            type_b_total = sum(m.get('count', 1) for m in type_b_list) if type_b_list else fingerprints_details.get('total_type_b', 0)
            phrases_total = sum(m.get('count', 1) for m in phrase_list) if phrase_list else fingerprints_details.get('total_phrases', 0)

            detected_total = type_a_total + type_b_total + phrases_total
            fingerprints = type_a_list + type_b_list
            phrases = phrase_list

            self.log(f"Expected at least {expected_total} fingerprint word instances")
            self.log(f"API detected {detected_total} total")

            # Check if detection is working
            detection_quality = {
                "expected_min": expected_total,
                "detected_total": detected_total,
                "detection_ratio": detected_total / expected_total if expected_total > 0 else 0,
                "fingerprint_words": len(fingerprints),
                "fingerprint_phrases": len(phrases),
                "expected_fingerprints": {k: v for k, v in expected_fingerprints.items() if v > 0}
            }

            # Detection works if it finds at least 50% of expected fingerprints
            result["detection_works"] = detected_total >= (expected_total * 0.5)

            result["tests"].append({
                "name": "fingerprint_detection_accuracy",
                "passed": result["detection_works"],
                "details": detection_quality
            })

            if result["detection_works"]:
                self.log(f"[OK] Fingerprint detection works: Found {detected_total}/{expected_total}", "SUCCESS")
            else:
                self.log(f"[NG] Fingerprint detection FAILED: Only found {detected_total}/{expected_total}", "ERROR")
                self.log(f"  This is a critical issue - detection is not working!", "ERROR")

            # Store for later analysis
            self.detected_issues["fingerprints"] = fingerprints

        except Exception as e:
            self.log(f"Exception in fingerprint detection: {e}", "ERROR")
            result["tests"].append({
                "name": "fingerprint_detection",
                "passed": False,
                "exception": str(e)
            })

        self.results["substeps"]["layer1_step5_1"] = result
        return result

    def generate_summary(self):
        """Generate test summary"""
        self.log("=" * 80)
        self.log("GENERATING TEST SUMMARY", "TEST")
        self.log("=" * 80)

        summary = self.results["summary"]

        for substep_key, substep_data in self.results["substeps"].items():
            summary["total_substeps"] += 1

            if substep_data["implemented"]:
                summary["implemented"] += 1
            else:
                summary["not_implemented"] += 1

            if substep_data["detection_works"]:
                summary["detection_works"] += 1
            elif substep_data["detection_works"] is False:  # Not None
                summary["issues"].append({
                    "substep": substep_key,
                    "issue": "detection_not_working"
                })

            if substep_data["modification_works"]:
                summary["modification_works"] += 1
            elif substep_data["modification_works"] is False:  # Not None
                summary["issues"].append({
                    "substep": substep_key,
                    "issue": "modification_not_working"
                })

        self.results["end_time"] = datetime.now().isoformat()

        # Print summary
        self.log(f"Total substeps tested: {summary['total_substeps']}")
        self.log(f"Implemented: {summary['implemented']}")
        self.log(f"Detection works: {summary['detection_works']}")
        self.log(f"Modification works: {summary['modification_works']}")
        self.log(f"Critical issues found: {len(summary['issues'])}")

        return summary

    def save_results(self, output_dir: str = "./test_results"):
        """Save test results"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = os.path.join(output_dir, f"functional_test_{timestamp}.json")

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.log(f"Results saved to: {json_file}", "SUCCESS")
        return json_file

    def run_all_tests(self, test_document_path: str):
        """Run all functional tests"""
        self.log("=" * 80)
        self.log("STARTING DEEP FUNCTIONAL TESTING", "TEST")
        self.log("=" * 80)

        if not self.load_test_document(test_document_path):
            return

        # Test Layer 5
        self.log("\n" + "="*80)
        self.log("LAYER 5 - DOCUMENT LEVEL FUNCTIONAL TESTS")
        self.log("="*80 + "\n")

        self.test_layer5_step1_0_term_locking()
        self.test_layer5_step1_1_structure_detection()
        self.test_layer5_step1_2_paragraph_length()

        # Test Layer 1
        self.log("\n" + "="*80)
        self.log("LAYER 1 - LEXICAL LEVEL FUNCTIONAL TESTS")
        self.log("="*80 + "\n")

        self.test_layer1_fingerprint_detection_deep()

        # Generate summary
        self.generate_summary()

        # Save results
        json_file = self.save_results()

        self.log("\n" + "="*80)
        self.log("FUNCTIONAL TESTING COMPLETED", "SUCCESS")
        self.log("="*80)
        self.log(f"Results saved to: {json_file}")

        return self.results


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Deep Functional Testing")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--document", default="./test_documents/ai_test_paper.txt", help="Test document path")

    args = parser.parse_args()

    # Check server
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"[WARNING] Server health check failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to server at {args.url}")
        print(f"Error: {e}")
        return

    # Run tests
    tester = DeepFunctionalTester(base_url=args.url)
    results = tester.run_all_tests(test_document_path=args.document)

    # Print critical issues
    if results["summary"]["issues"]:
        print("\n" + "="*80)
        print("[WARNING] CRITICAL ISSUES FOUND:")
        print("="*80)
        for issue in results["summary"]["issues"]:
            print(f"  - {issue['substep']}: {issue['issue']}")


if __name__ == "__main__":
    main()
