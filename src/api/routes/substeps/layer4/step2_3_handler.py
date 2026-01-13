"""
Step 2.3 Handler: Internal Structure Similarity (章节内部结构相似性)
Layer 4 Section Level - LLM-based analysis with chain-call for section data

Analyze internal structure similarity across sections using LLM.
Uses chain-call pattern to first detect sections, then analyze similarity.
使用LLM分析章节内部结构相似性。使用链式调用模式先检测章节，再分析相似性。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.api.routes.substeps.base_handler import BaseSubstepHandler

logger = logging.getLogger(__name__)


class Step2_3Handler(BaseSubstepHandler):
    """Handler for Step 2.3: Internal Structure Similarity (with chain-call)"""

    def get_analysis_prompt(self) -> str:
        """Return the analysis prompt template"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze internal structure similarity across sections:

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

1. STRUCTURAL REPETITION
   - Do all sections follow the same internal pattern?
   - AI often produces sections with identical structures:
     * Same number of paragraphs
     * Same paragraph roles (topic -> support -> conclusion)
     * Same sentence patterns within paragraphs

2. PARAGRAPH FUNCTION DISTRIBUTION
   - Is paragraph function distribution too uniform across sections?
   - Human writing shows varied paragraph structures

3. HEADING PATTERNS
   - Are subheading depths identical across sections?
   - Do headings follow a rigid pattern?

4. ARGUMENT DENSITY
   - Is argument/evidence density uniform across all sections?
   - Human writing naturally varies in argument density

5. AI SIGNALS
   - High average similarity (> 0.7) between section structures
   - Identical paragraph role sequences
   - No variation in subheading depth

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "avg_similarity": 0.0-1.0,
    "similarity_matrix": [[1.0, 0.8], [0.8, 1.0]],
    "heading_variance": 0.0-1.0,
    "argument_density_cv": 0.0-1.0,
    "paragraph_functions": [
        {{
            "section_index": 0,
            "functions": ["topic", "support", "support", "conclusion"]
        }}
    ],
    "issues": [
        {{
            "type": "high_similarity|uniform_functions|rigid_headings",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["section_0", "section_1"],
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
        return """You are an expert academic writing editor. Diversify internal section structures to address:

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
2. Vary paragraph count between sections
3. Use different paragraph role sequences in each section
4. Vary subheading depths and styles
5. Create natural variation in argument density
6. Maintain academic quality while adding human-like variety

Return the diversified document as JSON:
{{
    "modified_text": "Full diversified document text",
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
        """Run internal structure similarity analysis with chain-call"""
        # Check analysis cache first
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Chain-call: First detect sections
        logger.info("Step 2.3: Chain-calling section detection")
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

        # Call LLM for similarity analysis
        logger.info("Step 2.3: Analyzing internal structure similarity")
        response_text = await self._call_llm(prompt, max_tokens=4096, temperature=0.3)

        # Parse result
        result = self._parse_json_response(response_text)
        result["detected_sections"] = sections

        # Save to cache
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")

        return result
