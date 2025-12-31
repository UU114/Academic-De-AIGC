"""
Risk scoring module - calculates comprehensive AIGC risk scores
风险评分模块 - 计算综合AIGC风险分数

Improved scoring system based on academic writing analysis:
- Tiered fingerprint detection (Level 1: Dead giveaways, Level 2: AI habits)
- zlib compression ratio as PPL alternative
- Human feature deduction mechanism
- Fixed structure patterns (no penalty for academic hedging)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import logging
import math
import zlib
import re

from src.config import get_settings, get_risk_weights
from src.core.analyzer.fingerprint import FingerprintMatch, FingerprintDetector

logger = logging.getLogger(__name__)
settings = get_settings()
risk_weights = get_risk_weights()


# Tiered fingerprint words for improved detection
# 分级指纹词用于改进检测

# Level 1: Dead giveaways - extremely rare in human writing (+40 points each)
# 一级：确凿证据 - 人类写作中极少见（每个+40分）
LEVEL_1_FINGERPRINTS: Set[str] = {
    "delve", "delves", "delving",
    "tapestry", "tapestries",
    "testament to",
    "in the realm of", "realm of",
    "landscape of",
    "multifaceted",
    "inextricably",
    "a plethora of", "plethora",
    "myriad of",
    "elucidate", "elucidates", "elucidating",
    "henceforth",
    "aforementioned",
    # Additional Level 1 patterns (very AI-specific)
    # 额外一级模式（非常AI特有）
    "cascading mechanisms",
    "interfacial",
    "valorization",
    "poses a dual threat",
    "systemic understanding",
    "remains fragmented",
    "critically synthesizes",
    "concurrent escalation",
}

# Level 2: AI habitual phrases - common but not definitive (+15 points each)
# 二级：AI惯用语 - 常见但非决定性（每个+15分）
# CLEANED: Removed domain-specific terms (remediation, circular economy, etc.)
# 已清理：移除学科特定术语
LEVEL_2_FINGERPRINTS: Set[str] = {
    # Academic clichés (not domain-specific)
    # 学术套话（非学科特定）
    "crucial", "pivotal", "paramount",
    "it is crucial to", "it is important to note",
    "underscores the importance", "underscore", "underscores",
    "plays a pivotal role", "plays a crucial role",
    "foster a culture", "foster", "fosters",
    "comprehensive", "holistic approach", "holistic",
    "facilitate", "facilitates", "facilitating",
    "leverage", "leveraging",
    "robust", "seamless",
    "noteworthy", "groundbreaking",
    # Structural connectors (AI overuse)
    # 结构连接词（AI过度使用）
    "furthermore", "moreover", "additionally",
    "in conclusion", "to summarize", "in summary",
}


# ============================================================================
# CAASS v2.0: Tone-Adaptive Weight Matrix
# CAASS v2.0: 语气自适应权重矩阵
# ============================================================================
# Tone Level 0-2: Hardcore Academic (allows complex vocabulary)
# Tone Level 3-4: Standard Academic (default thesis level)
# Tone Level 5: Simple/Accessible (penalizes all fancy words)
# 语气等级 0-2: 硬核学术（允许复杂词汇）
# 语气等级 3-4: 标准学术（默认论文级别）
# 语气等级 5: 简单易懂（惩罚所有花哨词汇）

TONE_WEIGHT_MATRIX = {
    # Type A: Dead Giveaways (AI-specific, always high penalty)
    # A类: 确凿证据（AI特有，始终高惩罚）
    "type_a": {
        0: 40, 1: 40, 2: 40,  # Academic: still penalized (AI marker, not academic)
        3: 40, 4: 45,         # Standard: normal penalty
        5: 50                 # Simple: even more penalty
    },
    # Type B: Academic Clichés (tone-dependent)
    # B类: 学术套话（取决于语气等级）
    "type_b": {
        0: 5,  1: 8,  2: 10,  # Academic: almost exempt (professors use these)
        3: 15, 4: 18,         # Standard: moderate penalty
        5: 25                 # Simple: strongly penalized
    },
    # Type C: Structural/Connector words (tone-dependent)
    # C类: 结构/连接词（取决于语气等级）
    "type_c": {
        0: 10, 1: 12, 2: 15,  # Academic: light penalty (normal in papers)
        3: 18, 4: 22,         # Standard: moderate penalty
        5: 30                 # Simple: strongly penalized
    }
}


def get_tone_adjusted_weight(word_type: str, tone_level: int) -> int:
    """
    Get the weight for a word type based on tone level (CAASS v2.0)
    根据语气等级获取词类权重（CAASS v2.0）

    Args:
        word_type: "type_a", "type_b", or "type_c"
        tone_level: 0-5 (0=most academic, 5=most simple)

    Returns:
        Weight value for scoring
    """
    # Clamp tone_level to 0-5 range
    # 将语气等级限制在 0-5 范围内
    tone_level = max(0, min(5, tone_level))

    matrix = TONE_WEIGHT_MATRIX.get(word_type, TONE_WEIGHT_MATRIX["type_b"])
    return matrix.get(tone_level, matrix.get(3, 15))  # Default to level 3


def classify_fingerprint_type(word: str) -> str:
    """
    Classify a fingerprint word into Type A/B/C
    将指纹词分类为 A/B/C 类型

    Type A: Dead giveaways (delve, tapestry, etc.)
    Type B: Academic clichés (crucial, utilize, etc.)
    Type C: Structural connectors (furthermore, moreover, etc.)
    """
    word_lower = word.lower()

    # Type A: Level 1 fingerprints are always dead giveaways
    # A类: 一级指纹词始终是确凿证据
    if word_lower in LEVEL_1_FINGERPRINTS or any(fp in word_lower for fp in LEVEL_1_FINGERPRINTS):
        return "type_a"

    # Type C: Connectors and structural words
    # C类: 连接词和结构词
    connectors = {"furthermore", "moreover", "additionally", "consequently",
                  "therefore", "thus", "hence", "subsequently", "accordingly",
                  "nevertheless", "nonetheless", "in conclusion", "to summarize"}
    if word_lower in connectors or any(c in word_lower for c in connectors):
        return "type_c"

    # Type B: Everything else (academic clichés)
    # B类: 其他所有（学术套话）
    return "type_b"


# ============================================================================
# CAASS v2.0 Phase 2: Context-Aware Baseline Scoring
# CAASS v2.0 第二阶段: 上下文感知基准评分
# ============================================================================

def calculate_text_ppl(text: str) -> float:
    """
    Calculate perplexity proxy using zlib compression ratio
    使用zlib压缩比计算困惑度代理

    Returns:
        PPL-like score (lower = more AI-like, higher = more human-like)
    """
    if not text or len(text) < 20:
        return 50.0  # Neutral for very short text

    try:
        text_bytes = text.encode('utf-8')
        compressed = zlib.compress(text_bytes, level=9)
        compression_ratio = len(compressed) / len(text_bytes)

        # Map compression ratio to PPL-like score
        # Lower compression ratio = more unique content = more human-like
        # 较低压缩比 = 更独特内容 = 更像人类
        if compression_ratio < 0.35:
            ppl = 15.0 + (compression_ratio * 30)
        elif compression_ratio < 0.50:
            ppl = 25.0 + (compression_ratio * 40)
        elif compression_ratio < 0.65:
            ppl = 45.0 + (compression_ratio * 30)
        else:
            ppl = 60.0 + (compression_ratio * 40)

        return max(5.0, min(100.0, ppl))

    except Exception:
        return 50.0


def calculate_context_baseline(
    paragraph_text: str,
    paragraph_ppl: Optional[float] = None
) -> int:
    """
    Calculate context baseline score based on paragraph-level PPL
    根据段落级PPL计算上下文基准分

    If the paragraph has very low PPL (strong AI signal), sentences within it
    get a baseline score added. This helps identify AI-generated paragraphs
    even when individual sentences seem acceptable.
    如果段落PPL非常低（强AI信号），其中的句子会获得基准分加成。
    这有助于识别AI生成的段落，即使单个句子看起来可接受。

    Args:
        paragraph_text: The full paragraph text
        paragraph_ppl: Pre-calculated PPL (optional)

    Returns:
        Context baseline score (0-25)
    """
    if paragraph_ppl is None:
        paragraph_ppl = calculate_text_ppl(paragraph_text)

    # Very low PPL = high AI probability = add baseline
    # 非常低的PPL = 高AI概率 = 添加基准分
    if paragraph_ppl < 20:
        return 25  # Strong AI signal
    elif paragraph_ppl < 30:
        return 15  # Moderate AI signal
    elif paragraph_ppl < 40:
        return 8   # Weak AI signal
    else:
        return 0   # Likely human


@dataclass
class ParagraphContext:
    """
    Context information for a paragraph
    段落的上下文信息
    """
    text: str
    ppl: float
    baseline: int
    sentence_count: int

    @classmethod
    def from_sentences(cls, sentences: List[str]) -> "ParagraphContext":
        """Create context from a list of sentences"""
        text = " ".join(sentences)
        ppl = calculate_text_ppl(text)
        baseline = calculate_context_baseline(text, ppl)
        return cls(
            text=text,
            ppl=ppl,
            baseline=baseline,
            sentence_count=len(sentences)
        )


@dataclass
class Issue:
    """
    Represents a detected issue
    表示检测到的问题
    """
    type: str  # fingerprint, ppl, structure, connector
    description: str
    description_zh: str
    severity: str  # low, medium, high
    position: Optional[int] = None
    word: Optional[str] = None


@dataclass
class SentenceAnalysisResult:
    """
    Complete analysis result for a sentence
    句子的完整分析结果
    """
    risk_score: int  # 0-100
    risk_level: str  # low, medium, high

    # Component scores
    # 组件分数
    ppl: float
    ppl_score: int
    ppl_risk: str

    fingerprint_density: float
    fingerprint_score: int

    burstiness_score: int
    structure_score: int

    # Issues
    # 问题
    issues: List[Issue] = field(default_factory=list)

    # Detector-specific views
    # 检测器特定视角
    turnitin_score: int = 0
    turnitin_issues: List[str] = field(default_factory=list)
    turnitin_issues_zh: List[str] = field(default_factory=list)

    gptzero_score: int = 0
    gptzero_issues: List[str] = field(default_factory=list)
    gptzero_issues_zh: List[str] = field(default_factory=list)


class RiskScorer:
    """
    Risk scoring engine
    风险评分引擎

    Calculates comprehensive AIGC risk scores based on:
    - Perplexity (PPL)
    - Fingerprint word density
    - Burstiness (sentence length variation)
    - Structure patterns
    """

    def __init__(self):
        """Initialize risk scorer"""
        self.fingerprint_detector = FingerprintDetector()
        self.weights = {
            "perplexity": risk_weights.perplexity,
            "fingerprint": risk_weights.fingerprint,
            "burstiness": risk_weights.burstiness,
            "structure": risk_weights.structure
        }

    def analyze(
        self,
        text: str,
        fingerprints: Optional[List[FingerprintMatch]] = None,
        context_sentences: Optional[List[str]] = None,
        include_turnitin: bool = True,
        include_gptzero: bool = True,
        tone_level: int = 4,
        whitelist: Optional[Set[str]] = None,
        context_baseline: int = 0,
        paragraph_context: Optional[ParagraphContext] = None
    ) -> SentenceAnalysisResult:
        """
        Perform complete risk analysis on text (CAASS v2.0 Phase 2)
        对文本进行完整的风险分析（CAASS v2.0 第二阶段）

        Args:
            text: Text to analyze
            fingerprints: Pre-computed fingerprint matches
            context_sentences: Surrounding sentences for burstiness calculation
            include_turnitin: Include Turnitin perspective
            include_gptzero: Include GPTZero perspective
            tone_level: User's target tone (0-5, 0=academic, 5=simple)
            whitelist: Domain-specific terms to exempt from scoring
            context_baseline: Pre-calculated paragraph context baseline (0-25)
            paragraph_context: Full paragraph context for baseline calculation

        Returns:
            SentenceAnalysisResult with all scores and issues
        """
        # Phase 2: Calculate context baseline from paragraph if provided
        # 第二阶段：如果提供了段落上下文，计算上下文基准分
        if paragraph_context is not None:
            context_baseline = paragraph_context.baseline
        issues = []
        whitelist = whitelist or set()

        # Calculate PPL score (used for context baseline in future)
        # 计算PPL分数（未来用于上下文基准）
        ppl = self._calculate_ppl(text)
        ppl_score, ppl_risk = self._score_ppl(ppl)

        if ppl_risk in ["medium", "high"]:
            issues.append(Issue(
                type="ppl",
                description=f"Low perplexity ({ppl:.1f}) indicates predictable AI-like text",
                description_zh=f"低困惑度 ({ppl:.1f}) 表明文本可预测性高，类似AI生成",
                severity=ppl_risk
            ))

        # Detect fingerprints
        # 检测指纹词
        if fingerprints is None:
            fingerprints = self.fingerprint_detector.detect(text)

        # Filter out whitelisted terms
        # 过滤白名单术语
        if whitelist:
            fingerprints = [fp for fp in fingerprints if fp.word.lower() not in whitelist]

        fingerprint_density = self.fingerprint_detector.calculate_density(text, fingerprints)

        # CAASS v2.0: Calculate fingerprint score using absolute weights + tone adaptation
        # CAASS v2.0: 使用绝对权重 + 语气适配计算指纹分数
        fingerprint_score = self._score_fingerprint_caass(fingerprints, tone_level)

        # Add fingerprint issues with type classification
        # 添加带类型分类的指纹问题
        for fp in fingerprints:
            fp_type = classify_fingerprint_type(fp.word)
            weight = get_tone_adjusted_weight(fp_type, tone_level)
            if weight >= 15:  # Only report significant issues
                type_label = {"type_a": "Dead Giveaway", "type_b": "AI Cliché", "type_c": "Connector"}
                type_label_zh = {"type_a": "确凿证据", "type_b": "AI套话", "type_c": "连接词"}
                issues.append(Issue(
                    type="fingerprint",
                    description=f"{type_label.get(fp_type, 'AI')} word: '{fp.word}' (+{weight})",
                    description_zh=f"{type_label_zh.get(fp_type, 'AI')}词: '{fp.word}' (+{weight}分)",
                    severity="high" if fp_type == "type_a" else "medium",
                    position=fp.position,
                    word=fp.word
                ))

        # Calculate burstiness score
        # 计算突发性分数
        burstiness_score = self._score_burstiness(text, context_sentences)

        # CAASS v2.0: Calculate structure score with tone adaptation
        # CAASS v2.0: 使用语气适配计算结构分数
        structure_score = self._score_structure_caass(text, tone_level)

        # Calculate human feature deduction
        # 计算人类特征减分
        human_deduction = self._calculate_human_deduction(text)

        # CAASS v2.0 Phase 2: Scoring formula with context baseline
        # CAASS v2.0 第二阶段: 带上下文基准的评分公式
        # Score = Context_baseline + FP_absolute + Structure_patterns - Human_bonus
        # 评分 = 上下文基准分 + 指纹词绝对分 + 结构模式分 - 人类特征减分
        raw_score = context_baseline + fingerprint_score + structure_score

        # Apply human deduction (but don't go below 0)
        # 应用人类减分（但不低于0）
        total_score = max(0, min(100, raw_score - human_deduction))

        # Log scoring details for debugging
        # 记录评分详情用于调试
        logger.debug(
            f"CAASS v2.0 Phase 2: Ctx={context_baseline}, FP={fingerprint_score}, "
            f"Struct={structure_score}, Human=-{human_deduction}, "
            f"Total={total_score}, Tone={tone_level}"
        )
        # DEBUG: Print scoring details to diagnose Track B 0-score issue
        # 调试：打印评分详情以诊断轨道B 0分问题
        # Use logger instead of print for cross-platform compatibility (Windows GBK / Linux UTF-8)
        # 使用logger而非print以实现跨平台兼容（Windows GBK / Linux UTF-8）
        logger.info(f"[DEBUG Scorer] Text len={len(text)}, Ctx={context_baseline}, FP={fingerprint_score}, Struct={structure_score}, Human=-{human_deduction}, Total={total_score}")

        # Determine risk level (adjusted thresholds for better sensitivity)
        # 确定风险等级（调整阈值以提高敏感度）
        # High: ≥50, Medium: ≥25, Low: ≥10, Safe: <10
        if total_score >= 50:
            risk_level = "high"
        elif total_score >= 25:
            risk_level = "medium"
        elif total_score >= 10:
            risk_level = "low"
        else:
            risk_level = "safe"  # No risk - likely human-written

        # Generate detector-specific views
        # 生成检测器特定视角
        turnitin_score, turnitin_issues, turnitin_issues_zh = (0, [], [])
        gptzero_score, gptzero_issues, gptzero_issues_zh = (0, [], [])

        if include_turnitin:
            turnitin_score, turnitin_issues, turnitin_issues_zh = self._turnitin_view(
                text, fingerprints, structure_score
            )

        if include_gptzero:
            gptzero_score, gptzero_issues, gptzero_issues_zh = self._gptzero_view(
                text, ppl, fingerprints, burstiness_score
            )

        return SentenceAnalysisResult(
            risk_score=total_score,
            risk_level=risk_level,
            ppl=ppl,
            ppl_score=ppl_score,
            ppl_risk=ppl_risk,
            fingerprint_density=fingerprint_density,
            fingerprint_score=fingerprint_score,
            burstiness_score=burstiness_score,
            structure_score=structure_score,
            issues=issues,
            turnitin_score=turnitin_score,
            turnitin_issues=turnitin_issues,
            turnitin_issues_zh=turnitin_issues_zh,
            gptzero_score=gptzero_score,
            gptzero_issues=gptzero_issues,
            gptzero_issues_zh=gptzero_issues_zh
        )

    def _calculate_ppl(self, text: str) -> float:
        """
        Calculate perplexity proxy using zlib compression ratio
        使用zlib压缩比计算困惑度代理

        Principle: AI-generated text has lower information density and more
        repetitive patterns, resulting in higher compression ratio.
        原理：AI生成的文本信息密度低，重复模式多，压缩比高。

        Note: This is a proxy for PPL. Production version should use GPT-2/LLaMA.
        注意：这是PPL的代理。生产版本应使用GPT-2/LLaMA模型。
        """
        if not text or len(text) < 10:
            return 100.0

        try:
            # Calculate zlib compression ratio
            # 计算zlib压缩比
            text_bytes = text.encode('utf-8')
            compressed = zlib.compress(text_bytes, level=9)
            compression_ratio = len(compressed) / len(text_bytes)

            # Lower compression ratio = more unique content = more human-like
            # AI text compresses better (ratio 0.3-0.5), human text less (ratio 0.5-0.8)
            # 较低压缩比 = 更独特内容 = 更像人类
            # AI文本压缩更好(比例0.3-0.5)，人类文本较差(比例0.5-0.8)

            # Convert compression ratio to PPL-like score (0-100)
            # 将压缩比转换为类PPL分数(0-100)
            # High PPL = human, Low PPL = AI
            if compression_ratio < 0.35:
                # Very high compression = very AI-like
                # 非常高的压缩率 = 非常像AI
                ppl = 15.0 + (compression_ratio * 30)
            elif compression_ratio < 0.50:
                # Medium-high compression = likely AI
                # 中高压缩率 = 可能是AI
                ppl = 25.0 + (compression_ratio * 40)
            elif compression_ratio < 0.65:
                # Medium compression = uncertain
                # 中等压缩率 = 不确定
                ppl = 45.0 + (compression_ratio * 30)
            else:
                # Low compression = likely human
                # 低压缩率 = 可能是人类
                ppl = 60.0 + (compression_ratio * 40)

            # Also factor in unique word ratio as secondary signal
            # 同时将唯一词比例作为次要信号
            words = text.split()
            if words:
                unique_ratio = len(set(w.lower() for w in words)) / len(words)
                # Adjust PPL based on vocabulary diversity
                # 根据词汇多样性调整PPL
                ppl = ppl * (0.8 + unique_ratio * 0.4)

            return max(5.0, min(100.0, ppl))

        except Exception as e:
            logger.warning(f"zlib compression failed, using fallback: {e}")
            # Fallback to simple method
            # 回退到简单方法
            words = text.split()
            if not words:
                return 100.0
            unique_ratio = len(set(w.lower() for w in words)) / len(words)
            return max(5.0, min(100.0, 30.0 + unique_ratio * 70))

    def _score_ppl(self, ppl: float) -> tuple:
        """
        Convert PPL to risk score and level
        将PPL转换为风险分数和等级
        """
        if ppl < settings.ppl_threshold_high:
            # Low PPL = high risk
            # 低PPL = 高风险
            score = int(90 - (ppl / settings.ppl_threshold_high) * 30)
            return (score, "high")
        elif ppl < settings.ppl_threshold_medium:
            # Medium PPL = medium risk
            # 中等PPL = 中等风险
            score = int(60 - ((ppl - settings.ppl_threshold_high) /
                             (settings.ppl_threshold_medium - settings.ppl_threshold_high)) * 30)
            return (score, "medium")
        else:
            # High PPL = low risk
            # 高PPL = 低风险
            score = int(30 - min(30, (ppl - settings.ppl_threshold_medium) / 2))
            return (max(0, score), "low")

    def _score_fingerprint(
        self,
        density: float,
        fingerprints: List[FingerprintMatch]
    ) -> int:
        """
        Calculate fingerprint risk score (legacy method)
        计算指纹风险分数（旧方法）
        """
        # Base score from density
        # 基于密度的基础分数
        density_score = min(100, int(density * 500))

        # Bonus for high-risk fingerprints
        # 高风险指纹的额外分数
        high_risk_count = sum(1 for fp in fingerprints if fp.risk_weight >= 0.8)
        high_risk_bonus = min(30, high_risk_count * 10)

        return min(100, density_score + high_risk_bonus)

    def _score_fingerprint_caass(
        self,
        fingerprints: List[FingerprintMatch],
        tone_level: int = 4
    ) -> int:
        """
        CAASS v2.0: Calculate fingerprint score using absolute weights
        CAASS v2.0: 使用绝对权重计算指纹分数

        Unlike density-based scoring, this uses fixed per-word penalties
        adjusted by tone level. This solves the short-sentence bias problem.
        与基于密度的评分不同，这使用按语气等级调整的固定每词惩罚。
        这解决了短句偏差问题。
        """
        total_score = 0

        for fp in fingerprints:
            # Classify the fingerprint word
            # 分类指纹词
            fp_type = classify_fingerprint_type(fp.word)

            # Get tone-adjusted weight
            # 获取语气调整后的权重
            weight = get_tone_adjusted_weight(fp_type, tone_level)
            total_score += weight

        # Cap at 80 to leave room for structure patterns
        # 上限80，为结构模式留出空间
        return min(80, total_score)

    def _score_burstiness(
        self,
        text: str,
        context_sentences: Optional[List[str]] = None
    ) -> int:
        """
        Calculate burstiness score (sentence length variation)
        计算突发性分数（句子长度变化）

        Low burstiness (uniform length) = high risk
        低突发性（长度均匀）= 高风险
        """
        if not context_sentences:
            # Without context, use word-level variation within sentence
            # 没有上下文时，使用句子内的词级变化
            words = text.split()
            if len(words) < 3:
                return 30  # Too short to measure

            # Calculate word length variation
            # 计算词长变化
            word_lengths = [len(w) for w in words]
            mean_len = sum(word_lengths) / len(word_lengths)
            variance = sum((l - mean_len) ** 2 for l in word_lengths) / len(word_lengths)
            std_dev = math.sqrt(variance)

            # Low variation = higher risk
            # 低变化 = 更高风险
            burstiness = std_dev / mean_len if mean_len > 0 else 0

            if burstiness < 0.3:
                return 70
            elif burstiness < 0.5:
                return 50
            else:
                return 30
        else:
            # With context, calculate sentence length variation
            # 有上下文时，计算句子长度变化
            all_sentences = context_sentences + [text]
            lengths = [len(s.split()) for s in all_sentences]

            mean_len = sum(lengths) / len(lengths)
            variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)

            burstiness = std_dev / mean_len if mean_len > 0 else 0

            if burstiness < 0.2:
                return 80  # Very uniform = high risk
            elif burstiness < 0.4:
                return 50
            else:
                return 20  # Good variation = low risk

    def _score_structure(self, text: str) -> int:
        """
        Calculate structure pattern score (improved version)
        计算结构模式分数（改进版）

        Changes from original:
        - Removed hedging word penalty (suggests, indicates) - these are academic norms
        - Removed quotation mark penalty - citations are human features
        - Added tiered fingerprint scoring
        - Added "not only...but also" double emphasis detection
        - Added sentence length variance penalty
        改进内容：
        - 移除犹豫词惩罚 - 这是学术写作规范
        - 移除引号惩罚 - 引用是人类特征
        - 添加分级指纹评分
        - 添加"not only...but also"双重强调检测
        - 添加句子长度方差惩罚
        """
        score = 0
        text_lower = text.lower().strip()
        words = text.split()
        word_count = len(words)

        # === TIERED FINGERPRINT DETECTION ===
        # === 分级指纹检测 ===

        # Level 1: Dead giveaways (+40 each, max 120)
        # 一级：确凿证据（每个+40，最高120）
        level_1_hits = 0
        for fp in LEVEL_1_FINGERPRINTS:
            if fp in text_lower:
                level_1_hits += 1
        score += min(120, level_1_hits * 40)

        # Level 2: AI habitual phrases (+15 each, max 60)
        # 二级：AI惯用语（每个+15，最高60）
        level_2_hits = 0
        for fp in LEVEL_2_FINGERPRINTS:
            if fp in text_lower:
                level_2_hits += 1
        score += min(60, level_2_hits * 15)

        # === PATTERN DETECTION ===
        # === 模式检测 ===

        # Double emphasis pattern: "not only... but also" (+20)
        # 双重强调模式（+20）
        if "not only" in text_lower and "but also" in text_lower:
            score += 20

        # Listing/enumeration with no logical lead-in (+25)
        # 无逻辑引导的列举（+25）
        if any(marker in text_lower for marker in ["firstly", "secondly", "thirdly", "first,", "second,", "third,"]):
            score += 25

        # Extreme sentence length (too uniform is suspicious)
        # 极端句子长度（过于均匀可疑）
        if word_count > 40:
            score += 25  # Very long single sentence = AI tendency
        elif word_count > 30:
            score += 15

        # === CONNECTOR OVERUSE (at sentence start) ===
        # === 连接词过度使用（句首）===

        connector_starts = [
            "furthermore", "moreover", "additionally", "consequently",
            "therefore", "thus", "notably", "importantly", "hence",
            "subsequently", "accordingly"
        ]
        for conn in connector_starts:
            if text_lower.startswith(conn):
                score += 20
                break

        # === VAGUE ACADEMIC PADDING ===
        # === 模糊学术填充 ===

        padding_phrases = [
            "complex dynamics", "intricate interplay", "evolving landscape",
            "holistic approach", "comprehensive framework", "nuanced understanding",
            "multifaceted nature", "serves as a testament",
            # Additional AI academic padding
            # 额外AI学术填充
            "dual threat", "poses a threat", "poses challenges",
            "systemic understanding", "systemic approach",
            "cascading effects", "cascading mechanisms",
            "interfacial", "valorization",
            "circular pathway", "circular economy",
            "life-cycle trade-offs", "trade-offs within",
            "remains fragmented", "remains unclear", "remains limited",
            "critically synthesizes", "critically examines", "critically analyzes",
            "concurrent escalation", "escalation of",
            "soil salinization", "ecosystem stability",
            "food security", "solid waste generation",
        ]
        padding_count = sum(1 for p in padding_phrases if p in text_lower)
        score += padding_count * 15

        # === AI ACADEMIC SENTENCE PATTERNS ===
        # === AI学术句式模式 ===

        # "The [adjective] [noun] of X and Y" pattern
        # AI喜欢的"The [形容词] [名词] of X and Y"模式
        if re.search(r'\bthe\s+\w+\s+(escalation|generation|threat|stability|security)\s+of\b', text_lower):
            score += 15

        # "offers/provides a [adjective] pathway/approach/framework"
        # "offers/provides a [形容词] pathway/approach/framework"
        if re.search(r'\b(offers?|provides?)\s+a\s+\w+\s+(pathway|approach|framework|solution)\b', text_lower):
            score += 15

        # "within [noun] systems" pattern
        # "within [名词] systems"模式
        if re.search(r'\bwithin\s+\w+\s+systems?\b', text_lower):
            score += 10

        # Very long academic sentences (>25 words) with multiple commas
        # 非常长的学术句子（>25词）且有多个逗号
        if word_count > 25 and text.count(',') >= 3:
            score += 20

        # === "IT IS" PASSIVE CONSTRUCTIONS ===
        # === "IT IS" 被动结构 ===
        # Only penalize very AI-specific patterns, not academic hedging
        # 只惩罚非常AI特有的模式，而非学术缓和语
        ai_passive_patterns = [
            "it is important to note that",
            "it is worth noting that",
            "it should be noted that",
            "it is evident that",
            "it is crucial to"
        ]
        for pattern in ai_passive_patterns:
            if pattern in text_lower:
                score += 20
                break

        return min(100, score)

    def _score_structure_caass(self, text: str, tone_level: int = 4) -> int:
        """
        CAASS v2.0: Calculate structure pattern score with tone adaptation
        CAASS v2.0: 使用语气适配计算结构模式分数

        This method focuses on structural patterns only (not fingerprint words,
        which are handled by _score_fingerprint_caass). This eliminates the
        double-counting issue in the original implementation.
        此方法仅关注结构模式（不包括指纹词，由 _score_fingerprint_caass 处理）。
        这消除了原实现中的重复计算问题。
        """
        score = 0
        text_lower = text.lower().strip()
        words = text.split()
        word_count = len(words)

        # Get tone-adjusted weights for structural patterns
        # 获取结构模式的语气调整权重
        type_c_weight = get_tone_adjusted_weight("type_c", tone_level)
        base_pattern_weight = max(10, type_c_weight // 2)  # Half of type_c for patterns

        # === PATTERN DETECTION (not fingerprint words) ===
        # === 模式检测（非指纹词）===

        # Double emphasis pattern: "not only... but also"
        # 双重强调模式
        if "not only" in text_lower and "but also" in text_lower:
            score += base_pattern_weight

        # Enumeration markers at sentence start
        # 句首列举标记
        if any(text_lower.startswith(m) for m in ["firstly", "secondly", "thirdly"]):
            score += base_pattern_weight

        # Very long single sentence (AI tendency)
        # 非常长的单句（AI倾向）
        if word_count > 40:
            score += 20
        elif word_count > 30:
            score += 10

        # Connector at sentence start (use type_c weight)
        # 句首连接词（使用C类权重）
        connector_starts = ["furthermore", "moreover", "additionally", "consequently",
                          "therefore", "hence", "subsequently", "accordingly"]
        if any(text_lower.startswith(c) for c in connector_starts):
            score += type_c_weight

        # AI passive constructions
        # AI被动结构
        ai_passives = ["it is important to note", "it is worth noting",
                       "it should be noted", "it is evident that", "it is crucial to"]
        if any(p in text_lower for p in ai_passives):
            score += base_pattern_weight

        # Long sentence with many commas (rigid structure)
        # 多逗号长句（僵化结构）
        if word_count > 25 and text.count(',') >= 3:
            score += 15

        # "offers/provides a [adjective] pathway/approach/framework"
        # AI典型句式
        if re.search(r'\b(offers?|provides?)\s+a\s+\w+\s+(pathway|approach|framework|solution)\b', text_lower):
            score += base_pattern_weight

        # Cap structure score to leave room for fingerprint score
        # 结构分数上限，为指纹分数留出空间
        return min(40, score)

    def _calculate_human_deduction(self, text: str) -> int:
        """
        Calculate human feature deduction (negative score)
        计算人类特征减分（负分）

        Human writing markers that should reduce AI suspicion:
        - First person with emotion
        - Informal parenthetical comments
        - Specific non-integer numbers
        - Colloquial expressions
        - Self-corrections or hesitation
        人类写作标记，应降低AI嫌疑：
        - 带情感的第一人称
        - 非正式括号内补充
        - 具体的非整数数字
        - 口语化表达
        - 自我纠正或犹豫
        """
        deduction = 0
        text_lower = text.lower()

        # First person with emotion (-20)
        # 带情感的第一人称（-20）
        emotional_first_person = [
            "i was surprised", "i found it", "i think", "i believe",
            "in my experience", "i noticed", "i realized", "i wondered",
            "we were surprised", "we found that", "interestingly,"
        ]
        if any(phrase in text_lower for phrase in emotional_first_person):
            deduction += 20

        # Informal parenthetical comments (-15)
        # 非正式括号补充（-15）
        if re.search(r'\([^)]*(?:which|but|though|actually|strictly speaking|to be fair)[^)]*\)', text_lower):
            deduction += 15
        elif '(' in text and ')' in text:
            # Any parenthetical that isn't a citation could be human
            # 任何非引用的括号可能是人类写作
            paren_content = re.findall(r'\(([^)]+)\)', text)
            for content in paren_content:
                # Skip if it looks like a citation
                # 跳过看起来像引用的内容
                if not re.match(r'^[\d,\s]+$', content) and not re.match(r'^[A-Z][a-z]+,?\s*\d{4}', content):
                    if len(content) > 10:  # Substantive comment
                        deduction += 10
                        break

        # Specific non-integer numbers (-10)
        # 具体非整数数字（-10）
        decimal_numbers = re.findall(r'\d+\.\d+', text)
        if decimal_numbers:
            # Check for specific values like "14.2%" or "p < 0.05"
            # 检查具体值如 "14.2%" 或 "p < 0.05"
            deduction += 10

        # Colloquial hedging (different from AI hedging) (-10)
        # 口语化缓和（不同于AI缓和）（-10）
        human_hedges = [
            "kind of", "sort of", "a bit", "pretty much",
            "to be honest", "honestly", "frankly", "actually"
        ]
        if any(hedge in text_lower for hedge in human_hedges):
            deduction += 10

        # Very short sentence mixed in context (sign of burstiness) (-5)
        # 上下文中混入的极短句子（突发性标志）（-5）
        if len(text.split()) < 8 and text.strip().endswith('.'):
            deduction += 5

        # Rhetorical question (-10)
        # 反问句（-10）
        if text.strip().endswith('?') and any(q in text_lower for q in ["why", "how", "what if", "isn't it"]):
            deduction += 10

        return min(50, deduction)  # Cap deduction at 50

    def _turnitin_view(
        self,
        text: str,
        fingerprints: List[FingerprintMatch],
        structure_score: int
    ) -> tuple:
        """
        Generate Turnitin-style analysis view
        生成Turnitin风格的分析视角
        """
        issues = []
        issues_zh = []
        score = 0

        # Turnitin focuses on: overall style, structure, citation patterns
        # Turnitin关注：整体风格、结构、引用模式

        # Check fingerprint density
        # 检查指纹密度
        if len(fingerprints) >= 3:
            issues.append("Multiple AI-characteristic phrases detected")
            issues_zh.append("检测到多个AI特征短语")
            score += 30

        # Check structure
        # 检查结构
        if structure_score >= 50:
            issues.append("Formulaic sentence structure")
            issues_zh.append("公式化的句子结构")
            score += 25

        # Check sentence completeness
        # 检查句子完整性
        if text.strip().endswith('.') and text[0].isupper():
            if len(text.split()) > 25:
                issues.append("Complex but grammatically perfect structure")
                issues_zh.append("复杂但语法完美的结构")
                score += 15

        return (min(100, score), issues, issues_zh)

    def _gptzero_view(
        self,
        text: str,
        ppl: float,
        fingerprints: List[FingerprintMatch],
        burstiness_score: int
    ) -> tuple:
        """
        Generate GPTZero-style analysis view
        生成GPTZero风格的分析视角
        """
        issues = []
        issues_zh = []
        score = 0

        # GPTZero focuses on: PPL, burstiness, word choice
        # GPTZero关注：PPL、突发性、词汇选择

        # PPL assessment
        # PPL评估
        if ppl < 20:
            issues.append(f"Very low perplexity ({ppl:.1f})")
            issues_zh.append(f"困惑度非常低 ({ppl:.1f})")
            score += 40
        elif ppl < 40:
            issues.append(f"Low perplexity ({ppl:.1f})")
            issues_zh.append(f"困惑度较低 ({ppl:.1f})")
            score += 25

        # Burstiness assessment
        # 突发性评估
        if burstiness_score >= 70:
            issues.append("Low burstiness - uniform sentence patterns")
            issues_zh.append("低突发性 - 句子模式均匀")
            score += 25

        # Word choice
        # 词汇选择
        high_risk_fps = [fp for fp in fingerprints if fp.risk_weight >= 0.8]
        if high_risk_fps:
            issues.append(f"AI-preferred vocabulary: {', '.join(fp.word for fp in high_risk_fps[:3])}")
            issues_zh.append(f"AI偏好词汇: {', '.join(fp.word for fp in high_risk_fps[:3])}")
            score += 20

        return (min(100, score), issues, issues_zh)

    def calculate_document_score(
        self,
        sentence_results: List[SentenceAnalysisResult]
    ) -> Dict[str, Any]:
        """
        Calculate overall document risk score
        计算文档整体风险分数
        """
        if not sentence_results:
            return {"score": 0, "level": "low"}

        # Weighted average based on sentence length/importance
        # 基于句子长度/重要性的加权平均
        total_score = sum(r.risk_score for r in sentence_results)
        avg_score = total_score / len(sentence_results)

        # Count risk levels
        # 统计风险等级
        high_count = sum(1 for r in sentence_results if r.risk_level == "high")
        medium_count = sum(1 for r in sentence_results if r.risk_level == "medium")

        # Adjust score based on high-risk concentration
        # 基于高风险集中度调整分数
        high_ratio = high_count / len(sentence_results)
        adjusted_score = avg_score + (high_ratio * 20)

        if adjusted_score >= 61:
            level = "high"
        elif adjusted_score >= 31:
            level = "medium"
        else:
            level = "low"

        return {
            "score": min(100, int(adjusted_score)),
            "level": level,
            "sentence_count": len(sentence_results),
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": len(sentence_results) - high_count - medium_count
        }
