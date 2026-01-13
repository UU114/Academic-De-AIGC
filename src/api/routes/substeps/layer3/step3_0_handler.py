"""
Step 3.0 Handler: Paragraph Identification (段落识别与分割)
Layer 3 Paragraph Level - LLM-based analysis

Identify paragraph boundaries and filter non-body content using LLM.
使用LLM识别段落边界并过滤非正文内容。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step3_0Handler(BaseSubstepHandler):
    """Handler for Step 3.0: Paragraph Identification"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for paragraph identification analysis"""
        return """You are an expert academic writing analyst.

Identify and analyze paragraphs in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Evaluate:

1. PARAGRAPH BOUNDARIES
   - Are paragraphs properly delineated?
   - Are there run-on paragraphs that should be split?
   - Are there fragmented paragraphs that should be merged?

2. NON-BODY CONTENT
   - Identify headers, keywords, references, figure captions
   - These should be filtered from analysis

3. PARAGRAPH STRUCTURE
   - Each paragraph should have a clear purpose
   - Topic sentence identification
   - Supporting content analysis

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "paragraphs": [
        {{
            "index": 0,
            "word_count": 120,
            "sentence_count": 5,
            "is_body": true,
            "preview": "First 100 characters..."
        }}
    ],
    "paragraph_count": 10,
    "filtered_count": 2,
    "issues": [
        {{
            "type": "fragmented|run_on|unclear_boundary",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_0", "para_1"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for paragraph restructuring"""
        return """You are an expert academic writing editor. Restructure paragraphs to address:

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
2. Merge fragmented paragraphs where appropriate
3. Split run-on paragraphs at logical points
4. Ensure each paragraph has a clear focus
5. Maintain proper paragraph boundaries

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full restructured document",
  "changes_summary_zh": "中文修改总结",
  "changes_count": 3,
  "issues_addressed": ["fragmented", "run_on"]
}}
"""
