"""
Paragraph Layer Orchestrator (Layer 3)
段落层编排器（第3层）

Handles paragraph-level analysis:
- Step 3.1: Paragraph Role Detection (段落角色识别)
- Step 3.2: Paragraph Internal Coherence (段落内部连贯性)
- Step 3.3: Anchor Density Analysis (锚点密度分析) - integrates anchor_density.py
- Step 3.4: Sentence Length Distribution (段内句子长度分布)

处理段落级分析：
- 步骤 3.1：段落角色识别
- 步骤 3.2：段落内部连贯性
- 步骤 3.3：锚点密度分析（集成 anchor_density.py）
- 步骤 3.4：段内句子长度分布
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
from src.core.analyzer.anchor_density import (
    AnchorDensityAnalyzer,
    ParagraphAnchorAnalysis,
)
from src.core.analyzer.paragraph_logic import ParagraphLogicAnalyzer

logger = logging.getLogger(__name__)


# Paragraph role patterns
PARAGRAPH_ROLE_PATTERNS = {
    "introduction": [
        r"^(this|the present) (paper|study|research|work|article)",
        r"^in (this|the present) (paper|study)",
        r"^we (present|propose|introduce|describe|report)",
    ],
    "background": [
        r"^(previous|prior|existing) (studies|research|work)",
        r"^(it is|it has been) (well )?(known|established|documented)",
        r"^(many|several|numerous) (studies|researchers|authors)",
    ],
    "methodology": [
        r"^(we|the) (used|employed|applied|adopted)",
        r"^(data|samples?) (were|was) (collected|obtained|gathered)",
        r"^(the )?(method|procedure|protocol|approach)",
    ],
    "results": [
        r"^(the )?(results?|findings?|data|analysis)",
        r"^(we|our results?) (found|observed|show|demonstrate)",
        r"^(figure|table|fig\.) \d",
    ],
    "discussion": [
        r"^(these|our|the) (results?|findings?)",
        r"^(this|these) (suggests?|indicates?|implies?|demonstrates?)",
        r"^(in|for) (comparison|contrast)",
    ],
    "conclusion": [
        r"^in (conclusion|summary)",
        r"^(to|in) (conclude|sum up)",
        r"^(overall|taken together)",
    ],
    "transition": [
        r"^(however|nevertheless|nonetheless|on the other hand)",
        r"^(moreover|furthermore|additionally|in addition)",
        r"^(therefore|thus|consequently|as a result)",
    ],
}


class ParagraphOrchestrator(BaseOrchestrator):
    """
    Layer 3: Paragraph-level orchestrator
    第3层：段落级编排器

    Responsibilities:
    - Classify paragraph functions (intro, body, conclusion, transition)
    - Analyze sentence relationships within paragraphs
    - Calculate anchor density (integrates anchor_density.py)
    - Analyze sentence length distribution within paragraphs

    职责：
    - 分类段落功能（引言、正文、结论、过渡）
    - 分析段落内句子关系
    - 计算锚点密度（集成 anchor_density.py）
    - 分析段落内句子长度分布
    """

    layer = LayerLevel.PARAGRAPH

    def __init__(self):
        super().__init__()
        self.anchor_analyzer = AnchorDensityAnalyzer()
        self.logic_analyzer = ParagraphLogicAnalyzer()

    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run paragraph-level analysis
        运行段落级分析

        Steps:
        3.1 - Paragraph Role Detection
        3.2 - Paragraph Internal Coherence
        3.3 - Anchor Density Analysis
        3.4 - Sentence Length Distribution
        """
        self.logger.info("Starting paragraph layer analysis (Layer 3)")

        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Ensure we have paragraphs
        if not context.paragraphs:
            self.logger.warning("No paragraphs in context")
            return LayerResult(
                layer=self.layer,
                risk_score=0,
                risk_level=RiskLevel.LOW,
                issues=[],
                updated_context=self._update_context(context),
            )

        # Step 3.1: Paragraph Role Detection
        role_result = self._analyze_paragraph_roles(context.paragraphs)
        issues.extend(role_result["issues"])
        details["roles"] = role_result["details"]
        context.paragraph_roles = role_result.get("roles", [])
        recommendations.extend(role_result["recommendations"])
        recommendations_zh.extend(role_result["recommendations_zh"])

        # Step 3.2: Paragraph Internal Coherence
        coherence_result = self._analyze_coherence(context.paragraphs)
        issues.extend(coherence_result["issues"])
        details["coherence"] = coherence_result["details"]
        context.paragraph_coherence = coherence_result.get("scores", [])
        recommendations.extend(coherence_result["recommendations"])
        recommendations_zh.extend(coherence_result["recommendations_zh"])

        # Step 3.3: Anchor Density Analysis (integrates anchor_density.py)
        anchor_result = self._analyze_anchor_density(context.paragraphs)
        issues.extend(anchor_result["issues"])
        details["anchor_density"] = anchor_result["details"]
        context.paragraph_anchor_density = anchor_result.get("densities", [])
        recommendations.extend(anchor_result["recommendations"])
        recommendations_zh.extend(anchor_result["recommendations_zh"])

        # Step 3.4: Sentence Length Distribution within paragraphs
        length_result = self._analyze_sentence_lengths(context.paragraphs)
        issues.extend(length_result["issues"])
        details["sentence_lengths"] = length_result["details"]
        context.paragraph_sentence_lengths = length_result.get("lengths", [])
        recommendations.extend(length_result["recommendations"])
        recommendations_zh.extend(length_result["recommendations_zh"])

        # Calculate overall risk score
        risk_score = self._calculate_layer_risk(role_result, coherence_result, anchor_result, length_result)
        risk_level = self._calculate_risk_level(risk_score)

        # Update context
        updated_context = self._update_context(context)

        self.logger.info(f"Paragraph layer analysis complete. Risk score: {risk_score}")

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

    def _analyze_paragraph_roles(self, paragraphs: List[str]) -> Dict[str, Any]:
        """
        Step 3.1: Paragraph Role Detection
        步骤 3.1：段落角色识别

        Classify each paragraph's function and detect role distribution anomalies.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        roles: List[str] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        for idx, para in enumerate(paragraphs):
            role = self._detect_paragraph_role(para)
            roles.append(role)

        # Analyze role distribution
        role_counts = Counter(roles)
        details["role_distribution"] = dict(role_counts)
        details["paragraph_roles"] = roles

        # Check for AI-like uniform role distribution
        total = len(roles)
        if total > 3:
            # Check if roles are too evenly distributed (AI pattern)
            body_ratio = role_counts.get("body", 0) / total
            if body_ratio > 0.8:
                issues.append(self._create_issue(
                    issue_type="homogeneous_paragraph_roles",
                    description=f"Most paragraphs ({body_ratio:.0%}) have no distinct function",
                    description_zh=f"大多数段落（{body_ratio:.0%}）没有明确功能",
                    severity=RiskLevel.MEDIUM,
                    suggestion="Add clear introductory, transitional, and concluding paragraphs",
                    suggestion_zh="添加明确的引言、过渡和结论段落",
                    body_ratio=body_ratio,
                ))
                recommendations.append("Diversify paragraph functions: add transitions, summaries, and bridging paragraphs")
                recommendations_zh.append("多样化段落功能：添加过渡、摘要和桥接段落")

            # Check for missing transition paragraphs (AI tends to skip these)
            transition_count = role_counts.get("transition", 0)
            if total > 5 and transition_count == 0:
                issues.append(self._create_issue(
                    issue_type="missing_transition_paragraphs",
                    description="No explicit transition paragraphs detected",
                    description_zh="未检测到显式过渡段落",
                    severity=RiskLevel.LOW,
                    suggestion="Add brief transition paragraphs between major sections",
                    suggestion_zh="在主要部分之间添加简短的过渡段落",
                ))

        return {
            "issues": issues,
            "details": details,
            "roles": roles,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _detect_paragraph_role(self, para: str) -> str:
        """
        Detect the role of a single paragraph
        检测单个段落的角色
        """
        para_lower = para.lower().strip()
        first_sentence = para_lower.split('.')[0] if '.' in para_lower else para_lower[:100]

        for role, patterns in PARAGRAPH_ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, first_sentence, re.IGNORECASE):
                    return role

        return "body"

    def _analyze_coherence(self, paragraphs: List[str]) -> Dict[str, Any]:
        """
        Step 3.2: Paragraph Internal Coherence
        步骤 3.2：段落内部连贯性

        Analyze sentence relationships within paragraphs using paragraph_logic.py.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        coherence_scores: List[float] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        para_analyses = []

        for idx, para in enumerate(paragraphs):
            try:
                # Use existing paragraph logic analyzer
                analysis = self.logic_analyzer.analyze(para)

                # Extract coherence indicators
                coherence_score = 1.0 - (analysis.overall_risk / 100)  # Invert risk to coherence
                coherence_scores.append(coherence_score)

                para_analysis = {
                    "paragraph_index": idx,
                    "coherence_score": coherence_score,
                    "subject_diversity": analysis.subject_diversity_score,
                    "length_variation_cv": analysis.length_variation_cv,
                    "logic_structure": analysis.logic_structure,
                    "connector_density": analysis.connector_density,
                    "issue_count": len(analysis.issues),
                }
                para_analyses.append(para_analysis)

                # Generate issues from analysis
                for issue in analysis.issues:
                    if issue.severity == "high":
                        issues.append(self._create_issue(
                            issue_type=issue.type,
                            description=issue.description,
                            description_zh=issue.description_zh,
                            severity=RiskLevel.HIGH,
                            position=f"para_{idx}",
                            suggestion=issue.suggestion,
                            suggestion_zh=issue.suggestion_zh,
                        ))

            except Exception as e:
                self.logger.warning(f"Coherence analysis failed for para {idx}: {e}")
                coherence_scores.append(0.5)  # Default score
                para_analyses.append({"paragraph_index": idx, "error": str(e)})

        details["paragraph_analyses"] = para_analyses
        details["avg_coherence"] = statistics.mean(coherence_scores) if coherence_scores else 0.5

        # Check for uniform coherence (AI pattern)
        if len(coherence_scores) > 2:
            cv = statistics.stdev(coherence_scores) / statistics.mean(coherence_scores) if statistics.mean(coherence_scores) > 0 else 0
            details["coherence_cv"] = cv

            if cv < 0.15:
                issues.append(self._create_issue(
                    issue_type="uniform_coherence",
                    description="Paragraph coherence is too uniform across document",
                    description_zh="段落连贯性在文档中过于均匀",
                    severity=RiskLevel.LOW,
                    suggestion="Vary paragraph complexity: some tightly argued, some more exploratory",
                    suggestion_zh="改变段落复杂度：有些紧密论证，有些更具探索性",
                    cv=cv,
                ))

        return {
            "issues": issues,
            "details": details,
            "scores": coherence_scores,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _analyze_anchor_density(self, paragraphs: List[str]) -> Dict[str, Any]:
        """
        Step 3.3: Anchor Density Analysis
        步骤 3.3：锚点密度分析

        Integrates anchor_density.py to detect hallucination risk.
        Low anchor density (<5 anchors/100 words) = high hallucination risk
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        densities: List[float] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        try:
            # Run anchor density analysis
            anchor_result = self.anchor_analyzer.analyze(paragraphs)

            for para_analysis in anchor_result.paragraph_analyses:
                densities.append(para_analysis.anchor_density)

                # Flag low anchor density paragraphs
                if para_analysis.has_hallucination_risk:
                    issues.append(self._create_issue(
                        issue_type="low_anchor_density",
                        description=f"Paragraph {para_analysis.paragraph_index} has low evidence density ({para_analysis.anchor_density:.1f} anchors/100 words)",
                        description_zh=f"段落 {para_analysis.paragraph_index} 证据密度低（{para_analysis.anchor_density:.1f} 锚点/100词）",
                        severity=RiskLevel.MEDIUM,
                        position=f"para_{para_analysis.paragraph_index}",
                        suggestion="Add specific numbers, citations, or concrete examples",
                        suggestion_zh="添加具体数字、引用或具体例子",
                        anchor_density=para_analysis.anchor_density,
                        word_count=para_analysis.word_count,
                    ))

            details["overall_density"] = anchor_result.overall_density
            details["hallucination_risk_paragraphs"] = [
                p.paragraph_index for p in anchor_result.paragraph_analyses
                if p.has_hallucination_risk
            ]
            details["anchor_type_distribution"] = anchor_result.anchor_type_distribution

            if anchor_result.overall_density < 5:
                recommendations.append("Add more concrete evidence: statistics, citations, measurements")
                recommendations_zh.append("添加更多具体证据：统计数据、引用、测量值")

        except Exception as e:
            self.logger.error(f"Anchor density analysis failed: {e}")
            details["error"] = str(e)

        return {
            "issues": issues,
            "details": details,
            "densities": densities,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _analyze_sentence_lengths(self, paragraphs: List[str]) -> Dict[str, Any]:
        """
        Step 3.4: Sentence Length Distribution within paragraphs
        步骤 3.4：段落内句子长度分布

        AI tends to produce uniform sentence lengths. Human writing has more variation.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        all_lengths: List[List[int]] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        low_burstiness_paras = []

        for idx, para in enumerate(paragraphs):
            # Split into sentences
            sentences = re.split(r'[.!?]+', para)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) < 2:
                all_lengths.append([])
                continue

            # Calculate sentence lengths (word count)
            lengths = [len(s.split()) for s in sentences]
            all_lengths.append(lengths)

            # Calculate within-paragraph CV (burstiness indicator)
            if len(lengths) >= 2 and statistics.mean(lengths) > 0:
                mean_len = statistics.mean(lengths)
                stdev_len = statistics.stdev(lengths)
                cv = stdev_len / mean_len if mean_len > 0 else 0

                # Low CV = uniform sentence lengths = AI pattern
                if cv < 0.25:
                    low_burstiness_paras.append({
                        "index": idx,
                        "cv": cv,
                        "mean_length": mean_len,
                        "lengths": lengths,
                    })

                    issues.append(self._create_issue(
                        issue_type="low_sentence_length_variation",
                        description=f"Paragraph {idx} has uniform sentence lengths (CV: {cv:.2f})",
                        description_zh=f"段落 {idx} 句子长度均匀（变异系数：{cv:.2f}）",
                        severity=RiskLevel.MEDIUM if cv < 0.15 else RiskLevel.LOW,
                        position=f"para_{idx}",
                        suggestion="Mix short punchy sentences with longer complex ones",
                        suggestion_zh="混合简短有力的句子和较长复杂的句子",
                        cv=cv,
                        sentence_lengths=lengths,
                    ))

        details["paragraph_sentence_lengths"] = all_lengths
        details["low_burstiness_paragraphs"] = low_burstiness_paras
        details["low_burstiness_count"] = len(low_burstiness_paras)

        if len(low_burstiness_paras) > len(paragraphs) * 0.3:
            recommendations.append("Increase sentence length variation: add short (5-8 words) and long (25-30 words) sentences")
            recommendations_zh.append("增加句子长度变化：添加短句（5-8词）和长句（25-30词）")

        return {
            "issues": issues,
            "details": details,
            "lengths": all_lengths,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _calculate_layer_risk(
        self,
        role_result: Dict[str, Any],
        coherence_result: Dict[str, Any],
        anchor_result: Dict[str, Any],
        length_result: Dict[str, Any]
    ) -> int:
        """
        Calculate overall risk score for paragraph layer
        计算段落层的整体风险分数
        """
        score = 0

        # Role distribution contribution (max 25)
        role_issues = len(role_result.get("issues", []))
        score += min(role_issues * 10, 25)

        # Coherence contribution (max 25)
        avg_coherence = coherence_result.get("details", {}).get("avg_coherence", 0.5)
        score += int((1 - avg_coherence) * 25)

        # Anchor density contribution (max 25)
        overall_density = anchor_result.get("details", {}).get("overall_density", 10)
        if overall_density < 5:
            score += 25
        elif overall_density < 8:
            score += 15
        elif overall_density < 10:
            score += 5

        # Sentence length variation contribution (max 25)
        low_burst_count = length_result.get("details", {}).get("low_burstiness_count", 0)
        total_paras = len(length_result.get("lengths", []))
        if total_paras > 0:
            low_burst_ratio = low_burst_count / total_paras
            score += int(low_burst_ratio * 25)

        return min(100, score)
