"""
Step 1.4 Handler: Anchor Density
步骤1.4处理器：锚点密度

Provides LLM-based analysis and rewriting for concrete anchor density:
- Decimal numbers, percentages, statistical values
- Citations, units/measurements, chemical formulas
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step1_4Handler(BaseSubstepHandler):
    """
    Handler for Step 1.4: Anchor Density
    步骤1.4处理器：锚点密度
    """

    def get_analysis_prompt(self) -> str:
        """
        Analysis prompt for detecting anchor density
        检测锚点密度的分析prompt
        """
        return """You are an academic document anchor density analyzer. Analyze CONCRETE ANCHOR DENSITY only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASK:

Count the density of concrete anchors (evidence that LLMs can't fabricate):

**Anchor Types:**
1. Decimal numbers: 14.2, 3.56, 0.82 (weight: 1.0)
2. Percentages: 50%, 14.2% (weight: 1.2)
3. Statistical values: p < 0.05, r = 0.82, t-test (weight: 1.5)
4. Citations: [1], (Smith, 2020), et al. (weight: 1.5)
5. Units/measurements: 5mL, 20°C, 3kg (weight: 1.3)
6. Chemical formulas: H2O, CO2, C6H12O6 (weight: 1.2)

**Density Calculation:**
- Weighted anchor count per 100 words
- AI hallucination risk:
  - Density < 5.0: High risk (vague, abstract)
  - Density 5.0-10.0: Medium risk
  - Density > 10.0: Low risk (具体、可验证)

**Identify Low-Density Paragraphs:**
- Mark paragraphs with density < 3.0 as high-risk AI filler

## LOCKED TERMS:
{locked_terms}
Context: These terms will not be modified in rewriting.

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "issues": [
    {{
      "type": "low_anchor_density",
      "description": "Brief English description of the low density issue (1 sentence)",
      "description_zh": "简短中文描述锚点密度问题（1句话）",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices"],
      "evidence": "Show examples of vague paragraphs lacking concrete anchors",
      "detailed_explanation": "Explain why low anchor density suggests AI-generated abstract filler and how it differs from human academic writing (2-3 sentences)",
      "detailed_explanation_zh": "详细解释为什么低锚点密度表明AI生成的抽象内容以及与人类学术写作的区别（2-3句）",
      "current_density": 0.xx,
      "target_density": 5.0,
      "missing_anchor_types": ["statistical_values", "citations"],
      "fix_suggestions": [
        "Add specific statistical values (e.g., p-values, percentages)",
        "Include concrete citations and references",
        "Replace vague terms with specific measurements"
      ],
      "fix_suggestions_zh": [
        "添加具体统计值（如p值、百分比）",
        "包含具体引用和参考文献",
        "用具体测量值替换模糊术语"
      ]
    }}
  ],
  "overall_density": 0.xx,
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "recommendations": ["Overall English recommendations"],
  "recommendations_zh": ["整体中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """
        Rewrite prompt for enhancing anchor density
        增强锚点密度的改写prompt
        """
        return """You are an academic document anchor enhancement expert. Add concrete, verifiable anchors to low-density paragraphs while preserving locked terms.

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

**For Low Anchor Density:**
- Add specific numbers: Replace "many" with "73%", "most" with "85%"
- Add citations: Reference existing literature (user must verify)
- Add statistical evidence: p-values, correlation coefficients
- Add measurements: Specific quantities, temperatures, concentrations
- Replace vague statements with concrete examples

**WARNING:**
- Do NOT fabricate data or citations
- If specific values are unknown, use placeholders like "[AUTHOR, YEAR]" or "[XX%]"
- User must fill in real values

**Target Density:** ≥ 5.0 anchors per 100 words

## CONSTRAINTS:
1. Do NOT invent false data or citations
2. Use placeholders if specific values are unknown
3. Keep locked terms EXACTLY as listed
4. Output full modified document
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with added concrete anchors (use placeholders if needed)",
  "changes_summary_zh": "中文修改总结：描述添加的锚点类型（例如：1) 添加了3个统计值；2) 插入了5个引用占位符；3) 用具体百分比替换了模糊描述）",
  "changes_count": number_of_anchors_added,
  "issues_addressed": ["low_anchor_density"],
  "new_overall_density": 0.xx,
  "placeholders_needing_verification": ["list of placeholders user must replace with real values"]
}}
"""
