"""
Term Extractor - LLM-based technical term extraction for term locking
术语提取器 - 基于LLM的技术术语提取，用于词汇锁定

Part of Layer 5 Step 1.0: Term Locking
第5层 步骤 1.0：词汇锁定
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TermType(str, Enum):
    """Types of extractable terms / 可提取的术语类型"""
    TECHNICAL_TERM = "technical_term"  # Domain-specific vocabulary / 专业术语
    PROPER_NOUN = "proper_noun"  # Names of people, places, methods / 专有名词
    ACRONYM = "acronym"  # Technical abbreviations / 缩写词
    KEY_PHRASE = "key_phrase"  # Fixed expressions / 关键词组
    CORE_WORD = "core_word"  # High-frequency meaningful words / 高频核心词


@dataclass
class ExtractedTerm:
    """
    Represents an extracted term candidate for locking
    表示一个待锁定的术语候选项
    """
    term: str
    term_type: TermType
    frequency: int
    reason: str
    reason_zh: str
    recommended: bool = True  # Whether recommended for locking / 是否推荐锁定


@dataclass
class TermExtractionResult:
    """
    Result of term extraction
    术语提取结果
    """
    extracted_terms: List[ExtractedTerm] = field(default_factory=list)
    total_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    processing_time_ms: int = 0


class TermExtractor:
    """
    LLM-based term extractor for Step 1.0 Term Locking
    基于LLM的术语提取器，用于步骤1.0词汇锁定

    Extracts:
    - Technical terms (domain-specific vocabulary)
    - Proper nouns (names, places, methods)
    - Acronyms (technical abbreviations)
    - Key phrases (fixed expressions)
    - High-frequency core words
    """

    EXTRACTION_PROMPT = """You are an academic term extractor. Analyze the following document and extract terms that should be protected (not modified) during text rewriting.

## Document Text:
{document_text}

## Extract the following types of terms:

1. **TECHNICAL TERMS**: Domain-specific vocabulary that should not be changed
   - Scientific/technical concepts, methodology names, theoretical frameworks
   - Example: "machine learning", "neural network", "regression analysis"

2. **PROPER NOUNS**: Names that must remain unchanged
   - Author names with citations, place names, organization names, method/model names
   - Example: "Smith et al.", "AlphaFold", "North China Plain", "BERT"

3. **ACRONYMS**: Technical abbreviations
   - Must appear with definition or be well-known in the field
   - Example: "CNN", "LSTM", "PCR", "ANOVA", "GDP"

4. **KEY PHRASES**: Important fixed expressions
   - Multi-word technical terms, compound concepts
   - Example: "soil salinization", "feature extraction", "cross-validation"

5. **HIGH-FREQUENCY CORE WORDS**: Words appearing 3+ times that carry core meaning
   - Central concepts of the document that should remain consistent
   - NOT common words like "study", "results", "data", "method"

## Rules:
- Only extract terms that appear in the document
- Count actual frequency (how many times each term appears)
- Set recommended=true for terms that should definitely be locked
- Set recommended=false for borderline cases the user might want to skip
- Exclude common academic words (study, research, results, data, analysis, method, approach, etc.)
- Include citation formats exactly as they appear (e.g., "(Smith, 2020)", "[1]")

## Response (JSON only, no markdown code blocks):
{{
  "extracted_terms": [
    {{
      "term": "exact term as it appears",
      "term_type": "technical_term|proper_noun|acronym|key_phrase|core_word",
      "frequency": 5,
      "reason": "Why this should be locked",
      "reason_zh": "锁定原因（中文）",
      "recommended": true
    }}
  ]
}}"""

    def __init__(self):
        """Initialize the term extractor"""
        pass

    async def extract_terms(self, document_text: str) -> TermExtractionResult:
        """
        Extract terms from document using LLM
        使用LLM从文档中提取术语

        Args:
            document_text: Full document text

        Returns:
            TermExtractionResult with extracted terms
        """
        import time
        start_time = time.time()

        try:
            # Build prompt
            prompt = self.EXTRACTION_PROMPT.format(
                document_text=document_text[:8000]  # Limit text length for LLM
            )

            # Call LLM
            response = await self._call_llm(prompt)

            # Parse response
            result = self._parse_response(response)

            # Calculate processing time
            result.processing_time_ms = int((time.time() - start_time) * 1000)

            return result

        except Exception as e:
            logger.error(f"Term extraction failed: {e}")
            # Return fallback result with basic extraction
            return self._fallback_extraction(document_text)

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API for term extraction
        调用LLM API进行术语提取
        """
        try:
            # Use the same LLM calling logic as llm_track.py
            if settings.llm_provider == "volcengine" and settings.volcengine_api_key:
                return await self._call_volcengine(prompt)
            elif settings.llm_provider == "dashscope" and settings.dashscope_api_key:
                return await self._call_dashscope(prompt)
            elif settings.llm_provider == "gemini" and settings.gemini_api_key:
                return await self._call_gemini(prompt)
            elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
                return await self._call_deepseek(prompt)
            elif settings.llm_provider == "anthropic" and settings.anthropic_api_key:
                return await self._call_anthropic(prompt)
            elif settings.llm_provider == "openai" and settings.openai_api_key:
                return await self._call_openai(prompt)
            # Fallback chain
            elif settings.volcengine_api_key:
                return await self._call_volcengine(prompt)
            elif settings.dashscope_api_key:
                return await self._call_dashscope(prompt)
            elif settings.gemini_api_key:
                return await self._call_gemini(prompt)
            elif settings.deepseek_api_key:
                return await self._call_deepseek(prompt)
            else:
                raise ValueError("No LLM API configured")

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _call_volcengine(self, prompt: str) -> str:
        """Call Volcengine DeepSeek API"""
        import httpx

        async with httpx.AsyncClient(
            base_url=settings.volcengine_base_url,
            headers={
                "Authorization": f"Bearer {settings.volcengine_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3  # Lower temperature for more consistent extraction
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_dashscope(self, prompt: str) -> str:
        """Call DashScope (Aliyun) API"""
        import httpx

        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url,
            headers={
                "Authorization": f"Bearer {settings.dashscope_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.dashscope_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config={
                "max_output_tokens": 4096,
                "temperature": 0.3
            }
        )
        return response.text

    async def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API"""
        import httpx

        async with httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        message = await client.messages.create(
            model=settings.llm_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str) -> TermExtractionResult:
        """
        Parse LLM response to TermExtractionResult
        解析LLM响应为TermExtractionResult
        """
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            data = json.loads(response)

            extracted_terms = []
            by_type: Dict[str, int] = {}

            for item in data.get("extracted_terms", []):
                term_type_str = item.get("term_type", "core_word")
                try:
                    term_type = TermType(term_type_str)
                except ValueError:
                    term_type = TermType.CORE_WORD

                term = ExtractedTerm(
                    term=item.get("term", ""),
                    term_type=term_type,
                    frequency=item.get("frequency", 1),
                    reason=item.get("reason", ""),
                    reason_zh=item.get("reason_zh", ""),
                    recommended=item.get("recommended", True)
                )
                extracted_terms.append(term)

                # Count by type
                type_key = term_type.value
                by_type[type_key] = by_type.get(type_key, 0) + 1

            return TermExtractionResult(
                extracted_terms=extracted_terms,
                total_count=len(extracted_terms),
                by_type=by_type
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return TermExtractionResult()
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            return TermExtractionResult()

    def _fallback_extraction(self, document_text: str) -> TermExtractionResult:
        """
        Fallback extraction using rule-based methods when LLM fails
        LLM失败时使用基于规则的备用提取方法
        """
        extracted_terms = []

        # Extract acronyms (2-5 uppercase letters)
        acronyms = re.findall(r'\b[A-Z]{2,5}\b', document_text)
        acronym_counts = {}
        for acr in acronyms:
            acronym_counts[acr] = acronym_counts.get(acr, 0) + 1

        for acr, count in acronym_counts.items():
            if count >= 2:  # At least 2 occurrences
                extracted_terms.append(ExtractedTerm(
                    term=acr,
                    term_type=TermType.ACRONYM,
                    frequency=count,
                    reason="Frequently used acronym",
                    reason_zh="高频缩写词",
                    recommended=True
                ))

        # Extract citation patterns
        # Parenthetical citations: (Author, Year)
        citations = re.findall(r'\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\)', document_text)
        for cit in set(citations):
            extracted_terms.append(ExtractedTerm(
                term=cit,
                term_type=TermType.PROPER_NOUN,
                frequency=citations.count(cit),
                reason="Citation reference",
                reason_zh="引用文献",
                recommended=True
            ))

        # Numeric citations: [1], [2,3]
        num_citations = re.findall(r'\[\d+(?:[,\-–]\s*\d+)*\]', document_text)
        for cit in set(num_citations):
            extracted_terms.append(ExtractedTerm(
                term=cit,
                term_type=TermType.PROPER_NOUN,
                frequency=num_citations.count(cit),
                reason="Numeric citation",
                reason_zh="数字引用",
                recommended=True
            ))

        # Count by type
        by_type: Dict[str, int] = {}
        for term in extracted_terms:
            type_key = term.term_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        return TermExtractionResult(
            extracted_terms=extracted_terms,
            total_count=len(extracted_terms),
            by_type=by_type
        )


# Convenience function
async def extract_document_terms(document_text: str) -> TermExtractionResult:
    """
    Extract terms from document
    从文档中提取术语
    """
    extractor = TermExtractor()
    return await extractor.extract_terms(document_text)
