"""
Step 2.2 Handler: Section Length Analysis (章节长度分析)
Layer 4 Section Level - LLM-based analysis with chain-call for section data

Analyze section length distribution using LLM.
Uses chain-call pattern to first detect sections, then analyze their lengths.
使用LLM分析章节长度分布。使用链式调用模式先检测章节，再分析长度。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.api.routes.substeps.base_handler import BaseSubstepHandler

logger = logging.getLogger(__name__)


class Step2_2Handler(BaseSubstepHandler):
    """Handler for Step 2.2: Section Length Analysis (with chain-call)"""

    def get_analysis_prompt(self) -> str:
        """
        Return the analysis prompt template for section length analysis.
        This prompt expects {sections_data} to be filled with detected sections.
        返回章节长度分析的prompt模板。此prompt需要填充{sections_data}为检测到的章节。
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze section lengths in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

<detected_sections>
{sections_data}
</detected_sections>

Based on the detected sections above, evaluate using De-AIGC principles:

=== CORE PRINCIPLES FOR HUMAN-LIKE WRITING ===
1. Discussion section should be the LONGEST (most important for analysis)
2. Conclusion should usually be the SHORTEST (1-2 paragraphs)
3. Adjacent sections should NOT have identical paragraph counts
4. CV (Coefficient of Variation) should be > 0.3 for natural variation
5. Section length should reflect content importance, not artificial balance

=== EVALUATION CRITERIA ===

1. PARAGRAPH COUNT UNIFORMITY (HIGH PRIORITY)
   - Are all sections having the same paragraph count? (e.g., all 2 paragraphs) - This is a MAJOR AI signal
   - Calculate paragraph count CV - if all sections have identical paragraphs, CV = 0 (extremely AI-like)
   - Adjacent sections with same paragraph count = AI pattern

2. DISCUSSION SECTION CHECK
   - Is Discussion the longest section? If not, this is a key issue
   - Discussion should typically have MORE paragraphs than other sections
   - If Discussion is not prominent, recommend expanding it FIRST

3. CONCLUSION CHECK
   - Is Conclusion appropriately short? (1-2 paragraphs ideal)
   - Long conclusions are unusual in human academic writing

4. LENGTH CV ANALYSIS
   - Word count CV < 0.3 = too uniform (AI-like)
   - Paragraph count CV = 0 = all sections same paragraph count (highly AI-like)
   - Target: CV >= 0.3 for both metrics

5. AI SIGNALS (RED FLAGS)
   - All sections same paragraph count (HIGH RISK)
   - Perfect symmetry in structure (HIGH RISK)
   - Discussion not being the longest (MEDIUM RISK)
   - Conclusion being too long (MEDIUM RISK)

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "length_cv": 0.0-1.0,
    "paragraph_count_cv": 0.0-1.0,
    "sections": [
        {{
            "index": 0,
            "role": "introduction",
            "word_count": 150,
            "paragraph_count": 2,
            "deviation": "normal|short|long"
        }}
    ],
    "extreme_sections": [1, 3],
    "key_weight_issues": [
        {{
            "section_index": 0,
            "issue": "too_short|too_long|should_be_longer"
        }}
    ],
    "issues": [
        {{
            "type": "uniform_length|extreme_section|weight_imbalance",
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
        return """You are an expert academic writing editor specializing in De-AIGC (making AI-generated text appear more human-like).

Your task is to adjust section paragraph counts to break the uniform/formulaic structure typical of AI writing.

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

=== CORE PRINCIPLES (MUST FOLLOW) ===

1. **Discussion section MUST be the longest** - This is the most important section in academic papers where authors demonstrate deep analysis. When dealing with uniform paragraph counts, ALWAYS prioritize expanding Discussion first.

2. **Conclusion should usually be the shortest** - Typically 1-2 paragraphs is sufficient.

3. **Adjacent sections MUST NOT have identical paragraph counts** - This breaks the AI-typical uniformity pattern.

4. **Variation Coefficient (CV) should be > 0.3** - Natural human writing has noticeable variation in section lengths.

5. **Each section should reflect its importance** - Don't distribute paragraphs evenly; weight them by content significance.

=== EXAMPLE PATTERNS (Reference Only, Not Strict Rules) ===

These are just examples showing acceptable variation. You may freely adjust based on the document's specific content needs:

Pattern A - Discussion Emphasis:
- Introduction: 2 paragraphs
- Methodology: 3 paragraphs
- Results: 2 paragraphs
- Discussion: 5 paragraphs (core analysis)
- Conclusion: 1 paragraph

Pattern B - Results + Discussion Dual Focus:
- Introduction: 2 paragraphs
- Methodology: 2 paragraphs
- Results: 4 paragraphs
- Discussion: 4 paragraphs
- Conclusion: 1 paragraph

Pattern C - Progressive Increase:
- Introduction: 1 paragraph
- Methodology: 2 paragraphs
- Results: 3 paragraphs
- Discussion: 5 paragraphs
- Conclusion: 2 paragraphs

IMPORTANT: These patterns are just illustrations. The key is following the CORE PRINCIPLES, not copying exact numbers. Create natural variation that fits the document's content.

=== REQUIREMENTS ===

1. PRESERVE all locked terms exactly as they appear
2. When splitting sections, add substantive content (not filler)
3. When merging, maintain logical flow and key information
4. The resulting structure should feel naturally uneven, not artificially balanced
5. Discussion expansion is ALWAYS the first priority when addressing uniformity issues

Return the adjusted document as JSON:
{{
    "modified_text": "Full adjusted document text with paragraph variations applied",
    "changes_summary_zh": "中文修改总结，说明各章节段落数的调整",
    "changes_count": 0,
    "issues_addressed": ["issue types addressed"],
    "new_paragraph_distribution": {{
        "introduction": 2,
        "methodology": 3,
        "results": 2,
        "discussion": 5,
        "conclusion": 1
    }}
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
        Run section length analysis with chain-call for section detection
        使用链式调用进行章节长度分析

        First detects sections, then analyzes their lengths.
        先检测章节，再分析长度。
        """
        # Check analysis cache first
        if use_cache and session_id and step_name:
            cached_result = await self._load_from_cache(session_id, step_name)
            if cached_result:
                logger.info(f"Using cached analysis result for {step_name}")
                return cached_result

        # Chain-call: First detect sections
        # 链式调用：首先检测章节
        logger.info("Step 2.2: Chain-calling section detection")
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

        # Call LLM for length analysis
        logger.info("Step 2.2: Analyzing section lengths")
        response_text = await self._call_llm(prompt, max_tokens=4096, temperature=0.3)

        # Parse result
        result = self._parse_json_response(response_text)

        # Include detected sections in result for reference
        result["detected_sections"] = sections

        # Save to cache
        if use_cache and session_id and step_name:
            await self._save_to_cache(session_id, step_name, result, status="completed")

        return result
