"""
Step 4.0 Handler: Sentence Identification (句子识别与标注)
Layer 2 Sentence Level - LLM-based analysis

Identify sentences and label type/function using LLM.
使用LLM识别句子并标注类型和功能。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_0Handler(BaseSubstepHandler):
    """Handler for Step 4.0: Sentence Identification"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for sentence identification

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Identify and classify sentences in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

For each sentence, analyze:

1. SENTENCE TYPE
   - Simple: One independent clause
   - Compound: Multiple independent clauses (and, but, or)
   - Complex: Independent + dependent clauses
   - Compound-Complex: Multiple independent + dependent

2. FUNCTION ROLE
   - Topic: States main idea
   - Evidence: Presents data/facts
   - Analysis: Interprets evidence
   - Transition: Connects ideas
   - Conclusion: Summarizes/concludes

3. VOICE
   - Active: Subject performs action
   - Passive: Subject receives action

4. AI PATTERNS
   - Dominance of simple sentences (> 60% is AI-like)
   - Lack of complex/compound-complex sentences
   - Uniform sentence structure

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "sentences": [
        {{
            "index": 0,
            "text": "The study examines...",
            "paragraph_index": 0,
            "word_count": 15,
            "sentence_type": "simple|compound|complex|compound_complex",
            "function_role": "topic|evidence|analysis|transition|conclusion",
            "has_subordinate": false,
            "clause_depth": 0,
            "voice": "active|passive",
            "opener_word": "the"
        }}
    ],
    "sentence_count": 25,
    "type_distribution": {{
        "simple": 15,
        "compound": 5,
        "complex": 4,
        "compound_complex": 1
    }},
    "issues": [
        {{
            "type": "simple_dominance|no_complex|uniform_structure",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["sent_0", "sent_1"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for sentence structure improvement

        Returns template with placeholders: {document_text}, {selected_issues}, {locked_terms}, {user_notes}
        """
        return """You are an expert academic writing editor. Improve sentence structure to address:

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
2. Combine simple sentences into compound/complex where appropriate
3. Add subordinate clauses to create complexity
4. Vary sentence types throughout
5. Target: < 50% simple sentences
6. Maintain meaning while improving structure

Return the improved document text only.
"""
