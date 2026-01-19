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
    # Two-Stage Section Analysis (LLM Structure + Rule Statistics)
    # 两阶段章节分析（LLM结构识别 + 规则统计）
    # ==========================================================================

    # LLM prompt for identifying section structure ONLY (no statistics)
    # LLM提示词仅用于识别章节结构（不做统计）
    SECTION_STRUCTURE_PROMPT = """Identify the MAIN SECTIONS of this academic document.

## DOCUMENT TEXT:
{document_text}

## STRICT RULES - VIOLATIONS WILL CAUSE ERRORS:

### ⚠️ ABSOLUTELY DO NOT INCLUDE THESE (CRITICAL):
- "1.1", "1.2", "2.1", "2.2", "3.1", "4.1", "4.2" etc. - These are SUBSECTIONS, NOT main sections!
- Any header with TWO OR MORE numbers separated by dots (X.Y, X.Y.Z) is a SUBSECTION
- If you see "2.1 Background" or "4.2 Results" - SKIP IT, it's a subsection!

### ✓ ONLY INCLUDE THESE (main sections):
- Headers starting with SINGLE number: "1.", "2.", "3.", "4.", "5." (NOT "1.1", "2.1")
- Standalone titles: "Abstract", "Introduction", "Conclusion", "References"

### ✓ EACH ROLE APPEARS EXACTLY ONCE:
A typical paper has 5-8 main sections total, NOT 12-15!
Example of correct output: abstract, introduction, methodology, experiments, results, conclusion
If you output more than 8 sections, you are probably including subsections by mistake!

### Role mapping:
- title: Document title only
- abstract: Abstract
- introduction: Introduction (1. Introduction)
- background: Background (2. Background) - use ONLY if it's a main section "2.", not "2.1"
- literature_review: Related Work / Literature Review
- methodology: Methods/Methodology (use for the MAIN methodology section only)
- experiments: Experiments
- results: Results
- discussion: Discussion
- conclusion: Conclusion
- references: References
- body: Other

## OUTPUT (JSON only):
{{
  "document_title": "Paper Title",
  "sections": [
    {{"role": "title", "title": "Paper Title", "start_line": 0}},
    {{"role": "abstract", "title": "Abstract", "start_line": 2}},
    {{"role": "introduction", "title": "1. Introduction", "start_line": 5}},
    {{"role": "methodology", "title": "2. Methodology", "start_line": 15}},
    {{"role": "experiments", "title": "3. Experiments", "start_line": 30}},
    {{"role": "conclusion", "title": "4. Conclusion", "start_line": 50}}
  ]
}}

FINAL CHECK: If your output has more than 8 sections, DELETE the subsections (X.Y format)!
"""

    async def identify_section_structure(
        self,
        document_text: str,
        session_id: str = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Stage 1: Use LLM to identify section structure (cacheable)
        阶段1：使用LLM识别章节结构（可缓存）

        LLM is good at semantic understanding - identifying titles, section headers, and roles.
        LLM擅长语义理解 - 识别标题、章节标题和角色。

        Args:
            document_text: Document text to analyze
            session_id: Session ID for caching
            use_cache: Whether to use cached structure

        Returns:
            Dict with 'document_title' and 'sections' (structure only, no statistics)
        """
        # Check cache first
        # 先检查缓存
        cache_key = "section-structure"
        if use_cache and session_id:
            cached_result = await self._load_from_cache(session_id, cache_key)
            if cached_result and cached_result.get("sections"):
                logger.info(f"Using cached section structure for session {session_id}")
                return cached_result

        # Build prompt - use line-based truncation to preserve line number accuracy
        # 构建提示词 - 使用基于行的截断以保持行号准确性
        lines = document_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        max_lines = 200  # Limit to first 200 lines for structure identification
        truncated_lines = lines[:max_lines]
        truncated_text = '\n'.join(truncated_lines)

        # If document is longer, add note to LLM
        # 如果文档更长，向LLM添加说明
        if len(lines) > max_lines:
            truncated_text += f"\n\n[NOTE: Document continues beyond line {max_lines}. Total lines: {len(lines)}]"

        prompt = self.SECTION_STRUCTURE_PROMPT.format(
            document_text=truncated_text
        )

        # Call LLM with low temperature for consistency
        logger.info("Identifying section structure via LLM")
        response_text = await self._call_llm(prompt, max_tokens=2048, temperature=0.2)

        # Parse response
        result = self._parse_json_response(response_text)

        # Validate result has required fields
        if "sections" not in result:
            result["sections"] = []
        if "document_title" not in result:
            result["document_title"] = ""

        # Cache the result
        if use_cache and session_id and result.get("sections"):
            await self._save_to_cache(session_id, cache_key, result, status="completed")
            logger.info(f"Cached section structure with {len(result['sections'])} sections for session {session_id}")

        return result

    async def get_sections_with_statistics(
        self,
        document_text: str,
        session_id: str = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Two-stage section analysis: LLM structure + Rule statistics
        两阶段章节分析：LLM结构识别 + 规则统计

        Stage 1 (LLM, cacheable): Identify section structure (titles, roles, boundaries)
        Stage 2 (Rules, fresh): Calculate accurate statistics (word count, paragraph count, etc.)

        阶段1（LLM，可缓存）：识别章节结构（标题、角色、边界）
        阶段2（规则，新鲜计算）：计算准确统计数据（词数、段落数等）

        Args:
            document_text: Document text to analyze
            session_id: Session ID for caching section structure
            use_cache: Whether to use cached structure (statistics always fresh)

        Returns:
            List of section dictionaries with both structure and statistics
        """
        # Import here to avoid circular import
        # 在此导入以避免循环导入
        from src.services.text_parsing_service import get_text_parsing_service

        # Stage 1: Get section structure from LLM (cacheable)
        # 阶段1：从LLM获取章节结构（可缓存）
        structure = await self.identify_section_structure(document_text, session_id, use_cache)
        llm_sections = structure.get("sections", [])
        document_title = structure.get("document_title", "")

        logger.info(f"LLM identified {len(llm_sections)} sections, document title: '{document_title}'")

        # Stage 2: Calculate statistics using rules (always fresh)
        # 阶段2：使用规则计算统计数据（总是新鲜计算）
        parsing_service = get_text_parsing_service()
        sections_with_stats = parsing_service.calculate_section_statistics(
            document_text, llm_sections
        )

        logger.info(f"Calculated statistics for {len(sections_with_stats)} sections")

        return sections_with_stats

    # Keep old method for backward compatibility, but redirect to new implementation
    # 保留旧方法以保持向后兼容，但重定向到新实现
    async def detect_sections(
        self,
        document_text: str,
        session_id: str = None,
        use_cache: bool = True
    ) -> list:
        """
        [DEPRECATED] Use get_sections_with_statistics() instead
        [已弃用] 请使用 get_sections_with_statistics()

        This method is kept for backward compatibility.
        此方法保留以保持向后兼容。
        """
        logger.warning("detect_sections() is deprecated, use get_sections_with_statistics() instead")
        return await self.get_sections_with_statistics(document_text, session_id, use_cache)

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

        # Handle missing modified_text - use original text as fallback
        # 处理缺少modified_text的情况 - 使用原始文本作为备用
        if "modified_text" not in result:
            logger.warning("LLM response missing 'modified_text' field, using original text")
            # Check if LLM returned plain text instead of JSON
            # 检查LLM是否返回了纯文本而不是JSON
            if response_text and not response_text.strip().startswith('{'):
                # LLM returned plain text, use it as modified text
                # LLM返回了纯文本，将其用作修改后的文本
                result["modified_text"] = response_text.strip()
                result["changes_summary_zh"] = "LLM直接返回了修改后的文本"
            else:
                # Fallback to original text
                # 回退到原始文本
                result["modified_text"] = document_text
                result["changes_summary_zh"] = "修改失败，保留原文"

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

    def _format_issues_list(self, selected_issues: List[Any]) -> str:
        """
        Format selected issues into a readable list
        格式化选定问题为可读列表

        IMPORTANT: Includes issue TYPE so LLM knows which strategy to apply
        重要：包含问题类型，以便LLM知道应用哪种修改策略

        Supports both dict and Pydantic model objects
        支持字典和Pydantic模型对象
        """
        issues_list = ""
        for i, issue in enumerate(selected_issues, 1):
            # Handle both dict and Pydantic model objects
            # 处理字典和Pydantic模型对象
            if hasattr(issue, 'model_dump'):
                # Pydantic v2 model
                issue = issue.model_dump()
            elif hasattr(issue, 'dict'):
                # Pydantic v1 model
                issue = issue.dict()
            elif not isinstance(issue, dict):
                # Try to convert to dict using __dict__
                issue = vars(issue) if hasattr(issue, '__dict__') else {"type": "unknown"}

            issue_type = issue.get("type", "unknown")
            desc_zh = issue.get("description_zh", issue.get("description", ""))
            desc_en = issue.get("description", desc_zh)
            severity = issue.get("severity", "medium").upper()

            # Include issue type prominently so LLM can match it to strategies
            # 突出显示问题类型，以便LLM可以将其与策略匹配
            issues_list += f"{i}. Issue Type: {issue_type}\n"
            issues_list += f"   Severity: [{severity}]\n"
            issues_list += f"   Description: {desc_en}\n"
            if desc_zh != desc_en:
                issues_list += f"   中文描述: {desc_zh}\n"

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
            timeout=300.0,  # 5 minutes for large documents
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
            timeout=300.0,  # 5 minutes for large documents
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
            timeout=300.0,  # 5 minutes for large documents
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
        # Log raw response for debugging (truncated)
        # 记录原始响应用于调试（截断）
        logger.debug(f"Raw LLM response (first 500 chars): {response_text[:500]}")

        # Try to extract JSON from markdown code blocks (use greedy matching for nested braces)
        # 从markdown代码块中提取JSON（使用贪婪匹配处理嵌套大括号）
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\})\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
            logger.debug("Found JSON in markdown code block")
        else:
            # Try to find JSON object directly using brace matching
            # 使用大括号匹配直接查找JSON对象
            json_str = self._extract_json_by_braces(response_text)
            if not json_str:
                logger.error(f"Could not find JSON in response: {response_text[:500]}")
                # Return fallback response instead of raising exception
                # 返回备用响应而不是抛出异常
                return {
                    "risk_score": 50,
                    "risk_level": "medium",
                    "issues": [{
                        "type": "json_extraction_error",
                        "description": "LLM did not return valid JSON - please retry",
                        "description_zh": "LLM未返回有效JSON - 请重试",
                        "severity": "medium",
                        "affected_positions": [],
                        "fix_suggestions": ["Retry the analysis"],
                        "fix_suggestions_zh": ["重试分析"]
                    }],
                    "recommendations": ["Analysis could not be completed - please retry"],
                    "recommendations_zh": ["分析无法完成 - 请重试"],
                    "diversified_text": response_text[:5000] if response_text else "",  # For step4-5
                    "optimized_text": response_text[:5000] if response_text else "",  # For step4-4
                }
            logger.debug("Found JSON via brace matching")

        # First attempt: direct parse
        try:
            result = json.loads(json_str)
            logger.debug("JSON parsed successfully on first attempt")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"First JSON parse attempt failed: {e}. Position: {e.pos}, Line: {e.lineno}, Col: {e.colno}")
            # Log the problematic part
            # 记录有问题的部分
            if e.pos:
                start = max(0, e.pos - 50)
                end = min(len(json_str), e.pos + 50)
                logger.warning(f"JSON context around error: ...{json_str[start:end]}...")

        # Second attempt: fix common issues
        # 第二次尝试：修复常见问题
        fixed_json = json_str

        # Fix trailing commas before ] or }
        # 修复数组或对象末尾的多余逗号
        fixed_json = re.sub(r',\s*([}\]])', r'\1', fixed_json)

        # Fix missing commas between array elements (common LLM error)
        # 修复数组元素之间缺少逗号的问题
        fixed_json = re.sub(r'}\s*\n\s*{', r'},\n{', fixed_json)
        fixed_json = re.sub(r'"\s*\n\s*"', '",\n"', fixed_json)
        fixed_json = re.sub(r']\s*\n\s*"', '],\n"', fixed_json)

        # Fix unescaped newlines within strings (replace \n inside strings)
        # 修复字符串内的未转义换行符
        fixed_json = self._fix_unescaped_newlines(fixed_json)

        # Fix common LLM hallucinations in JSON
        # 修复LLM在JSON中的常见错误
        fixed_json = fixed_json.replace('True', 'true').replace('False', 'false')
        fixed_json = fixed_json.replace('None', 'null')

        try:
            result = json.loads(fixed_json)
            logger.debug("JSON parsed successfully on second attempt (after fixes)")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Second JSON parse attempt failed: {e}")

        # Third attempt: try to truncate at last valid point
        # 第三次尝试：截断到最后一个有效点
        truncated_json = self._extract_json_by_braces(fixed_json)
        if truncated_json:
            try:
                result = json.loads(truncated_json)
                logger.debug("JSON parsed successfully on third attempt (truncated)")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Third JSON parse attempt (truncated) failed: {e}")

        # Final fallback: return minimal valid response
        # 最终后备：返回最小有效响应
        logger.error(f"All JSON parse attempts failed. Full response:\n{json_str[:1000]}...")
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

    def _extract_json_by_braces(self, text: str) -> Optional[str]:
        """
        Extract JSON object by matching braces
        通过匹配大括号提取JSON对象
        """
        # Find the first opening brace
        # 找到第一个开括号
        start_pos = text.find('{')
        if start_pos == -1:
            return None

        brace_count = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start_pos:], start_pos):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_pos:i+1]

        return None

    def _fix_unescaped_newlines(self, json_str: str) -> str:
        """
        Fix unescaped newlines within JSON strings
        修复JSON字符串中未转义的换行符
        """
        result = []
        in_string = False
        escape_next = False
        i = 0

        while i < len(json_str):
            char = json_str[i]

            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue

            if char == '\\':
                escape_next = True
                result.append(char)
                i += 1
                continue

            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue

            if in_string and char == '\n':
                # Replace unescaped newline with escaped version
                # 将未转义的换行符替换为转义版本
                result.append('\\n')
                i += 1
                continue

            result.append(char)
            i += 1

        return ''.join(result)

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
