"""
Step 3.4 Handler: Sentence Length Distribution (句子长度分布)
Layer 3 Paragraph Level - LLM-based analysis

Analyze sentence length distribution within paragraphs using LLM.
使用LLM分析段落内句子长度分布。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step3_4Handler(BaseSubstepHandler):
    """Handler for Step 3.4: Sentence Length Distribution"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for sentence length analysis"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze sentence length distribution in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

For each paragraph, analyze:

1. SENTENCE LENGTH VARIATION
   - Calculate mean, standard deviation, CV
   - Target CV >= 0.4 for human-like writing
   - CV < 0.3 indicates AI-like uniformity

2. BURSTINESS
   - Human writing is "bursty" - clusters of short or long sentences
   - AI writing tends to be evenly paced
   - Look for rhythm changes within paragraphs

3. SHORT SENTENCES
   - Human writing includes punchy short sentences (< 10 words)
   - AI often lacks very short sentences
   - Short sentences add emphasis and rhythm

4. LONG SENTENCES
   - Complex ideas require longer sentences
   - AI may avoid very long sentences (> 40 words)
   - Long sentences show sophisticated structure

5. RHYTHM SCORE
   - Alternation between lengths creates rhythm
   - Monotonous length patterns are AI-like

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "paragraph_lengths": [
        {{
            "paragraph_index": 0,
            "sentence_count": 5,
            "sentence_lengths": [12, 25, 8, 30, 15],
            "mean_length": 18.0,
            "std_length": 8.5,
            "cv": 0.47,
            "burstiness": 0.6,
            "has_short_sentence": true,
            "has_long_sentence": true,
            "rhythm_score": 0.7
        }}
    ],
    "low_burstiness_paragraphs": [2, 4],
    "overall_cv": 0.35,
    "issues": [
        {{
            "type": "low_cv|no_short_sentences|no_burstiness",
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
        """Generate prompt for sentence length variation"""
        return """You are an expert academic writing editor. Vary sentence lengths to address:

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
2. Add short punchy sentences (5-10 words) for emphasis
3. Include some long complex sentences (30+ words) for detail
4. Create burstiness - clusters of similar lengths followed by contrast
5. Target CV >= 0.4 for sentence length variation
6. Maintain meaning while varying structure

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with varied sentence lengths",
  "changes_summary_zh": "中文修改总结",
  "changes_count": 3,
  "issues_addressed": ["low_cv", "no_short_sentences"]
}}
"""
