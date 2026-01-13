"""
Step 4.2 Handler: In-Paragraph Length Analysis (段落内句子长度分析)
Layer 2 Sentence Level - LLM-based analysis

Analyze sentence length patterns within paragraphs using LLM.
使用LLM分析段落内句子长度模式。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_2Handler(BaseSubstepHandler):
    """Handler for Step 4.2: In-Paragraph Sentence Length Analysis"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for in-paragraph length analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze sentence length patterns within paragraphs in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Analyze sentence length at the paragraph level:

1. LENGTH VARIATION PER PARAGRAPH
   - Calculate Coefficient of Variation (CV) for each paragraph
   - CV = standard_deviation / mean
   - CV < 0.25: Too uniform (AI-like pattern)
   - CV 0.25-0.40: Moderate variation
   - CV > 0.40: Natural human variation

2. SENTENCE LENGTH CATEGORIES
   - Very short: 1-10 words (emphatic, punchy)
   - Short: 11-20 words (clear, direct)
   - Medium: 21-30 words (standard academic)
   - Long: 31-40 words (detailed, complex)
   - Very long: 40+ words (may need splitting)

3. MERGE CANDIDATES
   - Adjacent short sentences (both < 15 words)
   - Same subject or topic
   - Could flow better as one sentence

4. SPLIT CANDIDATES
   - Very long sentences (> 45 words)
   - Multiple independent ideas
   - Complex structures that reduce readability

5. AI DETECTION PATTERNS
   - Uniform sentence lengths = AI-like
   - Missing very short or very long = AI-like
   - No length variation within paragraphs = AI-like

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "paragraphs": [
        {{
            "index": 0,
            "sentence_count": 5,
            "lengths": [15, 22, 18, 25, 20],
            "mean_length": 20.0,
            "cv": 0.18,
            "uniformity": "high|medium|low"
        }}
    ],
    "document_cv": 0.25,
    "length_distribution": {{
        "very_short": 2,
        "short": 10,
        "medium": 15,
        "long": 3,
        "very_long": 0
    }},
    "merge_candidates": [
        {{
            "paragraph_index": 0,
            "sentence_indices": [2, 3],
            "lengths": [12, 10],
            "reason": "Adjacent short sentences on same topic"
        }}
    ],
    "split_candidates": [
        {{
            "paragraph_index": 1,
            "sentence_index": 4,
            "length": 52,
            "reason": "Overly long sentence with multiple clauses"
        }}
    ],
    "issues": [
        {{
            "type": "uniform_lengths|needs_merge|needs_split|missing_variety",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_0", "sent_0_2"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for length optimization

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Optimize sentence lengths to address:

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
1. PRESERVE all locked terms exactly
2. For merge candidates:
   - Combine adjacent short sentences using connectors
   - Maintain logical flow and readability
3. For split candidates:
   - Break overly long sentences into 2-3 shorter ones
   - Preserve all information and meaning
4. For uniform length paragraphs:
   - Add variety by shortening some and expanding others
   - Include emphatic short sentences
   - Include detailed long sentences
5. Target CV >= 0.35 per paragraph
6. Maintain all length categories in document

Return the improved document text only.
"""
