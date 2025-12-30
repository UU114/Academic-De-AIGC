"""
LLM-based suggestion track (Track A)
基于LLM的建议轨道（轨道A）
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.config import get_settings, ColloquialismConfig

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Change:
    """Represents a single change made"""
    original: str
    replacement: str
    reason: str
    reason_zh: str


@dataclass
class LLMSuggestionResult:
    """Result from LLM suggestion generation"""
    rewritten: str
    changes: List[Change] = field(default_factory=list)
    predicted_risk: int = 50
    semantic_similarity: float = 0.9
    explanation: str = ""
    explanation_zh: str = ""


class LLMTrack:
    """
    LLM-powered humanization suggestion engine (Track A)
    基于LLM的人源化建议引擎（轨道A）

    Uses Claude/GPT-4 to generate contextually appropriate
    humanization suggestions based on:
    - Detected AIGC issues
    - Target colloquialism level
    - Protected terms
    """

    # Style guides for different colloquialism levels
    # 不同口语化等级的风格指南
    STYLE_GUIDES = {
        "academic_strict": """
Style: Most Academic (Journal Paper Level)
- Use formal academic register exclusively
- Prefer Latinate vocabulary (utilize, demonstrate, indicate)
- Use passive voice where appropriate
- Avoid contractions entirely (do not, cannot, will not)
- Use hedging language (it appears that, evidence suggests)
- Maintain impersonal tone (avoid "I/we" when possible)
- Complex sentence structures with subordinate clauses
""",
        "academic_moderate": """
Style: Academic Moderate (Thesis Level)
- Use formal academic vocabulary
- First person plural acceptable (we found, our results)
- Avoid contractions in main text
- Balance passive and active voice
- Clear but sophisticated sentence structures
- Some hedging appropriate (suggests, appears to)
""",
        "semi_formal": """
Style: Semi-formal (Conference Paper Level)
- Mix of academic and common vocabulary
- Contractions acceptable occasionally (don't, isn't)
- Prefer active voice for clarity
- Varied sentence length (short and medium)
- Direct statements preferred over hedging
- First person acceptable throughout
""",
        "casual_professional": """
Style: Casual Professional (Tech Blog Level)
- Prefer common everyday words over academic jargon
- Contractions encouraged (we've, that's, won't)
- Active voice strongly preferred
- Short, punchy sentences
- Conversational but professional tone
- Direct engagement with reader acceptable
""",
        "casual_informal": """
Style: Casual Informal (Discussion Level)
- Use everyday conversational language
- Contractions always preferred
- Informal expressions acceptable (kind of, a lot, pretty much)
- Very short sentences, even fragments okay
- Rhetorical questions acceptable
- Colloquialisms and mild slang okay
"""
    }

    # Word preferences by level
    # 按等级的词汇偏好
    WORD_PREFERENCES = {
        (0, 2): {
            "utilize": "utilize", "demonstrate": "demonstrate",
            "subsequently": "subsequently", "numerous": "numerous",
            "commence": "commence", "regarding": "regarding"
        },
        (3, 4): {
            "utilize": "use", "demonstrate": "show",
            "subsequently": "then", "numerous": "many",
            "commence": "begin", "regarding": "concerning"
        },
        (5, 6): {
            "utilize": "use", "demonstrate": "show",
            "subsequently": "then", "numerous": "many",
            "commence": "start", "regarding": "about"
        },
        (7, 10): {
            "utilize": "use", "demonstrate": "show",
            "subsequently": "after that", "numerous": "a lot of",
            "commence": "start", "regarding": "about"
        }
    }

    def __init__(self, colloquialism_level: int = 4):
        """
        Initialize LLM track

        Args:
            colloquialism_level: Target formality level (0-10)
        """
        self.level = colloquialism_level
        self.style_guide = self._get_style_guide()
        self.word_preferences = self._get_word_preferences()

    def _get_style_guide(self) -> str:
        """Get style guide for current level"""
        level_range = ColloquialismConfig.get_level_range(self.level)
        return self.STYLE_GUIDES.get(level_range, self.STYLE_GUIDES["academic_moderate"])

    def _get_word_preferences(self) -> Dict[str, str]:
        """Get word preferences for current level"""
        for level_range, prefs in self.WORD_PREFERENCES.items():
            if level_range[0] <= self.level <= level_range[1]:
                return prefs
        return self.WORD_PREFERENCES[(3, 4)]

    def _build_prompt(
        self,
        sentence: str,
        issues: List[Dict[str, Any]],
        locked_terms: List[str],
        target_lang: str
    ) -> str:
        """
        Build the prompt for LLM
        构建LLM的提示词
        """
        # Format issues
        # 格式化问题
        issues_text = "\n".join([
            f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
            for issue in issues
        ]) if issues else "No specific issues detected"

        # Format word preferences
        # 格式化词汇偏好
        prefs_text = "\n".join([
            f"  • '{formal}' → '{preferred}'"
            for formal, preferred in self.word_preferences.items()
        ])

        prompt = f"""## TASK: REWRITE to pass AI detection (lower perplexity uniformity)

You are an expert at making AI-generated text appear human-written. REWRITE this sentence to PASS AI detectors like GPTZero and Turnitin.

## Original Sentence
{sentence}

## Detected Issues
{issues_text}

## Protected Terms (KEEP UNCHANGED)
{', '.join(locked_terms) if locked_terms else 'None'}

## Colloquialism Level: {self.level}/10
{self.style_guide}

## CRITICAL DE-AIGC TECHNIQUES (Apply ALL that fit):

### 1. ELIMINATE AI Fingerprint Words (HIGH PRIORITY)
Replace: delve→explore/examine, crucial/paramount/pivotal→important/key, utilize→use, facilitate→help/enable, comprehensive→full/complete, multifaceted→complex, subsequently→then/after, realm→area/field, tapestry→mix, underscore→highlight, foster→encourage, nuanced→subtle, inextricably→closely

### 2. BREAK AI Sentence Templates
- "Not only X but also Y" → "X. Also, Y." or "Beyond X, Y."
- "It is crucial/important to" → "We must" or "The X requires"
- "serves as a" → "acts as" or "is" or "forms"
- "In conclusion/summary" → "Ultimately" or "Findings suggest"

### 3. REMOVE Connector Word Overuse
AVOID starting with: Furthermore, Moreover, Additionally, Consequently, Therefore, Thus, Notably, Importantly
USE INSTEAD: semantic flow (This X..., Such Y..., The result...)

### 4. ADD Human Writing Markers
- Vary sentence length (mix short punchy + longer explanatory)
- Use specific numbers when possible (e.g., "35% increase" not "significant increase")
- Use direct voice over passive ("We found" not "It was found")
- Add slight hedging ("appears to", "suggests") or conviction ("clearly shows")

### 5. AVOID Vague Academic Padding
Remove: "complex dynamics", "intricate interplay", "evolving landscape", "holistic approach"
Replace with SPECIFIC descriptions of what actually happens

## Response (JSON ONLY, no markdown):
{{
  "rewritten": "the rewritten sentence applying above techniques",
  "changes": [
    {{"original": "word/phrase", "replacement": "new", "reason": "technique used", "reason_zh": "使用的技巧"}}
  ],
  "explanation": "Techniques applied",
  "explanation_zh": "应用的技巧",
  "risk_reduction": "high/medium/low"
}}"""

        return prompt

    async def generate_suggestion(
        self,
        sentence: str,
        issues: List[Dict[str, Any]],
        locked_terms: List[str],
        target_lang: str = "zh"
    ) -> Optional[LLMSuggestionResult]:
        """
        Generate humanization suggestion using LLM
        使用LLM生成人源化建议

        Args:
            sentence: Original sentence
            issues: Detected issues
            locked_terms: Terms to protect
            target_lang: Target language for explanations

        Returns:
            LLMSuggestionResult or None if failed
        """
        prompt = self._build_prompt(sentence, issues, locked_terms, target_lang)

        try:
            # Try to use configured LLM provider
            # 尝试使用配置的LLM提供商
            if settings.llm_provider == "deepseek" and settings.deepseek_api_key:
                response = await self._call_deepseek(prompt)
            elif settings.llm_provider == "anthropic" and settings.anthropic_api_key:
                response = await self._call_anthropic(prompt)
            elif settings.llm_provider == "openai" and settings.openai_api_key:
                response = await self._call_openai(prompt)
            elif settings.deepseek_api_key:
                # Fallback to DeepSeek if available
                # 如果可用则回退到DeepSeek
                response = await self._call_deepseek(prompt)
            else:
                # Fallback to rule-based simulation for MVP
                # MVP阶段回退到基于规则的模拟
                logger.warning("No LLM API configured, using fallback")
                return self._fallback_suggestion(sentence, issues, locked_terms)

            # Parse response
            # 解析响应
            return self._parse_response(response, sentence)

        except Exception as e:
            logger.error(f"LLM suggestion generation failed: {e}")
            return self._fallback_suggestion(sentence, issues, locked_terms)

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

            message = await client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text
        except ImportError:
            logger.error("anthropic package not installed")
            raise
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature
            )

            return response.choices[0].message.content
        except ImportError:
            logger.error("openai package not installed")
            raise
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _call_deepseek(self, prompt: str) -> str:
        """
        Call DeepSeek API (OpenAI-compatible)
        调用DeepSeek API（OpenAI兼容）
        """
        try:
            import httpx

            # Use httpx directly to avoid proxy issues
            # 直接使用httpx以避免代理问题
            async with httpx.AsyncClient(
                base_url=settings.deepseek_base_url,
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=90.0,
                trust_env=False  # Ignore system proxy settings
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature
                })

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except ImportError:
            logger.error("httpx package not installed (required for DeepSeek)")
            raise
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise

    def _parse_response(self, response: str, original: str) -> Optional[LLMSuggestionResult]:
        """
        Parse LLM response JSON
        解析LLM响应JSON
        """
        try:
            # Clean response (remove markdown code blocks if present)
            # 清理响应（如果存在则移除markdown代码块）
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            data = json.loads(response)

            changes = [
                Change(
                    original=c.get("original", ""),
                    replacement=c.get("replacement", ""),
                    reason=c.get("reason", ""),
                    reason_zh=c.get("reason_zh", "")
                )
                for c in data.get("changes", [])
            ]

            # Estimate risk reduction
            # 估计风险降低
            risk_reduction = data.get("risk_reduction", "medium")
            predicted_risk = {
                "high": 25,
                "medium": 40,
                "low": 55
            }.get(risk_reduction, 40)

            # Calculate semantic similarity (simplified)
            # 计算语义相似度（简化版）
            rewritten = data.get("rewritten", original)
            similarity = self._estimate_similarity(original, rewritten)

            return LLMSuggestionResult(
                rewritten=rewritten,
                changes=changes,
                predicted_risk=predicted_risk,
                semantic_similarity=similarity,
                explanation=data.get("explanation", ""),
                explanation_zh=data.get("explanation_zh", "")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            return None

    def _estimate_similarity(self, original: str, rewritten: str) -> float:
        """
        Estimate semantic similarity (simplified)
        估计语义相似度（简化版）

        Production should use Sentence-BERT
        生产环境应使用Sentence-BERT
        """
        # Simple word overlap ratio
        # 简单的词重叠比例
        orig_words = set(original.lower().split())
        new_words = set(rewritten.lower().split())

        if not orig_words:
            return 1.0

        overlap = len(orig_words & new_words)
        similarity = overlap / len(orig_words)

        # Adjust for length difference
        # 调整长度差异
        len_ratio = min(len(rewritten), len(original)) / max(len(rewritten), len(original))

        return min(1.0, (similarity + len_ratio) / 2 + 0.3)

    def _fallback_suggestion(
        self,
        sentence: str,
        issues: List[Dict[str, Any]],
        locked_terms: List[str]
    ) -> LLMSuggestionResult:
        """
        Fallback suggestion when LLM is unavailable
        LLM不可用时的备用建议
        """
        # Simple word replacement based on preferences
        # 基于偏好的简单词替换
        rewritten = sentence
        changes = []

        # Common AI fingerprint replacements
        # 常见AI指纹替换
        replacements = {
            "delve": "explore",
            "delves": "explores",
            "crucial": "important",
            "paramount": "key",
            "utilize": "use",
            "utilizes": "uses",
            "utilizing": "using",
            "comprehensive": "full",
            "subsequently": "then",
            "facilitate": "help",
            "facilitates": "helps",
        }

        for old, new in replacements.items():
            if old.lower() in rewritten.lower():
                # Check if not in locked terms
                # 检查是否不在锁定术语中
                if not any(old.lower() in term.lower() for term in locked_terms):
                    import re
                    pattern = re.compile(re.escape(old), re.IGNORECASE)
                    rewritten = pattern.sub(new, rewritten)
                    changes.append(Change(
                        original=old,
                        replacement=new,
                        reason="AI fingerprint word replacement",
                        reason_zh="AI指纹词替换"
                    ))

        return LLMSuggestionResult(
            rewritten=rewritten,
            changes=changes,
            predicted_risk=50,
            semantic_similarity=0.95,
            explanation="Basic fingerprint word replacements applied",
            explanation_zh="应用了基本的指纹词替换"
        )
