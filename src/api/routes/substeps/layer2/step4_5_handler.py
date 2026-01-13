"""
Step 4.5 Handler: Sentence Rewriting (句子改写)
Layer 2 Sentence Level - LLM-based analysis and rewriting

Rewrite sentences to address AI detection issues using LLM.
使用LLM改写句子以解决AI检测问题。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_5Handler(BaseSubstepHandler):
    """Handler for Step 4.5: Sentence Rewriting"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for sentence-level diversification and rewriting

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing editor specializing in eliminating AI-generated content patterns.

Your task is to REWRITE the following text to eliminate AI fingerprints and diversify sentence patterns:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

REWRITING REQUIREMENTS:

1. ELIMINATE AI FINGERPRINTS
   - "It is important to note that X" -> Rewrite as direct statement
   - "plays a crucial role" -> Use specific action verb
   - "It is essential to..." -> Remove or make direct
   - Remove formulaic academic phrases

2. DIVERSIFY SENTENCE STRUCTURE
   - Vary sentence openers (don't start multiple with "The", "This", "It")
   - Mix simple, compound, and complex sentences
   - Add subordinate clauses where appropriate
   - Use occasional passive voice (15-25%)

3. VARY SENTENCE LENGTH
   - Include short emphatic sentences (10-15 words)
   - Include longer detailed sentences (30-40 words)
   - Target CV >= 0.35 for length variation

4. IMPROVE CONNECTORS
   - Remove unnecessary explicit connectors
   - Use implicit connections through content flow
   - Vary transition methods

IMPORTANT: You MUST rewrite the text and return the improved version.

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "diversified_text": "THE COMPLETE REWRITTEN TEXT WITH ALL IMPROVEMENTS APPLIED",
    "changes": [
        {{
            "sentence_index": 0,
            "original": "Original sentence text",
            "modified": "Rewritten sentence text",
            "change_type": "opener_variation|voice_switch|structure_change|ai_elimination",
            "strategy": "Brief description of change",
            "improvement_type": "diversity|naturalness|rhythm"
        }}
    ],
    "applied_strategies": {{
        "opener_variations": 5,
        "voice_switches": 2,
        "structure_changes": 3,
        "ai_eliminations": 4,
        "length_adjustments": 2
    }},
    "before_metrics": {{
        "simple_ratio": 0.65,
        "compound_ratio": 0.20,
        "complex_ratio": 0.15,
        "compound_complex_ratio": 0.0,
        "opener_diversity": 0.3,
        "voice_balance": 0.95,
        "length_cv": 0.18,
        "overall_score": 35
    }},
    "after_metrics": {{
        "simple_ratio": 0.45,
        "compound_ratio": 0.25,
        "complex_ratio": 0.25,
        "compound_complex_ratio": 0.05,
        "opener_diversity": 0.7,
        "voice_balance": 0.78,
        "length_cv": 0.38,
        "overall_score": 72
    }},
    "improvement_summary": {{
        "total_changes": 12,
        "score_improvement": 37,
        "key_improvements": ["Varied sentence openers", "Added complex structures", "Eliminated AI phrases"]
    }},
    "issues": [
        {{
            "type": "ai_patterns_found",
            "description": "English description of patterns found and fixed",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["sent_0", "sent_5"],
            "fix_suggestions": ["Applied fixes"],
            "fix_suggestions_zh": ["已应用的修复"]
        }}
    ],
    "recommendations": ["Further improvements if any"],
    "recommendations_zh": ["进一步改进建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for sentence rewriting

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Rewrite sentences to address:

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
2. Rewrite AI fingerprint sentences:
   - "It is important to note that X" -> "X matters because..." or direct statement
   - "plays a crucial role" -> specific action verb
   - Remove empty hedging
3. Add structural variety:
   - Combine simple sentences
   - Add subordinate clauses
4. Fix connector issues:
   - Replace repetitive connectors
   - Remove unnecessary connectors
5. Vary sentence lengths
6. Maintain original meaning and academic tone

Return the rewritten document text only.
"""
