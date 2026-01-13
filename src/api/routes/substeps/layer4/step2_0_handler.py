"""
Step 2.0 Handler: Section Identification (章节识别与角色标注)
Layer 4 Section Level - LLM-based analysis

Automatically detect section boundaries and identify functional roles using LLM.
使用LLM自动检测章节边界并识别功能角色。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step2_0Handler(BaseSubstepHandler):
    """Handler for Step 2.0: Section Identification"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for section identification analysis"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns at the section level.

Analyze the following document for section structure and role identification:

<document>
{document_text}
</document>

<document_info>
- Total paragraphs: {paragraph_count}
- Valid paragraph indices: 0 to {paragraph_count_minus_1}
</document_info>

<locked_terms>
{locked_terms}
</locked_terms>

IMPORTANT: The document has {paragraph_count} paragraphs (indexed 0 to {paragraph_count_minus_1}).
All start_paragraph and end_paragraph values MUST be within this range [0, {paragraph_count_minus_1}].

Identify and analyze:

1. SECTION BOUNDARIES
   - Where do natural section breaks occur?
   - Are sections clearly demarcated or fluid?

2. SECTION ROLES
   - Introduction / Background
   - Literature Review
   - Methodology / Methods
   - Results / Findings
   - Discussion / Analysis
   - Conclusion / Summary

3. AI-LIKE PATTERNS
   - Are sections too evenly distributed? (AI tends to create balanced sections)
   - Is there a rigid template-like structure?
   - Do section boundaries feel artificial?

4. HUMAN-LIKE INDICATORS
   - Natural variation in section lengths
   - Organic transitions between sections
   - Sections that blend or overlap

IMPORTANT: For each section, you MUST provide:
- paragraph_count: Number of paragraphs in the section
- word_count: Approximate word count for the section (count the words in the text between start_paragraph and end_paragraph)

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "sections": [
        {{
            "index": 0,
            "role": "introduction|methodology|results|discussion|conclusion|body",
            "start_paragraph": 0,
            "end_paragraph": 2,
            "paragraph_count": 3,
            "word_count": 150,
            "confidence": 0.0-1.0
        }}
    ],
    "issues": [
        {{
            "type": "rigid_template|unbalanced_sections|missing_section",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["section_0", "section_1"],
            "fix_suggestions": ["suggestion 1"],
            "fix_suggestions_zh": ["建议1"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for section restructuring"""
        return """You are an expert academic writing editor. Restructure the document to address the following section-level issues:

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
1. PRESERVE all locked terms exactly as they appear
2. Maintain original meaning and academic rigor
3. Create more natural section boundaries
4. Vary section lengths for human-like writing
5. Ensure smooth transitions between sections

Return the restructured document text only, no explanations.
"""
