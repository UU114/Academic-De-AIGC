"""
Base Substep Handler
基础子步骤处理器

Provides common functionality for all substeps:
- LLM calling
- JSON parsing
- Locked terms protection
- Standard response formatting

为所有子步骤提供通用功能：
- LLM调用
- JSON解析
- 锁定词保护
- 标准响应格式化
"""

import json
import logging
import httpx
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from src.config import get_settings

logger = logging.getLogger(__name__)


class BaseSubstepHandler(ABC):
    """
    Base class for all substep handlers
    所有子步骤处理器的基类

    Each substep should inherit from this and implement:
    - get_analysis_prompt() - Returns analysis prompt template
    - get_rewrite_prompt() - Returns rewrite prompt template
    """

    def __init__(self):
        """Initialize the handler"""
        self.settings = get_settings()

    # ==========================================================================
    # Section Detection Helper (for chain-call pattern)
    # 章节检测辅助方法（用于链式调用模式）
    # ==========================================================================

    SECTION_DETECTION_PROMPT = """Analyze the document and identify its logical sections.

## DOCUMENT TEXT:
{document_text}

## YOUR TASK:
Identify section boundaries based on:
- Explicit headers (e.g., "Introduction", "Methods", "1.", "2.")
- Topic shifts between paragraphs
- Structural markers (transition words, conclusion phrases)

For each section, determine:
- role: introduction|background|literature_review|method|methodology|results|discussion|conclusion|body|abstract
- title: The section's explicit title or a brief descriptive title
- start_paragraph: 0-indexed paragraph number where section starts
- end_paragraph: 0-indexed paragraph number where section ends (inclusive)
- paragraph_count: Number of paragraphs in this section
- word_count: Approximate word count for this section

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "sections": [
    {{
      "index": 0,
      "role": "introduction",
      "title": "Introduction",
      "start_paragraph": 0,
      "end_paragraph": 1,
      "paragraph_count": 2,
      "word_count": 150
    }}
  ]
}}
"""

    async def detect_sections(
        self,
        document_text: str,
        session_id: str = None,
        use_cache: bool = True
    ) -> list:
        """
        Detect sections in document using LLM (chain-call helper)
        使用LLM检测文档中的章节（链式调用辅助方法）

        This method can be called by substeps that need section data.
        此方法可被需要章节数据的子步骤调用。

        Args:
            document_text: Document text to analyze
            session_id: Session ID for caching
            use_cache: Whether to use cached sections

        Returns:
            List of section dictionaries with role, title, paragraph_count, etc.
        """
        # Check cache first
        # 先检查缓存
        cache_key = "sections-detection"
        if use_cache and session_id:
            cached_result = await self._load_from_cache(session_id, cache_key)
            if cached_result and cached_result.get("sections"):
                logger.info(f"Using cached sections for session {session_id}")
                return cached_result.get("sections", [])

        # Build prompt
        prompt = self.SECTION_DETECTION_PROMPT.format(
            document_text=document_text[:8000]  # Limit for section detection
        )

        # Call LLM with low temperature for consistency
        logger.info("Detecting sections via LLM chain-call")
        response_text = await self._call_llm(prompt, max_tokens=2048, temperature=0.2)

        # Parse response
        result = self._parse_json_response(response_text)
        sections = result.get("sections", [])

        # Cache the result
        if use_cache and session_id and sections:
            await self._save_to_cache(session_id, cache_key, {"sections": sections}, status="completed")
            logger.info(f"Cached {len(sections)} sections for session {session_id}")

        return sections

    @abstractmethod
    def get_analysis_prompt(self) -> str:
        """
        Return the analysis prompt template for this substep
        返回此子步骤的分析prompt模板

        Should contain placeholders: {document_text}, {locked_terms}, etc.
        """
        pass

    @abstractmethod
    def get_rewrite_prompt(self) -> str:
        """
        Return the rewrite prompt template for this substep
        返回此子步骤的改写prompt模板

        Should contain placeholders: {document_text}, {selected_issues}, {user_notes}, {locked_terms}, etc.
        """
        pass

    async def analyze(
        self,
        document_text: str,
        locked_terms: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        step_name: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run LLM analysis for this substep with caching support
        运行此子步骤的LLM分析（支持缓存）

        Args:
            document_text: Document text to analyze
            locked_terms: Terms to protect (from Step 1.0)
            session_id: Session ID for caching
            step_name: Step name (e.g., "layer5-step1-1") for caching
            use_cache: Whether to use cache (default: True)
            **kwargs: Additional parameters for specific substeps

        Returns:
            Parsed JSON response with issues, risk_score, recommendations
        """
        # Check cache if session_id and step_name provided
        # 如果提供了 session_id 和 step_name，检查缓存
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Build locked terms string
        locked_terms = locked_terms or []
        locked_terms_str = "\n".join(f"- {term}" for term in locked_terms) if locked_terms else "None"

        # Get analysis prompt template
        prompt_template = self.get_analysis_prompt()

        # Prepare template parameters
        # 准备模板参数
        template_params = {
            "document_text": document_text[:10000],  # Limit text length
            "locked_terms": locked_terms_str,
            **kwargs
        }

        # Add paragraph_count_minus_1 if paragraph_count is provided
        # 如果提供了paragraph_count，添加paragraph_count_minus_1
        if "paragraph_count" in template_params:
            template_params["paragraph_count_minus_1"] = template_params["paragraph_count"] - 1

        # Fill in placeholders
        prompt = prompt_template.format(**template_params)

        # Call LLM with higher max_tokens for analysis (sentence-level needs more space)
        # 使用更高的 max_tokens 进行分析（句子级别需要更多空间）
        logger.info(f"Calling LLM for analysis (step: {step_name})")
        response_text = await self._call_llm(prompt, max_tokens=8192, temperature=0.3)

        # Parse JSON response
        result = self._parse_json_response(response_text)

        # Save to cache if session_id and step_name provided
        # 如果提供了 session_id 和 step_name，保存到缓存
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")
            logger.info(f"Saved analysis result to cache for {step_name}")

        return result

    async def generate_rewrite_prompt(
        self,
        document_text: str,
        selected_issues: List[Dict[str, Any]],
        user_notes: Optional[str] = None,
        locked_terms: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a prompt for user to copy (for use with other AI tools)
        生成供用户复制的prompt（用于其他AI工具）

        Args:
            document_text: Original document text
            selected_issues: List of selected issues to fix
            user_notes: User's additional guidance
            locked_terms: Terms to protect
            **kwargs: Additional parameters

        Returns:
            Dict with 'prompt' and 'prompt_zh'
        """
        # Build locked terms string
        locked_terms = locked_terms or []
        locked_terms_str = "\n".join(f"- {term}" for term in locked_terms) if locked_terms else "None"

        # Build issues list
        issues_list = self._format_issues_list(selected_issues)

        # Get rewrite prompt template
        prompt_template = self.get_rewrite_prompt()

        # Fill in placeholders
        prompt = prompt_template.format(
            document_text=document_text,
            selected_issues=issues_list,
            user_notes=user_notes or "No additional notes",
            locked_terms=locked_terms_str,
            **kwargs
        )

        # For generate_rewrite_prompt, we just return the prompt itself
        # User can copy it to use elsewhere
        return {
            "prompt": prompt,
            "prompt_zh": f"已生成修改提示词，包含 {len(selected_issues)} 个问题的修复指导",
            "issues_summary_zh": f"选择了 {len(selected_issues)} 个问题进行修复",
            "estimated_changes": len(selected_issues)
        }

    async def apply_rewrite(
        self,
        document_text: str,
        selected_issues: List[Dict[str, Any]],
        user_notes: Optional[str] = None,
        locked_terms: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply AI modification directly
        直接应用AI修改

        Args:
            document_text: Original document text
            selected_issues: List of selected issues to fix
            user_notes: User's additional guidance
            locked_terms: Terms to protect
            **kwargs: Additional parameters

        Returns:
            Dict with 'modified_text', 'changes_summary_zh', 'issues_addressed'
        """
        # Build locked terms string
        locked_terms = locked_terms or []
        locked_terms_str = "\n".join(f"- {term}" for term in locked_terms) if locked_terms else "None"

        # Build issues list
        issues_list = self._format_issues_list(selected_issues)

        # Get rewrite prompt template
        prompt_template = self.get_rewrite_prompt()

        # Fill in placeholders
        prompt = prompt_template.format(
            document_text=document_text,
            selected_issues=issues_list,
            user_notes=user_notes or "No additional notes",
            locked_terms=locked_terms_str,
            **kwargs
        )

        # Call LLM for rewriting (higher max_tokens for full document)
        response_text = await self._call_llm(prompt, max_tokens=8192, temperature=0.5)

        # Parse JSON response
        result = self._parse_json_response(response_text)

        # Validate response has required fields
        if "modified_text" not in result:
            raise ValueError("LLM response missing 'modified_text' field")

        # Verify locked terms are preserved
        preserved = self._verify_locked_terms_preserved(
            document_text, result["modified_text"], locked_terms
        )

        if not preserved:
            logger.warning("Some locked terms may have been lost during rewrite")

        return {
            "modified_text": result.get("modified_text", document_text),
            "changes_summary_zh": result.get("changes_summary_zh", "修改完成"),
            "changes_count": result.get("changes_count", len(selected_issues)),
            "issues_addressed": result.get("issues_addressed", [issue["type"] for issue in selected_issues]),
            "remaining_attempts": 3,
            "locked_terms_preserved": preserved
        }

    # =========================================================================
    # Helper Methods
    # 辅助方法
    # =========================================================================

    def _format_issues_list(self, selected_issues: List[Dict[str, Any]]) -> str:
        """Format selected issues into a readable list"""
        issues_list = ""
        for i, issue in enumerate(selected_issues, 1):
            desc_zh = issue.get("description_zh", issue.get("description", ""))
            desc_en = issue.get("description", desc_zh)
            severity = issue.get("severity", "medium").upper()

            issues_list += f"{i}. [{severity}] {desc_en}\n"
            if desc_zh != desc_en:
                issues_list += f"   中文: {desc_zh}\n"

            affected = issue.get("affected_positions", [])
            if affected:
                issues_list += f"   Affected positions: {', '.join(affected)}\n"

            issues_list += "\n"

        return issues_list.strip()

    def _verify_locked_terms_preserved(
        self,
        original_text: str,
        modified_text: str,
        locked_terms: List[str]
    ) -> bool:
        """
        Verify all locked terms are preserved in modified text
        验证所有锁定词在修改后的文本中被保留
        """
        for term in locked_terms:
            # Case-insensitive check
            if term.lower() in original_text.lower():
                if term.lower() not in modified_text.lower():
                    logger.warning(f"Locked term '{term}' may have been lost")
                    return False
        return True

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> str:
        """
        Call LLM API
        调用LLM API

        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            LLM response text
        """
        try:
            # Determine provider and call appropriate API
            if self.settings.llm_provider == "volcengine" and self.settings.volcengine_api_key:
                return await self._call_volcengine(prompt, max_tokens, temperature)
            elif self.settings.llm_provider == "dashscope" and self.settings.dashscope_api_key:
                return await self._call_dashscope(prompt, max_tokens, temperature)
            elif self.settings.llm_provider == "deepseek" and self.settings.deepseek_api_key:
                return await self._call_deepseek(prompt, max_tokens, temperature)
            elif self.settings.llm_provider == "gemini" and self.settings.gemini_api_key:
                return await self._call_gemini(prompt, max_tokens, temperature)
            # Fallback chain
            elif self.settings.volcengine_api_key:
                return await self._call_volcengine(prompt, max_tokens, temperature)
            elif self.settings.dashscope_api_key:
                return await self._call_dashscope(prompt, max_tokens, temperature)
            else:
                raise ValueError("No LLM provider configured")

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _call_volcengine(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Volcengine API"""
        async with httpx.AsyncClient(
            base_url=self.settings.volcengine_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.volcengine_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": self.settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_dashscope(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call DashScope API"""
        async with httpx.AsyncClient(
            base_url=self.settings.dashscope_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.dashscope_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": self.settings.dashscope_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_deepseek(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call DeepSeek API"""
        async with httpx.AsyncClient(
            base_url=self.settings.deepseek_base_url or "https://api.deepseek.com",
            headers={
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0,
            trust_env=False
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": self.settings.deepseek_model or "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call Google Gemini API"""
        from google import genai

        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=self.settings.llm_model,
            contents=prompt,
            config={
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }
        )
        return response.text

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response
        从LLM响应中解析JSON

        Handles cases where LLM wraps JSON in markdown code blocks.
        Also attempts to fix common JSON formatting issues from LLM output.
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                logger.error(f"Could not find JSON in response: {response_text[:200]}")
                raise ValueError("LLM response does not contain valid JSON")

        # First attempt: direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"First JSON parse attempt failed: {e}")

        # Second attempt: fix common issues
        # 第二次尝试：修复常见问题
        fixed_json = json_str

        # Fix trailing commas before ] or }
        # 修复数组或对象末尾的多余逗号
        fixed_json = re.sub(r',\s*([}\]])', r'\1', fixed_json)

        # Fix missing commas between array elements (common LLM error)
        # 修复数组元素之间缺少逗号的问题
        fixed_json = re.sub(r'}\s*\n\s*{', r'},\n{', fixed_json)

        # Fix unescaped newlines in strings
        # 修复字符串中未转义的换行符
        # This is tricky - be careful not to break valid JSON

        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError as e:
            logger.warning(f"Second JSON parse attempt failed: {e}")

        # Third attempt: try to truncate at last valid point
        # 第三次尝试：截断到最后一个有效点
        # Find matching braces
        brace_count = 0
        last_valid_pos = 0
        for i, char in enumerate(fixed_json):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    last_valid_pos = i + 1
                    break

        if last_valid_pos > 0:
            truncated_json = fixed_json[:last_valid_pos]
            try:
                return json.loads(truncated_json)
            except json.JSONDecodeError as e:
                logger.warning(f"Third JSON parse attempt (truncated) failed: {e}")

        # Final fallback: return minimal valid response
        # 最终后备：返回最小有效响应
        logger.error(f"All JSON parse attempts failed. Response preview: {json_str[:500]}...")
        return {
            "risk_score": 50,
            "risk_level": "medium",
            "issues": [{
                "type": "parse_error",
                "description": "Failed to parse LLM analysis response",
                "description_zh": "无法解析LLM分析响应",
                "severity": "medium",
                "affected_positions": [],
                "fix_suggestions": ["Please try again"],
                "fix_suggestions_zh": ["请重试"]
            }],
            "recommendations": ["Analysis may be incomplete due to parsing error"],
            "recommendations_zh": ["由于解析错误，分析可能不完整"]
        }

    async def _load_from_cache(self, session_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """
        Load cached analysis result from database
        从数据库加载缓存的分析结果

        Args:
            session_id: Session ID
            step_name: Step name (e.g., "layer5-step1-1")

        Returns:
            Cached analysis result or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"http://localhost:8000/api/v1/substep-state/load/{session_id}/{step_name}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("analysis_result")
                elif response.status_code == 404:
                    # No cache found
                    return None
                else:
                    logger.warning(f"Failed to load cache: {response.status_code}")
                    return None
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            return None

    async def _save_to_cache(
        self,
        session_id: str,
        step_name: str,
        analysis_result: Dict[str, Any],
        status: str = "completed"
    ) -> bool:
        """
        Save analysis result to cache database
        保存分析结果到缓存数据库

        Args:
            session_id: Session ID
            step_name: Step name (e.g., "layer5-step1-1")
            analysis_result: LLM analysis result
            status: Status (pending/completed/skipped)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/substep-state/save",
                    json={
                        "session_id": session_id,
                        "step_name": step_name,
                        "analysis_result": analysis_result,
                        "status": status
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Cache save failed: {e}")
            return False
