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
- STRICTLY FORBIDDEN: First-person pronouns (I, we, my, our, us, me)
- USE INSTEAD: "this study", "the present research", "the analysis", "the findings", passive voice
- Complex sentence structures with subordinate clauses
""",
        "academic_moderate": """
Style: Academic Moderate (Thesis Level)
- Use formal academic vocabulary
- STRICTLY FORBIDDEN: First-person pronouns (I, we, my, our, us, me)
- USE INSTEAD: "this research", "the current study", "the investigation", passive constructions
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
- STRICTLY FORBIDDEN: First-person pronouns (I, we, my, our, us, me)
- USE INSTEAD: "this paper", "the study", "the authors", passive voice
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

    # Threshold for strict pronoun prohibition (levels 0-5)
    # 严格禁止人称代词的阈值（0-5级）
    ACADEMIC_LEVEL_THRESHOLD = 5

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
        target_lang: str,
        is_paraphrase: bool = False
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

        # Add paraphrase instruction if needed
        paraphrase_instruction = ""
        if is_paraphrase:
            paraphrase_instruction = """
## PARAPHRASE PROTECTION (CRITICAL):
This sentence is a PARAPHRASE of cited work.
1. You MUST preserve the exact meaning (Semantic Similarity >= 0.95).
2. You MUST preserve the citation in its EXACT original format - NO format changes allowed.
   - "(Smith, 2020)" must stay as "(Smith, 2020)" - NOT "Smith (2020)"
   - "[1]" must stay as "[1]" - same position, same punctuation
3. Only make minor stylistic changes to reduce AI detection, do not rewrite structure completely.
4. If you cannot improve the sentence without changing the citation format, return the original sentence unchanged.
"""

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
{paraphrase_instruction}
## FIRST-PERSON PRONOUN RULES (CRITICAL FOR LEVEL 0-5):
If Colloquialism Level is 0-5 (academic writing):
- STRICTLY FORBIDDEN: I, we, my, our, us, me (all forms)
- USE INSTEAD: "this study", "this research", "the analysis", "the present investigation", "the findings"
- USE passive voice: "It was found that...", "The results indicate...", "X was observed..."
- USE impersonal subjects: "The data suggest...", "Evidence demonstrates...", "This approach enables..."
VIOLATION of this rule will result in REJECTION. Check your output before returning.

## CRITICAL DE-AIGC TECHNIQUES (Apply ALL that fit):

### 1. ELIMINATE AI Fingerprint Words (HIGH PRIORITY)
Replace: delve→explore/examine, crucial/paramount/pivotal→important/key, utilize→use, facilitate→help/enable, comprehensive→full/complete, multifaceted→complex, subsequently→then/after, realm→area/field, tapestry→mix, underscore→highlight, foster→encourage, nuanced→subtle, inextricably→closely

### 2. BREAK AI Sentence Templates
- "Not only X but also Y" → "X. Also, Y." or "Beyond X, Y."
- "It is crucial/important to" → "This requires" or "The X necessitates" (avoid "We must" for Level 0-5)
- "serves as a" → "acts as" or "is" or "forms"
- "In conclusion/summary" → "Ultimately" or "Findings suggest"

### 3. REMOVE Connector Word Overuse
AVOID starting with: Furthermore, Moreover, Additionally, Consequently, Therefore, Thus, Notably, Importantly
USE INSTEAD: semantic flow (This X..., Such Y..., The result...)

### 4. ADD Human Writing Markers
- Vary sentence length (mix short punchy + longer explanatory)
- Use specific numbers when possible (e.g., "35% increase" not "significant increase")
- For Level 6+: Use direct voice ("We found...")
- For Level 0-5: Use impersonal constructs ("This study found...", "The analysis reveals...", passive voice)
- Add slight hedging ("appears to", "suggests") or conviction ("clearly shows")

### 5. AVOID Vague Academic Padding
Remove: "complex dynamics", "intricate interplay", "evolving landscape", "holistic approach"
Replace with SPECIFIC descriptions of what actually happens

### 6. USE IMPLICIT LOGICAL CONNECTORS (隐性连接)
Instead of explicit connectors, use semantic echo or embedded structure:
- Instead of "Furthermore, X..." → "This pattern extends to X..." (echo previous concept)
- Instead of "However, Y..." → "Y, though, complicates this picture." (embed contrast)
- Instead of "Therefore, Z..." → "Such evidence points to Z." (implication as connector)

### 7. VARY SUBJECT ACROSS CONTEXT (主语多样性)
Avoid repeating the same subject. Transform:
- "The model... The model..." → "The model... This capability... Such precision..."
- "The study... The study..." → "The study... This analysis... The findings..."
- For Level 0-5: NEVER use first-person (I, we, my, our, us, me)
- Use impersonal alternatives: "This research demonstrates...", "The results indicate...", "Evidence suggests..."

### 8. APPLY ANI STRUCTURE IF REWRITING MULTIPLE SENTENCES (断言-细微-深意)
For complex rewrites, consider Assertion-Nuance-Implication:
- ASSERTION: Direct claim without hedging ("X fundamentally determines Y.")
- NUANCE: Acknowledge conditions/limits ("Yet this holds only under condition Z.")
- IMPLICATION: Deeper meaning ("The broader implication: ...")

### 9. VARY SENTENCE LENGTH FOR RHYTHM (节奏感)
Create rhythm through length variation:
- LONG (20-30 words): Build context, explain mechanism
- SHORT (8-12 words): Deliver punch, state key finding
- MEDIUM (15-20 words): Develop nuance, transition
Example rhythm: Long→Short→Medium creates human-like flow

### 10. BALANCE HEDGING AND CONVICTION (语气词策略)
Mix uncertainty and certainty markers for human-like balance:
- HEDGING (where uncertain): "may contribute", "appears to", "suggests that", "could potentially"
- CONVICTION (where data supports): "clearly demonstrates", "consistently shows", "definitively establishes"
- AVOID AI clichés: "It is important to note", "It should be noted that"
- Use hedging strategically: "Results clearly show X (p<0.01). Whether this extends to Y remains less certain."

### 11. INTENTIONAL IMPERFECTION (有意的不完美)
Human writers are NOT perfect. Add these human-like markers:
- Start 10-15% of sentences with conjunctions (And, But, So) for rhythm
- Use em-dashes (—) to insert abrupt thoughts: "X works—surprisingly well, actually—under Y."
- Allow slight grammatical looseness: "Which is why this matters." as standalone sentence
- Add conversational academic phrases: "frankly", "to put it simply", "interestingly enough"
- Avoid textbook perfection - mix structures irregularly
- Use sentence fragments for emphasis: "A significant finding. One that changes everything."

### 12. CITATION PRESERVATION (引用格式保护) - CRITICAL
Citations MUST remain in their EXACT original format. DO NOT modify:

- Parenthetical citations: "(Smith, 2023)", "(Johnson et al., 2019)" → KEEP AS-IS
- Numeric citations: "[1]", "[2,3]", "[1-5]" → KEEP AS-IS
- Citation position and punctuation → KEEP AS-IS

FORBIDDEN:
- Do NOT convert "(Smith, 2023)" to "Smith (2023)"
- Do NOT move citations to different positions
- Do NOT change citation punctuation or spacing
- Do NOT merge or split citations

ONLY rewrite the NON-CITATION parts of the sentence.

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
        target_lang: str = "zh",
        is_paraphrase: bool = False
    ) -> Optional[LLMSuggestionResult]:
        """
        Generate humanization suggestion using LLM
        使用LLM生成人源化建议

        Args:
            sentence: Original sentence
            issues: Detected issues
            locked_terms: Terms to protect
            target_lang: Target language for explanations
            is_paraphrase: Whether sentence is a paraphrase

        Returns:
            LLMSuggestionResult or None if failed
        """
        prompt = self._build_prompt(sentence, issues, locked_terms, target_lang, is_paraphrase)

        try:
            # Try to use configured LLM provider
            # 尝试使用配置的LLM提供商
            if settings.llm_provider == "volcengine" and settings.volcengine_api_key:
                # Volcengine (火山引擎) - faster DeepSeek access
                # 火山引擎 - 更快的 DeepSeek 访问
                response = await self._call_volcengine(prompt)
            elif settings.llm_provider == "gemini" and settings.gemini_api_key:
                response = await self._call_gemini(prompt)
            elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
                response = await self._call_deepseek(prompt)
            elif settings.llm_provider == "anthropic" and settings.anthropic_api_key:
                response = await self._call_anthropic(prompt)
            elif settings.llm_provider == "openai" and settings.openai_api_key:
                response = await self._call_openai(prompt)
            elif settings.volcengine_api_key:
                # Fallback to Volcengine if available (preferred)
                # 如果可用则回退到火山引擎（首选）
                response = await self._call_volcengine(prompt)
            elif settings.gemini_api_key:
                # Fallback to Gemini if available
                # 如果可用则回退到Gemini
                response = await self._call_gemini(prompt)
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

    async def _call_volcengine(self, prompt: str) -> str:
        """
        Call Volcengine (火山引擎) DeepSeek API - OpenAI compatible format
        调用火山引擎 DeepSeek API - OpenAI 兼容格式
        """
        try:
            import httpx

            async with httpx.AsyncClient(
                base_url=settings.volcengine_base_url,
                headers={
                    "Authorization": f"Bearer {settings.volcengine_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=120.0,  # 2 minutes timeout
                trust_env=False  # Ignore system proxy settings
            ) as client:
                response = await client.post("/chat/completions", json={
                    "model": settings.volcengine_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature
                })

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except ImportError:
            logger.error("httpx package not installed (required for Volcengine)")
            raise
        except Exception as e:
            logger.error(f"Volcengine API error: {e}")
            raise

    async def _call_deepseek(self, prompt: str) -> str:
        """
        Call DeepSeek API (OpenAI-compatible) - official, slower than Volcengine
        调用DeepSeek API（OpenAI兼容）- 官方，比火山引擎慢
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
                timeout=120.0,  # 2 minutes timeout
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

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Google Gemini API using google-genai library
        使用google-genai库调用Google Gemini API
        """
        try:
            from google import genai

            # Create client (will use GEMINI_API_KEY env var by default)
            # 创建客户端（默认使用GEMINI_API_KEY环境变量）
            client = genai.Client(api_key=settings.gemini_api_key)

            # Use async API for non-blocking call
            # 使用异步API进行非阻塞调用
            response = await client.aio.models.generate_content(
                model=settings.llm_model,
                contents=prompt,
                config={
                    "max_output_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature
                }
            )

            return response.text

        except ImportError:
            logger.error("google-genai package not installed (pip install google-genai)")
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
