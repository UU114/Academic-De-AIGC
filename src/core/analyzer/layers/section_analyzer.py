"""
Section Layer Analyzer (Layer 4)
章节层分析器（第4层）

Handles section-level analysis:
- Step 2.1: Section Logic Flow (章节逻辑流)
- Step 2.2: Section Transitions (章节衔接)
- Step 2.3: Section Length Distribution (章节长度分布)

处理章节级分析：
- 步骤 2.1：章节逻辑流
- 步骤 2.2：章节衔接
- 步骤 2.3：章节长度分布
"""

import re
import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from src.core.analyzer.layers.base import (
    BaseOrchestrator,
    LayerContext,
    LayerResult,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
)

logger = logging.getLogger(__name__)


# Section role patterns (for detecting section functions)
SECTION_ROLE_PATTERNS = {
    "introduction": [
        r"\bintroduction\b", r"\bbackground\b", r"\boverview\b",
        r"\bthis (paper|study|research|work)\b", r"\bwe (present|propose|introduce)\b"
    ],
    "literature_review": [
        r"\bliterature\s+review\b", r"\brelated\s+work\b", r"\bprior\s+(work|research)\b",
        r"\bprevious\s+studies\b", r"\bstate\s+of\s+the\s+art\b"
    ],
    "methodology": [
        r"\bmethodology\b", r"\bmethods?\b", r"\bapproach\b", r"\bprocedure\b",
        r"\bexperimental\s+design\b", r"\bdata\s+collection\b"
    ],
    "results": [
        r"\bresults?\b", r"\bfindings?\b", r"\bobservation\b",
        r"\b(we|our)\s+(found|observed|noted)\b", r"\bthe\s+data\s+show\b"
    ],
    "discussion": [
        r"\bdiscussion\b", r"\bimplications?\b", r"\binterpreting\b",
        r"\bthese\s+(results|findings)\s+(suggest|indicate|demonstrate)\b"
    ],
    "conclusion": [
        r"\bconclusion\b", r"\bsummary\b", r"\bin\s+conclusion\b",
        r"\bfuture\s+(work|research|directions?)\b", r"\blimitations?\b"
    ],
}

# Transition markers between sections
TRANSITION_MARKERS = {
    "strong": [
        r"\bhaving\s+established\b", r"\bbuilding\s+on\b", r"\bgiven\s+the\b",
        r"\bwith\s+this\s+(understanding|foundation)\b", r"\bbased\s+on\b"
    ],
    "moderate": [
        r"\bnow\b", r"\bnext\b", r"\bturning\s+to\b", r"\bmoving\s+to\b",
        r"\bfirst\b", r"\bsecond\b", r"\bfinally\b"
    ],
    "weak": [
        r"\bhowever\b", r"\bmoreover\b", r"\bfurthermore\b", r"\badditionally\b",
        r"\bin\s+addition\b", r"\bconsequently\b"
    ],
}


class SectionAnalyzer(BaseOrchestrator):
    """
    Layer 4: Section-level analyzer
    第4层：章节级分析器

    Responsibilities:
    - Analyze logical relationships between sections
    - Evaluate transition quality between sections
    - Analyze length balance across sections
    - Detect structural anomalies

    职责：
    - 分析章节之间的逻辑关系
    - 评估章节之间的过渡质量
    - 分析章节间的长度平衡
    - 检测结构异常
    """

    layer = LayerLevel.SECTION

    def __init__(self):
        super().__init__()

    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run section-level analysis
        运行章节级分析

        Steps:
        2.1 - Section Logic Flow
        2.2 - Section Transitions
        2.3 - Section Length Distribution
        """
        self.logger.info("Starting section layer analysis (Layer 4)")

        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Detect sections from paragraphs
        sections = self._detect_sections(context.paragraphs)
        context.sections = sections
        details["sections"] = sections
        details["section_count"] = len(sections)

        # Step 2.1: Section Logic Flow
        logic_result = self._analyze_logic_flow(sections)
        issues.extend(logic_result["issues"])
        details["logic_flow"] = logic_result["details"]
        recommendations.extend(logic_result["recommendations"])
        recommendations_zh.extend(logic_result["recommendations_zh"])

        # Step 2.2: Section Transitions
        transition_result = self._analyze_transitions(sections, context.paragraphs)
        issues.extend(transition_result["issues"])
        details["transitions"] = transition_result["details"]
        context.section_transitions = transition_result.get("transitions", [])
        recommendations.extend(transition_result["recommendations"])
        recommendations_zh.extend(transition_result["recommendations_zh"])

        # Step 2.3: Section Length Distribution
        length_result = self._analyze_length_distribution(sections)
        issues.extend(length_result["issues"])
        details["length_distribution"] = length_result["details"]
        recommendations.extend(length_result["recommendations"])
        recommendations_zh.extend(length_result["recommendations_zh"])

        # Calculate overall risk score
        risk_score = self._calculate_layer_risk(logic_result, transition_result, length_result)
        risk_level = self._calculate_risk_level(risk_score)

        # Update context
        context.section_boundaries = [s.get("start_para_idx", 0) for s in sections]
        updated_context = self._update_context(context)

        self.logger.info(f"Section layer analysis complete. Risk score: {risk_score}")

        return LayerResult(
            layer=self.layer,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
            details=details,
            updated_context=updated_context,
        )

    def _detect_sections(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """
        Detect sections and their roles from paragraphs
        从段落中检测章节及其角色

        Uses heuristics:
        1. Look for section header patterns
        2. Analyze content to determine role
        3. Group consecutive paragraphs
        """
        sections = []
        current_section = {
            "role": "unknown",
            "paragraphs": [],
            "start_para_idx": 0,
            "word_count": 0,
        }

        for idx, para in enumerate(paragraphs):
            # Detect role from content
            detected_role = self._detect_paragraph_role(para)

            # Check if this starts a new section (role change or significant content shift)
            if detected_role != current_section["role"] and detected_role != "body":
                # Save current section if it has content
                if current_section["paragraphs"]:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "role": detected_role,
                    "paragraphs": [idx],
                    "start_para_idx": idx,
                    "word_count": len(para.split()),
                }
            else:
                # Continue current section
                current_section["paragraphs"].append(idx)
                current_section["word_count"] += len(para.split())

        # Add final section
        if current_section["paragraphs"]:
            sections.append(current_section)

        # If no sections detected, treat entire document as one section
        if not sections:
            sections = [{
                "role": "body",
                "paragraphs": list(range(len(paragraphs))),
                "start_para_idx": 0,
                "word_count": sum(len(p.split()) for p in paragraphs),
            }]

        return sections

    def _detect_paragraph_role(self, para: str) -> str:
        """
        Detect the role of a paragraph based on content patterns
        根据内容模式检测段落的角色
        """
        para_lower = para.lower()

        for role, patterns in SECTION_ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, para_lower):
                    return role

        return "body"

    def _analyze_logic_flow(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 2.1: Section Logic Flow
        步骤 2.1：章节逻辑流

        Check:
        - Expected section order (intro → lit review → methods → results → discussion → conclusion)
        - Missing critical sections
        - Unexpected section sequences
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Expected academic paper structure
        expected_order = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
        detected_roles = [s["role"] for s in sections]

        details["detected_roles"] = detected_roles
        details["expected_order"] = expected_order

        # Check for linear/predictable structure (AI pattern)
        order_match_score = self._calculate_order_match(detected_roles, expected_order)
        details["order_match_score"] = order_match_score

        if order_match_score >= 0.8:
            issues.append(self._create_issue(
                issue_type="predictable_section_order",
                description="Section order follows a highly predictable academic template",
                description_zh="章节顺序遵循高度可预测的学术模板",
                severity=RiskLevel.MEDIUM,
                suggestion="Consider non-linear narrative elements or integrated discussions",
                suggestion_zh="考虑非线性叙事元素或整合式讨论",
                order_match_score=order_match_score,
            ))
            recommendations.append("Add digressions or integrate discussion with results")
            recommendations_zh.append("添加旁白或将讨论与结果整合")

        # Check for missing sections
        missing_critical = []
        for role in ["introduction", "methodology", "conclusion"]:
            if role not in detected_roles:
                missing_critical.append(role)

        if missing_critical:
            details["missing_sections"] = missing_critical
            issues.append(self._create_issue(
                issue_type="missing_critical_sections",
                description=f"Missing critical sections: {', '.join(missing_critical)}",
                description_zh=f"缺少关键章节：{', '.join(missing_critical)}",
                severity=RiskLevel.LOW,
                suggestion="Ensure all critical sections are present",
                suggestion_zh="确保所有关键章节都存在",
            ))

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _calculate_order_match(self, detected: List[str], expected: List[str]) -> float:
        """
        Calculate how closely detected order matches expected
        计算检测到的顺序与预期顺序的匹配程度
        """
        if not detected:
            return 0.0

        # Filter to only roles that appear in expected
        filtered_detected = [r for r in detected if r in expected]
        if not filtered_detected:
            return 0.0

        # Calculate longest increasing subsequence ratio
        matches = 0
        last_expected_idx = -1

        for role in filtered_detected:
            if role in expected:
                expected_idx = expected.index(role)
                if expected_idx > last_expected_idx:
                    matches += 1
                    last_expected_idx = expected_idx

        return matches / len(filtered_detected) if filtered_detected else 0.0

    def _analyze_transitions(
        self,
        sections: List[Dict[str, Any]],
        paragraphs: List[str]
    ) -> Dict[str, Any]:
        """
        Step 2.2: Section Transitions
        步骤 2.2：章节衔接

        Analyze transition quality between sections:
        - Detect abrupt topic changes
        - Evaluate cross-section coherence
        - Check for AI-like explicit transitions
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        transitions: List[Dict[str, Any]] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        if len(sections) < 2:
            details["transition_count"] = 0
            return {
                "issues": issues,
                "details": details,
                "transitions": transitions,
                "recommendations": recommendations,
                "recommendations_zh": recommendations_zh,
            }

        explicit_transition_count = 0
        weak_transition_count = 0

        for i in range(len(sections) - 1):
            current_section = sections[i]
            next_section = sections[i + 1]

            # Get transition paragraph (first para of next section)
            if next_section["paragraphs"]:
                trans_para_idx = next_section["paragraphs"][0]
                if trans_para_idx < len(paragraphs):
                    trans_para = paragraphs[trans_para_idx]

                    # Analyze transition quality
                    trans_quality = self._analyze_transition_quality(trans_para)
                    transitions.append({
                        "from_section": current_section["role"],
                        "to_section": next_section["role"],
                        "quality": trans_quality["quality"],
                        "markers_found": trans_quality["markers"],
                    })

                    if trans_quality["is_explicit"]:
                        explicit_transition_count += 1

                    if trans_quality["quality"] == "weak":
                        weak_transition_count += 1

        details["transition_count"] = len(transitions)
        details["explicit_transition_count"] = explicit_transition_count
        details["weak_transition_count"] = weak_transition_count

        # AI tends to use explicit transitions
        if len(transitions) > 0:
            explicit_ratio = explicit_transition_count / len(transitions)
            details["explicit_ratio"] = explicit_ratio

            if explicit_ratio >= 0.7:
                issues.append(self._create_issue(
                    issue_type="excessive_explicit_transitions",
                    description=f"Too many explicit section transitions ({explicit_transition_count}/{len(transitions)})",
                    description_zh=f"显式章节过渡过多（{explicit_transition_count}/{len(transitions)}）",
                    severity=RiskLevel.MEDIUM,
                    suggestion="Use more subtle, implicit transitions between sections",
                    suggestion_zh="在章节之间使用更微妙、隐性的过渡",
                    explicit_ratio=explicit_ratio,
                ))
                recommendations.append("Replace explicit transitions with lexical echoes and implicit references")
                recommendations_zh.append("用词汇回声和隐性引用替换显式过渡")

        return {
            "issues": issues,
            "details": details,
            "transitions": transitions,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _analyze_transition_quality(self, para: str) -> Dict[str, Any]:
        """
        Analyze the quality of a transition paragraph
        分析过渡段落的质量
        """
        para_lower = para.lower()
        markers_found = []

        # Check for explicit transition markers
        is_explicit = False
        for quality, patterns in TRANSITION_MARKERS.items():
            for pattern in patterns:
                if re.search(pattern, para_lower):
                    markers_found.append({"type": quality, "pattern": pattern})
                    if quality in ["strong", "moderate"]:
                        is_explicit = True

        # Determine overall quality
        if not markers_found:
            quality = "implicit"
        elif any(m["type"] == "weak" for m in markers_found):
            quality = "weak"
        elif any(m["type"] == "strong" for m in markers_found):
            quality = "strong"
        else:
            quality = "moderate"

        return {
            "quality": quality,
            "markers": markers_found,
            "is_explicit": is_explicit,
        }

    def _analyze_length_distribution(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 2.3: Section Length Distribution
        步骤 2.3：章节长度分布

        Analyze length balance across sections:
        - Detect abnormal length patterns
        - Calculate length CV (coefficient of variation)
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        if len(sections) < 2:
            details["length_cv"] = 0
            return {
                "issues": issues,
                "details": details,
                "recommendations": recommendations,
                "recommendations_zh": recommendations_zh,
            }

        # Calculate section lengths
        lengths = [s["word_count"] for s in sections]
        details["section_lengths"] = lengths
        details["total_words"] = sum(lengths)

        # Calculate CV
        if len(lengths) >= 2 and statistics.mean(lengths) > 0:
            mean_length = statistics.mean(lengths)
            stdev_length = statistics.stdev(lengths) if len(lengths) > 1 else 0
            cv = stdev_length / mean_length if mean_length > 0 else 0

            details["mean_length"] = mean_length
            details["stdev_length"] = stdev_length
            details["length_cv"] = cv

            # AI tends to produce uniform section lengths
            if cv < 0.3:
                issues.append(self._create_issue(
                    issue_type="uniform_section_lengths",
                    description=f"Section lengths are too uniform (CV: {cv:.2f})",
                    description_zh=f"章节长度过于均匀（变异系数：{cv:.2f}）",
                    severity=RiskLevel.MEDIUM if cv < 0.2 else RiskLevel.LOW,
                    suggestion="Vary section lengths - some should be substantially longer/shorter",
                    suggestion_zh="改变章节长度——有些应该明显更长/更短",
                    cv=cv,
                ))
                recommendations.append("Create asymmetric section lengths: detailed methodology, brief background")
                recommendations_zh.append("创建非对称章节长度：详细的方法论，简短的背景")

            # Check for extremely long or short sections
            for idx, (section, length) in enumerate(zip(sections, lengths)):
                ratio = length / mean_length if mean_length > 0 else 1

                if ratio < 0.3 and length < 100:
                    issues.append(self._create_issue(
                        issue_type="very_short_section",
                        description=f"Section '{section['role']}' is very short ({length} words)",
                        description_zh=f"章节 '{section['role']}' 过短（{length}字）",
                        severity=RiskLevel.LOW,
                        position=str(idx),
                        section_role=section["role"],
                    ))

                elif ratio > 3.0:
                    issues.append(self._create_issue(
                        issue_type="very_long_section",
                        description=f"Section '{section['role']}' is very long ({length} words)",
                        description_zh=f"章节 '{section['role']}' 过长（{length}字）",
                        severity=RiskLevel.LOW,
                        position=str(idx),
                        suggestion="Consider splitting into subsections",
                        suggestion_zh="考虑拆分为子章节",
                        section_role=section["role"],
                    ))

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _calculate_layer_risk(
        self,
        logic_result: Dict[str, Any],
        transition_result: Dict[str, Any],
        length_result: Dict[str, Any]
    ) -> int:
        """
        Calculate overall risk score for section layer
        计算章节层的整体风险分数
        """
        score = 0

        # Logic flow contribution
        order_match = logic_result.get("details", {}).get("order_match_score", 0)
        score += int(order_match * 30)  # Max 30 points

        # Transition contribution
        explicit_ratio = transition_result.get("details", {}).get("explicit_ratio", 0)
        score += int(explicit_ratio * 35)  # Max 35 points

        # Length distribution contribution
        cv = length_result.get("details", {}).get("length_cv", 0.5)
        if cv < 0.3:
            score += int((0.3 - cv) / 0.3 * 35)  # Max 35 points for very uniform

        return min(100, score)
