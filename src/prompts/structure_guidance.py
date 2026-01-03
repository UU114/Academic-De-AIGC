"""
Structure Guidance Prompts for Level 1 Guided Interaction
Level 1 指引式交互的结构指导提示词

This module contains prompts for generating detailed guidance
for structure issues in academic papers.
"""

# =============================================================================
# Issue Type Definitions
# 问题类型定义
# =============================================================================

# Issue types that can generate reference versions
# 可以生成参考版本的问题类型
REFERENCEABLE_ISSUES = {
    "explicit_connector",      # 显性连接词
    "linear_flow",            # 线性流程（可建议顺序调整）
    "predictable_structure",  # 可预测结构（可建议重组）
    "missing_semantic_echo",  # 缺少语义回声
    "formulaic_opening",      # 公式化开头
    "weak_transition",        # 薄弱过渡（可改写过渡句）
}

# Issue types that only provide advice (no reference)
# 只提供建议的问题类型（无参考版本）
ADVICE_ONLY_ISSUES = {
    "paragraph_too_short",    # 段落过短
    "paragraph_too_long",     # 段落过长
    "logic_gap",              # 逻辑断裂
    "missing_evidence",       # 缺少论据
    "uniform_length",         # 均匀段落长度
    "need_expansion",         # 需要扩展
}


# =============================================================================
# Main Guidance Generation Prompt
# 主指引生成提示词
# =============================================================================

STRUCTURE_ISSUE_GUIDANCE_PROMPT = """You are an expert academic writing consultant specializing in De-AIGC (removing AI writing patterns from academic papers).

## TASK
Generate specific, actionable guidance for fixing a structural issue in an academic paper. Your guidance should help the user understand WHY this is a problem and HOW to fix it.

## ISSUE INFORMATION
- **Issue Type**: {issue_type}
- **Issue Category**: {issue_category}
- **Severity**: {severity}
- **Brief Description**: {issue_description}

## CONTEXT

### Affected Text:
```
{affected_text}
```

### Position in Document: {position}

### Previous Paragraph (for context):
```
{prev_paragraph}
```

### Next Paragraph (for context):
```
{next_paragraph}
```

### Document Core Thesis (if available):
{core_thesis}

## CAN GENERATE REFERENCE: {can_generate_reference}

## REQUIREMENTS

### 1. Detailed Guidance (REQUIRED)
Provide comprehensive guidance in Chinese that includes:
- **问题分析**: WHY this is an AI writing pattern (with specific evidence/statistics if applicable)
- **改进策略**: WHAT strategies the user can use to fix it
- **具体建议**: HOW to implement the fix with step-by-step guidance

### 2. Reference Version (CONDITIONAL)
- If can_generate_reference is True: Generate a concrete rewritten version that removes the AI pattern
- If can_generate_reference is False: Set reference_version to null

### 3. Key Concepts (for semantic echo)
Extract key concepts from surrounding paragraphs that can be used for creating semantic connections.

## OUTPUT FORMAT (JSON)
{{
  "guidance_zh": "【问题分析】\\n详细解释为什么这是AI写作模式...\\n\\n【改进策略】\\n1. 策略一...\\n2. 策略二...\\n\\n【具体建议】\\n针对这段文字，建议...",
  "guidance_en": "Brief English summary of the guidance...",
  "reference_version": "The rewritten text that removes the AI pattern..." or null,
  "reference_explanation_zh": "解释为什么这样改写能消除AI痕迹" or null,
  "why_no_reference": "如果没有参考版本，解释原因（如：需要用户专业知识补充内容）" or null,
  "key_concepts": {{
    "from_prev": ["concept1", "concept2"],
    "from_next": ["concept3", "concept4"]
  }},
  "confidence": 0.85
}}

## CRITICAL RULES
1. guidance_zh MUST be detailed (at least 150 Chinese characters)
2. guidance_zh MUST use the format with【问题分析】【改进策略】【具体建议】sections
3. If generating reference_version, it MUST preserve the original academic meaning
4. Reference version should be in the SAME LANGUAGE as the original text
5. Be specific - quote actual text from the paragraph when explaining issues
6. Provide actionable advice, not generic suggestions
"""


# =============================================================================
# Issue-Specific Prompt Templates
# 问题类型专用提示词模板
# =============================================================================

ISSUE_SPECIFIC_PROMPTS = {

    # =========================================================================
    # Explicit Connector Issue
    # 显性连接词问题
    # =========================================================================
    "explicit_connector": """
## SPECIFIC CONTEXT: Explicit Connector Removal

The connector word "{connector_word}" at the beginning of this paragraph/sentence is a typical AI fingerprint.

### AI Writing Statistics:
- AI models use "Furthermore" 4.7x more frequently than human academic writers
- AI models use "Moreover" 3.2x more frequently than humans
- AI models use "Additionally" 2.8x more frequently than humans
- AI models use "However" at paragraph starts 2.1x more than humans

### Recommended Rewriting Strategies:
1. **Semantic Echo (语义回声)**: Reference a key concept from the previous paragraph to create natural flow
2. **Direct Connection**: Remove the connector entirely, let the meaning flow naturally
3. **Implicit Logic**: Use demonstrative pronouns (this, these, such findings)
4. **Concept Bridge**: Start with a concept that bridges both paragraphs

### Key Concepts from Previous Paragraph:
{prev_key_concepts}

### Example Transformations:
- "Furthermore, the results show..." → "This pattern of results indicates..."
- "Moreover, we found that..." → "The data reveals a consistent trend where..."
- "However, there are limitations..." → "These findings, while promising, face certain constraints..."

IMPORTANT: Generate a reference version that uses semantic echo or another natural transition strategy.
""",

    # =========================================================================
    # Paragraph Too Short Issue
    # 段落过短问题
    # =========================================================================
    "paragraph_too_short": """
## SPECIFIC CONTEXT: Short Paragraph

This paragraph has only {word_count} words, while neighboring paragraphs average {neighbor_avg} words.

### Why This Is an AI Signal:
Uniform paragraph length is a strong indicator of AI writing. AI tends to generate paragraphs of similar length, while human writers naturally vary paragraph length based on content complexity.

### Current Paragraph Length Distribution:
{length_distribution}

### Improvement Strategies (Advice Only - No Reference):
1. **Add Supporting Evidence**: Include specific examples, data points, or citations
2. **Discuss Limitations**: Add caveats, boundary conditions, or exceptions
3. **Provide Counterarguments**: Briefly acknowledge and address opposing views
4. **Expand Methodology Details**: If applicable, add procedural specifics
5. **Merge Option**: Consider combining with an adjacent paragraph if topically related

### Why No Reference Version:
Content expansion requires domain expertise and access to relevant literature that the system cannot provide. The user must decide what specific content to add based on their research materials.

DO NOT generate a reference version. Set reference_version to null.
Set why_no_reference to explain that content expansion requires the user's domain expertise and research materials.
""",

    # =========================================================================
    # Linear Flow Issue
    # 线性流程问题
    # =========================================================================
    "linear_flow": """
## SPECIFIC CONTEXT: Linear Flow Pattern

The document follows a predictable A→B→C→D linear structure that is characteristic of AI writing.

### Current Document Flow:
{current_flow}

### Why This Is an AI Signal:
AI models tend to generate content in a strictly linear, logical sequence. Human writers often use more dynamic narrative structures:
- Starting with a compelling finding
- Interleaving problems and solutions
- Using flashbacks or flash-forwards
- Building tension before resolution

### Disruption Strategies:
1. **Hook Opening (钩子开头)**: Start a section with a surprising finding, then explain the methodology
2. **Problem-Solution Interleave**: Alternate between presenting issues and approaches
3. **Inverted Pyramid**: Lead with conclusions, then provide supporting details
4. **Thematic Clustering**: Group by theme rather than chronological order

### Suggested Paragraph Reordering:
{suggested_reorder}

### Important Constraints:
- Introduction should generally remain first
- Conclusion should generally remain last
- Related evidence paragraphs should stay grouped
- Limit changes to 2-3 position swaps to maintain coherence

Generate guidance about which paragraphs could be reordered and why.
""",

    # =========================================================================
    # Missing Semantic Echo Issue
    # 缺少语义回声问题
    # =========================================================================
    "missing_semantic_echo": """
## SPECIFIC CONTEXT: Missing Semantic Echo

The transition from {from_position} to {to_position} lacks semantic connection. The paragraphs are only connected by structure, not by meaning.

### Previous Paragraph Ending:
"{prev_ending}"

### Current Paragraph Opening:
"{current_opening}"

### What is Semantic Echo?
Semantic echo is a technique where you reference key terms or concepts from the previous paragraph to create a natural bridge. Unlike explicit connectors ("Furthermore", "Moreover"), semantic echo creates implicit logical flow.

### Key Concepts Available for Echo:
From previous paragraph: {echo_candidates}

### Rewriting Strategies:
1. **Term Echo**: Repeat a key term from the previous paragraph
   - "This convergence behavior..." (echoing "convergence" from previous)
2. **Concept Reference**: Use a demonstrative phrase
   - "Such findings suggest..." / "These patterns indicate..."
3. **Logical Extension**: Extend the previous paragraph's conclusion
   - "Building on this observation..." (without using "Building on")

Generate a reference version for the opening 1-2 sentences that creates semantic echo.
""",

    # =========================================================================
    # Uniform Length Issue
    # 均匀段落长度问题
    # =========================================================================
    "uniform_length": """
## SPECIFIC CONTEXT: Uniform Paragraph Length

The document's paragraphs have suspiciously uniform lengths, which is a strong AI writing signal.

### Paragraph Length Statistics:
- Mean length: {mean_length} words
- Standard deviation: {std_dev} words
- Coefficient of variation: {cv}%
- Human writing typically has CV > 30%, this document has {cv}%

### Length Distribution:
{length_distribution}

### Why This Is Problematic:
Human writers naturally vary paragraph length based on:
- Complexity of the point being made
- Importance of the argument
- Need for examples or evidence
- Transitional requirements

### Improvement Strategies (Advice Only):
1. **Identify Key Arguments**: Expand paragraphs containing central claims
2. **Condense Supporting Points**: Shorten paragraphs with secondary information
3. **Vary by Function**: Introductory paragraphs can be shorter; evidence paragraphs longer
4. **Natural Rhythm**: Alternate between longer analytical paragraphs and shorter transitional ones

### Specific Recommendations:
{specific_recommendations}

DO NOT generate a reference version. This requires the user to decide which paragraphs to expand or condense based on content importance.
""",

    # =========================================================================
    # Formulaic Opening Issue
    # 公式化开头问题
    # =========================================================================
    "formulaic_opening": """
## SPECIFIC CONTEXT: Formulaic Paragraph Opening

The paragraph opening follows a formulaic pattern typical of AI writing.

### Detected Pattern: {pattern_type}
### Original Opening: "{original_opening}"

### Common AI Formulaic Patterns:
1. "In this section, we will discuss..." → Too meta, breaks immersion
2. "It is important to note that..." → Unnecessary hedging
3. "As mentioned earlier..." → Explicit back-reference
4. "The following section presents..." → Roadmap language
5. "[Topic] plays a crucial role in..." → Generic importance claim

### Rewriting Strategies:
1. **Direct Statement**: Start with the actual content/claim
2. **Specific Detail**: Lead with a concrete example or data point
3. **Question Hook**: Pose an implicit question the paragraph answers
4. **Contrast Setup**: Begin with what is NOT the case

### Example Transformations:
- "In this section, we discuss the results..." → "The experimental results reveal three key patterns..."
- "It is important to note that..." → Direct statement of the important point
- "As mentioned earlier, X affects Y..." → "X's influence on Y manifests in..."

Generate a reference version with a more natural, direct opening.
""",

    # =========================================================================
    # Logic Gap Issue
    # 逻辑断裂问题
    # =========================================================================
    "logic_gap": """
## SPECIFIC CONTEXT: Logic Gap Between Paragraphs

There is a logical discontinuity between {from_position} and {to_position}. The transition feels abrupt or unmotivated.

### Previous Paragraph Summary:
{prev_summary}

### Current Paragraph Summary:
{current_summary}

### Gap Analysis:
The previous paragraph discusses: {prev_topic}
The current paragraph shifts to: {current_topic}
Missing logical bridge: {missing_bridge}

### Why This Happens:
AI models sometimes generate paragraphs that are individually coherent but lack inter-paragraph logical flow. This creates a "list-like" structure where paragraphs could be reordered without affecting meaning.

### Improvement Strategies (Advice Only):
1. **Add Bridging Sentence**: End the previous paragraph with a sentence that motivates the next topic
2. **Reorder Paragraphs**: Consider if a different order would create more natural flow
3. **Insert Transitional Paragraph**: Add a short paragraph that explicitly connects the two ideas
4. **Strengthen Topic Relationship**: Revise to make the logical connection between topics clearer

### Questions to Consider:
- Why does topic B follow topic A?
- What assumption connects these two paragraphs?
- Could a reader predict this transition?

DO NOT generate a reference version. The user needs to determine the logical relationship between these topics based on their argument structure.
"""
}


# =============================================================================
# Reorder Suggestion Prompt
# 重排建议提示词
# =============================================================================

STRUCTURE_REORDER_PROMPT = """You are an expert at restructuring academic papers to remove AI-like linear patterns while maintaining logical coherence.

## DOCUMENT ANALYSIS

### Current Paragraph Structure:
{paragraph_summaries}

### Detected Structural Issues:
- Linear flow pattern detected: {has_linear_flow}
- Uniform paragraph lengths: {has_uniform_length}
- Predictable structure: {has_predictable_order}
- Structure score: {structure_score}/100 (higher = more AI-like)

### Core Thesis:
{core_thesis}

## TASK
Suggest a paragraph reordering that:
1. Breaks the linear A→B→C→D pattern
2. Maintains logical coherence and argument flow
3. Does NOT damage the overall argument structure
4. Creates more human-like narrative dynamics

## CONSTRAINTS
- Introduction (first paragraph) should generally stay first
- Conclusion (last paragraph) should generally stay last
- Related evidence/analysis paragraphs should stay grouped
- Maximum 2-3 position changes recommended for maintainability
- Each change must have clear justification

## OUTPUT FORMAT (JSON)
{{
  "current_order": [0, 1, 2, 3, 4, 5],
  "suggested_order": [0, 3, 1, 2, 4, 5],
  "changes": [
    {{
      "action": "move",
      "paragraph_index": 3,
      "from_position": 3,
      "to_position": 1,
      "paragraph_summary": "Brief summary of what P3 contains",
      "reason_zh": "将实验结果概述前置，采用'结论先行'策略，打破'方法→结果'的线性模式",
      "reason_en": "Move results overview earlier using 'conclusion-first' strategy"
    }}
  ],
  "overall_guidance_zh": "建议采用的整体重组策略说明...",
  "warnings_zh": ["注意：移动后需要调整相关段落的开头句", "另一个注意事项..."],
  "preview_flow_zh": "引言 → 关键发现 → 方法 → 详细结果 → 讨论 → 结论",
  "estimated_improvement": 15,
  "confidence": 0.8
}}

## IMPORTANT
- Be conservative with changes - fewer well-justified changes are better than many
- Always explain WHY each change helps remove AI patterns
- Consider the reader's experience - the new order should still make sense
"""


# =============================================================================
# Helper function to get issue-specific prompt
# 获取问题类型专用提示词的辅助函数
# =============================================================================

def get_issue_specific_prompt(issue_type: str, context: dict) -> str:
    """
    Get the issue-specific prompt template with context filled in.
    获取填充了上下文的问题类型专用提示词模板。

    Args:
        issue_type: Type of the issue
        context: Dictionary containing context variables

    Returns:
        Formatted prompt string
    """
    if issue_type not in ISSUE_SPECIFIC_PROMPTS:
        return ""

    template = ISSUE_SPECIFIC_PROMPTS[issue_type]

    # Fill in context variables, using empty string for missing keys
    # 填充上下文变量，缺失的键使用空字符串
    try:
        return template.format(**{k: context.get(k, "") for k in _extract_format_keys(template)})
    except KeyError:
        return template


def _extract_format_keys(template: str) -> list:
    """
    Extract format keys from a template string.
    从模板字符串中提取格式键。
    """
    import re
    # Match {key} but not {{escaped}}
    pattern = r'\{(\w+)\}'
    return re.findall(pattern, template)


def can_generate_reference(issue_type: str) -> bool:
    """
    Check if an issue type can generate a reference version.
    检查问题类型是否可以生成参考版本。

    Args:
        issue_type: Type of the issue

    Returns:
        True if reference can be generated, False otherwise
    """
    return issue_type in REFERENCEABLE_ISSUES
