"""
Step 1.3 Handler: Progression Pattern & Closure
步骤1.3处理器：推进模式与闭合

Provides LLM-based analysis and rewriting for:
- Monotonic progression (单调推进)
- Too-strong closure (过度闭合)
- Missing qualification (缺少条件限定)
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step1_3Handler(BaseSubstepHandler):
    """
    Handler for Step 1.3: Progression Pattern & Closure
    步骤1.3处理器：推进模式与闭合
    """

    def get_analysis_prompt(self) -> str:
        """
        Analysis prompt for detecting progression and closure patterns
        检测推进和闭合模式的分析prompt
        """
        return """You are an academic document progression analyzer. Analyze PROGRESSION PATTERN and CLOSURE STRENGTH only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

1. **Detect Monotonic Progression (单调推进)**
   - Check for linear, step-by-step topic advancement without回溯
   - AI-like: Topic A → Topic B → Topic C (never revisits A or B)
   - Human-like: Topic A → Topic B → back to A with new insight → Topic C

2. **Detect Too-Strong Closure (过度闭合)**
   - Check for formulaic conclusion patterns
   - AI-like: "In conclusion, this study has shown...", "To summarize..."
   - Human-like: Open questions, unresolved tensions, future research needs

3. **Detect Missing Conditional/Qualification (缺少条件限定)**
   - AI tends to make absolute statements
   - Human-like: "In certain contexts...", "Under these conditions...", "However..."

## LOCKED TERMS:
{locked_terms}
Preserve these terms exactly as they appear. Do NOT modify them.

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "issues": [
    {{
      "type": "monotonic_progression|too_strong_closure|missing_qualification",
      "description": "Brief English description (1 sentence)",
      "description_zh": "简短中文描述（1句话）",
      "severity": "high|medium|low",
      "affected_positions": ["section or paragraph indices"],
      "evidence": "Specific text excerpts showing the pattern (2-3 examples)",
      "detailed_explanation": "Detailed explanation of why this is an AI-like pattern and how it differs from human argumentation (2-3 sentences)",
      "detailed_explanation_zh": "详细解释为什么这是AI模式以及与人类论证的区别（2-3句）",
      "fix_suggestions": [
        "Specific actionable suggestion 1",
        "Specific actionable suggestion 2",
        "Specific actionable suggestion 3"
      ],
      "fix_suggestions_zh": [
        "具体可操作的建议1",
        "具体可操作的建议2",
        "具体可操作的建议3"
      ]
    }}
  ],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["Overall English recommendations"],
  "recommendations_zh": ["整体中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """
        Rewrite prompt for fixing progression and closure issues
        修复推进和闭合问题的改写prompt
        """
        return """You are an academic document progression optimizer. Apply the following modifications to create more human-like argumentation flow while preserving locked terms.

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

**For Monotonic Progression:**
- Add回溯: After introducing Topic B, revisit Topic A with new perspective
- Add conditional logic: "In contrast to X, when Y conditions apply..."
- Introduce non-sequential discussion

**For Too-Strong Closure:**
- Soften conclusions: Replace "This proves..." with "This suggests..."
- Add open questions: "Future research should explore..."
- Leave some tensions unresolved

**For Missing Qualification:**
- Add hedging: "may", "appears to", "in most cases"
- Add contextual conditions: "Under these specific conditions..."
- Add counter-examples or exceptions

## CONSTRAINTS:
1. Preserve all core arguments and evidence
2. Maintain academic credibility
3. Keep locked terms EXACTLY as listed
4. Output full modified document
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with improved progression logic",
  "changes_summary_zh": "中文修改总结：列出具体做了哪些推进模式调整（例如：1) 在讨论方法B后回溯到方法A进行对比；2) 软化了结论的绝对性；3) 添加了条件限定语）",
  "changes_count": number_of_modifications,
  "issues_addressed": ["issue types"]
}}
"""
