"""
Rule-based suggestion track (Track B)
基于规则的建议轨道（轨道B）

Integrates with Step 1.0 Term Locking to protect locked terms during rewriting.
集成步骤1.0词汇锁定，在改写过程中保护锁定的术语。
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from src.config import ColloquialismConfig

logger = logging.getLogger(__name__)


def get_locked_terms_from_session(session_id: Optional[str]) -> List[str]:
    """
    Get locked terms from session for rule-based processing
    从会话中获取锁定术语以用于规则处理

    Args:
        session_id: Session identifier (optional)

    Returns:
        List of locked terms, or empty list if none
    """
    if not session_id:
        return []

    try:
        # Import here to avoid circular imports
        from src.api.routes.analysis.term_lock import get_session_locked_terms
        return get_session_locked_terms(session_id)
    except ImportError:
        logger.warning("Could not import term_lock module")
        return []
    except Exception as e:
        logger.warning(f"Could not get locked terms: {e}")
        return []


@dataclass
class Change:
    """Represents a single change made"""
    original: str
    replacement: str
    reason: str
    reason_zh: str


@dataclass
class RuleSuggestionResult:
    """Result from rule-based suggestion generation"""
    rewritten: str
    changes: List[Change] = field(default_factory=list)
    predicted_risk: int = 50
    semantic_similarity: float = 0.95
    explanation: str = ""
    explanation_zh: str = ""


class RuleTrack:
    """
    Rule-based humanization suggestion engine (Track B)
    基于规则的人源化建议引擎（轨道B）

    Uses deterministic rules for:
    - Synonym replacement (fingerprint words)
    - Syntax restructuring
    - BERT MLM context-aware replacement (future)
    """

    # Fingerprint word replacements with level-appropriate alternatives
    # 指纹词替换及等级适当的替代词
    # Level 1 (Dead giveaways) and Level 2 (AI tendency) words
    # 一级（确凿证据）和二级（AI倾向）词汇
    FINGERPRINT_REPLACEMENTS: Dict[str, Dict[str, List[str]]] = {
        # === LEVEL 1: Dead Giveaways (一级：确凿证据) ===
        "delve": {
            "academic": ["explore", "examine", "investigate"],
            "moderate": ["explore", "look at", "study"],
            "casual": ["look at", "check out", "dig into"]
        },
        "delves": {
            "academic": ["explores", "examines", "investigates"],
            "moderate": ["explores", "looks at", "studies"],
            "casual": ["looks at", "checks out", "digs into"]
        },
        "delving": {
            "academic": ["exploring", "examining", "investigating"],
            "moderate": ["exploring", "looking at", "studying"],
            "casual": ["looking at", "checking out", "digging into"]
        },
        "tapestry": {
            "academic": ["collection", "array", "combination"],
            "moderate": ["mix", "collection", "range"],
            "casual": ["mix", "combination", "bunch"]
        },
        "multifaceted": {
            "academic": ["complex", "diverse", "varied"],
            "moderate": ["complex", "varied", "diverse"],
            "casual": ["complex", "mixed", "varied"]
        },
        "inextricably": {
            "academic": ["closely", "deeply", "fundamentally"],
            "moderate": ["closely", "deeply", "tightly"],
            "casual": ["closely", "tightly", "strongly"]
        },
        "plethora": {
            "academic": ["abundance", "multitude", "numerous"],
            "moderate": ["many", "lots of", "numerous"],
            "casual": ["lots of", "many", "a bunch of"]
        },
        "myriad": {
            "academic": ["numerous", "countless", "manifold"],
            "moderate": ["many", "numerous", "various"],
            "casual": ["many", "lots of", "tons of"]
        },
        "elucidate": {
            "academic": ["clarify", "explain", "illuminate"],
            "moderate": ["explain", "clarify", "make clear"],
            "casual": ["explain", "make clear", "show"]
        },
        "elucidates": {
            "academic": ["clarifies", "explains", "illuminates"],
            "moderate": ["explains", "clarifies", "shows"],
            "casual": ["explains", "makes clear", "shows"]
        },
        "henceforth": {
            "academic": ["from now on", "thereafter", "subsequently"],
            "moderate": ["from now on", "going forward", "after this"],
            "casual": ["from now on", "after this", "now"]
        },
        "aforementioned": {
            "academic": ["previously mentioned", "above-mentioned", "foregoing"],
            "moderate": ["mentioned", "these", "the above"],
            "casual": ["these", "this", "what I mentioned"]
        },
        # === LEVEL 2: AI Tendency (二级：AI倾向) ===
        "crucial": {
            "academic": ["essential", "critical", "vital"],
            "moderate": ["important", "key", "essential"],
            "casual": ["important", "key", "big"]
        },
        "pivotal": {
            "academic": ["critical", "essential", "central"],
            "moderate": ["key", "important", "central"],
            "casual": ["key", "important", "main"]
        },
        "paramount": {
            "academic": ["essential", "critical", "primary"],
            "moderate": ["important", "key", "main"],
            "casual": ["most important", "key", "main"]
        },
        "underscore": {
            "academic": ["emphasize", "highlight", "stress"],
            "moderate": ["highlight", "show", "point out"],
            "casual": ["show", "point out", "highlight"]
        },
        "underscores": {
            "academic": ["emphasizes", "highlights", "stresses"],
            "moderate": ["highlights", "shows", "points out"],
            "casual": ["shows", "points out", "highlights"]
        },
        "foster": {
            "academic": ["promote", "encourage", "cultivate"],
            "moderate": ["encourage", "support", "help"],
            "casual": ["help", "support", "build"]
        },
        "fosters": {
            "academic": ["promotes", "encourages", "cultivates"],
            "moderate": ["encourages", "supports", "helps"],
            "casual": ["helps", "supports", "builds"]
        },
        "furthermore": {
            "academic": ["additionally", "also", "in addition"],
            "moderate": ["also", "and", "plus"],
            "casual": ["also", "and", "plus"]
        },
        "moreover": {
            "academic": ["additionally", "also", "in addition"],
            "moderate": ["also", "and", "plus"],
            "casual": ["also", "and", "besides"]
        },
        "additionally": {
            "academic": ["also", "further", "in addition"],
            "moderate": ["also", "and", "plus"],
            "casual": ["also", "and", "plus"]
        },
        "consequently": {
            "academic": ["therefore", "as a result", "thus"],
            "moderate": ["so", "as a result", "therefore"],
            "casual": ["so", "because of this", "then"]
        },
        "comprehensive": {
            "academic": ["thorough", "extensive", "complete"],
            "moderate": ["full", "complete", "thorough"],
            "casual": ["full", "complete", "detailed"]
        },
        "holistic": {
            "academic": ["integrated", "complete", "overall"],
            "moderate": ["complete", "full", "overall"],
            "casual": ["complete", "full", "whole"]
        },
        "facilitate": {
            "academic": ["enable", "support", "assist"],
            "moderate": ["help", "enable", "support"],
            "casual": ["help", "make easier", "allow"]
        },
        "facilitates": {
            "academic": ["enables", "supports", "assists"],
            "moderate": ["helps", "enables", "supports"],
            "casual": ["helps", "makes easier", "allows"]
        },
        "leverage": {
            "academic": ["employ", "use", "harness"],
            "moderate": ["use", "apply", "take advantage of"],
            "casual": ["use", "take advantage of"]
        },
        "leveraging": {
            "academic": ["employing", "using", "harnessing"],
            "moderate": ["using", "applying", "taking advantage of"],
            "casual": ["using", "taking advantage of"]
        },
        "robust": {
            "academic": ["strong", "resilient", "substantial"],
            "moderate": ["strong", "solid", "reliable"],
            "casual": ["strong", "solid", "good"]
        },
        "seamless": {
            "academic": ["smooth", "integrated", "unified"],
            "moderate": ["smooth", "easy", "simple"],
            "casual": ["smooth", "easy", "simple"]
        },
        "noteworthy": {
            "academic": ["notable", "significant", "remarkable"],
            "moderate": ["notable", "important", "significant"],
            "casual": ["important", "worth noting", "interesting"]
        },
        "groundbreaking": {
            "academic": ["innovative", "novel", "pioneering"],
            "moderate": ["new", "innovative", "important"],
            "casual": ["new", "big", "major"]
        },
        "utilize": {
            "academic": ["employ", "apply", "use"],
            "moderate": ["use", "apply", "employ"],
            "casual": ["use", "work with"]
        },
        "utilizes": {
            "academic": ["employs", "applies", "uses"],
            "moderate": ["uses", "applies", "employs"],
            "casual": ["uses", "works with"]
        },
        "utilizing": {
            "academic": ["employing", "applying", "using"],
            "moderate": ["using", "applying", "employing"],
            "casual": ["using", "working with"]
        },
        "subsequently": {
            "academic": ["thereafter", "following this", "later"],
            "moderate": ["then", "later", "after that"],
            "casual": ["then", "after that", "next"]
        },
        "endeavor": {
            "academic": ["attempt", "undertaking", "effort"],
            "moderate": ["try", "attempt", "effort"],
            "casual": ["try", "effort", "work"]
        },
        "commence": {
            "academic": ["begin", "initiate", "start"],
            "moderate": ["start", "begin"],
            "casual": ["start", "begin", "kick off"]
        },
        "optimal": {
            "academic": ["most effective", "ideal", "best"],
            "moderate": ["best", "ideal", "most effective"],
            "casual": ["best", "ideal"]
        },
        "synergistic": {
            "academic": ["combined", "cooperative", "complementary"],
            "moderate": ["combined", "working together", "joint"],
            "casual": ["combined", "together", "joint"]
        },
        "synergy": {
            "academic": ["cooperation", "collaboration", "combined effect"],
            "moderate": ["cooperation", "teamwork", "working together"],
            "casual": ["teamwork", "working together", "combo"]
        },
        "dynamics": {
            "academic": ["interactions", "relationships", "processes"],
            "moderate": ["interactions", "changes", "patterns"],
            "casual": ["changes", "patterns", "how things work"]
        },
        "mechanisms": {
            "academic": ["processes", "methods", "systems"],
            "moderate": ["processes", "methods", "ways"],
            "casual": ["ways", "methods", "how it works"]
        },
        "notably": {
            "academic": ["particularly", "especially", "significantly"],
            "moderate": ["especially", "particularly", "in particular"],
            "casual": ["especially", "particularly", "mainly"]
        },
        "importantly": {
            "academic": ["significantly", "crucially", "notably"],
            "moderate": ["significantly", "especially", "notably"],
            "casual": ["also", "especially", "mainly"]
        },
        "hence": {
            "academic": ["therefore", "thus", "as a result"],
            "moderate": ["so", "therefore", "thus"],
            "casual": ["so", "that's why", "therefore"]
        },
        "thereby": {
            "academic": ["thus", "in this way", "by doing so"],
            "moderate": ["so", "this way", "by doing this"],
            "casual": ["so", "this way", "and"]
        },
        "nonetheless": {
            "academic": ["nevertheless", "however", "still"],
            "moderate": ["still", "however", "but"],
            "casual": ["still", "but", "even so"]
        },
        "notwithstanding": {
            "academic": ["despite", "nevertheless", "regardless"],
            "moderate": ["despite", "still", "even so"],
            "casual": ["despite", "but", "even so"]
        },
        "whilst": {
            "academic": ["while", "although", "whereas"],
            "moderate": ["while", "although", "as"],
            "casual": ["while", "although", "as"]
        },
        "wherein": {
            "academic": ["in which", "where", "within which"],
            "moderate": ["where", "in which"],
            "casual": ["where", "in which"]
        },
        "thereof": {
            "academic": ["of it", "of that", "of this"],
            "moderate": ["of it", "of this", "of that"],
            "casual": ["of it", "of this"]
        },
    }

    # Phrase replacements
    # 短语替换
    PHRASE_REPLACEMENTS: Dict[str, Dict[str, str]] = {
        # === Important/Note patterns (重要性/注释模式) ===
        "it is important to note that": {
            "academic": "notably",
            "moderate": "note that",
            "casual": "note that"
        },
        "it is worth noting that": {
            "academic": "notably",
            "moderate": "notably",
            "casual": "it's worth noting"
        },
        "it is crucial to": {
            "academic": "we must",
            "moderate": "we need to",
            "casual": "we need to"
        },
        "it is essential to": {
            "academic": "we must",
            "moderate": "we need to",
            "casual": "we need to"
        },
        # === Role/Importance patterns (作用/重要性模式) ===
        "plays a crucial role": {
            "academic": "is essential",
            "moderate": "is important",
            "casual": "matters a lot"
        },
        "plays a pivotal role": {
            "academic": "is central",
            "moderate": "is key",
            "casual": "is really important"
        },
        "plays an important role": {
            "academic": "is significant",
            "moderate": "is important",
            "casual": "matters"
        },
        "plays a significant role": {
            "academic": "is significant",
            "moderate": "is important",
            "casual": "matters"
        },
        # === Emphasis patterns (强调模式) ===
        "underscores the importance": {
            "academic": "shows the significance",
            "moderate": "shows how important",
            "casual": "shows how important"
        },
        "highlights the importance": {
            "academic": "shows the significance",
            "moderate": "shows how important",
            "casual": "shows how important"
        },
        # === Context patterns (语境模式) ===
        "in the context of": {
            "academic": "regarding",
            "moderate": "in",
            "casual": "for"
        },
        "in the realm of": {
            "academic": "in",
            "moderate": "in",
            "casual": "in"
        },
        "in terms of": {
            "academic": "regarding",
            "moderate": "for",
            "casual": "for"
        },
        "with regard to": {
            "academic": "regarding",
            "moderate": "about",
            "casual": "about"
        },
        "with respect to": {
            "academic": "regarding",
            "moderate": "about",
            "casual": "about"
        },
        # === Quantity patterns (数量模式) ===
        "a wide range of": {
            "academic": "various",
            "moderate": "many",
            "casual": "lots of"
        },
        "a plethora of": {
            "academic": "numerous",
            "moderate": "many",
            "casual": "lots of"
        },
        "a myriad of": {
            "academic": "numerous",
            "moderate": "many",
            "casual": "lots of"
        },
        "a multitude of": {
            "academic": "numerous",
            "moderate": "many",
            "casual": "lots of"
        },
        # === Cause/Result patterns (因果模式) ===
        "due to the fact that": {
            "academic": "because",
            "moderate": "because",
            "casual": "since"
        },
        "owing to the fact that": {
            "academic": "because",
            "moderate": "because",
            "casual": "since"
        },
        "as a consequence of": {
            "academic": "because of",
            "moderate": "because of",
            "casual": "because of"
        },
        # === Purpose patterns (目的模式) ===
        "in order to": {
            "academic": "to",
            "moderate": "to",
            "casual": "to"
        },
        "with the aim of": {
            "academic": "to",
            "moderate": "to",
            "casual": "to"
        },
        "for the purpose of": {
            "academic": "to",
            "moderate": "to",
            "casual": "to"
        },
        # === Conclusion patterns (结论模式) ===
        "in conclusion": {
            "academic": "to conclude",
            "moderate": "finally",
            "casual": "finally"
        },
        "to summarize": {
            "academic": "in summary",
            "moderate": "to sum up",
            "casual": "so"
        },
        "in summary": {
            "academic": "overall",
            "moderate": "to sum up",
            "casual": "so"
        },
        # === Approach patterns (方法模式) ===
        "holistic approach": {
            "academic": "integrated approach",
            "moderate": "complete approach",
            "casual": "full approach"
        },
        "comprehensive approach": {
            "academic": "thorough approach",
            "moderate": "full approach",
            "casual": "complete approach"
        },
        # === Relationship patterns (关系模式) ===
        "testament to": {
            "academic": "evidence of",
            "moderate": "proof of",
            "casual": "shows"
        },
        "landscape of": {
            "academic": "field of",
            "moderate": "area of",
            "casual": "area of"
        },
        # === AI padding phrases (AI填充短语) ===
        "it is evident that": {
            "academic": "clearly",
            "moderate": "clearly",
            "casual": "clearly"
        },
        "it can be seen that": {
            "academic": "clearly",
            "moderate": "we can see",
            "casual": "we can see"
        },
        "it should be noted that": {
            "academic": "notably",
            "moderate": "note that",
            "casual": "note that"
        },
        "it goes without saying that": {
            "academic": "clearly",
            "moderate": "obviously",
            "casual": "obviously"
        },
        "needless to say": {
            "academic": "clearly",
            "moderate": "obviously",
            "casual": "obviously"
        },
        # === Complex dynamics (复杂动态) ===
        "complex dynamics": {
            "academic": "interactions",
            "moderate": "relationships",
            "casual": "how things work"
        },
        "intricate dynamics": {
            "academic": "interactions",
            "moderate": "relationships",
            "casual": "how things work"
        },
    }

    def __init__(self, colloquialism_level: int = 4, session_id: Optional[str] = None):
        """
        Initialize rule track

        Args:
            colloquialism_level: Target formality level (0-10)
            session_id: Optional session ID for accessing locked terms from Step 1.0
        """
        self.level = colloquialism_level
        self.session_id = session_id
        self.style_category = self._get_style_category()

        # Load locked terms from session (Step 1.0)
        # 从会话加载锁定术语（步骤1.0）
        self.session_locked_terms = get_locked_terms_from_session(session_id)
        if self.session_locked_terms:
            logger.info(f"RuleTrack loaded {len(self.session_locked_terms)} locked terms from session {session_id}")

    def _get_style_category(self) -> str:
        """Get style category based on level"""
        if self.level <= 2:
            return "academic"
        elif self.level <= 6:
            return "moderate"
        else:
            return "casual"

    def generate_suggestion(
        self,
        sentence: str,
        issues: List[Dict[str, Any]],
        locked_terms: List[str]
    ) -> RuleSuggestionResult:
        """
        Generate humanization suggestion using rules
        使用规则生成人源化建议

        Args:
            sentence: Original sentence
            issues: Detected issues
            locked_terms: Terms to protect (in addition to session locked terms)

        Returns:
            RuleSuggestionResult with rewritten sentence and changes
        """
        # Merge session locked terms with passed locked_terms (Step 1.0 integration)
        # 合并会话锁定术语与传入的锁定术语（步骤1.0集成）
        all_locked_terms = list(set(self.session_locked_terms + (locked_terms or [])))
        if all_locked_terms and len(all_locked_terms) != len(locked_terms or []):
            logger.debug(f"RuleTrack merged locked terms: {len(locked_terms or [])} passed + {len(self.session_locked_terms)} session = {len(all_locked_terms)} total")

        rewritten = sentence
        changes = []

        # Step 1: Replace phrases first (longer patterns)
        # 步骤1: 首先替换短语（较长的模式）
        rewritten, phrase_changes = self._replace_phrases(rewritten, all_locked_terms)
        changes.extend(phrase_changes)

        # Step 2: Replace individual words
        # 步骤2: 替换单个词
        rewritten, word_changes = self._replace_words(rewritten, all_locked_terms)
        changes.extend(word_changes)

        # Step 3: Apply syntax adjustments if needed
        # 步骤3: 如果需要则应用句法调整
        if self._needs_syntax_adjustment(rewritten, issues):
            rewritten, syntax_changes = self._adjust_syntax(rewritten, all_locked_terms)
            changes.extend(syntax_changes)

        # Calculate predicted risk (simplified)
        # 计算预测风险（简化版）
        risk_reduction = len(changes) * 5
        predicted_risk = max(20, 70 - risk_reduction)

        # Calculate similarity
        # 计算相似度
        similarity = self._calculate_similarity(sentence, rewritten)

        # Generate explanation
        # 生成解释
        explanation, explanation_zh = self._generate_explanation(changes)

        return RuleSuggestionResult(
            rewritten=rewritten,
            changes=changes,
            predicted_risk=predicted_risk,
            semantic_similarity=similarity,
            explanation=explanation,
            explanation_zh=explanation_zh
        )

    def _replace_phrases(
        self,
        text: str,
        locked_terms: List[str]
    ) -> Tuple[str, List[Change]]:
        """
        Replace fingerprint phrases
        替换指纹短语
        """
        changes = []
        result = text

        for phrase, replacements in self.PHRASE_REPLACEMENTS.items():
            # Case-insensitive search
            # 不区分大小写搜索
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            match = pattern.search(result)

            if match:
                original = match.group(0)

                # Check if overlaps with locked terms
                # 检查是否与锁定术语重叠
                if any(term.lower() in original.lower() for term in locked_terms):
                    continue

                replacement = replacements.get(self.style_category, replacements["moderate"])

                # Preserve case of first letter
                # 保留首字母大小写
                if original[0].isupper():
                    replacement = replacement.capitalize()

                result = pattern.sub(replacement, result, count=1)
                changes.append(Change(
                    original=original,
                    replacement=replacement,
                    reason="AI-preferred phrase replacement",
                    reason_zh="AI偏好短语替换"
                ))

        return result, changes

    def _replace_words(
        self,
        text: str,
        locked_terms: List[str]
    ) -> Tuple[str, List[Change]]:
        """
        Replace fingerprint words (avoiding chain replacements)
        替换指纹词（避免链式替换）

        Uses two-pass approach: first find all matches in original text,
        then apply replacements from end to start.
        使用两遍方法：先在原文中找到所有匹配，然后从后往前应用替换。
        """
        changes = []

        # First pass: find all fingerprint words and their positions in original text
        # 第一遍：在原文中找到所有指纹词及其位置
        replacements_to_make = []

        for word, replacements in self.FINGERPRINT_REPLACEMENTS.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)

            for match in pattern.finditer(text):
                original = match.group(0)
                start = match.start()
                end = match.end()

                # Check if part of locked term
                # 检查是否是锁定术语的一部分
                skip = False
                for term in locked_terms:
                    if original.lower() in term.lower() or term.lower() in original.lower():
                        skip = True
                        break

                if skip:
                    continue

                # Check if this position overlaps with existing replacement
                # 检查此位置是否与现有替换重叠
                overlaps = False
                for existing in replacements_to_make:
                    if not (end <= existing['start'] or start >= existing['end']):
                        overlaps = True
                        break

                if overlaps:
                    continue

                # Get level-appropriate replacement
                # 获取等级适当的替换
                alternatives = replacements.get(self.style_category, replacements["moderate"])
                replacement = alternatives[0] if alternatives else word

                # Preserve case
                # 保留大小写
                if original[0].isupper():
                    replacement = replacement.capitalize()
                if original.isupper():
                    replacement = replacement.upper()

                replacements_to_make.append({
                    'start': start,
                    'end': end,
                    'original': original,
                    'replacement': replacement
                })

        # Sort by position (reverse order to maintain indices)
        # 按位置排序（逆序以保持索引正确）
        replacements_to_make.sort(key=lambda x: x['start'], reverse=True)

        # Apply replacements from end to start (to preserve indices)
        # 从后往前应用替换（以保持索引正确）
        result = text
        for rep in replacements_to_make:
            result = result[:rep['start']] + rep['replacement'] + result[rep['end']:]
            changes.append(Change(
                original=rep['original'],
                replacement=rep['replacement'],
                reason="AI fingerprint word replacement",
                reason_zh="AI指纹词替换"
            ))

        # Reverse changes list to match original order in text
        # 反转changes列表以匹配文本中的原始顺序
        changes.reverse()

        return result, changes

    def _needs_syntax_adjustment(
        self,
        text: str,
        issues: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if syntax adjustment is needed
        检查是否需要句法调整
        """
        # Check for structure-related issues
        # 检查与结构相关的问题
        for issue in issues:
            if issue.get("type") in ["structure", "burstiness"]:
                return True

        # Check for very long sentences
        # 检查非常长的句子
        word_count = len(text.split())
        if word_count > 35:
            return True

        return False

    def _adjust_syntax(
        self,
        text: str,
        locked_terms: List[str]
    ) -> Tuple[str, List[Change]]:
        """
        Apply syntax adjustments
        应用句法调整

        Current implementations:
        - Insert hedging language
        - Add transitional elements
        """
        changes = []
        result = text

        # Add hedging language for statements
        # 为陈述添加hedging语言
        hedging_patterns = [
            (r'^(This|The|It)\s+(shows?|demonstrates?|proves?)\s+that',
             r'\1 seems to \2 that',
             "Added hedging language",
             "添加了hedging语言"),
            (r'^(This|The|It)\s+(is)\s+(clear|evident|obvious)',
             r'\1 appears to be \3',
             "Softened absolute statement",
             "软化了绝对性陈述"),
        ]

        for pattern, replacement, reason_en, reason_zh in hedging_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                if new_result != result:
                    changes.append(Change(
                        original=re.search(pattern, result, re.IGNORECASE).group(0),
                        replacement=re.search(pattern, replacement, re.IGNORECASE).group(0) if re.search(pattern, replacement, re.IGNORECASE) else replacement,
                        reason=reason_en,
                        reason_zh=reason_zh
                    ))
                    result = new_result
                    break  # Only one syntax change per call

        return result, changes

    def _calculate_similarity(self, original: str, rewritten: str) -> float:
        """
        Calculate simple similarity score
        计算简单相似度分数
        """
        orig_words = set(original.lower().split())
        new_words = set(rewritten.lower().split())

        if not orig_words:
            return 1.0

        overlap = len(orig_words & new_words)
        total = len(orig_words | new_words)

        return overlap / total if total > 0 else 1.0

    def _generate_explanation(self, changes: List[Change]) -> Tuple[str, str]:
        """
        Generate explanation for changes
        为改动生成解释
        """
        if not changes:
            return (
                "No changes were necessary",
                "无需修改"
            )

        # Group changes by type
        # 按类型分组改动
        word_changes = [c for c in changes if "word" in c.reason.lower()]
        phrase_changes = [c for c in changes if "phrase" in c.reason.lower()]
        other_changes = [c for c in changes if c not in word_changes and c not in phrase_changes]

        parts_en = []
        parts_zh = []

        if word_changes:
            words = [f"'{c.original}'→'{c.replacement}'" for c in word_changes[:3]]
            parts_en.append(f"Replaced {len(word_changes)} AI fingerprint word(s): {', '.join(words)}")
            parts_zh.append(f"替换了{len(word_changes)}个AI指纹词: {', '.join(words)}")

        if phrase_changes:
            parts_en.append(f"Replaced {len(phrase_changes)} AI-preferred phrase(s)")
            parts_zh.append(f"替换了{len(phrase_changes)}个AI偏好短语")

        if other_changes:
            parts_en.append(f"Made {len(other_changes)} syntax adjustment(s)")
            parts_zh.append(f"进行了{len(other_changes)}处句法调整")

        return (
            "; ".join(parts_en),
            "；".join(parts_zh)
        )

    def get_replacement_options(
        self,
        word: str
    ) -> List[str]:
        """
        Get all replacement options for a word
        获取一个词的所有替换选项

        Returns list of alternatives based on current style level
        """
        word_lower = word.lower()

        if word_lower in self.FINGERPRINT_REPLACEMENTS:
            return self.FINGERPRINT_REPLACEMENTS[word_lower].get(
                self.style_category,
                self.FINGERPRINT_REPLACEMENTS[word_lower]["moderate"]
            )

        return []
