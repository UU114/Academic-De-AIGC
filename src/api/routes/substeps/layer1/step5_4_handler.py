"""
Step 5.4 Handler: Paragraph Rewriting (段落级改写)
Layer 1 Lexical Level - LLM-based analysis and rewriting

Rewrite paragraphs at lexical level using LLM.
使用LLM在词汇层面改写段落。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step5_4Handler(BaseSubstepHandler):
    """Handler for Step 5.4: Paragraph Rewriting"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for paragraph rewrite analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst. Identify paragraphs needing lexical-level rewriting.

Analyze the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

For each paragraph, evaluate:

1. AI FINGERPRINT DENSITY
   - Count AI-typical words/phrases
   - Density > 2 per 100 words = needs rewriting

2. VOCABULARY REPETITION
   - Repeated non-locked words
   - Low lexical variety within paragraph

3. FORMALITY CONSISTENCY
   - Overly formal throughout
   - Register shifts

4. HUMAN FEATURE PRESENCE
   - Lacks personal voice
   - No natural hedging
   - Too polished/perfect

Identify which paragraphs need complete lexical rewriting.

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "paragraphs": [
        {{
            "index": 0,
            "needs_rewrite": true,
            "fingerprint_density": 3.5,
            "vocabulary_variety": 0.3,
            "formality_score": 0.9,
            "human_features": 0,
            "issues": ["high_fingerprint", "low_variety"]
        }}
    ],
    "paragraphs_to_rewrite": [0, 2, 4],
    "issues": [
        {{
            "type": "paragraph_needs_rewrite",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_0"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for paragraph rewriting

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Rewrite the document at lexical level to address:

<issues>
{selected_issues}
</issues>

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>
{user_notes}

Requirements:
1. PRESERVE all locked terms EXACTLY - verify each one is unchanged
2. Remove ALL AI fingerprint words:
   - delve, utilize, facilitate, leverage, plethora, myriad, etc.
3. Increase vocabulary variety:
   - Use different words for repeated concepts
4. Add human features:
   - Natural hedging
   - Occasional first person
   - Appropriate informality
5. Maintain original meaning completely
6. Preserve academic quality

Return the rewritten document text only.
"""
