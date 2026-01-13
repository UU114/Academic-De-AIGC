"""
Step 4.4 Handler: Connector Optimization (连接词优化)
Layer 2 Sentence Level - LLM-based analysis

Analyze and optimize sentence connectors using LLM.
使用LLM分析并优化句子连接词。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step4_4Handler(BaseSubstepHandler):
    """Handler for Step 4.4: Connector Optimization"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for connector optimization analysis

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert academic writing analyst specializing in detecting AI-generated content patterns.

Analyze sentence connectors and transitions in the following document:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Analyze connector usage and identify optimization opportunities:

1. CONNECTOR TYPES
   - Additive: Also, Furthermore, Moreover, In addition, Additionally
   - Adversative: However, Nevertheless, On the other hand, Conversely
   - Causal: Therefore, Thus, Consequently, As a result, Hence
   - Sequential: First, Second, Finally, Then, Next
   - Exemplifying: For example, For instance, Such as, Specifically

2. AI DETECTION PATTERNS
   - Overuse of additive connectors (Furthermore, Moreover) = AI-like
   - Formulaic sequences (First... Second... Third...) = AI-like
   - Connector at start of almost every sentence = AI-like
   - Lack of implicit connections = AI-like
   - Repetitive connector patterns = AI-like

3. CONNECTOR DENSITY
   - High density (> 30% of sentences start with connector) = AI-like
   - Target: 15-25% explicit connectors
   - Rest should use implicit logical flow

4. VARIETY ANALYSIS
   - AI tends to repeat same connectors
   - Human writing uses diverse connectors
   - Or uses no connector (implicit logic)

5. OPTIMIZATION OPPORTUNITIES
   - Remove unnecessary connectors
   - Replace overused connectors with alternatives
   - Use implicit transitions where appropriate
   - Break sequential patterns

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "connector_instances": [
        {{
            "sentence_index": 2,
            "connector": "Furthermore",
            "connector_type": "additive",
            "position": "start|middle|end",
            "necessary": true,
            "suggestion": "Remove or replace with implicit connection"
        }}
    ],
    "connector_types": {{
        "additive": 5,
        "adversative": 2,
        "causal": 3,
        "sequential": 4,
        "exemplifying": 1
    }},
    "connector_density": 0.35,
    "repeated_connectors": [
        {{
            "connector": "Furthermore",
            "count": 4,
            "sentence_indices": [2, 5, 8, 12]
        }}
    ],
    "sequential_patterns": [
        {{
            "pattern": "First-Second-Third",
            "sentence_indices": [3, 4, 5],
            "suggestion": "Vary transitions or remove some"
        }}
    ],
    "issues": [
        {{
            "type": "high_density|repetition|sequential_pattern|overuse_additive",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["sent_2", "sent_5"],
            "fix_suggestions": ["suggestion"],
            "fix_suggestions_zh": ["建议"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for connector optimization

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Optimize connector usage to address:

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
2. Remove excessive connectors:
   - Delete "Furthermore" / "Moreover" where not needed
   - Let logical flow speak for itself
   - Use implicit transitions where appropriate
3. Break sequential patterns:
   - "First... Second... Third..." -> varied or implicit transitions
   - Replace with context-specific transitions
4. Diversify connector types:
   - Replace repeated connectors with alternatives
   - Balance additive, adversative, causal types
5. Optimize connector density:
   - Target: 15-25% of sentences with explicit connectors
   - Remove connectors where logic is self-evident
6. Use varied positions:
   - Not always at sentence start
   - Embed connectors mid-sentence when natural
7. Alternative strategies:
   - Use pronouns to link ideas
   - Use semantic connections instead of explicit markers
   - Rely on paragraph structure for flow

Return the optimized document text only.
"""
