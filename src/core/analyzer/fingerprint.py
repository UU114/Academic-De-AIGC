"""
AI Fingerprint word detection module
AI指纹词检测模块
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class FingerprintMatch:
    """
    Represents a detected fingerprint word/phrase
    表示检测到的指纹词/短语
    """
    word: str
    position: int
    end_position: int
    risk_weight: float
    category: str  # high_freq, phrase, connector, academic_fluff
    replacements: List[str] = field(default_factory=list)


class FingerprintDetector:
    """
    AI Fingerprint detection engine
    AI指纹检测引擎

    Detects words and phrases commonly overused by AI:
    - High-frequency AI words (delve, crucial, paramount)
    - AI-preferred phrases (it is important to note)
    - Overused connectors (however, therefore, moreover)
    - Academic fluff words (significantly, comprehensive)
    """

    # High-frequency AI fingerprint words with risk weights and replacements
    # 高频AI指纹词及其风险权重和替换词
    HIGH_FREQ_WORDS: Dict[str, dict] = {
        "delve": {"weight": 1.0, "replacements": ["explore", "examine", "look at", "investigate", "study"]},
        "delves": {"weight": 1.0, "replacements": ["explores", "examines", "looks at", "investigates"]},
        "crucial": {"weight": 0.8, "replacements": ["important", "key", "essential", "critical"]},
        "paramount": {"weight": 0.9, "replacements": ["important", "key", "main", "central", "chief"]},
        "utilize": {"weight": 0.7, "replacements": ["use", "apply", "employ"]},
        "utilizes": {"weight": 0.7, "replacements": ["uses", "applies", "employs"]},
        "utilizing": {"weight": 0.7, "replacements": ["using", "applying", "employing"]},
        "facilitate": {"weight": 0.7, "replacements": ["help", "enable", "support", "allow"]},
        "facilitates": {"weight": 0.7, "replacements": ["helps", "enables", "supports"]},
        "comprehensive": {"weight": 0.6, "replacements": ["full", "complete", "thorough", "detailed"]},
        "subsequently": {"weight": 0.7, "replacements": ["then", "later", "after that", "next"]},
        "aforementioned": {"weight": 0.8, "replacements": ["these", "this", "the above", "mentioned"]},
        "multifaceted": {"weight": 0.8, "replacements": ["complex", "varied", "diverse"]},
        "realm": {"weight": 0.7, "replacements": ["area", "field", "domain", "sphere"]},
        "tapestry": {"weight": 0.9, "replacements": ["mix", "combination", "blend"]},
        "leverage": {"weight": 0.6, "replacements": ["use", "apply", "exploit", "take advantage of"]},
        "leveraging": {"weight": 0.6, "replacements": ["using", "applying", "exploiting"]},
        "robust": {"weight": 0.5, "replacements": ["strong", "solid", "reliable"]},
        "seamless": {"weight": 0.6, "replacements": ["smooth", "easy", "simple"]},
        "cutting-edge": {"weight": 0.6, "replacements": ["advanced", "modern", "latest", "new"]},
        "pivotal": {"weight": 0.7, "replacements": ["key", "central", "important", "critical"]},
        "intricate": {"weight": 0.6, "replacements": ["complex", "detailed", "elaborate"]},
        "nuanced": {"weight": 0.6, "replacements": ["subtle", "detailed", "complex"]},
        "plethora": {"weight": 0.8, "replacements": ["many", "lots of", "numerous", "plenty of"]},
        "myriad": {"weight": 0.7, "replacements": ["many", "numerous", "various", "countless"]},
        "foster": {"weight": 0.5, "replacements": ["encourage", "promote", "support", "develop"]},
        "fosters": {"weight": 0.5, "replacements": ["encourages", "promotes", "supports"]},
        "endeavor": {"weight": 0.7, "replacements": ["try", "attempt", "effort", "work"]},
        "endeavors": {"weight": 0.7, "replacements": ["tries", "attempts", "efforts"]},
        "embark": {"weight": 0.6, "replacements": ["start", "begin", "set out"]},
        "embarking": {"weight": 0.6, "replacements": ["starting", "beginning", "setting out"]},
        "commence": {"weight": 0.7, "replacements": ["start", "begin", "initiate"]},
        "commences": {"weight": 0.7, "replacements": ["starts", "begins"]},
        "underscore": {"weight": 0.6, "replacements": ["highlight", "emphasize", "stress"]},
        "underscores": {"weight": 0.6, "replacements": ["highlights", "emphasizes", "stresses"]},
        "elucidate": {"weight": 0.8, "replacements": ["explain", "clarify", "describe"]},
        "elucidates": {"weight": 0.8, "replacements": ["explains", "clarifies", "describes"]},
        "pertaining": {"weight": 0.6, "replacements": ["about", "related to", "concerning"]},
        "optimal": {"weight": 0.5, "replacements": ["best", "ideal", "most effective"]},
        "enhance": {"weight": 0.4, "replacements": ["improve", "boost", "increase"]},
        "enhances": {"weight": 0.4, "replacements": ["improves", "boosts", "increases"]},
        "noteworthy": {"weight": 0.6, "replacements": ["notable", "important", "significant"]},
        "groundbreaking": {"weight": 0.7, "replacements": ["innovative", "pioneering", "new"]},
    }

    # AI-preferred phrases
    # AI偏好短语
    PHRASE_PATTERNS: Dict[str, dict] = {
        "it is important to note that": {"weight": 0.9, "replacements": ["note that", "importantly"]},
        "it is worth noting that": {"weight": 0.8, "replacements": ["notably", "note that"]},
        "it should be noted that": {"weight": 0.8, "replacements": ["note that", "notably"]},
        "plays a crucial role": {"weight": 0.8, "replacements": ["is important", "matters", "is key"]},
        "plays a pivotal role": {"weight": 0.9, "replacements": ["is important", "is central", "is key"]},
        "plays an important role": {"weight": 0.5, "replacements": ["matters", "is important"]},
        "in the context of": {"weight": 0.6, "replacements": ["in", "for", "regarding", "with"]},
        "in the realm of": {"weight": 0.8, "replacements": ["in", "within", "in the field of"]},
        "a wide range of": {"weight": 0.5, "replacements": ["many", "various", "different"]},
        "a myriad of": {"weight": 0.8, "replacements": ["many", "numerous", "various"]},
        "a plethora of": {"weight": 0.9, "replacements": ["many", "lots of", "numerous"]},
        "due to the fact that": {"weight": 0.7, "replacements": ["because", "since", "as"]},
        "in order to": {"weight": 0.4, "replacements": ["to"]},
        "as a result of": {"weight": 0.4, "replacements": ["because of", "due to", "from"]},
        "with respect to": {"weight": 0.5, "replacements": ["about", "regarding", "for"]},
        "in terms of": {"weight": 0.4, "replacements": ["for", "regarding", "in"]},
        "on the other hand": {"weight": 0.3, "replacements": ["but", "however", "yet"]},
        "it is evident that": {"weight": 0.7, "replacements": ["clearly", "evidently"]},
        "it is clear that": {"weight": 0.5, "replacements": ["clearly"]},
        "serves as a": {"weight": 0.5, "replacements": ["is a", "acts as a", "works as a"]},
        "can be seen as": {"weight": 0.5, "replacements": ["is", "seems like", "appears to be"]},
        "has the potential to": {"weight": 0.5, "replacements": ["can", "may", "could"]},
        "is of paramount importance": {"weight": 0.9, "replacements": ["is very important", "matters greatly"]},
        "the advent of": {"weight": 0.6, "replacements": ["the arrival of", "the introduction of"]},
    }

    # Overused connectors
    # 过度使用的连接词
    CONNECTOR_PATTERNS: Dict[str, dict] = {
        "however": {"weight": 0.3, "replacements": ["but", "yet", "still"]},
        "therefore": {"weight": 0.3, "replacements": ["so", "thus", "hence"]},
        "moreover": {"weight": 0.4, "replacements": ["also", "besides", "furthermore"]},
        "furthermore": {"weight": 0.4, "replacements": ["also", "besides", "in addition"]},
        "additionally": {"weight": 0.4, "replacements": ["also", "besides", "plus"]},
        "consequently": {"weight": 0.4, "replacements": ["so", "as a result", "thus"]},
        "nevertheless": {"weight": 0.4, "replacements": ["but", "still", "yet"]},
        "nonetheless": {"weight": 0.4, "replacements": ["but", "still", "yet"]},
        "thus": {"weight": 0.3, "replacements": ["so", "therefore"]},
        "hence": {"weight": 0.4, "replacements": ["so", "therefore", "thus"]},
        "whereby": {"weight": 0.6, "replacements": ["where", "by which", "through which"]},
        "wherein": {"weight": 0.6, "replacements": ["where", "in which"]},
        "henceforth": {"weight": 0.7, "replacements": ["from now on", "from this point"]},
    }

    def __init__(self, custom_fingerprints_path: Optional[str] = None):
        """
        Initialize fingerprint detector
        初始化指纹检测器

        Args:
            custom_fingerprints_path: Path to custom fingerprints JSON file
        """
        self.high_freq_words = dict(self.HIGH_FREQ_WORDS)
        self.phrase_patterns = dict(self.PHRASE_PATTERNS)
        self.connector_patterns = dict(self.CONNECTOR_PATTERNS)

        if custom_fingerprints_path:
            self._load_custom_fingerprints(custom_fingerprints_path)

        # Compile patterns
        # 编译模式
        self._compile_patterns()

    def _load_custom_fingerprints(self, path: str):
        """
        Load custom fingerprints from JSON file
        从JSON文件加载自定义指纹
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "words" in data:
                self.high_freq_words.update(data["words"])
            if "phrases" in data:
                self.phrase_patterns.update(data["phrases"])
            if "connectors" in data:
                self.connector_patterns.update(data["connectors"])

            logger.info(f"Loaded custom fingerprints from {path}")
        except Exception as e:
            logger.warning(f"Failed to load custom fingerprints: {e}")

    def _compile_patterns(self):
        """
        Compile regex patterns for efficient matching
        编译正则表达式以提高匹配效率
        """
        # Compile phrase patterns (case insensitive)
        # 编译短语模式（不区分大小写）
        self.compiled_phrases = {
            phrase: re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            for phrase in self.phrase_patterns
        }

        # Word pattern for boundary matching
        # 用于边界匹配的单词模式
        self.word_boundary = re.compile(r'\b\w+\b')

    def detect(self, text: str) -> List[FingerprintMatch]:
        """
        Detect all fingerprint words and phrases in text
        检测文本中所有指纹词和短语

        Args:
            text: Input text to analyze

        Returns:
            List of FingerprintMatch objects sorted by position
        """
        matches = []

        # Detect phrases first (longer patterns take precedence)
        # 首先检测短语（较长的模式优先）
        matches.extend(self._detect_phrases(text))

        # Get positions covered by phrases
        # 获取被短语覆盖的位置
        covered_positions = set()
        for match in matches:
            covered_positions.update(range(match.position, match.end_position))

        # Detect individual words (skip if already covered by phrase)
        # 检测单个词（如果已被短语覆盖则跳过）
        matches.extend(self._detect_words(text, covered_positions))

        # Detect connectors
        # 检测连接词
        matches.extend(self._detect_connectors(text, covered_positions))

        # Sort by position
        # 按位置排序
        matches.sort(key=lambda m: m.position)

        return matches

    def _detect_phrases(self, text: str) -> List[FingerprintMatch]:
        """
        Detect fingerprint phrases
        检测指纹短语
        """
        matches = []

        for phrase, pattern in self.compiled_phrases.items():
            info = self.phrase_patterns[phrase]
            for match in pattern.finditer(text):
                matches.append(FingerprintMatch(
                    word=match.group(0),
                    position=match.start(),
                    end_position=match.end(),
                    risk_weight=info["weight"],
                    category="phrase",
                    replacements=info.get("replacements", [])
                ))

        return matches

    def _detect_words(self, text: str, covered_positions: Set[int]) -> List[FingerprintMatch]:
        """
        Detect fingerprint words
        检测指纹词
        """
        matches = []
        text_lower = text.lower()

        for word_match in self.word_boundary.finditer(text):
            # Skip if position is covered by a phrase
            # 如果位置被短语覆盖则跳过
            if word_match.start() in covered_positions:
                continue

            word = word_match.group(0).lower()

            if word in self.high_freq_words:
                info = self.high_freq_words[word]
                matches.append(FingerprintMatch(
                    word=word_match.group(0),
                    position=word_match.start(),
                    end_position=word_match.end(),
                    risk_weight=info["weight"],
                    category="high_freq",
                    replacements=info.get("replacements", [])
                ))

        return matches

    def _detect_connectors(self, text: str, covered_positions: Set[int]) -> List[FingerprintMatch]:
        """
        Detect overused connectors
        检测过度使用的连接词
        """
        matches = []

        for connector, info in self.connector_patterns.items():
            pattern = re.compile(r'\b' + re.escape(connector) + r'\b', re.IGNORECASE)

            for match in pattern.finditer(text):
                # Skip if position is covered
                # 如果位置被覆盖则跳过
                if match.start() in covered_positions:
                    continue

                matches.append(FingerprintMatch(
                    word=match.group(0),
                    position=match.start(),
                    end_position=match.end(),
                    risk_weight=info["weight"],
                    category="connector",
                    replacements=info.get("replacements", [])
                ))

        return matches

    def calculate_density(self, text: str, matches: Optional[List[FingerprintMatch]] = None) -> float:
        """
        Calculate fingerprint density in text
        计算文本中的指纹密度

        Args:
            text: Input text
            matches: Optional pre-computed matches

        Returns:
            Density score (0-1)
        """
        if matches is None:
            matches = self.detect(text)

        if not text.strip():
            return 0.0

        # Count words in text
        # 统计文本中的词数
        word_count = len(self.word_boundary.findall(text))

        if word_count == 0:
            return 0.0

        # Calculate weighted match count
        # 计算加权匹配数
        weighted_count = sum(m.risk_weight for m in matches)

        # Density = weighted matches / total words
        # 密度 = 加权匹配数 / 总词数
        return min(1.0, weighted_count / word_count)

    def get_high_risk_matches(
        self,
        matches: List[FingerprintMatch],
        threshold: float = 0.7
    ) -> List[FingerprintMatch]:
        """
        Get matches above risk threshold
        获取超过风险阈值的匹配

        Args:
            matches: List of matches
            threshold: Risk weight threshold

        Returns:
            Filtered list of high-risk matches
        """
        return [m for m in matches if m.risk_weight >= threshold]

    def get_replacement_suggestions(
        self,
        matches: List[FingerprintMatch],
        colloquialism_level: int = 4
    ) -> Dict[str, List[str]]:
        """
        Get replacement suggestions for matches based on colloquialism level
        根据口语化等级获取匹配的替换建议

        Args:
            matches: List of matches
            colloquialism_level: Target formality level (0-10)

        Returns:
            Dict mapping original words to suggested replacements
        """
        suggestions = {}

        for match in matches:
            if not match.replacements:
                continue

            # Adjust suggestions based on colloquialism level
            # 根据口语化等级调整建议
            if colloquialism_level <= 2:
                # Keep more formal alternatives
                # 保留更正式的替代词
                suggestions[match.word] = match.replacements[:2]
            elif colloquialism_level <= 6:
                # Middle ground
                # 中等
                suggestions[match.word] = match.replacements[:3]
            else:
                # Prefer more casual alternatives
                # 偏好更随意的替代词
                suggestions[match.word] = match.replacements

        return suggestions


# Convenience function
# 便捷函数
def detect_fingerprints(text: str) -> List[FingerprintMatch]:
    """
    Convenience function to detect fingerprints
    检测指纹的便捷函数
    """
    detector = FingerprintDetector()
    return detector.detect(text)
