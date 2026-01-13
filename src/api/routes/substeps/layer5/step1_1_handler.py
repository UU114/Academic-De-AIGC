"""
Step 1.1 Handler: Structure Framework Detection
步骤1.1处理器：结构框架检测

Provides LLM-based analysis and rewriting for structural patterns:
- Linear flow (First-Second-Third)
- Repetitive patterns
- Uniform length
- Predictable order
- Symmetry
"""

from src.api.routes.substeps.base_handler import BaseSubstepHandler


class Step1_1Handler(BaseSubstepHandler):
    """
    Handler for Step 1.1: Structure Framework Detection
    步骤1.1处理器：结构框架检测
    """

    def get_analysis_prompt(self) -> str:
        """
        Analysis prompt for detecting structural AI patterns
        检测结构性AI模式的分析prompt
        """
        return """You are an academic document structure analyzer. Analyze the GLOBAL STRUCTURAL PATTERNS only.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

### TASK A: SECTION IDENTIFICATION (章节识别) - REQUIRED
First, identify the document's logical sections based on content, NOT just paragraph breaks.
Look for:
- Explicit section headers (e.g., "Introduction", "Methods", "1.", "2.")
- Topic shifts between paragraphs
- Structural markers (transition words, conclusion phrases)

For each section, determine:
- role: introduction|background|literature_review|method|methodology|results|discussion|conclusion|body|abstract
- title: The section's explicit title if present, or a brief descriptive title based on content
- paragraph_count: Number of paragraphs in this section
- word_count: Approximate word count for this section

### TASK B: AI PATTERN DETECTION (AI模式检测)

1. **Detect Linear Flow Pattern (线性流动)**
   - Look for "First...Second...Third" or "Initially...Subsequently...Finally" enumeration
   - Check if sections progress in a formulaic, step-by-step manner
   - AI-like: Predictable sequential progression
   - Human-like: Non-linear, with回溯, jumps, or conditional logic

2. **Detect Repetitive Pattern (重复模式)**
   - Check if multiple sections have identical structures
   - Example: All sections follow "Problem → Analysis → Solution" pattern
   - AI-like: Copy-paste section structure
   - Human-like: Varied section approaches based on content needs

3. **Detect Uniform Length (均匀长度)**
   - Calculate coefficient of variation (CV) of paragraph word counts
   - AI-like: CV < 0.30 (all paragraphs similar length)
   - Human-like: CV ≥ 0.40 (varied paragraph lengths)

4. **Detect Predictable Order (可预测顺序)**
   - Check if sections follow formulaic academic order
   - AI-like: Perfect Intro → Literature → Method → Results → Discussion → Conclusion
   - Human-like: Some sections merged, reordered, or unconventional structure

5. **Detect Symmetry (对称结构)**
   - Check if all sections have equal number of paragraphs
   - AI-like: All sections have exactly 3-4 paragraphs
   - Human-like: Asymmetric distribution based on content importance

## LOCKED TERMS:
{locked_terms}
Preserve these terms exactly as they appear. Do NOT modify them in any analysis.

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "sections": [
    {{
      "index": 0,
      "role": "introduction|background|literature_review|method|methodology|results|discussion|conclusion|body|abstract",
      "title": "Section title or descriptive name",
      "paragraph_count": 2,
      "word_count": 150
    }}
  ],
  "structure_pattern": "AI-typical|Human-like|Mixed|Unknown",
  "issues": [
    {{
      "type": "linear_flow|repetitive_pattern|uniform_length|predictable_order|symmetry",
      "description": "Brief English description (1 sentence)",
      "description_zh": "简短中文描述（1句话）",
      "severity": "high|medium|low",
      "affected_positions": ["section numbers or paragraph positions"],
      "evidence": "Specific text excerpts showing the pattern (2-3 examples)",
      "detailed_explanation": "Detailed explanation of why this is an AI-like pattern and how it differs from human writing (2-3 sentences)",
      "detailed_explanation_zh": "详细解释为什么这是AI模式以及与人类写作的区别（2-3句）",
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
  "recommendations": ["Overall English recommendations for the document"],
  "recommendations_zh": ["整体中文建议"]
}}
"""

    def get_rewrite_prompt(self) -> str:
        """
        Rewrite prompt for fixing structural issues
        修复结构问题的改写prompt
        """
        return """You are an academic document restructuring expert. Apply the following modifications to DISRUPT AI-like structural patterns while PRESERVING content quality and locked terms.

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

**For Linear Flow:**
- Break "First...Second...Third" progression
- Introduce non-sequential logic (e.g., discuss outlier first, then general case)
- Add conditional transitions ("In certain contexts...", "However, when...")

**For Repetitive Pattern:**
- Vary section structures (some sections detailed, some concise)
- Use different organizational approaches per section

**For Uniform Length:**
- Create intentional length asymmetry
- Expand critical sections, compress routine content
- Target CV ≥ 0.40

**For Predictable Order:**
- Merge or reorder sections if logical
- Example: Combine Literature + Methodology, or present Results before Method rationale

**For Symmetry:**
- Redistribute paragraphs asymmetrically
- Key sections get more paragraphs, routine sections get fewer

## CONSTRAINTS:
1. Preserve all factual content and arguments
2. Maintain academic rigor and citation accuracy
3. Keep locked terms EXACTLY as listed
4. Output full modified document (not just changes)
5. Write in the same language as the original document

## OUTPUT FORMAT (JSON only, no markdown code blocks):
{{
  "modified_text": "Full rewritten document with structural changes applied",
  "changes_summary_zh": "中文修改总结：列出具体做了哪些结构调整，例如：1) 打破了First-Second-Third线性模式，改为条件式推进；2) 重新分配段落长度，扩展了方法论章节；3) 调整章节顺序，将结果讨论融入方法部分",
  "changes_count": 3,
  "issues_addressed": ["linear_flow", "uniform_length", "predictable_order"]
}}
"""
