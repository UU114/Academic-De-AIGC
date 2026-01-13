"""
Step 3.3 Handler: Anchor Density Analysis (信息锚点密度)
Layer 3 Paragraph Level - LLM-based analysis

Analyze anchor density and hallucination risk using LLM.
使用LLM分析信息锚点密度和幻觉风险。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step3_3Handler(BaseSubstepHandler):
    """Handler for Step 3.3: Anchor Density Analysis"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for anchor density analysis"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content and hallucination patterns.

Analyze anchor density in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

ANCHORS are specific, verifiable details that "ground" the writing:
- Numbers and statistics (85%, 1.2 million)
- Dates (2023, March 15)
- Names (Dr. Smith, Harvard University)
- Citations ([1], (Smith, 2020))
- Specific locations (New York, Building A)
- Technical terms with precise definitions

AI-generated text often:
1. LACKS ANCHORS - vague, generic statements
2. HAS FAKE ANCHORS - plausible-sounding but fabricated details
3. HAS LOW ANCHOR DENSITY - few specifics per 100 words

Target anchor density: >= 5 anchors per 100 words

For each paragraph, evaluate:

1. ANCHOR COUNT
   - How many specific, verifiable details?
   - Types: numbers, dates, names, citations

2. ANCHOR QUALITY
   - Are anchors verifiable?
   - Do they seem fabricated?
   - Are they vague approximations ("about 50%")?

3. HALLUCINATION RISK
   - Paragraphs with zero anchors are high risk
   - Generic paragraphs suggest AI generation
   - Fake-sounding specifics suggest hallucination

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "overall_density": 0.0,
    "paragraph_densities": [
        {{
            "paragraph_index": 0,
            "word_count": 100,
            "anchor_count": 3,
            "density": 3.0,
            "has_hallucination_risk": false,
            "risk_level": "low|medium|high",
            "anchor_types": {{
                "numbers": 1,
                "dates": 0,
                "names": 2,
                "citations": 0
            }}
        }}
    ],
    "high_risk_paragraphs": [2, 4],
    "anchor_type_distribution": {{
        "numbers": 5,
        "dates": 2,
        "names": 3,
        "citations": 4
    }},
    "document_hallucination_risk": "low|medium|high",
    "issues": [
        {{
            "type": "low_density|no_anchors|suspected_hallucination",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_2"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for anchor enrichment"""
        return """You are an expert academic writing editor. Add anchors and specificity to address:

## ISSUES TO FIX:
{selected_issues}

## ORIGINAL DOCUMENT:
{document_text}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## Requirements:
1. PRESERVE all locked terms exactly
2. Add specific numbers, dates, names where appropriate
3. Replace vague statements with specific claims
4. Add citation placeholders [citation needed] for unverifiable claims
5. Target >= 5 anchors per 100 words
6. Remove or flag potentially hallucinated content

IMPORTANT: Only add verifiable details or mark claims as needing verification.
Do not fabricate specific numbers or names.

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with enriched anchors",
  "changes_summary_zh": "中文修改总结",
  "changes_count": 3,
  "issues_addressed": ["low_density", "no_anchors"]
}}
"""
