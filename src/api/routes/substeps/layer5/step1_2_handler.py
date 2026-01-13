"""
Step 1.2 Handler: Paragraph Length Regularity
步骤1.2处理器：段落长度规律性

Provides LLM-based analysis and rewriting for paragraph length patterns:
- Uniform paragraph length (CV < 0.30)
- Split/expand/merge suggestions
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step1_2Handler(BaseSubstepHandler):
    """
    Handler for Step 1.2: Paragraph Length Regularity
    步骤1.2处理器：段落长度规律性
    """

    def get_analysis_prompt(self) -> str:
        """
        Analysis prompt for detecting paragraph length uniformity
        检测段落长度均匀性的分析prompt
        """
        return """You are an academic document paragraph length analyzer. Analyze PARAGRAPH LENGTH DISTRIBUTION only.

## DOCUMENT TEXT:
{document_text}

## IMPORTANT: PARAGRAPH IDENTIFICATION RULES
Before analyzing, you MUST identify ONLY actual body paragraphs. EXCLUDE:
- Section titles/headers (e.g., "Introduction", "1. Methods", "Chapter 2")
- Figure captions (e.g., "Figure 1: ...", "Fig. 2...")
- Table headers (e.g., "Table 1: ...", "Tab. 3...")
- Keywords lines (e.g., "Keywords: ...")
- Reference entries (e.g., "[1] Smith, J. (2020)...")
- Abstract label, Author names, Affiliations
- Any line with fewer than 10 words that appears to be a header

Only count substantive body paragraphs with actual content (typically 30+ words).

## YOUR TASKS:

### TASK 1: Count and List Body Paragraphs
- Identify each body paragraph (exclude non-body content per rules above)
- Count words in each paragraph
- Report: total paragraph count, word counts per paragraph

### TASK 2: Calculate Statistics
- Mean paragraph length (words)
- Standard deviation
- CV (Coefficient of Variation) = stdev / mean
- Min and max paragraph lengths

### TASK 3: Evaluate Against Criteria
- AI-like: CV < 0.30 (paragraphs too uniform in length)
- Borderline: 0.30 ≤ CV < 0.40
- Human-like: CV ≥ 0.40 (healthy natural variation)

### TASK 4: Provide Analysis Conclusion
ALWAYS provide a conclusion, even if no issues found:
- If CV < 0.30: Report as HIGH risk issue with specific fix suggestions
- If 0.30 ≤ CV < 0.40: Report as MEDIUM risk with improvement suggestions
- If CV ≥ 0.40: Report as LOW risk / PASS with positive summary

## LOCKED TERMS:
{locked_terms}

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "paragraph_analysis": {{
    "total_body_paragraphs": 15,
    "paragraph_lengths": [45, 78, 120, 95, ...],
    "excluded_items": ["Title: Introduction", "Figure 1: ...", "Keywords: ..."]
  }},
  "statistics": {{
    "mean_length": 85.5,
    "stdev_length": 32.1,
    "cv": 0.375,
    "min_length": 32,
    "max_length": 185
  }},
  "issues": [
    {{
      "type": "uniform_length|length_variation_ok",
      "description": "Brief English description (1 sentence)",
      "description_zh": "简短中文描述（1句话）",
      "severity": "high|medium|low",
      "affected_positions": ["paragraph indices if applicable"],
      "evidence": "Show current CV value and length distribution",
      "detailed_explanation": "Explain the finding (2-3 sentences)",
      "detailed_explanation_zh": "详细解释发现（2-3句）",
      "current_cv": 0.xx,
      "target_cv": 0.40,
      "split_candidates": ["para_index: reason"],
      "expand_candidates": ["para_index: reason"],
      "merge_candidates": [["para1_index", "para2_index", "reason"]],
      "fix_suggestions": ["Specific suggestion 1", "Specific suggestion 2"],
      "fix_suggestions_zh": ["具体建议1", "具体建议2"]
    }}
  ],
  "risk_score": 0-100,
  "risk_level": "high|medium|low",
  "summary": "One-sentence summary of the analysis result",
  "summary_zh": "分析结果的一句话总结",
  "recommendations": ["Overall English recommendations"],
  "recommendations_zh": ["整体中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """
        Rewrite prompt for fixing paragraph length uniformity
        修复段落长度均匀性的改写prompt
        """
        return """You are an academic document paragraph length optimizer. Apply paragraph length adjustments to achieve natural variation while preserving content quality and locked terms.

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

**Split Strategy (拆分):**
- Break long paragraphs at natural topic shifts
- Create varied lengths: one long parent → one short + one medium child

**Expand Strategy (扩展):**
- Add concrete examples, case studies, or elaborations
- Avoid generic filler; add substantive content

**Merge Strategy (合并):**
- Combine fragmented paragraphs that discuss the same subtopic
- Create longer, cohesive paragraphs for key sections

**Target Distribution:**
- Short paragraphs: 30-60 words (10-20%)
- Medium paragraphs: 80-120 words (50-60%)
- Long paragraphs: 150-250 words (20-30%)
- Target CV ≥ 0.40

## CONSTRAINTS:
1. Preserve all factual content
2. Maintain logical flow
3. Keep locked terms EXACTLY as listed
4. Output full modified document
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full document with adjusted paragraph lengths",
  "changes_summary_zh": "中文修改总结：描述拆分/扩展/合并的具体操作（例如：1) 将第3段拆分为两个段落；2) 扩展了第5段添加案例；3) 合并了第7、8段）",
  "changes_count": number_of_paragraphs_modified,
  "issues_addressed": ["uniform_length"],
  "new_cv": 0.xx
}}
"""
