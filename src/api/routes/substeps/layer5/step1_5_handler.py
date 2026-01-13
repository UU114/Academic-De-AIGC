"""
Step 1.5 Handler: Transitions & Connectors
步骤1.5处理器：衔接与连接词

Provides LLM-based analysis and rewriting for:
- Explicit connectors at paragraph openings
- Formulaic topic sentences
- Too-smooth transitions
- Summary endings
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step1_5Handler(BaseSubstepHandler):
    """
    Handler for Step 1.5: Transitions & Connectors
    步骤1.5处理器：衔接与连接词
    """

    def get_analysis_prompt(self) -> str:
        """
        Analysis prompt for detecting transition and connector patterns
        检测过渡和连接词模式的分析prompt
        """
        return """You are an academic document transition analyzer. Analyze PARAGRAPH TRANSITIONS and CONNECTOR USAGE only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Detect Explicit Connectors at Paragraph Openings (显性连接词)**
   - AI-like: "Furthermore, ...", "Moreover, ...", "Additionally, ...", "However, ..."
   - Human-like: Implicit semantic connection, lexical echoes

2. **Detect Formulaic Topic Sentences (公式化主题句)**
   - AI-like: Every paragraph starts with "This study...", "The results show..."
   - Human-like: Varied sentence openers

3. **Detect Too-Smooth Transitions (过度平滑过渡)**
   - AI-like: Every paragraph seamlessly connects with perfect logical flow
   - Human-like: Some abrupt topic shifts are natural

4. **Detect Summary Endings (公式化总结结尾)**
   - AI-like: Paragraphs end with "Thus, ...", "Therefore, ...", "In summary, ..."
   - Human-like: Varied endings, some abrupt

## LOCKED TERMS:
{locked_terms}
Preserve these terms exactly as they appear. Do NOT modify them.

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "issues": [
    {{
      "type": "explicit_connector|formulaic_topic_sentence|too_smooth_transition|summary_ending",
      "description": "Brief English description (1 sentence)",
      "description_zh": "简短中文描述（1句话）",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices or transition points"],
      "evidence": "Specific connector words or formulaic patterns found (2-3 examples)",
      "detailed_explanation": "Explain why this connector/transition pattern is AI-like and how it differs from human writing (2-3 sentences)",
      "detailed_explanation_zh": "详细解释为什么这种连接词/过渡模式是AI特征以及与人类写作的区别（2-3句）",
      "connector_word": "Furthermore|Moreover|However|...",
      "fix_suggestions": [
        "Replace explicit connector with lexical echo",
        "Create implicit semantic connection",
        "Vary sentence openers"
      ],
      "fix_suggestions_zh": [
        "用词汇呼应替换显性连接词",
        "创建隐性语义连接",
        "变化句子开头"
      ]
    }}
  ],
  "connector_density": "X connectors per 100 words",
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["Overall English recommendations"],
  "recommendations_zh": ["整体中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """
        Rewrite prompt for fixing transition and connector issues
        修复过渡和连接词问题的改写prompt
        """
        return """You are an academic document transition optimizer. Remove explicit connectors and create implicit semantic connections while preserving locked terms.

## ORIGINAL DOCUMENT:
{document_text}

## SELECTED ISSUES TO FIX:
{selected_issues}

## USER'S ADDITIONAL GUIDANCE:
{user_notes}

## LOCKED TERMS (MUST PRESERVE):
{locked_terms}
These terms must appear EXACTLY as shown. Do NOT modify, rephrase, or translate them.

## MODIFICATION STRATEGIES:

**For Explicit Connectors:**
- Replace "Furthermore, ..." with lexical echo (repeat key term from previous paragraph)
- Replace "However, ..." with contrasting content word
- Use implicit semantic connection instead of explicit markers

**For Formulaic Topic Sentences:**
- Vary paragraph openers: start with context, evidence, or question
- Avoid repetitive patterns like "This study...", "The results..."

**For Too-Smooth Transitions:**
- Allow some abrupt topic shifts (natural in human writing)
- Don't force perfect logical flow everywhere

**For Summary Endings:**
- Remove "Thus, ...", "Therefore, ..." endings
- Let paragraphs end naturally without forced summaries
- Vary ending styles

## CONSTRAINTS:
1. Preserve all content and arguments
2. Maintain overall coherence
3. Keep locked terms EXACTLY as listed
4. Output full modified document
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with improved transitions",
  "changes_summary_zh": "中文修改总结：列出具体做了哪些过渡修改（例如：1) 移除了5个'Furthermore'连接词；2) 用词汇呼应替换了显性过渡；3) 变化了段落开头模式）",
  "changes_count": number_of_transitions_modified,
  "issues_addressed": ["issue types"],
  "new_connector_density": "X per 100 words"
}}
"""
