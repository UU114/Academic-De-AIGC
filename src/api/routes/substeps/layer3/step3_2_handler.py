"""
Step 3.2 Handler: Internal Coherence Analysis (段落内部连贯性)
Layer 3 Paragraph Level - LLM-based analysis

Analyze internal coherence of paragraphs using LLM.
使用LLM分析段落内部连贯性。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step3_2Handler(BaseSubstepHandler):
    """Handler for Step 3.2: Internal Coherence Analysis"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for coherence analysis"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze internal coherence of paragraphs:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

For each paragraph, evaluate:

1. SUBJECT DIVERSITY
   - Does the paragraph stick to one subject or shift naturally?
   - AI paragraphs often have unnaturally unified subjects
   - Human writing includes natural subject drift

2. SENTENCE LENGTH VARIATION
   - Is there burstiness (mix of short and long sentences)?
   - AI tends to produce uniform sentence lengths
   - CV < 0.3 is AI-like, target CV >= 0.4

3. LOGIC STRUCTURE
   - Linear: A -> B -> C (AI-like when too rigid)
   - Hierarchical: Main point with sub-points
   - Mixed: Most human-like

4. CONNECTOR DENSITY
   - AI overuses connectors (However, Moreover, Furthermore)
   - Human writing uses more implicit connections

5. FIRST-PERSON USAGE
   - Appropriate use of "I/we" varies by field
   - Complete absence may indicate AI

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "paragraph_coherence": [
        {{
            "paragraph_index": 0,
            "subject_diversity": 0.0-1.0,
            "length_variation_cv": 0.0-1.0,
            "logic_structure": "linear|hierarchical|mixed",
            "connector_density": 0.0-1.0,
            "first_person_ratio": 0.0-1.0,
            "overall_score": 0-100
        }}
    ],
    "overall_coherence_score": 0-100,
    "high_risk_paragraphs": [1, 3],
    "issues": [
        {{
            "type": "low_diversity|uniform_length|high_connector|no_first_person",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_1"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for coherence improvement"""
        return """You are an expert academic writing editor. Improve paragraph coherence to address:

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
2. Add natural subject variation within paragraphs
3. Vary sentence lengths (add short punchy sentences)
4. Remove excessive connectors
5. Use implicit logical connections
6. Add appropriate first-person references where natural

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with improved coherence",
  "changes_summary_zh": "中文修改总结",
  "changes_count": 3,
  "issues_addressed": ["low_diversity", "uniform_length"]
}}
"""
