"""
Sentence Structure Analyzer - Detects sentence types, clause nesting depth, and structure distribution
句式结构分析器 - 检测句型、从句嵌套深度和结构分布

This module provides tools to analyze sentence structures for de-AIGC purposes:
1. Sentence type detection (simple, compound, complex, compound-complex)
2. Clause nesting depth analysis
3. Structure distribution validation
4. Active/Passive voice detection

Human academic writing characteristics:
- Simple sentences: 15-25%
- Compound sentences: 20-30%
- Complex sentences: 35-45%
- Compound-complex: 10-20%
- Nesting depth variation (not always shallow)
- Mixed active/passive (50-70% active)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class SentenceType(str, Enum):
    """Sentence structure types / 句式结构类型"""
    SIMPLE = "simple"                    # Simple sentence / 简单句
    COMPOUND = "compound"                # Compound sentence / 并列句
    COMPLEX = "complex"                  # Complex sentence / 复杂句
    COMPOUND_COMPLEX = "compound_complex"  # Compound-complex / 并列复合句


class VoiceType(str, Enum):
    """Voice types / 语态类型"""
    ACTIVE = "active"
    PASSIVE = "passive"
    MIXED = "mixed"


@dataclass
class SentenceAnalysis:
    """Analysis result for a single sentence / 单句分析结果"""
    text: str
    sentence_type: SentenceType
    nesting_depth: int
    voice: VoiceType
    word_count: int
    has_subordinate_clause: bool
    has_coordination: bool
    subordinate_markers: List[str] = field(default_factory=list)
    coordination_markers: List[str] = field(default_factory=list)


@dataclass
class StructureDistribution:
    """Structure distribution statistics / 结构分布统计"""
    total_sentences: int
    type_counts: Dict[str, int]
    type_percentages: Dict[str, float]
    nesting_depth_distribution: Dict[int, int]
    average_nesting_depth: float
    voice_distribution: Dict[str, int]
    active_percentage: float
    issues: List[Dict] = field(default_factory=list)
    is_human_like: bool = True


class SentenceStructureAnalyzer:
    """
    Analyzer for sentence structure diversity
    句式结构多样性分析器

    Detects:
    - Sentence type (simple/compound/complex/compound-complex)
    - Clause nesting depth
    - Active/Passive voice
    - Distribution issues (AI-like patterns)
    """

    # Subordinate clause markers (indicate complex sentences)
    # 从属从句标志词（表示复杂句）
    SUBORDINATE_MARKERS = [
        # Relative pronouns / 关系代词
        "which", "that", "who", "whom", "whose", "where", "when", "whereby",
        # Subordinating conjunctions / 从属连词
        "because", "since", "although", "though", "while", "whereas",
        "if", "unless", "until", "before", "after", "as", "when",
        "provided that", "given that", "assuming that", "in order that",
        "so that", "such that", "even though", "even if",
        # Other markers / 其他标志
        "whether", "how", "why", "what", "whoever", "whatever",
    ]

    # Coordination markers (indicate compound sentences)
    # 并列标志词（表示并列句）
    COORDINATION_MARKERS = [
        # Coordinating conjunctions / 并列连词
        ", and ", "; and ", " and ",
        ", but ", "; but ", " but ",
        ", or ", "; or ", " or ",
        ", nor ", " nor ",
        ", yet ", " yet ",
        ", so ", " so ",
        # Semicolon as coordination / 分号作为并列
        "; ",
    ]

    # Passive voice indicators / 被动语态标志
    PASSIVE_PATTERNS = [
        r"\b(?:is|are|was|were|been|being|be)\s+\w+ed\b",
        r"\b(?:is|are|was|were|been|being|be)\s+\w+en\b",
        r"\bby\s+(?:the|a|an|\w+)\b",
    ]

    # Human-like distribution targets / 人类化分布目标
    TARGET_DISTRIBUTION = {
        SentenceType.SIMPLE: (0.15, 0.25),        # 15-25%
        SentenceType.COMPOUND: (0.20, 0.30),      # 20-30%
        SentenceType.COMPLEX: (0.35, 0.45),       # 35-45%
        SentenceType.COMPOUND_COMPLEX: (0.10, 0.20),  # 10-20%
    }

    # Target nesting depth distribution / 目标嵌套深度分布
    TARGET_NESTING = {
        0: (0.15, 0.25),  # Depth 0: 15-25%
        1: (0.40, 0.50),  # Depth 1: 40-50%
        2: (0.20, 0.30),  # Depth 2: 20-30%
        3: (0.05, 0.15),  # Depth 3+: 5-15%
    }

    def __init__(self):
        """Initialize analyzer with compiled patterns"""
        self.passive_patterns = [re.compile(p, re.IGNORECASE) for p in self.PASSIVE_PATTERNS]

    def analyze_sentence(self, sentence: str) -> SentenceAnalysis:
        """
        Analyze a single sentence structure
        分析单个句子的结构

        Args:
            sentence: The sentence to analyze

        Returns:
            SentenceAnalysis with type, nesting depth, voice, etc.
        """
        sentence_lower = sentence.lower()
        word_count = len(sentence.split())

        # Detect subordinate clause markers
        # 检测从属从句标志
        subordinate_markers = []
        for marker in self.SUBORDINATE_MARKERS:
            if marker in sentence_lower:
                subordinate_markers.append(marker)
        has_subordinate = len(subordinate_markers) > 0

        # Detect coordination markers
        # 检测并列标志
        coordination_markers = []
        for marker in self.COORDINATION_MARKERS:
            if marker in sentence_lower or marker in sentence:
                coordination_markers.append(marker.strip())
        has_coordination = len(coordination_markers) > 0

        # Determine sentence type
        # 确定句型
        sentence_type = self._determine_type(has_subordinate, has_coordination)

        # Calculate nesting depth
        # 计算嵌套深度
        nesting_depth = self._calculate_nesting_depth(sentence_lower, subordinate_markers)

        # Detect voice
        # 检测语态
        voice = self._detect_voice(sentence)

        return SentenceAnalysis(
            text=sentence,
            sentence_type=sentence_type,
            nesting_depth=nesting_depth,
            voice=voice,
            word_count=word_count,
            has_subordinate_clause=has_subordinate,
            has_coordination=has_coordination,
            subordinate_markers=subordinate_markers,
            coordination_markers=coordination_markers,
        )

    def _determine_type(self, has_subordinate: bool, has_coordination: bool) -> SentenceType:
        """
        Determine sentence type based on clause markers
        根据从句标志确定句型
        """
        if has_subordinate and has_coordination:
            return SentenceType.COMPOUND_COMPLEX
        elif has_subordinate:
            return SentenceType.COMPLEX
        elif has_coordination:
            return SentenceType.COMPOUND
        else:
            return SentenceType.SIMPLE

    def _calculate_nesting_depth(self, sentence_lower: str, markers: List[str]) -> int:
        """
        Calculate clause nesting depth
        计算从句嵌套深度

        Depth is approximated by counting nested subordinate markers
        """
        if not markers:
            return 0

        # Count occurrences of markers
        # 计算标志词出现次数
        total_markers = 0
        for marker in self.SUBORDINATE_MARKERS:
            count = sentence_lower.count(marker)
            if count > 0:
                total_markers += count

        # Approximate depth based on marker count
        # 根据标志词数量近似计算深度
        if total_markers >= 4:
            return 3
        elif total_markers >= 2:
            return 2
        elif total_markers >= 1:
            return 1
        return 0

    def _detect_voice(self, sentence: str) -> VoiceType:
        """
        Detect active/passive voice
        检测主动/被动语态
        """
        passive_count = 0
        for pattern in self.passive_patterns:
            if pattern.search(sentence):
                passive_count += 1

        if passive_count >= 2:
            return VoiceType.PASSIVE
        elif passive_count == 1:
            return VoiceType.MIXED
        return VoiceType.ACTIVE

    def analyze_paragraph(self, sentences: List[str]) -> StructureDistribution:
        """
        Analyze structure distribution of a paragraph
        分析段落的结构分布

        Args:
            sentences: List of sentences in the paragraph

        Returns:
            StructureDistribution with statistics and issues
        """
        if not sentences:
            return StructureDistribution(
                total_sentences=0,
                type_counts={},
                type_percentages={},
                nesting_depth_distribution={},
                average_nesting_depth=0.0,
                voice_distribution={},
                active_percentage=0.0,
                issues=[{"type": "empty_paragraph", "description": "No sentences to analyze"}],
                is_human_like=False,
            )

        # Analyze each sentence
        # 分析每个句子
        analyses = [self.analyze_sentence(s) for s in sentences]
        total = len(analyses)

        # Count sentence types
        # 统计句型
        type_counts = {t.value: 0 for t in SentenceType}
        for a in analyses:
            type_counts[a.sentence_type.value] += 1

        type_percentages = {t: c / total for t, c in type_counts.items()}

        # Count nesting depths
        # 统计嵌套深度
        nesting_counts = {}
        total_depth = 0
        for a in analyses:
            depth = min(a.nesting_depth, 3)  # Cap at 3+
            nesting_counts[depth] = nesting_counts.get(depth, 0) + 1
            total_depth += a.nesting_depth

        avg_nesting = total_depth / total

        # Count voice types
        # 统计语态
        voice_counts = {v.value: 0 for v in VoiceType}
        for a in analyses:
            voice_counts[a.voice.value] += 1

        active_count = voice_counts[VoiceType.ACTIVE.value] + voice_counts[VoiceType.MIXED.value] * 0.5
        active_pct = active_count / total

        # Detect issues
        # 检测问题
        issues = self._detect_distribution_issues(
            type_percentages, nesting_counts, total, active_pct, analyses
        )

        is_human_like = len(issues) == 0

        return StructureDistribution(
            total_sentences=total,
            type_counts=type_counts,
            type_percentages=type_percentages,
            nesting_depth_distribution=nesting_counts,
            average_nesting_depth=avg_nesting,
            voice_distribution=voice_counts,
            active_percentage=active_pct,
            issues=issues,
            is_human_like=is_human_like,
        )

    def _detect_distribution_issues(
        self,
        type_pct: Dict[str, float],
        nesting_counts: Dict[int, int],
        total: int,
        active_pct: float,
        analyses: List[SentenceAnalysis]
    ) -> List[Dict]:
        """
        Detect AI-like distribution issues
        检测AI化的分布问题
        """
        issues = []

        # Check sentence type distribution
        # 检查句型分布
        for stype, (min_pct, max_pct) in self.TARGET_DISTRIBUTION.items():
            pct = type_pct.get(stype.value, 0)
            if pct < min_pct:
                issues.append({
                    "type": "low_type_percentage",
                    "description": f"{stype.value} sentences too few ({pct:.0%} < {min_pct:.0%})",
                    "description_zh": f"{stype.value} 句型过少 ({pct:.0%} < {min_pct:.0%})",
                    "severity": "medium",
                    "suggestion": f"Add more {stype.value} sentences",
                })
            elif pct > max_pct:
                issues.append({
                    "type": "high_type_percentage",
                    "description": f"{stype.value} sentences too many ({pct:.0%} > {max_pct:.0%})",
                    "description_zh": f"{stype.value} 句型过多 ({pct:.0%} > {max_pct:.0%})",
                    "severity": "medium",
                    "suggestion": f"Reduce {stype.value} sentences, add variety",
                })

        # Check for all shallow nesting (AI signature)
        # 检查是否全部浅嵌套（AI特征）
        deep_count = sum(nesting_counts.get(d, 0) for d in [2, 3])
        deep_pct = deep_count / total if total > 0 else 0
        if deep_pct < 0.15:
            issues.append({
                "type": "shallow_nesting",
                "description": f"All sentences have shallow nesting (deep {deep_pct:.0%} < 15%)",
                "description_zh": f"所有句子嵌套都很浅（深嵌套 {deep_pct:.0%} < 15%）",
                "severity": "high",
                "suggestion": "Add sentences with 2+ levels of nested clauses (which/that/where)",
            })

        # Check voice distribution
        # 检查语态分布
        if active_pct < 0.50:
            issues.append({
                "type": "too_much_passive",
                "description": f"Too much passive voice ({1-active_pct:.0%} passive)",
                "description_zh": f"被动语态过多 ({1-active_pct:.0%} 被动)",
                "severity": "medium",
                "suggestion": "Convert some passive sentences to active voice",
            })
        elif active_pct > 0.80:
            issues.append({
                "type": "too_much_active",
                "description": f"Too much active voice ({active_pct:.0%} active)",
                "description_zh": f"主动语态过多 ({active_pct:.0%} 主动)",
                "severity": "low",
                "suggestion": "Add some passive constructions for variety",
            })

        # Check for consecutive same type (AI pattern)
        # 检查连续相同句型（AI模式）
        consecutive_issues = self._check_consecutive_same_type(analyses)
        issues.extend(consecutive_issues)

        return issues

    def _check_consecutive_same_type(self, analyses: List[SentenceAnalysis]) -> List[Dict]:
        """
        Check for 3+ consecutive sentences of same type
        检查是否有3+个连续相同句型的句子
        """
        issues = []
        if len(analyses) < 3:
            return issues

        consecutive_count = 1
        current_type = analyses[0].sentence_type
        start_idx = 0

        for i in range(1, len(analyses)):
            if analyses[i].sentence_type == current_type:
                consecutive_count += 1
            else:
                if consecutive_count >= 3:
                    issues.append({
                        "type": "consecutive_same_type",
                        "description": f"{consecutive_count} consecutive {current_type.value} sentences (positions {start_idx+1}-{i})",
                        "description_zh": f"{consecutive_count} 个连续的 {current_type.value} 句型（位置 {start_idx+1}-{i}）",
                        "severity": "medium",
                        "positions": list(range(start_idx, i)),
                        "suggestion": "Break up consecutive same-type sentences with different structures",
                    })
                consecutive_count = 1
                current_type = analyses[i].sentence_type
                start_idx = i

        # Check the last group
        # 检查最后一组
        if consecutive_count >= 3:
            issues.append({
                "type": "consecutive_same_type",
                "description": f"{consecutive_count} consecutive {current_type.value} sentences at end",
                "description_zh": f"结尾处有 {consecutive_count} 个连续的 {current_type.value} 句型",
                "severity": "medium",
                "positions": list(range(start_idx, len(analyses))),
                "suggestion": "Break up consecutive same-type sentences with different structures",
            })

        return issues

    def get_improvement_suggestions(self, distribution: StructureDistribution) -> List[Dict]:
        """
        Generate improvement suggestions based on distribution analysis
        根据分布分析生成改进建议

        Args:
            distribution: The analyzed structure distribution

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        for issue in distribution.issues:
            suggestion = {
                "issue_type": issue["type"],
                "description": issue["description"],
                "description_zh": issue.get("description_zh", ""),
                "severity": issue.get("severity", "medium"),
                "action": issue.get("suggestion", ""),
            }

            # Add specific grammar tools based on issue type
            # 根据问题类型添加具体的语法工具
            if issue["type"] == "shallow_nesting":
                suggestion["grammar_tools"] = [
                    "Nested relative clauses: which/that/where/whereby",
                    "Participial phrases: involving/mediated by/resulting in",
                    "Conditional chains: provided that/given that/assuming that",
                ]
            elif issue["type"] == "low_type_percentage":
                if "complex" in issue["description"]:
                    suggestion["grammar_tools"] = [
                        "Add subordinate clauses with: because/although/while/if/when",
                        "Use relative clauses: which/that/who",
                    ]
                elif "compound" in issue["description"]:
                    suggestion["grammar_tools"] = [
                        "Use coordinating conjunctions: and/but/or/yet/so",
                        "Use semicolons for related independent clauses",
                    ]
            elif issue["type"] == "too_much_passive":
                suggestion["grammar_tools"] = [
                    "Convert 'X was done by Y' to 'Y did X'",
                    "Use active subjects: 'The study shows' instead of 'It is shown that'",
                ]

            suggestions.append(suggestion)

        return suggestions


# Convenience functions / 便捷函数

def analyze_sentence_structure(sentence: str) -> SentenceAnalysis:
    """
    Analyze a single sentence structure
    分析单个句子结构
    """
    analyzer = SentenceStructureAnalyzer()
    return analyzer.analyze_sentence(sentence)


def analyze_paragraph_structure(sentences: List[str]) -> StructureDistribution:
    """
    Analyze paragraph structure distribution
    分析段落结构分布
    """
    analyzer = SentenceStructureAnalyzer()
    return analyzer.analyze_paragraph(sentences)


def get_structure_issues(sentences: List[str]) -> List[Dict]:
    """
    Get structure issues for a paragraph
    获取段落的结构问题
    """
    analyzer = SentenceStructureAnalyzer()
    distribution = analyzer.analyze_paragraph(sentences)
    return distribution.issues


def is_human_like_structure(sentences: List[str]) -> bool:
    """
    Check if paragraph has human-like structure distribution
    检查段落是否具有人类化的结构分布
    """
    analyzer = SentenceStructureAnalyzer()
    distribution = analyzer.analyze_paragraph(sentences)
    return distribution.is_human_like
