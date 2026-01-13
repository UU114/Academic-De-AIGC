"""
Step 2.5 Handler: Inter-Section Logic Analysis (章节间逻辑分析)
Layer 4 Section Level - LLM-based analysis with chain-call for section data

Analyze logical flow between sections using LLM.
Uses chain-call pattern to first detect sections, then analyze logic.
使用LLM分析章节间的逻辑流程。使用链式调用模式先检测章节，再分析逻辑。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.api.routes.substeps.base_handler import BaseSubstepHandler

logger = logging.getLogger(__name__)


class Step2_5Handler(BaseSubstepHandler):
    """Handler for Step 2.5: Inter-Section Logic Analysis (with chain-call)"""

    def get_analysis_prompt(self) -> str:
        """Return the analysis prompt template"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze inter-section logic in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

<detected_sections>
{sections_data}
</detected_sections>

Based on the detected sections above, evaluate logical relationships between them:

1. ARGUMENT CHAIN COMPLETENESS
   - Is there a clear argument thread across sections?
   - Does each section build on the previous?
   - Are there logical gaps or jumps?

2. REDUNDANCY
   - Is content repeated across sections unnecessarily?
   - AI often restates ideas in different sections
   - Human writing avoids redundant content

3. PROGRESSION PATTERN
   - Linear (A -> B -> C): More AI-like when too rigid
   - Branching (A -> B1, B2): More human-like
   - Recursive (A -> B -> A' -> C): Most human-like

4. CAUSAL DENSITY
   - How often are causal markers used? (because, therefore, thus)
   - AI overuses explicit causation
   - Human writing implies causation more often

5. LINEARITY SCORE
   - How predictable is the logical flow?
   - Perfect linearity = high AI risk
   - Some non-linearity = more human-like

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "argument_chain_score": 0-100,
    "redundancy_issues": [
        {{
            "section_a": 0,
            "section_b": 2,
            "overlap_content": "repeated concept description"
        }}
    ],
    "progression_pattern": "linear|branching|recursive|mixed",
    "causal_density": 0.0-1.0,
    "linearity_score": 0-100,
    "issues": [
        {{
            "type": "high_linearity|redundancy|broken_chain|high_causal_density",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["section_0", "section_2"],
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
        return """You are an expert academic writing editor. Improve inter-section logic to address:

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
2. Remove redundant content between sections
3. Add branching or recursive elements to break linearity
4. Reduce explicit causal markers (because, therefore)
5. Use implicit causation and logical implication
6. Strengthen argument chain where broken

Return the improved document as JSON:
{{
    "modified_text": "Full improved document text",
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
        """Run inter-section logic analysis with chain-call"""
        # Check analysis cache first
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Chain-call: First detect sections
        logger.info("Step 2.5: Chain-calling section detection")
        sections = await self.detect_sections(document_text, session_id, use_cache)

        # Format sections data for prompt
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

        # Call LLM for logic analysis
        logger.info("Step 2.5: Analyzing inter-section logic")
        response_text = await self._call_llm(prompt, max_tokens=4096, temperature=0.3)

        # Parse result
        result = self._parse_json_response(response_text)
        result["detected_sections"] = sections

        # Save to cache
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")

        return result
