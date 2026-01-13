"""
Step 4.1 Handler: Sentence Pattern Detection (句式模式检测)
Layer 2 Sentence Level - LLM-based analysis

Detect sentence patterns and syntactic voids using LLM.
使用LLM检测句式模式和句法空洞。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_1Handler(BaseSubstepHandler):
    """Handler for Step 4.1: Sentence Pattern Detection"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for sentence pattern detection

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze sentence patterns in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Analyze the following aspects:

1. SENTENCE TYPE DISTRIBUTION
   - Simple sentences: One independent clause only
   - Compound sentences: Two+ independent clauses (joined by and, but, or)
   - Complex sentences: Independent + dependent clause(s)
   - Compound-Complex: Multiple independent + dependent clauses
   AI-generated text often has >60% simple sentences

2. OPENER ANALYSIS
   - Count how many times each first word is used to start sentences
   - Identify the most repeated opener words
   - Calculate opener repetition rate (repeated openers / total sentences)
   - Calculate subject-first rate (sentences starting with The/This/It/They/We/I/A)
   AI text often starts 70%+ sentences with "The", "This", "It"

3. VOICE DISTRIBUTION
   - Count active voice sentences
   - Count passive voice sentences
   Natural writing: 15-30% passive, AI often has <10% or >40%

4. SYNTACTIC VOIDS (AI Telltales)
   - "It is [adjective] that..." patterns
   - "There is/are..." existence statements
   - "As mentioned above/previously..."
   - Empty hedging: "It can be argued that..."

5. HIGH RISK PARAGRAPHS
   Identify paragraphs with multiple AI indicators

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "type_distribution": {{
        "simple": {{"count": 15, "percentage": 0.6, "is_risk": true, "threshold": 0.5}},
        "compound": {{"count": 5, "percentage": 0.2, "is_risk": false, "threshold": 0.35}},
        "complex": {{"count": 4, "percentage": 0.16, "is_risk": false, "threshold": 0.3}},
        "compound_complex": {{"count": 1, "percentage": 0.04, "is_risk": false, "threshold": 0.15}}
    }},
    "opener_analysis": {{
        "opener_counts": {{"The": 12, "This": 8, "It": 5, "However": 3}},
        "top_repeated": ["The", "This", "It"],
        "repetition_rate": 0.35,
        "subject_opening_rate": 0.75,
        "issues": ["High repetition of 'The' as sentence opener", "主语开头率过高"]
    }},
    "voice_distribution": {{
        "active": 20,
        "passive": 5
    }},
    "clause_depth_stats": {{
        "mean": 0.8,
        "max": 3
    }},
    "parallel_structure_count": 2,
    "high_risk_paragraphs": [
        {{
            "paragraph_index": 0,
            "risk_score": 75,
            "risk_level": "high",
            "simple_ratio": 0.7,
            "length_cv": 0.2,
            "opener_repetition": 0.4,
            "sentence_count": 8
        }}
    ],
    "syntactic_voids": [
        {{
            "pattern_type": "it_is_that",
            "matched_text": "It is important to note that...",
            "position": 0,
            "end_position": 30,
            "severity": "high",
            "abstract_words": ["important"],
            "suggestion": "Rephrase to be more direct",
            "suggestion_zh": "改为更直接的表达"
        }}
    ],
    "void_score": 30,
    "void_density": 0.05,
    "has_critical_void": true,
    "issues": [
        {{
            "type": "simple_sentence_dominance",
            "description": "60% simple sentences exceeds 50% threshold",
            "description_zh": "简单句比例60%超过50%阈值",
            "severity": "high",
            "affected_positions": ["para_0", "para_2"],
            "fix_suggestions": ["Combine simple sentences using subordinate clauses"],
            "fix_suggestions_zh": ["使用从句合并简单句"]
        }}
    ],
    "recommendations": ["Vary sentence openers", "Add more complex sentences"],
    "recommendations_zh": ["变化句首词", "增加复杂句"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for pattern elimination

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Eliminate AI patterns to address:

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
2. Rewrite syntactic voids:
   - "It is important that X" -> "X matters because..."
   - "There is evidence that" -> "[Subject] shows..."
3. Vary sentence openers - don't start multiple with "The", "This", "It"
4. Remove formulaic phrases:
   - "plays a crucial role" -> specific verb
   - "is of paramount importance" -> explain why specifically
5. Balance passive/active voice (target 15-30% passive)

Return the improved document text only.
"""
