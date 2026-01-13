"""
Step 5.1 Handler: Fingerprint Detection (AI指纹检测)
Layer 1 Lexical Level - LLM-based analysis

Detect AI fingerprint words and phrases using LLM.
使用LLM检测AI指纹词汇和短语。
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step5_1Handler(BaseSubstepHandler):
    """Handler for Step 5.1: Fingerprint Detection"""

    def get_analysis_prompt(self) -> str:
        """Generate prompt for AI fingerprint detection

        Returns template with placeholders: {document_text}, {locked_terms}
        """
        return """You are an expert in detecting AI-generated text through lexical analysis.

Analyze the following document for AI fingerprints:

<document>
{document_text}
</document>

<locked_terms>
{locked_terms}
</locked_terms>

Detect three types of AI fingerprints:

TYPE A - DEAD GIVEAWAYS (Single words that scream AI):
- "delve" (AI favorite)
- "utilize" (instead of "use")
- "facilitate" (overused by AI)
- "leverage" (business AI speak)
- "aforementioned" (overly formal)
- "plethora" (AI overuses this)
- "myriad" (AI favorite)
- "pivotal" (AI cliche)
- "paramount" (AI cliche)
- "comprehensive" (overused)
- "robust" (AI favorite)
- "intricate" (AI overuses)
- "underscore" (AI favorite)
- "showcase" (AI cliche)
- "foster" (AI favorite)
- "realm" (AI fantasy word)
- "landscape" (AI metaphor)
- "navigate" (AI metaphor)
- "embark" (AI dramatic)
- "streamline" (AI business speak)

TYPE B - CLICHES (Phrases AI loves):
- "plays a crucial role"
- "is of paramount importance"
- "it is worth noting"
- "it is important to note"
- "in today's world"
- "in the modern era"
- "a wide range of"
- "various aspects of"
- "this underscores the importance"
- "has become increasingly"
- "needless to say"
- "it goes without saying"

TYPE C - FILLER PHRASES (Padding):
- "as previously mentioned"
- "it can be argued that"
- "in light of the above"
- "with this in mind"
- "taking into account"

Return your analysis as JSON:
{{
    "risk_score": 0-100,
    "risk_level": "low|medium|high",
    "type_a_words": [
        {{
            "word": "delve",
            "count": 2,
            "positions": ["para_1_sent_3", "para_4_sent_1"],
            "severity": "high"
        }}
    ],
    "type_b_words": [
        {{
            "phrase": "plays a crucial role",
            "count": 1,
            "positions": ["para_2_sent_5"],
            "severity": "high"
        }}
    ],
    "type_c_phrases": [
        {{
            "phrase": "as previously mentioned",
            "count": 1,
            "positions": ["para_3_sent_1"],
            "severity": "medium"
        }}
    ],
    "total_fingerprints": 4,
    "fingerprint_density": 0.8,
    "ppl_score": null,
    "ppl_risk_level": null,
    "issues": [
        {{
            "type": "type_a_fingerprint|type_b_cliche|type_c_filler",
            "description": "English description",
            "description_zh": "中文描述",
            "severity": "high|medium|low",
            "affected_positions": ["para_1_sent_3"],
            "fix_suggestions": ["Replace 'delve' with 'examine' or 'explore'"],
            "fix_suggestions_zh": ["将 'delve' 替换为 'examine' 或 'explore'"]
        }}
    ],
    "recommendations": ["English recommendations"],
    "recommendations_zh": ["中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """Generate prompt for fingerprint removal

        Returns template with placeholders: {document_text}, {locked_terms}, {selected_issues}, {user_notes}
        """
        return """You are an expert academic writing editor. Remove AI fingerprints to address:

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

REPLACEMENTS:
Type A words:
- "delve" -> "examine", "explore", "investigate"
- "utilize" -> "use"
- "facilitate" -> "help", "enable", "allow"
- "leverage" -> "use", "apply"
- "plethora" -> "many", "numerous", "variety"
- "myriad" -> "many", "various"
- "pivotal" -> "key", "central", "important"
- "paramount" -> "critical", "essential"
- "comprehensive" -> "thorough", "complete"
- "robust" -> "strong", "solid"
- "intricate" -> "complex", "detailed"
- "underscore" -> "emphasize", "highlight"
- "showcase" -> "show", "demonstrate"
- "foster" -> "encourage", "promote"
- "realm" -> "area", "field", "domain"
- "landscape" -> "situation", "environment"
- "navigate" -> "handle", "manage"
- "embark" -> "start", "begin"
- "streamline" -> "simplify", "improve"

Type B cliches - Rewrite completely:
- "plays a crucial role" -> use specific verbs
- "is of paramount importance" -> explain why specifically
- "it is worth noting" -> just state the point
- "in today's world" -> be specific about time/context

Type C fillers - DELETE or rewrite:
- "as previously mentioned" -> remove or repeat key point
- "it can be argued that" -> just argue it

Requirements:
1. PRESERVE all locked terms exactly
2. Replace ALL Type A words
3. Rewrite ALL Type B cliches
4. Remove ALL Type C fillers
5. Maintain original meaning

Return the cleaned document text only.
"""
