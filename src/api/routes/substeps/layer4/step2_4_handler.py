"""
Step 2.4 Handler: Section Transition Analysis (章节衔接分析)
Layer 4 Section Level - LLM-based analysis with chain-call for section data

Analyze transitions between sections using LLM.
Uses chain-call pattern to first detect sections, then analyze transitions.
使用LLM分析章节间的衔接。使用链式调用模式先检测章节，再分析衔接。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.api.routes.substeps.base_handler import BaseSubstepHandler

logger = logging.getLogger(__name__)


class Step2_4Handler(BaseSubstepHandler):
    """Handler for Step 2.4: Section Transition Analysis (with chain-call)"""

    def get_analysis_prompt(self) -> str:
        """Return the analysis prompt template"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze section transitions in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

<detected_sections>
{sections_data}
</detected_sections>

Based on the detected sections above, evaluate transitions between them:

1. EXPLICIT TRANSITION MARKERS
   - "In this section, we will..."
   - "Moving on to..."
   - "Now, let's discuss..."
   - These are AI telltales when overused

2. SEMANTIC ECHO
   - Does the end of one section echo into the beginning of the next?
   - Natural writing uses thematic bridges, not explicit markers
   - Look for keyword/concept repetition across section boundaries

3. OPENER PATTERNS
   - Are section openings formulaic?
   - "This section presents..." (AI-like)
   - "Having discussed X, we now turn to Y" (AI-like)

4. TRANSITION STRENGTH
   - Strong (explicit markers) - AI-like
   - Moderate (semantic bridges) - Human-like
   - Weak (abrupt) - May need improvement

5. AI SIGNALS
   - High explicit transition ratio (> 50%)
   - Formulaic section openers
   - No semantic echo (pure explicit transitions)

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "explicit_transition_ratio": 0.0-1.0,
    "semantic_echo_score": 0.0-1.0,
    "opener_patterns": [
        {{
            "section_index": 1,
            "opener": "In this section...",
            "is_formulaic": true
        }}
    ],
    "transition_words": [
        {{
            "from_section": 0,
            "to_section": 1,
            "words": ["Furthermore", "Moving on"],
            "strength": "strong|moderate|weak"
        }}
    ],
    "strength_distribution": {{
        "strong": 2,
        "moderate": 1,
        "weak": 0
    }},
    "issues": [
        {{
            "type": "high_explicit_ratio|formulaic_opener|no_semantic_echo",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["transition_0_1"],
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
        return """You are an expert academic writing editor. Improve section transitions to address:

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
2. Replace explicit transition markers with semantic echoes
3. Use concept/keyword bridges instead of formulaic phrases
4. Remove "In this section..." and similar AI-like openers
5. Create natural thematic connections between sections
6. Vary transition strength (some implicit, some moderate)

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
        """Run section transition analysis with chain-call"""
        # Check analysis cache first
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Chain-call: First detect sections
        logger.info("Step 2.4: Chain-calling section detection")
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

        # Call LLM for transition analysis
        logger.info("Step 2.4: Analyzing section transitions")
        response_text = await self._call_llm(prompt, max_tokens=4096, temperature=0.3)

        # Parse result
        result = self._parse_json_response(response_text)
        result["detected_sections"] = sections

        # Save to cache
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")

        return result
