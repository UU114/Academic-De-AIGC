"""
Structure Predictability Scoring Model
结构预测性评分模型

Core insight: "AI's key feature is not linearity, but high structural predictability"
核心洞察："AI的核心特征不是线性，而是结构高度可预测"

This module quantifies how predictable a document's structure is.
Higher score = more AI-like (predictable)
Lower score = more human-like (non-monotonic, asymmetric, weak closure)

Five dimensions of predictability:
1. Progression Predictability - monotonic vs non-monotonic flow
2. Function Uniformity - even vs asymmetric paragraph functions
3. Closure Strength - strong summary vs weak/open ending
4. Length Regularity - uniform vs varied paragraph lengths
5. Connector Explicitness - explicit connectors vs lexical echo
"""

import re
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class PredictabilityScore:
    """
    Structure Predictability Score Result
    结构预测性评分结果
    """
    # Total score (0-100, higher = more predictable/AI-like)
    # 总分（0-100，越高越可预测/像AI）
    total_score: int

    # Sub-scores (0-100 each)
    # 子分数（每项0-100）
    progression_predictability: int    # 推进可预测性
    function_uniformity: int           # 功能均匀性
    closure_strength: int              # 闭合强度
    length_regularity: int             # 长度规律性
    connector_explicitness: int        # 连接词显性度

    # Detected patterns
    # 检测到的模式
    progression_type: str  # "monotonic" | "non_monotonic" | "mixed"
    function_distribution: str  # "uniform" | "asymmetric" | "balanced"
    closure_type: str  # "strong" | "moderate" | "weak" | "open"

    # Lexical echo score (0-1, higher = better implicit connection)
    # 词汇回声分数（0-1，越高隐性连接越好）
    lexical_echo_score: float

    # Risk level based on total score
    # 基于总分的风险等级
    risk_level: str  # "low" | "medium" | "high"

    # Detailed breakdown for each dimension
    # 每个维度的详细分解
    details: Dict[str, Dict] = field(default_factory=dict)

    # Recommendations
    # 建议
    recommendations: List[str] = field(default_factory=list)
    recommendations_zh: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_score": self.total_score,
            "progression_predictability": self.progression_predictability,
            "function_uniformity": self.function_uniformity,
            "closure_strength": self.closure_strength,
            "length_regularity": self.length_regularity,
            "connector_explicitness": self.connector_explicitness,
            "progression_type": self.progression_type,
            "function_distribution": self.function_distribution,
            "closure_type": self.closure_type,
            "lexical_echo_score": self.lexical_echo_score,
            "risk_level": self.risk_level,
            "details": self.details,
            "recommendations": self.recommendations,
            "recommendations_zh": self.recommendations_zh,
        }


class StructurePredictabilityAnalyzer:
    """
    Analyzes structural predictability of documents
    分析文档的结构预测性

    Core principle: Break "structural predictability" not "clarity"
    核心原则：破坏"结构可预测性"而非"清晰度"
    """

    # Weight for each dimension in total score
    # 各维度在总分中的权重
    DIMENSION_WEIGHTS = {
        "progression": 0.25,      # 推进可预测性
        "function": 0.20,         # 功能均匀性
        "closure": 0.20,          # 闭合强度
        "length": 0.15,           # 长度规律性
        "connector": 0.20,        # 连接词显性度
    }

    # Monotonic progression indicators (AI pattern)
    # 单调推进指示词（AI模式）
    MONOTONIC_MARKERS = {
        "sequential": [
            "first", "second", "third", "fourth", "fifth",
            "firstly", "secondly", "thirdly",
            "next", "then", "finally", "lastly",
            "to begin with", "in the first place",
        ],
        "additive": [
            "furthermore", "moreover", "additionally", "also",
            "in addition", "besides", "similarly", "likewise",
        ],
        "causal": [
            "therefore", "thus", "hence", "consequently",
            "as a result", "accordingly", "so",
        ],
    }

    # Non-monotonic progression indicators (Human pattern)
    # 非单调推进指示词（人类模式）
    NON_MONOTONIC_MARKERS = {
        "return": [
            "as noted earlier", "as mentioned", "returning to",
            "revisiting", "recall that", "as we saw",
        ],
        "conditional": [
            "if", "when", "unless", "provided that",
            "in cases where", "under conditions",
        ],
        "contrastive": [
            "however", "but", "yet", "nevertheless",
            "on the other hand", "conversely", "in contrast",
        ],
        "concessive": [
            "although", "though", "despite", "even though",
            "while", "whereas", "notwithstanding",
        ],
    }

    # Strong closure patterns (AI pattern)
    # 强闭合模式（AI模式）
    STRONG_CLOSURE_PATTERNS = [
        r"^in (conclusion|summary|sum)",
        r"^to (conclude|summarize|sum up)",
        r"^(overall|ultimately|finally),?\s",
        r"this (paper|study|research|analysis) (has )?(demonstrated|shown|proved|established)",
        r"(clearly|evidently|definitively) (demonstrates?|shows?|proves?|establishes?)",
        r"the (findings|results|evidence) (clearly )?(demonstrate|show|prove|confirm)",
    ]

    # Weak/open closure patterns (Human pattern)
    # 弱/开放闭合模式（人类模式）
    WEAK_CLOSURE_PATTERNS = [
        r"(remains|remain) (unclear|uncertain|open|unresolved)",
        r"further (research|investigation|study|work) (is|may be|will be) (needed|required)",
        r"(questions|issues|challenges) remain",
        r"what .* unclear",
        r"the implications (extend|go) beyond",
        r"whether .* remains to be (seen|determined)",
    ]

    # Paragraph function keywords
    # 段落功能关键词
    FUNCTION_KEYWORDS = {
        "introduction": ["introduce", "overview", "background", "context", "purpose", "aim"],
        "methodology": ["method", "approach", "procedure", "design", "sample", "data collection"],
        "results": ["result", "finding", "data show", "analysis reveal", "table", "figure"],
        "discussion": ["discuss", "interpret", "explain", "implication", "suggest"],
        "conclusion": ["conclude", "summary", "in conclusion", "finally", "overall"],
        "evidence": ["evidence", "support", "demonstrate", "example", "case"],
        "analysis": ["analyze", "examine", "explore", "investigate"],
        "transition": ["turning to", "moving on", "having discussed", "with this in mind"],
    }

    def __init__(self):
        """Initialize the analyzer"""
        # Compile patterns
        self._strong_closure_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.STRONG_CLOSURE_PATTERNS
        ]
        self._weak_closure_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.WEAK_CLOSURE_PATTERNS
        ]

    def analyze(self, paragraphs: List[str]) -> PredictabilityScore:
        """
        Analyze structure predictability of document
        分析文档的结构预测性

        Args:
            paragraphs: List of paragraph texts

        Returns:
            PredictabilityScore with all metrics
        """
        if len(paragraphs) < 3:
            return self._get_insufficient_data_result()

        details = {}

        # 1. Progression Predictability
        # 1. 推进可预测性
        prog_score, prog_type, prog_details = self._analyze_progression(paragraphs)
        details["progression"] = prog_details

        # 2. Function Uniformity
        # 2. 功能均匀性
        func_score, func_dist, func_details = self._analyze_function_distribution(paragraphs)
        details["function"] = func_details

        # 3. Closure Strength
        # 3. 闭合强度
        closure_score, closure_type, closure_details = self._analyze_closure(paragraphs)
        details["closure"] = closure_details

        # 4. Length Regularity
        # 4. 长度规律性
        length_score, length_details = self._analyze_length_regularity(paragraphs)
        details["length"] = length_details

        # 5. Connector Explicitness
        # 5. 连接词显性度
        conn_score, conn_details = self._analyze_connector_explicitness(paragraphs)
        details["connector"] = conn_details

        # 6. Lexical Echo Score (bonus metric)
        # 6. 词汇回声分数（附加指标）
        echo_score, echo_details = self._calculate_lexical_echo(paragraphs)
        details["lexical_echo"] = echo_details

        # Calculate weighted total
        # 计算加权总分
        total = int(
            prog_score * self.DIMENSION_WEIGHTS["progression"] +
            func_score * self.DIMENSION_WEIGHTS["function"] +
            closure_score * self.DIMENSION_WEIGHTS["closure"] +
            length_score * self.DIMENSION_WEIGHTS["length"] +
            conn_score * self.DIMENSION_WEIGHTS["connector"]
        )

        # Determine risk level
        # 确定风险等级
        if total >= 60:
            risk_level = "high"
        elif total >= 35:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate recommendations
        # 生成建议
        recommendations, recommendations_zh = self._generate_recommendations(
            prog_score, func_score, closure_score, length_score, conn_score, echo_score
        )

        return PredictabilityScore(
            total_score=total,
            progression_predictability=prog_score,
            function_uniformity=func_score,
            closure_strength=closure_score,
            length_regularity=length_score,
            connector_explicitness=conn_score,
            progression_type=prog_type,
            function_distribution=func_dist,
            closure_type=closure_type,
            lexical_echo_score=echo_score,
            risk_level=risk_level,
            details=details,
            recommendations=recommendations,
            recommendations_zh=recommendations_zh,
        )

    def _analyze_progression(
        self, paragraphs: List[str]
    ) -> Tuple[int, str, Dict]:
        """
        Analyze progression predictability
        分析推进可预测性

        Monotonic (AI): sequential, additive, one-directional
        Non-monotonic (Human): returns, conditionals, reversals
        """
        monotonic_count = 0
        non_monotonic_count = 0
        markers_found = {"monotonic": [], "non_monotonic": []}

        for i, para in enumerate(paragraphs):
            para_lower = para.lower()

            # Check monotonic markers
            for category, markers in self.MONOTONIC_MARKERS.items():
                for marker in markers:
                    if para_lower.startswith(marker) or f" {marker}" in para_lower[:100]:
                        monotonic_count += 1
                        markers_found["monotonic"].append({
                            "paragraph": i,
                            "marker": marker,
                            "category": category
                        })
                        break

            # Check non-monotonic markers
            for category, markers in self.NON_MONOTONIC_MARKERS.items():
                for marker in markers:
                    if marker in para_lower:
                        non_monotonic_count += 1
                        markers_found["non_monotonic"].append({
                            "paragraph": i,
                            "marker": marker,
                            "category": category
                        })
                        break

        # Calculate score (higher = more monotonic = more AI-like)
        total_markers = monotonic_count + non_monotonic_count
        if total_markers == 0:
            score = 50  # Neutral
            prog_type = "mixed"
        else:
            monotonic_ratio = monotonic_count / total_markers
            score = int(monotonic_ratio * 100)

            if monotonic_ratio > 0.7:
                prog_type = "monotonic"
            elif monotonic_ratio < 0.3:
                prog_type = "non_monotonic"
            else:
                prog_type = "mixed"

        # Boost score if sequential markers found (First, Second, Third...)
        sequential_found = len([
            m for m in markers_found["monotonic"]
            if m["category"] == "sequential"
        ])
        if sequential_found >= 3:
            score = min(100, score + 20)

        return (score, prog_type, {
            "monotonic_count": monotonic_count,
            "non_monotonic_count": non_monotonic_count,
            "markers": markers_found,
            "sequential_markers": sequential_found,
        })

    def _analyze_function_distribution(
        self, paragraphs: List[str]
    ) -> Tuple[int, str, Dict]:
        """
        Analyze paragraph function distribution
        分析段落功能分布

        Uniform (AI): each paragraph has similar function weight
        Asymmetric (Human): some paragraphs get deep treatment, others brief
        """
        functions = []
        function_lengths = {}

        for i, para in enumerate(paragraphs):
            func = self._detect_function(para)
            functions.append(func)

            if func not in function_lengths:
                function_lengths[func] = []
            function_lengths[func].append(len(para.split()))

        # Calculate function distribution uniformity
        function_counts = Counter(functions)
        unique_functions = len(function_counts)
        total_paras = len(paragraphs)

        # Check for asymmetry: one function dominates
        max_function = function_counts.most_common(1)[0]
        max_ratio = max_function[1] / total_paras

        # Calculate length variance within each function
        length_variances = []
        for func, lengths in function_lengths.items():
            if len(lengths) > 1:
                avg = sum(lengths) / len(lengths)
                variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
                cv = (variance ** 0.5) / avg if avg > 0 else 0
                length_variances.append(cv)

        avg_length_cv = sum(length_variances) / len(length_variances) if length_variances else 0

        # Score: higher = more uniform = more AI-like
        # Low unique functions + high max_ratio = uniform
        if unique_functions <= 2 and max_ratio > 0.6:
            score = 80
            dist_type = "uniform"
        elif unique_functions >= 4 and max_ratio < 0.4:
            score = 30
            dist_type = "asymmetric"
        else:
            score = 50
            dist_type = "balanced"

        # Adjust for length variance (high CV = more asymmetric = lower score)
        if avg_length_cv > 0.4:
            score = max(0, score - 15)
            if dist_type == "uniform":
                dist_type = "balanced"

        return (score, dist_type, {
            "functions": functions,
            "function_counts": dict(function_counts),
            "unique_functions": unique_functions,
            "dominant_function": max_function,
            "length_cv": avg_length_cv,
        })

    def _detect_function(self, paragraph: str) -> str:
        """Detect paragraph function type"""
        para_lower = paragraph.lower()

        for func_type, keywords in self.FUNCTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in para_lower:
                    return func_type

        return "body"

    def _analyze_closure(
        self, paragraphs: List[str]
    ) -> Tuple[int, str, Dict]:
        """
        Analyze closure pattern
        分析闭合模式

        Strong (AI): definitive conclusions, "In conclusion..."
        Weak (Human): open questions, unresolved tensions
        """
        if not paragraphs:
            return (50, "moderate", {})

        last_para = paragraphs[-1]
        second_last = paragraphs[-2] if len(paragraphs) > 1 else ""

        # Check for strong closure patterns
        strong_matches = []
        for pattern in self._strong_closure_patterns:
            if pattern.search(last_para) or pattern.search(second_last):
                strong_matches.append(pattern.pattern)

        # Check for weak/open closure patterns
        weak_matches = []
        for pattern in self._weak_closure_patterns:
            if pattern.search(last_para) or pattern.search(second_last):
                weak_matches.append(pattern.pattern)

        # Calculate score
        if strong_matches and not weak_matches:
            score = 90
            closure_type = "strong"
        elif weak_matches and not strong_matches:
            score = 20
            closure_type = "open"
        elif strong_matches and weak_matches:
            score = 50
            closure_type = "moderate"
        else:
            # No clear pattern - check for summary-like language
            if any(word in last_para.lower() for word in ["thus", "therefore", "shows", "demonstrates"]):
                score = 60
                closure_type = "moderate"
            else:
                score = 40
                closure_type = "weak"

        return (score, closure_type, {
            "strong_patterns": strong_matches,
            "weak_patterns": weak_matches,
            "last_paragraph_preview": last_para[:200] + "..." if len(last_para) > 200 else last_para,
        })

    def _analyze_length_regularity(
        self, paragraphs: List[str]
    ) -> Tuple[int, Dict]:
        """
        Analyze paragraph length regularity
        分析段落长度规律性

        High regularity (AI): all paragraphs similar length
        Low regularity (Human): varied lengths
        """
        lengths = [len(p.split()) for p in paragraphs]

        if len(lengths) < 2:
            return (50, {"lengths": lengths, "cv": 0})

        mean_len = statistics.mean(lengths)
        stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = stdev / mean_len if mean_len > 0 else 0

        # Score: higher CV = less regular = lower score
        if cv < 0.2:
            score = 90  # Very uniform = AI-like
        elif cv < 0.3:
            score = 70
        elif cv < 0.4:
            score = 50
        elif cv < 0.5:
            score = 30
        else:
            score = 15  # Highly varied = human-like

        return (score, {
            "lengths": lengths,
            "mean": mean_len,
            "stdev": stdev,
            "cv": cv,
            "min": min(lengths),
            "max": max(lengths),
        })

    def _analyze_connector_explicitness(
        self, paragraphs: List[str]
    ) -> Tuple[int, Dict]:
        """
        Analyze connector explicitness
        分析连接词显性度

        High explicitness (AI): heavy use of Furthermore, Moreover, etc.
        Low explicitness (Human): semantic/lexical connections
        """
        explicit_connectors = [
            "furthermore", "moreover", "additionally", "consequently",
            "therefore", "thus", "hence", "accordingly",
            "in addition", "as a result", "for this reason",
            "first", "second", "third", "finally",
            "on the other hand", "however", "nevertheless",
        ]

        connector_count = 0
        connectors_found = []

        for i, para in enumerate(paragraphs):
            para_lower = para.lower()
            for conn in explicit_connectors:
                if para_lower.startswith(conn) or f". {conn}" in para_lower:
                    connector_count += 1
                    connectors_found.append({"paragraph": i, "connector": conn})

        # Calculate density
        density = connector_count / len(paragraphs) if paragraphs else 0

        # Score: higher density = more explicit = more AI-like
        if density > 0.6:
            score = 90
        elif density > 0.4:
            score = 70
        elif density > 0.25:
            score = 50
        elif density > 0.1:
            score = 30
        else:
            score = 15

        return (score, {
            "connector_count": connector_count,
            "density": density,
            "connectors_found": connectors_found,
        })

    def _calculate_lexical_echo(
        self, paragraphs: List[str]
    ) -> Tuple[float, Dict]:
        """
        Calculate lexical echo score between adjacent paragraphs
        计算相邻段落之间的词汇回声分数

        High score = good implicit connection (human-like)
        """
        if len(paragraphs) < 2:
            return (0.5, {})

        echo_scores = []
        echo_details = []

        for i in range(1, len(paragraphs)):
            prev_para = paragraphs[i - 1]
            curr_para = paragraphs[i]

            # Extract key content words from end of prev paragraph
            prev_words = self._extract_key_words(prev_para[-300:])  # Last 300 chars
            # Extract key content words from start of current paragraph
            curr_words = self._extract_key_words(curr_para[:200])  # First 200 chars

            # Calculate overlap (lexical echo)
            if prev_words and curr_words:
                overlap = prev_words & curr_words
                echo_ratio = len(overlap) / min(len(prev_words), len(curr_words))
            else:
                overlap = set()
                echo_ratio = 0

            echo_scores.append(echo_ratio)
            echo_details.append({
                "from_para": i - 1,
                "to_para": i,
                "echoed_words": list(overlap)[:5],
                "score": echo_ratio,
            })

        avg_echo = sum(echo_scores) / len(echo_scores) if echo_scores else 0

        return (avg_echo, {
            "average_echo": avg_echo,
            "transitions": echo_details,
        })

    def _extract_key_words(self, text: str) -> Set[str]:
        """Extract key content words (nouns, verbs) excluding stopwords"""
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "this", "that", "these", "those", "it", "its", "of", "to", "in",
            "for", "on", "with", "at", "by", "from", "as", "into", "through",
            "and", "or", "but", "if", "because", "while", "although", "though",
            "which", "who", "whom", "whose", "what", "where", "when", "why", "how",
        }

        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        return {w for w in words if w not in stopwords}

    def _generate_recommendations(
        self,
        prog_score: int,
        func_score: int,
        closure_score: int,
        length_score: int,
        conn_score: int,
        echo_score: float
    ) -> Tuple[List[str], List[str]]:
        """Generate recommendations based on scores"""
        recs = []
        recs_zh = []

        if prog_score > 60:
            recs.append("Break monotonic progression: add returns to earlier points, conditionals, or local reversals")
            recs_zh.append("打破单调推进：添加回扣、条件触发或局部反转")

        if func_score > 60:
            recs.append("Create asymmetric layout: deep-dive one argument, briefly scan others")
            recs_zh.append("创建非对称布局：深入展开一个论点，简要扫过其他")

        if closure_score > 60:
            recs.append("Weaken closure: end with open question or unresolved tension instead of definitive summary")
            recs_zh.append("弱化闭合：以开放问题或未解决的张力结尾，而非明确总结")

        if length_score > 60:
            recs.append("Vary paragraph lengths: mix short (50-80 words) with long (150-200 words)")
            recs_zh.append("变化段落长度：混合短段落(50-80词)和长段落(150-200词)")

        if conn_score > 60:
            recs.append("Replace explicit connectors with lexical echo: reference concepts from previous paragraph")
            recs_zh.append("用词汇回声替代显性连接词：引用上段概念")

        if echo_score < 0.3:
            recs.append("Increase lexical echo: naturally use key terms from paragraph end in next paragraph opening")
            recs_zh.append("增加词汇回声：在下段开头自然使用上段结尾的关键词")

        if not recs:
            recs.append("Structure appears human-like. Minor adjustments may still help.")
            recs_zh.append("结构已较为人类化。可进行微调。")

        return (recs, recs_zh)

    def _get_insufficient_data_result(self) -> PredictabilityScore:
        """Return default result for insufficient data"""
        return PredictabilityScore(
            total_score=0,
            progression_predictability=0,
            function_uniformity=0,
            closure_strength=0,
            length_regularity=0,
            connector_explicitness=0,
            progression_type="unknown",
            function_distribution="unknown",
            closure_type="unknown",
            lexical_echo_score=0.0,
            risk_level="low",
            details={"error": "Insufficient paragraphs for analysis (need at least 3)"},
            recommendations=["Document too short for structure analysis"],
            recommendations_zh=["文档太短，无法进行结构分析"],
        )


def analyze_structure_predictability(paragraphs: List[str]) -> Dict:
    """
    Convenience function to analyze structure predictability
    分析结构预测性的便捷函数

    Args:
        paragraphs: List of paragraph texts

    Returns:
        Dictionary with predictability analysis
    """
    analyzer = StructurePredictabilityAnalyzer()
    result = analyzer.analyze(paragraphs)
    return result.to_dict()
