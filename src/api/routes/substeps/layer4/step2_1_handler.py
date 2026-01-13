"""
Step 2.1 Handler: Section Order Analysis (章节顺序与模板匹配)
Layer 4 Section Level - LLM-based analysis with chain-call for section data

Analyze section order and template matching using LLM.
Uses chain-call pattern to first detect sections, then analyze their order.
使用LLM分析章节顺序和模板匹配。使用链式调用模式先检测章节，再分析顺序。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.api.routes.substeps.base_handler import BaseSubstepHandler

logger = logging.getLogger(__name__)


class Step2_1Handler(BaseSubstepHandler):
    """Handler for Step 2.1: Section Order Analysis (with chain-call)"""

    def get_analysis_prompt(self) -> str:
        """
        Return the analysis prompt template for section order analysis.
        This prompt expects {sections_data} to be filled with detected sections.
        返回章节顺序分析的prompt模板。此prompt需要填充{sections_data}为检测到的章节。
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze the section ordering of the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

<detected_sections>
{sections_data}
</detected_sections>

Based on the detected sections above, evaluate:

1. TEMPLATE MATCHING
   - Does the section order follow a rigid academic template? (Introduction -> Literature -> Methods -> Results -> Discussion -> Conclusion)
   - AI often produces predictable, template-like ordering

2. SECTION ORDER PATTERNS
   - Is the ordering too predictable?
   - Are there creative deviations that indicate human writing?
   - Is there function fusion (combining sections)?

3. MISSING/EXTRA SECTIONS
   - Are any expected sections missing?
   - Are there unconventional sections that add variety?

4. AI SIGNALS
   - Perfect template adherence (high AI risk)
   - No deviation from expected order (high AI risk)
   - Lack of function fusion (high AI risk)

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "order_match_score": 0-100,
    "current_order": ["introduction", "methodology", "results", "conclusion"],
    "expected_order": ["introduction", "literature", "methodology", "results", "discussion", "conclusion"],
    "missing_sections": ["literature", "discussion"],
    "function_fusion_score": 0-100,
    "issues": [
        {{
            "type": "rigid_template_order|missing_section|no_function_fusion",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["section_0"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Return the rewrite prompt template"""
        return """You are an expert academic writing editor. Reorganize the document sections to address:

<issues>
{selected_issues}
</issues>

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

User notes: {user_notes}

Requirements:
1. PRESERVE all locked terms exactly
2. Create more natural section ordering
3. Consider function fusion (combining related sections)
4. Add variety to break template patterns
5. Maintain logical flow and coherence

Return the reorganized document as JSON:
{{
    "modified_text": "Full reorganized document text",
    "changes_summary_zh": "中文修改总结",
    "changes_count": 0,
    "issues_addressed": ["issue types addressed"]
}}
"""

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
        Run section order analysis with chain-call for section detection
        使用链式调用进行章节顺序分析

        First detects sections, then analyzes their order.
        先检测章节，再分析顺序。
        """
        # Check analysis cache first
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Chain-call: First detect sections
        # 链式调用：首先检测章节
        logger.info("Step 2.1: Chain-calling section detection")
        sections = await self.detect_sections(document_text, session_id, use_cache)

        # Format sections data for prompt
        # 格式化章节数据用于prompt
        sections_data = json.dumps(sections, indent=2, ensure_ascii=False) if sections else "No sections detected"

        # Build locked terms string
        locked_terms = locked_terms or []
        locked_terms_str = "\n".join(f"- {term}" for term in locked_terms) if locked_terms else "None"

        # Get analysis prompt and fill in
        prompt_template = self.get_analysis_prompt()
        prompt = prompt_template.format(
            document_text=document_text[:10000],
            locked_terms=locked_terms_str,
            sections_data=sections_data
        )

        # Call LLM for order analysis
        logger.info("Step 2.1: Analyzing section order")
        response_text = await self._call_llm(prompt, max_tokens=4096, temperature=0.3)

        # Parse result
        result = self._parse_json_response(response_text)

        # Include detected sections in result for reference
        result["detected_sections"] = sections

        # Save to cache
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")

        return result
