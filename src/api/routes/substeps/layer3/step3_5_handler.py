"""
Step 3.5 Handler: Paragraph Transition Analysis (段落衔接分析)
Layer 3 Paragraph Level - LLM-based analysis

Analyze transitions between paragraphs using LLM.
使用LLM分析段落间的衔接。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step3_5Handler(BaseSubstepHandler):
    """Handler for Step 3.5: Paragraph Transition Analysis"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for paragraph transition analysis"""
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze paragraph transitions in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

For each paragraph transition, evaluate:

1. EXPLICIT CONNECTORS
   - "Furthermore", "Moreover", "In addition"
   - "However", "On the other hand", "Nevertheless"
   - High frequency = AI-like
   - Target: < 30% explicit transitions

2. SEMANTIC ECHO
   - Does the end of one paragraph echo in the start of the next?
   - Key word repetition across boundaries
   - Thematic continuation without explicit markers

3. TRANSITION QUALITY
   - Smooth: Natural flow (human-like)
   - Abrupt: Jarring shift (may need fixing)
   - Formulaic: "Moving on to..." (AI-like)

4. OPENER ANALYSIS
   - "This paragraph discusses..." (AI)
   - "It is important to note..." (AI)
   - Direct engagement with topic (human)

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "transitions": [
        {{
            "from_paragraph": 0,
            "to_paragraph": 1,
            "has_explicit_connector": true,
            "connector_word": "Furthermore",
            "semantic_echo_score": 0.0-1.0,
            "transition_quality": "smooth|abrupt|formulaic"
        }}
    ],
    "explicit_connector_count": 5,
    "explicit_ratio": 0.0-1.0,
    "avg_semantic_echo": 0.0-1.0,
    "suggestions": [
        {{
            "transition_index": 2,
            "current": "Furthermore, ...",
            "suggested": "Echo previous topic naturally"
        }}
    ],
    "issues": [
        {{
            "type": "high_explicit_ratio|formulaic_opener|low_echo",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["transition_2_3"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for transition improvement"""
        return """You are an expert academic writing editor. Improve paragraph transitions to address:

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
2. Remove explicit connectors (Furthermore, Moreover, However)
3. Use semantic echo instead - repeat key concepts naturally
4. Remove formulaic openers ("This section will...")
5. Create natural thematic bridges
6. Target < 30% explicit transition ratio

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with improved transitions",
  "changes_summary_zh": "中文修改总结",
  "changes_count": 3,
  "issues_addressed": ["high_explicit_ratio", "formulaic_opener"]
}}
"""
