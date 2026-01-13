"""
Step 5.3 Handler: Replacement Generation (替换词生成)
Layer 1 Lexical Level - LLM-based analysis

Generate word replacements using LLM.
使用LLM生成词汇替换。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step5_3Handler(BaseSubstepHandler):
    """Handler for Step 5.3: Replacement Generation"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for replacement analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert in lexical substitution for academic writing.

Analyze the following document and suggest word replacements:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

IMPORTANT: Never suggest replacements for locked terms.

For each word that should be replaced, provide:

1. AI FINGERPRINT REPLACEMENTS (Priority)
   - Replace AI-favorite words with natural alternatives
   - Example: "utilize" -> "use"

2. VARIETY REPLACEMENTS
   - Replace repeated words with synonyms
   - Increase vocabulary diversity

3. FORMALITY ADJUSTMENTS
   - Replace overly formal words
   - Match appropriate register

4. COLLOCATION IMPROVEMENTS
   - Replace awkward word combinations
   - Use more natural collocations

For each replacement:
- Ensure meaning is preserved
- Consider context appropriateness
- Provide multiple options when possible

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "replacements": [
        {{
            "original": "utilize",
            "position": "para_1_sent_2_word_5",
            "reason": "ai_fingerprint|variety|formality|collocation",
            "suggestions": ["use", "employ", "apply"],
            "recommended": "use",
            "context": "...we utilize machine learning..."
        }}
    ],
    "replacement_count": 15,
    "by_category": {{
        "ai_fingerprint": 5,
        "variety": 6,
        "formality": 2,
        "collocation": 2
    }},
    "issues": [
        {{
            "type": "needs_replacement",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_1_sent_2"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for applying replacements

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Apply word replacements to address:

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
1. PRESERVE all locked terms exactly - NEVER change them
2. Apply all suggested replacements
3. Ensure replacements fit grammatically
4. Maintain consistent register throughout
5. Preserve original meaning
6. Improve vocabulary diversity

Return the document with replacements applied.
"""
