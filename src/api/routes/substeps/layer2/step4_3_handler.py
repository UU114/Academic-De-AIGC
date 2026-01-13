"""
Step 4.3 Handler: Sentence Merge Suggestions (句子合并建议)
Layer 2 Sentence Level - LLM-based analysis

Analyze and suggest sentence merges to improve flow using LLM.
使用LLM分析并建议句子合并以改善文章流畅度。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_3Handler(BaseSubstepHandler):
    """Handler for Step 4.3: Sentence Merge Suggestions"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for merge suggestion analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze sentence merge opportunities in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Identify sentence merge candidates based on:

1. ADJACENT SHORT SENTENCES
   - Two or more consecutive short sentences (< 15 words each)
   - Creates choppy, robotic flow (AI-like pattern)
   - Could be combined for better rhythm

2. SAME SUBJECT/TOPIC
   - Adjacent sentences about the same subject
   - Repeated subject pronouns (It... It... It...)
   - Could share a single subject

3. CAUSE-EFFECT RELATIONSHIPS
   - Adjacent sentences with causal relationship
   - "X happened. Y resulted." -> "X happened, resulting in Y"
   - Natural connection not utilizing connectors

4. PARALLEL STRUCTURE
   - Adjacent sentences with parallel structure
   - Could be combined with "and" or semicolon
   - Example: "A does X. B does Y." -> "A does X, and B does Y."

5. EXAMPLE/ELABORATION
   - A general statement followed by specific example
   - Could use colon or dash to combine
   - "Studies show X. For example, Y found Z."

6. AI PATTERNS TO FIX
   - Excessive sentence fragmentation = AI-like
   - Too many simple sentences in sequence = AI-like
   - Lack of complex sentence structures = AI-like

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "merge_candidates": [
        {{
            "paragraph_index": 0,
            "sentence_indices": [2, 3],
            "sentences": ["First sentence text.", "Second sentence text."],
            "merge_type": "short_adjacent|same_subject|cause_effect|parallel|elaboration",
            "reason": "Why these should be merged",
            "reason_zh": "合并原因",
            "suggested_merge": "Suggested merged sentence",
            "suggested_merge_zh": "建议合并后的句子",
            "confidence": "high|medium|low"
        }}
    ],
    "fragmentation_score": 0.35,
    "short_sentence_ratio": 0.4,
    "issues": [
        {{
            "type": "excessive_fragmentation|choppy_flow|repeated_subject|missed_connection",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_0_sent_2", "para_0_sent_3"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for sentence merging

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Merge sentences to improve flow and address:

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
2. Merge adjacent short sentences:
   - Use coordinating conjunctions (and, but, yet)
   - Use subordinating conjunctions (because, although, when)
   - Use relative clauses (which, that, who)
   - Use semicolons for closely related ideas
3. Eliminate choppy flow:
   - Combine sentences with same subject
   - Connect cause-effect relationships
   - Merge general statements with examples
4. Maintain readability:
   - Don't create overly long sentences (> 45 words)
   - Preserve paragraph structure
   - Keep logical flow clear
5. Vary sentence structure:
   - Mix simple, compound, and complex sentences
   - Avoid monotonous patterns

Return the improved document text only.
"""
