"""
Step 5.2 Handler: Human Feature Analysis (人类特征分析)
Layer 1 Lexical Level - LLM-based analysis

Analyze human-like writing features using LLM.
使用LLM分析人类写作特征。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step5_2Handler(BaseSubstepHandler):
    """Handler for Step 5.2: Human Feature Analysis"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for human feature analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert in identifying human writing features that distinguish text from AI-generated content.

Analyze the following document for human writing features:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Look for these HUMAN FEATURES:

1. COLLOQUIALISMS
   - Contractions: "don't", "won't", "it's"
   - Informal expressions appropriate for context
   - Natural speech patterns

2. PERSONAL VOICE
   - First person usage: "I", "we", "my opinion"
   - Personal anecdotes or experiences
   - Subjective observations

3. IMPERFECTIONS
   - Minor redundancies (human-like)
   - Self-corrections: "Or rather...", "That is..."
   - Hedging: "I think", "perhaps", "maybe"

4. EMOTIONAL MARKERS
   - Enthusiasm: "fascinating", "exciting"
   - Frustration: "unfortunately", "disappointing"
   - Uncertainty: "I'm not sure", "arguably"

5. IDIOSYNCRATIC CHOICES
   - Unusual word choices
   - Regional expressions
   - Field-specific jargon used naturally

6. CONVERSATIONAL ELEMENTS
   - Rhetorical questions
   - Direct address to reader
   - Asides and tangents

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "human_features": [
        {{
            "type": "colloquialism|personal_voice|imperfection|emotion|idiosyncratic|conversational",
            "text": "I believe this approach works well",
            "position": "para_2_sent_3",
            "strength": "strong|moderate|weak"
        }}
    ],
    "feature_score": 35,
    "feature_density": 0.5,
    "missing_features": ["colloquialism", "personal_voice"],
    "issues": [
        {{
            "type": "no_human_features|too_formal|no_personal_voice",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["entire_document"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for adding human features

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Add human-like features to address:

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
2. Add appropriate contractions where natural
3. Include first-person perspective where appropriate:
   - "We found that..." instead of "It was found that..."
   - "In our view..." for opinions
4. Add natural hedging:
   - "perhaps", "arguably", "it seems"
5. Include rhetorical questions where appropriate
6. Add minor tangents or asides that show human thinking
7. Maintain academic appropriateness

Note: Don't overdo it - subtle human touches are more effective than obvious ones.

Return the humanized document text only.
"""
