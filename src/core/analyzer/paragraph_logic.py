"""
Paragraph-level sentence logic analyzer
段落内句子逻辑关系分析器

Detects AI-like patterns within paragraphs:
1. Linear/homogeneous structure (AI pattern)
2. Subject repetition (AI pattern)
3. Sentence length uniformity (AI pattern)
4. First-person overuse (needs passive alternatives)
5. Explicit connector stacking (AI pattern)

Provides suggestions for human-like restructuring using:
- ANI structure (Assertion-Nuance-Implication)
- Subject diversity strategies
- Implicit connector techniques
- Rhythm variation patterns
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from collections import Counter
import re
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class LogicIssue:
    """
    Represents a detected logic issue within paragraph
    表示段落内检测到的逻辑问题
    """
    type: str  # linear_structure, subject_repetition, uniform_length, first_person_overuse, weak_logic
    description: str
    description_zh: str
    severity: str  # low, medium, high
    position: Tuple[int, int]  # sentence indices affected (start, end)
    suggestion: str
    suggestion_zh: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParagraphLogicResult:
    """
    Complete analysis result for paragraph logic
    段落逻辑的完整分析结果
    """
    issues: List[LogicIssue]
    subject_diversity_score: float  # 0.0-1.0, higher = more diverse
    length_variation_cv: float  # Coefficient of variation
    logic_structure: str  # linear, mixed, varied
    first_person_ratio: float  # Ratio of first-person subject sentences
    connector_density: float  # Ratio of sentences starting with connectors
    overall_risk: int  # 0-100, contribution to paragraph risk

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "issues": [
                {
                    "type": i.type,
                    "description": i.description,
                    "description_zh": i.description_zh,
                    "severity": i.severity,
                    "position": list(i.position),
                    "suggestion": i.suggestion,
                    "suggestion_zh": i.suggestion_zh,
                    "details": i.details
                }
                for i in self.issues
            ],
            "subject_diversity_score": self.subject_diversity_score,
            "length_variation_cv": self.length_variation_cv,
            "logic_structure": self.logic_structure,
            "first_person_ratio": self.first_person_ratio,
            "connector_density": self.connector_density,
            "overall_risk": self.overall_risk
        }


class ParagraphLogicAnalyzer:
    """
    Analyzes logical relationships between sentences within a paragraph
    分析段落内句子之间的逻辑关系

    Detects AI-like patterns:
    - Linear additive structure (A + B + C + D)
    - Subject repetition (The X... The X... The X...)
    - Uniform sentence lengths (all ~20 words)
    - First-person overuse (We... We... We...)
    - Explicit connector stacking (Furthermore... Moreover... Additionally...)
    - Parenthetical citation overuse (Statement + (Author, Year) pattern)
    """

    # Logic relationship types
    # 逻辑关系类型
    LOGIC_TYPES = {
        "progression": "递进关系",      # A → A' (deeper)
        "causation": "推导关系",         # A → B (because/therefore)
        "contrast": "转折关系",          # A ↔ B (but/however)
        "emphasis": "强调关系",          # A → A! (indeed/clearly)
        "elaboration": "展开关系",       # A → A+details
        "parallel": "并列关系",          # A | B | C (flat, AI-like)
    }

    # Citation patterns for detection (Author, Year) format
    # 引用模式检测 (Author, Year) 格式
    CITATION_PATTERNS = [
        # Standard APA style: (Smith, 2023), (Smith & Jones, 2023), (Smith et al., 2023)
        r'\(([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)?),?\s*(\d{4}[a-z]?)\)',
        # Multiple citations: (Smith, 2023; Jones, 2022)
        r'\((?:[A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)?,?\s*\d{4}[a-z]?;\s*)+[A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)?,?\s*\d{4}[a-z]?\)',
        # With page numbers: (Smith, 2023, p. 45)
        r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)?,?\s*\d{4}[a-z]?,\s*p+\.\s*\d+(?:-\d+)?\)',
    ]

    # Explicit connectors that indicate AI-like additive structure
    # 表示AI式叠加结构的显性连接词
    EXPLICIT_CONNECTORS = {
        "additive": [
            "furthermore", "moreover", "additionally", "also",
            "in addition", "besides", "similarly", "likewise"
        ],
        "causal": [
            "therefore", "thus", "hence", "consequently",
            "as a result", "accordingly"
        ],
        "contrastive": [
            "however", "nevertheless", "nonetheless", "yet",
            "on the other hand", "in contrast", "conversely"
        ],
        "sequential": [
            "firstly", "secondly", "thirdly", "finally",
            "subsequently", "then", "next"
        ]
    }

    # First-person subject patterns
    # 第一人称主语模式
    FIRST_PERSON_PATTERNS = [
        r"^I\s",
        r"^We\s",
        r"^Our\s",
    ]

    def __init__(self):
        """Initialize paragraph logic analyzer"""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self._first_person_regex = [
            re.compile(p, re.IGNORECASE) for p in self.FIRST_PERSON_PATTERNS
        ]

        # Flatten all connectors for detection
        # 展平所有连接词用于检测
        self._all_connectors = []
        for category, connectors in self.EXPLICIT_CONNECTORS.items():
            for conn in connectors:
                self._all_connectors.append((conn, category))

        # Compile citation patterns
        # 编译引用模式
        self._citation_regex = [
            re.compile(p) for p in self.CITATION_PATTERNS
        ]

    def analyze_paragraph(self, sentences: List[str]) -> ParagraphLogicResult:
        """
        Analyze logic issues in a paragraph
        分析段落中的逻辑问题

        Args:
            sentences: List of sentences in the paragraph

        Returns:
            ParagraphLogicResult with all detected issues and metrics
        """
        if not sentences or len(sentences) < 2:
            return ParagraphLogicResult(
                issues=[],
                subject_diversity_score=1.0,
                length_variation_cv=0.0,
                logic_structure="insufficient",
                first_person_ratio=0.0,
                connector_density=0.0,
                overall_risk=0
            )

        issues = []

        # 1. Check subject diversity
        # 检查主语多样性
        subject_issues, subject_score, subjects = self._check_subject_diversity(sentences)
        issues.extend(subject_issues)

        # 2. Check sentence length variation
        # 检查句子长度变化
        length_issues, cv = self._check_length_variation(sentences)
        issues.extend(length_issues)

        # 3. Check logic flow (detect flat/parallel structure)
        # 检查逻辑流（检测平铺/并列结构）
        logic_issues, connector_density = self._check_logic_flow(sentences)
        issues.extend(logic_issues)

        # 4. Check first-person overuse
        # 检查第一人称过度使用
        fp_issues, fp_ratio = self._check_first_person_overuse(sentences)
        issues.extend(fp_issues)

        # 5. Check parenthetical citation pattern (AI pattern)
        # 检查括号引用模式（AI模式）
        citation_issues, citations_found = self._check_citation_pattern(sentences)
        issues.extend(citation_issues)

        # 6. Determine overall logic structure
        # 确定整体逻辑结构
        logic_structure = self._determine_logic_structure(
            connector_density, cv, subject_score
        )

        # 7. Calculate overall risk contribution
        # 计算整体风险贡献
        overall_risk = self._calculate_overall_risk(issues)

        return ParagraphLogicResult(
            issues=issues,
            subject_diversity_score=subject_score,
            length_variation_cv=cv,
            logic_structure=logic_structure,
            first_person_ratio=fp_ratio,
            connector_density=connector_density,
            overall_risk=overall_risk
        )

    def _check_subject_diversity(
        self,
        sentences: List[str]
    ) -> Tuple[List[LogicIssue], float, List[str]]:
        """
        Check for subject repetition (AI pattern)
        检查主语重复（AI模式）

        Human pattern: Subject changes with argument flow
        人类模式：主语随论证流动而变化

        Returns:
            (issues, diversity_score, subjects_list)
        """
        issues = []
        subjects = []

        for sent in sentences:
            subject = self._extract_subject(sent)
            subjects.append(subject.lower() if subject else "")

        # Count subject occurrences
        # 统计主语出现次数
        valid_subjects = [s for s in subjects if s and len(s) > 1]
        if not valid_subjects:
            return ([], 1.0, subjects)

        subject_counts = Counter(valid_subjects)
        unique_ratio = len(subject_counts) / len(valid_subjects)

        # Check for repeated subjects
        # 检查重复主语
        for subject, count in subject_counts.items():
            ratio = count / len(sentences)
            if ratio > 0.4 and count >= 3:
                severity = "high" if ratio > 0.6 else "medium"

                # Find positions of this subject
                # 找到该主语的位置
                positions = [i for i, s in enumerate(subjects) if s == subject]

                issues.append(LogicIssue(
                    type="subject_repetition",
                    description=f"Subject '{subject}' appears in {count}/{len(sentences)} sentences ({ratio:.0%})",
                    description_zh=f"主语 '{subject}' 在 {count}/{len(sentences)} 句中出现 ({ratio:.0%})",
                    severity=severity,
                    position=(min(positions), max(positions)),
                    suggestion="Vary subjects using: 'This X...', 'Such Y...', 'The implication...', or transform to passive voice",
                    suggestion_zh="变换主语：使用 'This X...', 'Such Y...', 'The implication...' 或转换为被动语态",
                    details={"subject": subject, "count": count, "positions": positions}
                ))

        return (issues, unique_ratio, subjects)

    def _extract_subject(self, sentence: str) -> str:
        """
        Extract main subject from sentence (simplified NLP)
        从句子中提取主语（简化NLP）

        Uses heuristics:
        - First noun/noun phrase before main verb
        - Handles common determiners
        """
        words = sentence.strip().split()
        if not words:
            return ""

        # Skip sentence-initial connectors
        # 跳过句首连接词
        start_idx = 0
        first_word_lower = words[0].lower().rstrip(',')
        for conn, _ in self._all_connectors:
            conn_words = conn.split()
            if len(conn_words) == 1 and first_word_lower == conn:
                start_idx = 1
                break
            elif len(conn_words) > 1:
                phrase = ' '.join(w.lower().rstrip(',') for w in words[:len(conn_words)])
                if phrase == conn:
                    start_idx = len(conn_words)
                    break

        if start_idx >= len(words):
            return ""

        words = words[start_idx:]
        if not words:
            return ""

        # Common determiners to skip
        # 需要跳过的常见限定词
        determiners = {"the", "a", "an", "this", "that", "these", "those", "our", "their", "its"}

        # First word is determiner
        # 第一个词是限定词
        if words[0].lower() in determiners:
            if len(words) >= 2:
                # Return next word as subject
                # 返回下一个词作为主语
                return words[1].rstrip('.,;:')
            return ""

        # First word might be the subject
        # 第一个词可能是主语
        return words[0].rstrip('.,;:')

    def _check_length_variation(
        self,
        sentences: List[str]
    ) -> Tuple[List[LogicIssue], float]:
        """
        Check sentence length uniformity (AI pattern)
        检查句子长度均匀性（AI模式）

        AI pattern: All sentences ~same length
        Human pattern: Mix of short punchy + long explanatory

        Returns:
            (issues, coefficient_of_variation)
        """
        issues = []
        lengths = [len(s.split()) for s in sentences]

        if len(lengths) < 3:
            return ([], 0.5)  # Not enough data

        mean_len = statistics.mean(lengths)
        stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev / mean_len if mean_len > 0 else 0  # Coefficient of variation

        if cv < 0.20:  # Very uniform = strongly AI-like
            issues.append(LogicIssue(
                type="uniform_length",
                description=f"Sentence lengths too uniform (CV={cv:.2f}). Lengths: {lengths}",
                description_zh=f"句子长度过于均匀 (变异系数={cv:.2f}). 长度: {lengths}",
                severity="high",
                position=(0, len(sentences) - 1),
                suggestion="Create rhythm: KEEP long sentences (20-30 words) with nested clauses for complexity, ADD short sentences (8-12 words) for emphasis. DO NOT split tight-logic sentences.",
                suggestion_zh="创造节奏感：保留长句(20-30词)并使用嵌套从句增加复杂度，添加短句(8-12词)用于强调。禁止拆分逻辑紧密的句子。",
                details={"lengths": lengths, "mean": mean_len, "cv": cv}
            ))
        elif cv < 0.30:  # Somewhat uniform
            issues.append(LogicIssue(
                type="uniform_length",
                description=f"Sentence lengths moderately uniform (CV={cv:.2f}). Lengths: {lengths}",
                description_zh=f"句子长度较为均匀 (变异系数={cv:.2f}). 长度: {lengths}",
                severity="medium",
                position=(0, len(sentences) - 1),
                suggestion="Add variation by: 1) Adding nested clauses (which/where/whereby) to medium sentences for complexity, 2) Adding short emphatic sentences. AVOID splitting tight-logic sentences.",
                suggestion_zh="通过以下方式增加变化：1) 对中等句子添加嵌套从句(which/where/whereby)增加复杂度，2) 添加短句用于强调。避免拆分逻辑紧密的句子。",
                details={"lengths": lengths, "mean": mean_len, "cv": cv}
            ))

        return (issues, cv)

    def _check_logic_flow(
        self,
        sentences: List[str]
    ) -> Tuple[List[LogicIssue], float]:
        """
        Check for flat/parallel logic (AI pattern)
        检查平铺/并列逻辑（AI模式）

        AI: A + B + C + D (additive, no depth)
        Human: A → A' (deeper) → BUT B → THEREFORE C

        Returns:
            (issues, connector_density)
        """
        issues = []
        connectors_found = []

        for i, sent in enumerate(sentences):
            sent_lower = sent.lower().strip()

            # Check each connector
            # 检查每个连接词
            for conn, category in self._all_connectors:
                # Check if sentence starts with connector
                # 检查句子是否以连接词开头
                if sent_lower.startswith(conn + " ") or sent_lower.startswith(conn + ","):
                    connectors_found.append({
                        "index": i,
                        "connector": conn,
                        "category": category
                    })
                    break

        connector_density = len(connectors_found) / len(sentences) if sentences else 0

        # Check for additive connector stacking (AI pattern)
        # 检查叠加连接词堆叠（AI模式）
        additive_count = sum(1 for c in connectors_found if c["category"] == "additive")

        if additive_count >= 3:
            issues.append(LogicIssue(
                type="linear_structure",
                description=f"Linear additive structure: {additive_count} additive connectors (Furthermore/Moreover/Additionally)",
                description_zh=f"线性叠加结构：{additive_count} 个叠加连接词 (Furthermore/Moreover/Additionally)",
                severity="high",
                position=(0, len(sentences) - 1),
                suggestion="Replace with ANI structure: Assertion→Nuance→Implication. Use semantic echo instead of explicit connectors.",
                suggestion_zh="替换为ANI结构：断言→细微差别→深层含义。使用语义回声代替显性连接词。",
                details={"connectors": connectors_found, "additive_count": additive_count}
            ))
        elif len(connectors_found) >= 4:
            issues.append(LogicIssue(
                type="connector_overuse",
                description=f"Too many explicit connectors: {len(connectors_found)}/{len(sentences)} sentences start with connectors",
                description_zh=f"显性连接词过多：{len(connectors_found)}/{len(sentences)} 句以连接词开头",
                severity="medium",
                position=(0, len(sentences) - 1),
                suggestion="Use implicit connections: echo concepts from previous sentence, embed contrast in structure",
                suggestion_zh="使用隐性连接：回应上句概念，将转折嵌入句子结构",
                details={"connectors": connectors_found}
            ))

        return (issues, connector_density)

    def _check_first_person_overuse(
        self,
        sentences: List[str]
    ) -> Tuple[List[LogicIssue], float]:
        """
        Check first-person pronoun overuse
        检查第一人称代词过度使用

        Returns:
            (issues, first_person_ratio)
        """
        issues = []
        first_person_count = 0
        fp_positions = []

        for i, sent in enumerate(sentences):
            for pattern in self._first_person_regex:
                if pattern.match(sent):
                    first_person_count += 1
                    fp_positions.append(i)
                    break

        ratio = first_person_count / len(sentences) if sentences else 0

        if ratio > 0.5 and first_person_count >= 3:
            issues.append(LogicIssue(
                type="first_person_overuse",
                description=f"First-person subjects in {first_person_count}/{len(sentences)} sentences ({ratio:.0%})",
                description_zh=f"第一人称主语在 {first_person_count}/{len(sentences)} 句中出现 ({ratio:.0%})",
                severity="high" if ratio > 0.7 else "medium",
                position=(min(fp_positions), max(fp_positions)),
                suggestion="Convert some to passive/impersonal: 'We found...' → 'Evidence suggests...' or 'The data reveals...'",
                suggestion_zh="部分转为被动/非人称：'We found...' → 'Evidence suggests...' 或 'The data reveals...'",
                details={"count": first_person_count, "positions": fp_positions}
            ))
        elif ratio > 0.35 and first_person_count >= 2:
            issues.append(LogicIssue(
                type="first_person_overuse",
                description=f"Moderate first-person usage: {first_person_count}/{len(sentences)} sentences ({ratio:.0%})",
                description_zh=f"第一人称使用较多：{first_person_count}/{len(sentences)} 句 ({ratio:.0%})",
                severity="low",
                position=(min(fp_positions), max(fp_positions)),
                suggestion="Consider varying with passive constructions for balance",
                suggestion_zh="考虑使用被动结构增加变化",
                details={"count": first_person_count, "positions": fp_positions}
            ))

        return (issues, ratio)

    def _check_citation_pattern(
        self,
        sentences: List[str]
    ) -> Tuple[List[LogicIssue], List[Dict[str, Any]]]:
        """
        Check for parenthetical citation overuse (AI pattern)
        检查括号引用过度使用（AI模式）

        AI pattern: Sentence ends with (Author, Year)
        Human pattern: Mix of narrative and parenthetical citations

        Returns:
            (issues, citations_found_list)
        """
        issues = []
        citations_found = []
        parenthetical_count = 0

        for i, sent in enumerate(sentences):
            for pattern in self._citation_regex:
                matches = list(pattern.finditer(sent))
                for match in matches:
                    citation_text = match.group(0)
                    position = match.start()
                    is_at_end = match.end() >= len(sent.rstrip()) - 2  # Allow for punctuation

                    citations_found.append({
                        "original": citation_text,
                        "position": position,
                        "sentence_index": i,
                        "is_parenthetical": True,
                        "is_at_end": is_at_end
                    })

                    # Count citations at end of sentence (typical AI pattern)
                    # 统计句末引用（典型的AI模式）
                    if is_at_end:
                        parenthetical_count += 1

        # Determine if there's an issue
        # 判断是否存在问题
        total_citations = len(citations_found)
        if total_citations >= 3 and parenthetical_count / total_citations > 0.7:
            issues.append(LogicIssue(
                type="citation_pattern",
                description=f"Overuse of parenthetical citations at sentence end: {parenthetical_count}/{total_citations} citations ({parenthetical_count/total_citations:.0%})",
                description_zh=f"句末括号引用过多：{parenthetical_count}/{total_citations} 个引用 ({parenthetical_count/total_citations:.0%})",
                severity="medium" if parenthetical_count >= 4 else "low",
                position=(0, len(sentences) - 1),
                suggestion="Transform some to narrative citations: 'Smith (2023) argues...' or 'As Jones et al. (2022) demonstrated...'",
                suggestion_zh="将部分转换为叙述引用：'Smith (2023) argues...' 或 'As Jones et al. (2022) demonstrated...'",
                details={
                    "citations": citations_found,
                    "parenthetical_count": parenthetical_count,
                    "total_count": total_citations
                }
            ))
        elif total_citations >= 2 and parenthetical_count == total_citations:
            # All citations are parenthetical - potential AI pattern
            # 所有引用都是括号式的 - 可能是AI模式
            issues.append(LogicIssue(
                type="citation_pattern",
                description=f"All {total_citations} citations are parenthetical (potential AI pattern)",
                description_zh=f"所有 {total_citations} 个引用都是括号式的（可能是AI模式）",
                severity="low",
                position=(0, len(sentences) - 1),
                suggestion="Consider varying citation styles with narrative citations for natural flow",
                suggestion_zh="考虑混合使用叙述引用以增加自然感",
                details={
                    "citations": citations_found,
                    "parenthetical_count": parenthetical_count,
                    "total_count": total_citations
                }
            ))

        return (issues, citations_found)

    def get_citations_for_entanglement(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        Extract citations for the citation entanglement strategy
        提取用于引用句法纠缠策略的引用

        Args:
            sentences: List of sentences to analyze

        Returns:
            List of citation dictionaries suitable for the prompt
        """
        _, citations_found = self._check_citation_pattern(sentences)
        return citations_found

    def _determine_logic_structure(
        self,
        connector_density: float,
        cv: float,
        subject_score: float
    ) -> str:
        """
        Determine overall logic structure type
        确定整体逻辑结构类型
        """
        # Calculate AI-likeness score
        # 计算AI相似度分数
        ai_score = 0

        if connector_density > 0.4:
            ai_score += 2
        elif connector_density > 0.25:
            ai_score += 1

        if cv < 0.2:
            ai_score += 2
        elif cv < 0.3:
            ai_score += 1

        if subject_score < 0.4:
            ai_score += 2
        elif subject_score < 0.6:
            ai_score += 1

        if ai_score >= 4:
            return "linear"  # Strong AI pattern
        elif ai_score >= 2:
            return "mixed"   # Some AI patterns
        else:
            return "varied"  # Human-like variation

    def _calculate_overall_risk(self, issues: List[LogicIssue]) -> int:
        """
        Calculate overall risk contribution from logic issues
        计算逻辑问题的整体风险贡献
        """
        risk = 0

        for issue in issues:
            if issue.severity == "high":
                risk += 15
            elif issue.severity == "medium":
                risk += 8
            else:
                risk += 3

        return min(50, risk)  # Cap at 50 to leave room for other factors


def analyze_paragraph_sentences(
    sentences: List[str]
) -> Dict[str, Any]:
    """
    Convenience function to analyze paragraph logic
    分析段落逻辑的便捷函数

    Args:
        sentences: List of sentences in the paragraph

    Returns:
        Dictionary with analysis results
    """
    analyzer = ParagraphLogicAnalyzer()
    result = analyzer.analyze_paragraph(sentences)
    return result.to_dict()
