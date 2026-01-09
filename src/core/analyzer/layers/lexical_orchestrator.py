"""
Lexical Layer Orchestrator (Layer 1)
词汇层编排器（第1层）

Handles word-level analysis:
- Step 5.1: Fingerprint Detection (指纹词检测) - consolidates all fingerprint logic
- Step 5.2: Connector Analysis (连接词分析) - consolidates connector detection
- Step 5.3: Word-Level Risk (词级风险) - PPL-based analysis

处理词汇级分析：
- 步骤 5.1：指纹词检测（整合所有指纹词逻辑）
- 步骤 5.2：连接词分析（整合连接词检测）
- 步骤 5.3：词级风险（基于PPL的分析）

This is the finest granularity layer, analyzing individual words and phrases.
这是最细粒度的层，分析单个词和短语。
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter, defaultdict

from src.core.analyzer.layers.base import (
    BaseOrchestrator,
    LayerContext,
    LayerResult,
    LayerLevel,
    RiskLevel,
    DetectionIssue,
)
from src.core.analyzer.fingerprint import FingerprintDetector
from src.core.analyzer.connector_detector import ConnectorDetector

logger = logging.getLogger(__name__)


# Consolidated fingerprint categories
# Type A: Dead Giveaways (+40 risk) - extremely AI-characteristic
FINGERPRINT_TYPE_A = {
    "delve", "delves", "delving", "delved",
    "tapestry", "tapestries",
    "multifaceted",
    "intricacies", "intricate",
    "holistic", "holistically",
    "pivotal",
    "nuanced", "nuances",
    "embark", "embarks", "embarking", "embarked",
    "realm", "realms",
    "landscape", "landscapes",
    "underscores", "underscore", "underscoring",
    "paramount",
    "ever-evolving",
}

# Type B: Academic Clichés (+5-25 risk) - common but less distinctive
FINGERPRINT_TYPE_B = {
    "crucial": 15,
    "comprehensive": 10,
    "robust": 15,
    "leverage": 15,
    "utilize": 10,
    "facilitate": 10,
    "enhance": 5,
    "significant": 5,
    "substantial": 10,
    "notable": 10,
    "remarkable": 15,
    "profound": 15,
    "fundamental": 10,
    "essential": 5,
    "meticulous": 20,
    "intrinsic": 15,
    "inherent": 10,
    "seminal": 20,
    "groundbreaking": 20,
    "cutting-edge": 15,
    "state-of-the-art": 15,
    "seamless": 15,
    "seamlessly": 15,
}

# Type C: Connector overuse patterns (+10-30 risk)
FINGERPRINT_TYPE_C_CONNECTORS = {
    "furthermore": 25,
    "moreover": 25,
    "additionally": 20,
    "consequently": 15,
    "subsequently": 20,
    "nevertheless": 15,
    "nonetheless": 15,
    "hence": 10,
    "thus": 10,
    "therefore": 10,
    "in addition": 20,
    "as a result": 15,
    "in contrast": 10,
    "on the other hand": 15,
    "in conclusion": 15,
    "to summarize": 20,
    "it is important to note that": 30,
    "it is worth noting that": 25,
    "it should be noted that": 25,
}

# Phrases that are strong AI indicators
FINGERPRINT_PHRASES = {
    "plays a crucial role": 30,
    "plays a pivotal role": 35,
    "plays an important role": 20,
    "serves as a testament": 35,
    "in the realm of": 30,
    "in the landscape of": 30,
    "it is important to note": 30,
    "it is worth mentioning": 25,
    "a wide range of": 20,
    "a plethora of": 30,
    "a myriad of": 30,
    "due to the fact that": 25,
    "in order to": 15,
    "with regard to": 15,
    "in terms of": 10,
    "on the basis of": 15,
    "in light of": 15,
    "in the context of": 15,
    "pertaining to": 20,
    "with respect to": 15,
}


class LexicalOrchestrator(BaseOrchestrator):
    """
    Layer 1: Lexical-level orchestrator
    第1层：词汇级编排器

    Responsibilities:
    - Consolidate all fingerprint detection (currently in 3 files)
    - Consolidate connector detection
    - Calculate word-level AIGC risk
    - Provide replacement suggestions

    职责：
    - 整合所有指纹词检测（目前分散在3个文件中）
    - 整合连接词检测
    - 计算词级AIGC风险
    - 提供替换建议
    """

    layer = LayerLevel.LEXICAL

    def __init__(self):
        super().__init__()
        self.fingerprint_detector = FingerprintDetector()
        self.connector_detector = ConnectorDetector()

    async def analyze(self, context: LayerContext) -> LayerResult:
        """
        Run lexical-level analysis
        运行词汇级分析

        Steps:
        5.1 - Fingerprint Detection (consolidated)
        5.2 - Connector Analysis (consolidated)
        5.3 - Word-Level Risk
        """
        self.logger.info("Starting lexical layer analysis (Layer 1)")

        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Step 5.1: Fingerprint Detection (consolidated)
        fingerprint_result = self._analyze_fingerprints(context)
        issues.extend(fingerprint_result["issues"])
        details["fingerprints"] = fingerprint_result["details"]
        recommendations.extend(fingerprint_result["recommendations"])
        recommendations_zh.extend(fingerprint_result["recommendations_zh"])

        # Step 5.2: Connector Analysis (consolidated)
        connector_result = self._analyze_connectors(context)
        issues.extend(connector_result["issues"])
        details["connectors"] = connector_result["details"]
        recommendations.extend(connector_result["recommendations"])
        recommendations_zh.extend(connector_result["recommendations_zh"])

        # Step 5.3: Word-Level Risk
        word_risk_result = self._calculate_word_level_risk(context, fingerprint_result, connector_result)
        issues.extend(word_risk_result["issues"])
        details["word_risk"] = word_risk_result["details"]
        recommendations.extend(word_risk_result["recommendations"])
        recommendations_zh.extend(word_risk_result["recommendations_zh"])

        # Calculate overall risk score
        risk_score = self._calculate_layer_risk(fingerprint_result, connector_result, word_risk_result)
        risk_level = self._calculate_risk_level(risk_score)

        # Update context
        updated_context = self._update_context(context)

        self.logger.info(f"Lexical layer analysis complete. Risk score: {risk_score}")

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

    def _analyze_fingerprints(self, context: LayerContext) -> Dict[str, Any]:
        """
        Step 5.1: Fingerprint Detection (consolidated)
        步骤 5.1：指纹词检测（整合）

        Consolidates detection from:
        - Type A: Dead Giveaways (+40 risk)
        - Type B: Academic Clichés (+5-25 risk)
        - Type C: Connectors (+10-30 risk)
        - Phrases: Multi-word patterns
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        text = context.full_text.lower()
        words = re.findall(r'\b[a-z]+(?:-[a-z]+)*\b', text)
        word_count = len(words)

        # Detect Type A fingerprints (Dead Giveaways)
        type_a_matches = []
        for word in FINGERPRINT_TYPE_A:
            count = text.count(word.lower())
            if count > 0:
                type_a_matches.append({"word": word, "count": count, "risk": 40})

        # Detect Type B fingerprints (Academic Clichés)
        type_b_matches = []
        for word, risk in FINGERPRINT_TYPE_B.items():
            count = text.count(word.lower())
            if count > 0:
                type_b_matches.append({"word": word, "count": count, "risk": risk})

        # Detect fingerprint phrases
        phrase_matches = []
        for phrase, risk in FINGERPRINT_PHRASES.items():
            count = text.count(phrase.lower())
            if count > 0:
                phrase_matches.append({"phrase": phrase, "count": count, "risk": risk})

        details["type_a_matches"] = type_a_matches
        details["type_b_matches"] = type_b_matches
        details["phrase_matches"] = phrase_matches
        details["total_type_a"] = sum(m["count"] for m in type_a_matches)
        details["total_type_b"] = sum(m["count"] for m in type_b_matches)
        details["total_phrases"] = sum(m["count"] for m in phrase_matches)

        # Calculate fingerprint density
        total_fingerprints = details["total_type_a"] + details["total_type_b"] + details["total_phrases"]
        density = (total_fingerprints / word_count * 100) if word_count > 0 else 0
        details["fingerprint_density"] = density

        # Generate issues
        if type_a_matches:
            for match in type_a_matches:
                issues.append(self._create_issue(
                    issue_type="fingerprint_type_a",
                    description=f"Dead giveaway AI word '{match['word']}' found {match['count']} time(s)",
                    description_zh=f"明显AI特征词 '{match['word']}' 出现 {match['count']} 次",
                    severity=RiskLevel.HIGH,
                    suggestion=f"Replace '{match['word']}' with more natural alternatives",
                    suggestion_zh=f"用更自然的替代词替换 '{match['word']}'",
                    word=match["word"],
                    count=match["count"],
                ))

        if density > 2.0:
            issues.append(self._create_issue(
                issue_type="high_fingerprint_density",
                description=f"High AI fingerprint density ({density:.1f}%)",
                description_zh=f"AI指纹词密度高（{density:.1f}%）",
                severity=RiskLevel.HIGH if density > 3.0 else RiskLevel.MEDIUM,
                suggestion="Reduce usage of AI-characteristic vocabulary",
                suggestion_zh="减少AI特征词汇的使用",
                density=density,
            ))
            recommendations.append("Replace AI fingerprint words with simpler, more natural alternatives")
            recommendations_zh.append("用更简单、更自然的替代词替换AI指纹词")

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _analyze_connectors(self, context: LayerContext) -> Dict[str, Any]:
        """
        Step 5.2: Connector Analysis (consolidated)
        步骤 5.2：连接词分析（整合）

        Detects overuse of explicit connectors (AI pattern).
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        text = context.full_text.lower()

        # Count connector usage
        connector_matches = []
        total_connector_risk = 0

        for connector, risk in FINGERPRINT_TYPE_C_CONNECTORS.items():
            # Match as whole word/phrase
            pattern = r'\b' + re.escape(connector) + r'\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            count = len(matches)

            if count > 0:
                connector_matches.append({
                    "connector": connector,
                    "count": count,
                    "risk": risk,
                    "total_risk": count * risk,
                })
                total_connector_risk += count * risk

        # Sort by risk contribution
        connector_matches.sort(key=lambda x: x["total_risk"], reverse=True)

        details["connector_matches"] = connector_matches
        details["total_connector_count"] = sum(m["count"] for m in connector_matches)
        details["total_connector_risk"] = total_connector_risk

        # Analyze by sentence position
        sentences = context.sentences if context.sentences else re.split(r'[.!?]+', context.full_text)
        sentence_start_connectors = 0

        for sentence in sentences:
            sentence_lower = sentence.strip().lower()
            for connector in FINGERPRINT_TYPE_C_CONNECTORS.keys():
                if sentence_lower.startswith(connector):
                    sentence_start_connectors += 1
                    break

        details["sentence_start_connector_count"] = sentence_start_connectors
        details["sentence_start_connector_ratio"] = sentence_start_connectors / len(sentences) if sentences else 0

        # Generate issues
        if details["sentence_start_connector_ratio"] > 0.2:
            issues.append(self._create_issue(
                issue_type="excessive_sentence_start_connectors",
                description=f"{details['sentence_start_connector_ratio']:.0%} of sentences start with explicit connectors",
                description_zh=f"{details['sentence_start_connector_ratio']:.0%} 的句子以显式连接词开头",
                severity=RiskLevel.HIGH if details["sentence_start_connector_ratio"] > 0.3 else RiskLevel.MEDIUM,
                suggestion="Remove explicit connectors; use lexical echo and implicit logical flow",
                suggestion_zh="移除显式连接词；使用词汇回声和隐式逻辑流",
                ratio=details["sentence_start_connector_ratio"],
            ))
            recommendations.append("Replace explicit connectors with implicit logical connections")
            recommendations_zh.append("用隐式逻辑连接替换显式连接词")

        # Flag top overused connectors
        for match in connector_matches[:3]:
            if match["count"] >= 3:
                issues.append(self._create_issue(
                    issue_type="connector_overuse",
                    description=f"Connector '{match['connector']}' overused ({match['count']} times)",
                    description_zh=f"连接词 '{match['connector']}' 使用过多（{match['count']} 次）",
                    severity=RiskLevel.MEDIUM,
                    suggestion=f"Reduce or replace '{match['connector']}'",
                    suggestion_zh=f"减少或替换 '{match['connector']}'",
                    connector=match["connector"],
                    count=match["count"],
                ))

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _calculate_word_level_risk(
        self,
        context: LayerContext,
        fingerprint_result: Dict[str, Any],
        connector_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 5.3: Word-Level Risk
        步骤 5.3：词级风险

        Calculate aggregate word-level risk and provide per-sentence breakdown.
        """
        issues: List[DetectionIssue] = []
        details: Dict[str, Any] = {}
        recommendations: List[str] = []
        recommendations_zh: List[str] = []

        # Calculate total lexical risk
        fingerprint_risk = 0
        for match in fingerprint_result["details"].get("type_a_matches", []):
            fingerprint_risk += match["count"] * match["risk"]
        for match in fingerprint_result["details"].get("type_b_matches", []):
            fingerprint_risk += match["count"] * match["risk"]
        for match in fingerprint_result["details"].get("phrase_matches", []):
            fingerprint_risk += match["count"] * match["risk"]

        connector_risk = connector_result["details"].get("total_connector_risk", 0)

        total_lexical_risk = fingerprint_risk + connector_risk

        # Normalize to 0-100 scale
        word_count = len(context.full_text.split())
        normalized_risk = min(100, (total_lexical_risk / max(word_count, 100)) * 10)

        details["fingerprint_risk"] = fingerprint_risk
        details["connector_risk"] = connector_risk
        details["total_lexical_risk"] = total_lexical_risk
        details["normalized_risk"] = normalized_risk
        details["word_count"] = word_count

        # Create replacement map for flagged words
        replacement_suggestions = self._generate_replacement_suggestions(
            fingerprint_result["details"],
            connector_result["details"]
        )
        details["replacement_suggestions"] = replacement_suggestions

        if normalized_risk > 50:
            issues.append(self._create_issue(
                issue_type="high_lexical_risk",
                description=f"High word-level AIGC risk (score: {normalized_risk:.0f})",
                description_zh=f"词级AIGC风险高（分数：{normalized_risk:.0f}）",
                severity=RiskLevel.HIGH,
                suggestion="Replace flagged words and phrases with natural alternatives",
                suggestion_zh="用自然的替代词替换标记的词和短语",
                risk_score=normalized_risk,
            ))
            recommendations.append("Prioritize replacing Type A fingerprints and reducing connector usage")
            recommendations_zh.append("优先替换A类指纹词并减少连接词使用")

        return {
            "issues": issues,
            "details": details,
            "recommendations": recommendations,
            "recommendations_zh": recommendations_zh,
        }

    def _generate_replacement_suggestions(
        self,
        fingerprint_details: Dict[str, Any],
        connector_details: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate replacement suggestions for flagged words
        为标记的词生成替换建议
        """
        suggestions = {}

        # Replacement map for common fingerprints
        REPLACEMENT_MAP = {
            "delve": ["explore", "examine", "investigate", "look into"],
            "utilize": ["use", "apply", "employ"],
            "comprehensive": ["full", "complete", "thorough"],
            "facilitate": ["help", "enable", "support", "allow"],
            "leverage": ["use", "apply", "build on"],
            "robust": ["strong", "reliable", "solid"],
            "crucial": ["important", "key", "essential"],
            "pivotal": ["key", "central", "important"],
            "multifaceted": ["complex", "varied", "diverse"],
            "holistic": ["complete", "whole", "integrated"],
            "nuanced": ["subtle", "complex", "detailed"],
            "paramount": ["most important", "critical", "essential"],
            "furthermore": ["also", "and", ""],  # Empty = remove
            "moreover": ["also", "and", ""],
            "additionally": ["also", "and", ""],
            "subsequently": ["then", "later", "after"],
            "consequently": ["so", "as a result", "therefore"],
        }

        # Add suggestions for detected fingerprints
        for match in fingerprint_details.get("type_a_matches", []):
            word = match["word"].lower()
            if word in REPLACEMENT_MAP:
                suggestions[word] = REPLACEMENT_MAP[word]
            else:
                suggestions[word] = ["[find simpler alternative]"]

        for match in fingerprint_details.get("type_b_matches", []):
            word = match["word"].lower()
            if word in REPLACEMENT_MAP:
                suggestions[word] = REPLACEMENT_MAP[word]

        # Add suggestions for connectors
        for match in connector_details.get("connector_matches", [])[:5]:
            connector = match["connector"].lower()
            if connector in REPLACEMENT_MAP:
                suggestions[connector] = REPLACEMENT_MAP[connector]
            else:
                suggestions[connector] = ["[remove or use implicit connection]"]

        return suggestions

    def _calculate_layer_risk(
        self,
        fingerprint_result: Dict[str, Any],
        connector_result: Dict[str, Any],
        word_risk_result: Dict[str, Any]
    ) -> int:
        """
        Calculate overall risk score for lexical layer
        计算词汇层的整体风险分数
        """
        # Use the normalized risk from word_risk calculation
        normalized_risk = word_risk_result.get("details", {}).get("normalized_risk", 0)

        # Add issue penalties
        fingerprint_issues = len(fingerprint_result.get("issues", []))
        connector_issues = len(connector_result.get("issues", []))

        issue_penalty = min((fingerprint_issues + connector_issues) * 5, 30)

        return min(100, int(normalized_risk + issue_penalty))
