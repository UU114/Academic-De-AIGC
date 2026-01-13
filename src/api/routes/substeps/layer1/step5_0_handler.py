"""
Step 5.0 Handler: Lexical Context Preparation (词汇环境准备)
Layer 1 Lexical Level - LLM-based analysis

Prepare lexical analysis context using LLM.
使用LLM准备词汇分析上下文。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step5_0Handler(BaseSubstepHandler):
    """Handler for Step 5.0: Lexical Context Preparation"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for lexical context preparation

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in lexical analysis.

Prepare lexical analysis context for the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Analyze:

1. VOCABULARY STATISTICS
   - Total words
   - Unique words
   - Vocabulary richness (unique/total)
   - Low richness (< 0.35) may indicate AI repetition

2. WORD FREQUENCY
   - Top 20 most frequent words
   - Overused words (appear > 1% of total)
   - AI tends to repeat certain words excessively

3. LOCKED TERMS STATUS
   - Verify locked terms are present
   - Count occurrences of each locked term
   - Flag any locked terms not found

4. LEXICAL DIVERSITY INDICATORS
   - Type-Token Ratio (TTR)
   - AI text often has lower TTR
   - Target TTR >= 0.4

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "vocabulary_stats": {{
        "total_words": 500,
        "unique_words": 200,
        "vocabulary_richness": 0.4,
        "ttr": 0.4
    }},
    "top_words": [
        {{"word": "the", "count": 25, "percentage": 5.0}},
        {{"word": "study", "count": 10, "percentage": 2.0}}
    ],
    "overused_words": ["the", "important"],
    "locked_terms_status": [
        {{"term": "machine learning", "found": true, "count": 3}}
    ],
    "issues": [
        {{
            "type": "low_richness|overused_word|missing_locked_term",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": [],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for lexical improvement

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Improve lexical variety to address:

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
1. PRESERVE all locked terms exactly - do not change them
2. Replace overused words with synonyms
3. Increase vocabulary diversity
4. Target vocabulary richness >= 0.4
5. Maintain academic register and meaning

Return the improved document text only.
"""
