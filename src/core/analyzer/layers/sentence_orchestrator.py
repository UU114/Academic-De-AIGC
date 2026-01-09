"""
Sentence Layer Orchestrator (Layer 2)
句子层编排器（第2层）

Handles sentence-level analysis with PARAGRAPH CONTEXT:
- Step 4.1: Sentence Pattern Detection (句式模式检测)
- Step 4.2: Syntactic Void Detection (句法空洞检测) - integrates syntactic_void.py
- Step 4.3: Sentence Role Classification (句子角色分类)
- Step 4.4: Sentence Polish context preparation (句子润色上下文准备)

**IMPORTANT DESIGN PRINCIPLE 重要设计原则:**
All sentence-level analysis MUST be performed within paragraph context.
Sentence rewriting with context-aware content requires paragraph-level information.
所有句子层分析必须在段落上下文中进行。
与上下文相关的句子改写需要段落级别信息的支持。
"""

import re
import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import Counter

from src.core.analyzer.layers.base import (
    BaseOrchestrator,
    LayerContext,
    LayerResult,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
)
from src.core.analyzer.syntactic_void import (
    SyntacticVoidDetector,
    VoidPatternType,
)
from src.core.analyzer.burstiness import BurstinessAnalyzer

logger = logging.getLogger(__name__)


class SentenceRole(Enum):
    """
    Sentence roles within a paragraph
    段落内的句子角色
    """
    CLAIM = "claim"            # Main assertion or argument
    EVIDENCE = "evidence"      # Supporting data or facts
    ANALYSIS = "analysis"      # Interpretation of evidence
    CRITIQUE = "critique"      # Evaluation or criticism
    CONCESSION = "concession"  # Acknowledging alternative views
    SYNTHESIS = "synthesis"    # Combining multiple ideas
    TRANSITION = "transition"  # Connecting sentences
    CONTEXT = "context"        # Background information
    IMPLICATION = "implication"# Consequences or significance
    ELABORATION = "elaboration"# Expanding on previous point


# Patterns for detecting sentence roles
SENTENCE_ROLE_PATTERNS = {
    SentenceRole.CLAIM: [
        r"^(we|this|the present|our) (argue|propose|suggest|claim|contend)",
        r"^(it is|there is) (clear|evident|apparent)",
        r"^(the|a) (main|key|central|primary) (argument|point|claim)",
    ],
    SentenceRole.EVIDENCE: [
        r"^(the )?(data|results?|findings?|evidence|analysis) (show|suggest|indicate|reveal)",
        r"^(according to|based on)",
        r"^(table|figure|fig\.) \d+ (shows?|presents?|illustrates?)",
        r"\(\w+,?\s*\d{4}\)",  # Citations
    ],
    SentenceRole.ANALYSIS: [
        r"^this (suggests?|indicates?|implies?|demonstrates?|shows?)",
        r"^(in other words|that is|this means)",
        r"^(the )?(implication|significance|meaning) (is|of)",
    ],
    SentenceRole.CRITIQUE: [
        r"^(however|although|while|despite|nevertheless)",
        r"^(this|such|the) (approach|method|view) (is|has) (limited|problematic)",
        r"^(one|a) (limitation|weakness|criticism|problem)",
    ],
    SentenceRole.CONCESSION: [
        r"^(admittedly|granted|certainly|indeed)",
        r"^(it is|may be) true that",
        r"^(while|although|even though) .*,",
    ],
    SentenceRole.TRANSITION: [
        r"^(moreover|furthermore|additionally|in addition)",
        r"^(first|second|third|finally|next|then)",
        r"^(turning to|moving to|with regard to)",
    ],
    SentenceRole.CONTEXT: [
        r"^(historically|traditionally|conventionally)",
        r"^(in|within) the (field|context|domain) of",
        r"^(previous|prior|existing) (research|studies|work)",
    ],
    SentenceRole.IMPLICATION: [
        r"^(therefore|thus|consequently|as a result|hence)",
        r"^(this|these) (has|have) implications for",
        r"^(future|further) (research|studies|work) (should|could|may)",
    ],
}


class SentenceOrchestrator(BaseOrchestrator):
    """
    Layer 2: Sentence-level orchestrator WITH PARAGRAPH CONTEXT
    第2层：带段落上下文的句子级编排器

    **CRITICAL**: This layer analyzes sentences WITHIN their paragraph context.
    Every sentence analysis includes:
    - Full paragraph text
    - Sentence position in paragraph
    - Previous/next sentence
    - Paragraph's role in section

    **关键**: 此层在段落上下文中分析句子。
    每个句子分析包括：
    - 完整段落文本
    - 句子在段落中的位置
    - 前后句子
    - 段落在章节中的角色
    """

    layer = LayerLevel.SENTENCE

    def __init__(self):
        super().__init__()
        self.void_detector = SyntacticVoidDetector()
        self.burstiness_analyzer = BurstinessAnalyzer()

    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run sentence-level analysis WITH paragraph context
        运行带段落上下文的句子级分析

        Steps:
        4.1 - Sentence Pattern Detection
        4.2 - Syntactic Void Detection (integrates syntactic_void.py)
        4.3 - Sentence Role Classification
        4.4 - Sentence Polish Context Preparation
        """
        self.logger.info("Starting sentence layer analysis (Layer 2) with paragraph context")

        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Extract sentences with paragraph mapping
        sentences_with_context = self._extract_sentences_with_context(context)
        context.sentences = [s["text"] for s in sentences_with_context]
        context.sentence_to_paragraph = [s["para_idx"] for s in sentences_with_context]

        details["total_sentences"] = len(sentences_with_context)
        details["paragraph_count"] = len(context.paragraphs)

        # Step 4.1: Sentence Pattern Detection (with paragraph context)
        pattern_result = self._analyze_sentence_patterns(sentences_with_context, context)
        issues.extend(pattern_result["issues"])
        details["patterns"] = pattern_result["details"]
        recommendations.extend(pattern_result["recommendations"])
        recommendations_zh.extend(pattern_result["recommendations_zh"])

        # Step 4.2: Syntactic Void Detection (integrates syntactic_void.py)
        void_result = await self._analyze_syntactic_voids(sentences_with_context, context)
        issues.extend(void_result["issues"])
        details["syntactic_voids"] = void_result["details"]
        recommendations.extend(void_result["recommendations"])
        recommendations_zh.extend(void_result["recommendations_zh"])

        # Step 4.3: Sentence Role Classification
        role_result = self._classify_sentence_roles(sentences_with_context, context)
        issues.extend(role_result["issues"])
        details["sentence_roles"] = role_result["details"]
        context.sentence_roles = role_result.get("roles", [])
        recommendations.extend(role_result["recommendations"])
        recommendations_zh.extend(role_result["recommendations_zh"])

        # Step 4.4: Prepare Sentence Polish Context
        polish_context = self._prepare_polish_context(sentences_with_context, context)
        details["polish_context"] = polish_context

        # Calculate overall risk score
        risk_score = self._calculate_layer_risk(pattern_result, void_result, role_result)
        risk_level = self._calculate_risk_level(risk_score)

        # Update context
        updated_context = self._update_context(context)

        self.logger.info(f"Sentence layer analysis complete. Risk score: {risk_score}")

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

    def _extract_sentences_with_context(self, context: LayerContext) -> List[Dict[str, Any]]:
        """
        Extract sentences with their paragraph context
        提取带段落上下文的句子

        Each sentence includes:
        - text: The sentence text
        - para_idx: Index of containing paragraph
        - para_text: Full paragraph text
        - position_in_para: Position within paragraph
        - prev_sentence: Previous sentence (if any)
        - next_sentence: Next sentence (if any)
        - para_role: Role of the paragraph (from Layer 3)
        """
        sentences_with_context = []
        global_sentence_idx = 0

        for para_idx, para in enumerate(context.paragraphs):
            # Split paragraph into sentences
            para_sentences = re.split(r'(?<=[.!?])\s+', para)
            para_sentences = [s.strip() for s in para_sentences if s.strip()]

            # Get paragraph role from context (if available from Layer 3)
            para_role = context.paragraph_roles[para_idx] if para_idx < len(context.paragraph_roles) else "body"

            for pos_in_para, sentence in enumerate(para_sentences):
                sentence_context = {
                    "text": sentence,
                    "global_idx": global_sentence_idx,
                    "para_idx": para_idx,
                    "para_text": para,
                    "position_in_para": pos_in_para,
                    "total_in_para": len(para_sentences),
                    "is_first_in_para": pos_in_para == 0,
                    "is_last_in_para": pos_in_para == len(para_sentences) - 1,
                    "prev_sentence": para_sentences[pos_in_para - 1] if pos_in_para > 0 else None,
                    "next_sentence": para_sentences[pos_in_para + 1] if pos_in_para < len(para_sentences) - 1 else None,
                    "para_role": para_role,
                }
                sentences_with_context.append(sentence_context)
                global_sentence_idx += 1

        return sentences_with_context

    def _analyze_sentence_patterns(
        self,
        sentences: List[Dict[str, Any]],
        context: LayerContext
    ) -> Dict[str, Any]:
        """
        Step 4.1: Sentence Pattern Detection
        步骤 4.1：句式模式检测

        Detect repetitive sentence structures WITHIN paragraph context.
        检测段落上下文中的重复句式结构。
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Analyze by paragraph for context-aware detection
        para_patterns = {}

        for para_idx in range(len(context.paragraphs)):
            para_sentences = [s for s in sentences if s["para_idx"] == para_idx]

            if len(para_sentences) < 2:
                continue

            # Detect repetitive sentence starts
            starts = []
            for s in para_sentences:
                text = s["text"].lower()
                # Get first 3 words
                words = text.split()[:3]
                start = " ".join(words) if words else ""
                starts.append(start)

            # Check for repetitive patterns
            start_counts = Counter(starts)
            repetitive_starts = {k: v for k, v in start_counts.items() if v >= 2 and k}

            if repetitive_starts:
                para_patterns[para_idx] = {
                    "repetitive_starts": repetitive_starts,
                    "sentence_count": len(para_sentences),
                }

                # Generate issue if significant repetition
                max_repeat = max(repetitive_starts.values())
                if max_repeat >= 3 or max_repeat / len(para_sentences) >= 0.5:
                    most_common_start = max(repetitive_starts, key=repetitive_starts.get)
                    issues.append(self._create_issue(
                        issue_type="repetitive_sentence_starts",
                        description=f"Paragraph {para_idx}: Repetitive sentence beginnings '{most_common_start}...' ({max_repeat} times)",
                        description_zh=f"段落 {para_idx}：句子开头重复 '{most_common_start}...'（{max_repeat}次）",
                        severity=RiskLevel.MEDIUM,
                        position=f"para_{para_idx}",
                        suggestion="Vary sentence openings: start with different subjects, phrases, or clauses",
                        suggestion_zh="变化句子开头：使用不同的主语、短语或从句",
                        repetitive_start=most_common_start,
                        count=max_repeat,
                        para_context=context.paragraphs[para_idx][:200],  # Include para context
                    ))

            # Analyze sentence length variation within paragraph
            lengths = [len(s["text"].split()) for s in para_sentences]
            if len(lengths) >= 2:
                cv = statistics.stdev(lengths) / statistics.mean(lengths) if statistics.mean(lengths) > 0 else 0
                para_patterns.setdefault(para_idx, {})["length_cv"] = cv

        details["paragraph_patterns"] = para_patterns
        details["paragraphs_with_patterns"] = len(para_patterns)

        if len(para_patterns) > len(context.paragraphs) * 0.3:
            recommendations.append("Use varied sentence structures: questions, inversions, complex clauses")
            recommendations_zh.append("使用多样化的句子结构：疑问句、倒装句、复杂从句")

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    async def _analyze_syntactic_voids(
        self,
        sentences: List[Dict[str, Any]],
        context: LayerContext
    ) -> Dict[str, Any]:
        """
        Step 4.2: Syntactic Void Detection
        步骤 4.2：句法空洞检测

        Integrates syntactic_void.py (spaCy en_core_web_md).
        Detects 7 void pattern types with paragraph context for severity weighting.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        void_matches = []
        void_by_paragraph = {}

        try:
            # Analyze each sentence with its paragraph context
            for sentence in sentences:
                result = self.void_detector.analyze(sentence["text"])

                if result.void_matches:
                    for match in result.void_matches:
                        void_info = {
                            "sentence_idx": sentence["global_idx"],
                            "para_idx": sentence["para_idx"],
                            "void_type": match.pattern_type.value,
                            "matched_text": match.matched_text,
                            "confidence": match.confidence,
                            "position_in_para": sentence["position_in_para"],
                            "para_context": sentence["para_text"][:200],
                        }
                        void_matches.append(void_info)

                        # Group by paragraph
                        void_by_paragraph.setdefault(sentence["para_idx"], []).append(void_info)

                        # Severity based on position: first/last sentences are more critical
                        severity = RiskLevel.HIGH if sentence["is_first_in_para"] or sentence["is_last_in_para"] else RiskLevel.MEDIUM

                        issues.append(self._create_issue(
                            issue_type="syntactic_void",
                            description=f"Syntactic void pattern '{match.pattern_type.value}': '{match.matched_text[:50]}...'",
                            description_zh=f"句法空洞模式 '{match.pattern_type.value}'：'{match.matched_text[:50]}...'",
                            severity=severity,
                            position=f"para_{sentence['para_idx']}_sent_{sentence['position_in_para']}",
                            suggestion="Replace with concrete, specific language",
                            suggestion_zh="用具体、明确的语言替换",
                            void_type=match.pattern_type.value,
                            sentence_text=sentence["text"],
                            para_context=sentence["para_text"][:300],
                        ))

            details["total_voids"] = len(void_matches)
            details["voids_by_type"] = Counter([v["void_type"] for v in void_matches])
            details["voids_by_paragraph"] = {k: len(v) for k, v in void_by_paragraph.items()}

            if len(void_matches) > 5:
                recommendations.append("Remove flowery but empty constructions; use direct, specific language")
                recommendations_zh.append("移除华丽但空洞的结构；使用直接、具体的语言")

        except Exception as e:
            self.logger.error(f"Syntactic void analysis failed: {e}")
            details["error"] = str(e)

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _classify_sentence_roles(
        self,
        sentences: List[Dict[str, Any]],
        context: LayerContext
    ) -> Dict[str, Any]:
        """
        Step 4.3: Sentence Role Classification
        步骤 4.3：句子角色分类

        Classifies each sentence into 10 roles, considering paragraph context.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        roles: List[str] = []
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        role_by_paragraph = {}

        for sentence in sentences:
            role = self._detect_sentence_role(sentence)
            roles.append(role.value)

            # Group by paragraph
            role_by_paragraph.setdefault(sentence["para_idx"], []).append(role.value)

        details["role_distribution"] = dict(Counter(roles))
        details["roles_by_paragraph"] = {k: dict(Counter(v)) for k, v in role_by_paragraph.items()}

        # Check for AI-like patterns in role distribution
        # AI tends to have uniform role distribution within paragraphs
        for para_idx, para_roles in role_by_paragraph.items():
            role_counts = Counter(para_roles)
            if len(para_roles) >= 3:
                # Check if one role dominates (AI pattern: all similar roles)
                max_ratio = max(role_counts.values()) / len(para_roles)
                if max_ratio >= 0.7 and len(role_counts) <= 2:
                    dominant_role = max(role_counts, key=role_counts.get)
                    issues.append(self._create_issue(
                        issue_type="homogeneous_sentence_roles",
                        description=f"Paragraph {para_idx}: Sentences have uniform roles ({dominant_role})",
                        description_zh=f"段落 {para_idx}：句子角色单一（{dominant_role}）",
                        severity=RiskLevel.LOW,
                        position=f"para_{para_idx}",
                        suggestion="Mix sentence roles: combine claims with evidence and analysis",
                        suggestion_zh="混合句子角色：将论点与证据和分析结合",
                        dominant_role=dominant_role,
                        max_ratio=max_ratio,
                    ))

        # Check for missing critical roles across document
        all_roles = set(roles)
        critical_roles = {SentenceRole.CLAIM.value, SentenceRole.EVIDENCE.value, SentenceRole.ANALYSIS.value}
        missing_critical = critical_roles - all_roles

        if missing_critical:
            details["missing_critical_roles"] = list(missing_critical)
            issues.append(self._create_issue(
                issue_type="missing_critical_sentence_roles",
                description=f"Document lacks sentences with roles: {', '.join(missing_critical)}",
                description_zh=f"文档缺少以下角色的句子：{', '.join(missing_critical)}",
                severity=RiskLevel.LOW,
                suggestion="Add sentences that make claims, provide evidence, or offer analysis",
                suggestion_zh="添加提出论点、提供证据或进行分析的句子",
            ))

        return {
            "issues": issues,
            "details": details,
            "roles": roles,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _detect_sentence_role(self, sentence: Dict[str, Any]) -> SentenceRole:
        """
        Detect the role of a sentence within its paragraph context
        在段落上下文中检测句子的角色
        """
        text = sentence["text"].lower()

        # Check patterns
        for role, patterns in SENTENCE_ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return role

        # Default based on position in paragraph
        if sentence["is_first_in_para"]:
            return SentenceRole.CLAIM
        elif sentence["is_last_in_para"]:
            return SentenceRole.SYNTHESIS
        else:
            return SentenceRole.ELABORATION

    def _prepare_polish_context(
        self,
        sentences: List[Dict[str, Any]],
        context: LayerContext
    ) -> Dict[str, Any]:
        """
        Step 4.4: Prepare Sentence Polish Context
        步骤 4.4：准备句子润色上下文

        **CONTEXT-CRITICAL**: Prepare all context needed for sentence rewriting.
        Rewriting prompts MUST include:
        - Full paragraph text for context
        - Sentence role in paragraph
        - Previous/next sentence for coherence
        - Paragraph's role in section
        """
        polish_contexts = []

        for sentence in sentences:
            polish_context = {
                "sentence_idx": sentence["global_idx"],
                "sentence_text": sentence["text"],

                # Full paragraph context
                "paragraph_text": sentence["para_text"],
                "paragraph_index": sentence["para_idx"],
                "paragraph_role": sentence["para_role"],

                # Position context
                "position_in_paragraph": sentence["position_in_para"],
                "total_sentences_in_paragraph": sentence["total_in_para"],
                "is_first_sentence": sentence["is_first_in_para"],
                "is_last_sentence": sentence["is_last_in_para"],

                # Adjacent sentences for coherence
                "previous_sentence": sentence["prev_sentence"],
                "next_sentence": sentence["next_sentence"],

                # Sentence role from Layer 2 analysis
                "sentence_role": context.sentence_roles[sentence["global_idx"]] if sentence["global_idx"] < len(context.sentence_roles) else "unknown",
            }
            polish_contexts.append(polish_context)

        return {
            "sentences_with_context": polish_contexts,
            "total_sentences": len(polish_contexts),
            "context_fields": [
                "paragraph_text",
                "paragraph_role",
                "previous_sentence",
                "next_sentence",
                "sentence_role",
                "position_in_paragraph",
            ],
        }

    def _calculate_layer_risk(
        self,
        pattern_result: Dict[str, Any],
        void_result: Dict[str, Any],
        role_result: Dict[str, Any]
    ) -> int:
        """
        Calculate overall risk score for sentence layer
        计算句子层的整体风险分数
        """
        score = 0

        # Pattern issues contribution (max 35)
        pattern_issues = len(pattern_result.get("issues", []))
        score += min(pattern_issues * 10, 35)

        # Syntactic void contribution (max 35)
        void_count = void_result.get("details", {}).get("total_voids", 0)
        score += min(void_count * 5, 35)

        # Role homogeneity contribution (max 30)
        role_issues = len(role_result.get("issues", []))
        score += min(role_issues * 10, 30)

        return min(100, score)
