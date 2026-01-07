"""
Structure-level De-AIGC Methods and Prompts
结构层面的 De-AIGC 方法与提示词

This module contains comprehensive methods for reducing AI detection at the document structure level.
All methods must maintain academic standards while reducing AI-generated patterns.
此模块包含在文档结构层面降低AI检测的综合方法。
所有方法必须在保持学术规范的同时降低AI生成模式。
"""

# Comprehensive structure-level De-AIGC knowledge base
# 结构层面 De-AIGC 知识库
STRUCTURE_DEAIGC_KNOWLEDGE = """
# Comprehensive De-AIGC Methods for Academic Paper Structure

## Core Principles

The most distinctive structural feature of AI-generated text is "excessive perfection" — overly linear logic, too-perfect symmetry, and overtly explicit transitions.
Human writing is characterized by "order with natural irregularity."

**IMPORTANT: All modifications must maintain academic rigor and professionalism. Never sacrifice academic quality to reduce AI detection.**

---

## I. Macro-Structure Optimization Methods

### 1.1 Breaking Linear Flow

**Problem**: AI tends to use a strict linear structure: Introduction → Methodology → Results → Discussion

**Academically-Friendly Solutions**:
- **Problem-First Approach**: Present a specific research paradox or anomaly in the introduction before providing background
- **Case-Opening Approach**: Begin with a specific experimental failure or research dilemma to increase narrative tension
- **Results Flashback**: Preview key findings in the methodology section to create a non-linear reading experience
- **Dialogue Embedding**: Insert "dialogues" with other researchers' viewpoints at appropriate points to break the single narrative line

**Example**:
Before: This paper investigates the effects of climate change on agriculture. First, we review existing literature...
After: A 40% crop failure in the North China Plain in 2022 defied all predictive models. This anomaly—the focus of our investigation—challenges fundamental assumptions about...

### 1.2 Section Function Reorganization

**Problem**: AI-generated sections have overly clear functional divisions, with each chapter doing only one thing

**Academically-Friendly Solutions**:
- **Function Fusion**: Incorporate preliminary results in methodology sections; embed method adjustments in results
- **Argument Interweaving**: Allow theoretical framework and empirical analysis to alternate within the same section
- **Depth Variation**: Arrange content of different depths within the same section, alternating overview paragraphs with in-depth analysis

**Note**: Fusion should not compromise readability; logical traceability must be maintained

### 1.3 Breaking Perfect Symmetry

**Problem**: AI tends to generate symmetric structures with similar paragraph counts per chapter and uniform word counts

**Academically-Friendly Solutions**:
- **Intentional Imbalance**: Key chapters can be 2-3x the length of others
- **Paragraph Length Variation**: Use long paragraphs for key arguments; short paragraphs for transitional content
- **Hierarchy Depth Variation**: Some chapters have 3 levels of subheadings, others only 2, reflecting actual content complexity

---

## II. Paragraph-Level Optimization Methods

### 2.1 Removing Explicit Connectors

**Problem**: AI overuses connectors like "Furthermore," "Moreover," "Additionally," "In conclusion"

**Academically-Friendly Replacement Strategies**:

#### 2.1.1 Semantic Echo
Use repetition of key concepts from the previous paragraph for natural continuation without explicit connectors
- Before: Furthermore, the temperature increase affects soil moisture.
- After: Soil moisture—directly impacted by these temperature shifts—demonstrates...

#### 2.1.2 Pronoun Bridge
Use "This," "Such," "These findings" for natural transitions
- Before: Moreover, our analysis reveals that...
- After: This pattern suggests that...

#### 2.1.3 Question-Driven Transition
Use rhetorical questions to introduce new content
- Before: Additionally, we examined the role of...
- After: How does this relate to agricultural output? Our examination of...

#### 2.1.4 Contrast Introduction
Transition naturally through contrast
- Before: However, some researchers disagree.
- After: Smith (2020) challenges this interpretation, arguing that...

### 2.2 Breaking Formulaic Paragraph Patterns

**Problem**: AI paragraphs often follow the formula: Topic sentence → Supporting evidence → Summary

**Academically-Friendly Variations**:
- **Evidence First**: Present data or citations first, then explain their significance
- **Progressive Development**: Move from specific to abstract, or abstract to specific
- **Refutation-Correction Structure**: Present possible objections first, then respond
- **Analogy Opening**: Begin paragraphs with analogies or metaphors

### 2.3 Sentence Length Variation

**Problem**: AI sentence lengths are too uniform

**Academically-Friendly Methods**:
- Use long sentences for complex arguments, short sentences for conclusions
- Insert a brief, powerful statement after a series of long sentences
- Use parenthetical information to vary sentence complexity

---

## III. Transition-Level Optimization Methods

### 3.1 Implicit Logical Connection

**Goal**: Let readers perceive logic without seeing obvious logical markers

**Methods**:
- **Implicit Temporal Sequence**: Use tense changes to suggest time progression
- **Implicit Causality**: Suggest cause-effect through sentence arrangement without "because," "therefore"
- **Implicit Contrast**: Juxtapose contrasting content without "however," "on the contrary"

### 3.2 Citations as Transitions

**Methods**:
- Use dialogue between different scholars' viewpoints to connect paragraphs
- Transition naturally with "X argued..., but Y later demonstrated..."
- Use the timeline or logical relationships inherent in citations for connection

### 3.3 Thematic Word Cycling

**Methods**:
- Repeat key words from the previous paragraph's ending in the next paragraph's opening
- Use synonyms or near-synonyms across different paragraphs to create "lexical echo"
- Use demonstrative pronouns (this phenomenon, such effects) to establish connections

---

## IV. Opening and Closing Optimization Methods

### 4.1 Avoiding Formulaic Openings

**Common AI Patterns**:
- "This paper aims to..."
- "In recent years, there has been growing interest in..."
- "The purpose of this study is to..."

**Academically-Friendly Alternatives**:
- Open with a research paradox or anomaly
- Open with specific data or case studies
- Open with academic controversy
- Open with the researcher's "puzzlement" (moderate use of first person)

### 4.2 Avoiding Over-Closed Endings

**Common AI Patterns**:
- "In conclusion, this study has demonstrated..."
- "To summarize, the findings indicate..."
- Perfectly addressing all research questions

**Academically-Friendly Alternatives**:
- **Open-Ended Closing**: Point to unresolved issues or new research directions
- **Cautious Closing**: Use hedging language ("may suggest," "appears to indicate")
- **Question-Style Closing**: End with new research questions
- **Limitation Acknowledgment**: Candidly discuss research limitations, leaving room for exploration

---

## V. Cross-Paragraph Optimization Methods

### 5.1 Building Cross-Reference Structure

**Problem**: AI text is often linear, lacking back-and-forth references

**Methods**:
- Explicitly reference earlier arguments or data ("As noted in Section 2...")
- Create "argument loops": Echo questions raised in the introduction in the conclusion
- Use footnotes or parentheses for cross-paragraph connections

### 5.2 Creating Controlled "Imperfection"

**Methods**:
- Allow some arguments to be preliminary explorations, not fully proven
- Retain some "unresolved" discussions
- Acknowledge data ambiguity or interpretation diversity

---

## VI. Solutions for Specific Issues

### 6.1 Overly Obvious Linear Flow
**Diagnosis**: Document follows a strict, linear progression: Introduction -> Methodology -> Results -> Conclusion
**Solutions**:
1. Insert brief discussion of expected results in methodology section
2. Review method adjustments in results section
3. Consider using "research story" narrative to document research twists and turns

### 6.2 Overly Formulaic IMRaD Structure
**Diagnosis**: Structure is a highly formulaic IMRaD format
**Solutions**:
1. Add "Research Background" or "Conceptual Framework" sections beyond standard chapters
2. Merge discussion and conclusion, or interweave methods and results
3. Add a separate "Research Limitations" section

### 6.3 Perfect Symmetric Structure
**Diagnosis**: Perfect symmetry: each section contains exactly one paragraph
**Solutions**:
1. Adjust paragraph count based on actual content needs
2. Key sections should have more paragraphs
3. Some sections can contain only overview content

### 6.4 Overly Uniform Paragraph Length
**Diagnosis**: All paragraphs are extremely short and uniform in length
**Solutions**:
1. Merge related short paragraphs
2. Expand key argument paragraphs
3. Create rhythm through alternating long and short paragraphs

### 6.5 Overuse of Explicit Connectors
**Diagnosis**: Explicit AI-fingerprint connectors detected (Furthermore, Moreover, etc.)
**Solutions**:
1. Use semantic echo replacement
2. Use pronoun bridge replacement
3. Use citations or data as transitions

### 6.6 Lack of Cross-Reference Structure
**Diagnosis**: No cross-references between sections
**Solutions**:
1. Add cross-references like "As mentioned earlier," "As discussed in Section X"
2. Echo the introduction in the conclusion
3. Reference earlier data in the discussion

---

## Important Reminders

1. **Academic Priority**: All modifications must serve academic expression; never sacrifice clarity to reduce AI detection
2. **Maintain Consistency**: The chosen style should remain consistent throughout
3. **Disciplinary Conventions**: Different fields have different writing conventions; modifications should conform to target field norms
4. **References**: All citations and data must be verifiable
5. **Moderation Principle**: Not all methods need to be used; select the 2-3 most appropriate ones
"""

# Issue-specific suggestion prompt template
# 针对特定问题的建议提示词模板
ISSUE_SUGGESTION_PROMPT = """You are an expert academic writing consultant specializing in De-AIGC (making AI-generated text appear more human-like while maintaining academic standards).

## BACKGROUND KNOWLEDGE
{knowledge_base}

## CURRENT DOCUMENT STRUCTURE ISSUE
**Issue Type**: {issue_type}
**Issue Description (EN)**: {issue_description}
**Issue Description (ZH)**: {issue_description_zh}
**Severity**: {severity}
**Affected Positions**: {affected_positions}

## DOCUMENT INFORMATION
**Total Sections**: {total_sections}
**Total Paragraphs**: {total_paragraphs}
**Structure Score**: {structure_score}/100 (Higher = More AI-like)
**Risk Level**: {risk_level}

## DOCUMENT CONTENT (Relevant Excerpt)
{document_excerpt}

## YOUR TASK
Based on the De-AIGC knowledge base and the specific issue identified, provide:
1. A detailed diagnosis of why this issue triggers AI detection
2. Specific, academically appropriate modification strategies
3. **For explicit_connector issues: Generate CONCRETE semantic echo replacements**
4. A sample modification prompt that the user can use with other AI tools to fix this issue

## OUTPUT FORMAT (JSON)
{{
  "diagnosis_zh": "【问题本质】详细解释这个问题为什么会被AI检测器识别...\\n【具体表现】在当前文档中的具体表现形式...",
  "strategies": [
    {{
      "name_zh": "策略名称",
      "description_zh": "详细的策略描述，包含具体的操作步骤",
      "example_before": "原文示例（如适用）",
      "example_after": "修改后示例（如适用）",
      "difficulty": "easy/medium/hard",
      "effectiveness": "high/medium/low"
    }}
  ],
  "semantic_echo_replacements": [
    {{
      "original_text": "原始包含显性连接词的句子",
      "connector_word": "检测到的连接词",
      "prev_paragraph_concepts": ["从前一段提取的关键概念1", "关键概念2"],
      "replacement_text": "使用语义回声重写后的句子（不含显性连接词）",
      "explanation_zh": "解释为什么这个替换有效，如何利用前段概念自然过渡"
    }}
  ],
  "modification_prompt": "一个完整的提示词，用户可以直接复制到其他AI工具中使用，用于修改这个特定问题。提示词应该包含:\\n1. 任务说明\\n2. 需要避免的AI写作模式\\n3. 期望的修改效果\\n4. 输出格式要求\\n5. 【重要】对于连接词问题，必须包含语义回声替换指导",
  "priority_tips_zh": "针对这个问题的优先修改建议（按重要性排序）",
  "caution_zh": "修改时需要注意的事项，确保不损害学术质量"
}}

## SPECIAL INSTRUCTIONS FOR EXPLICIT CONNECTOR ISSUES
When the issue_type is "explicit_connector" or involves connector words:
1. You MUST populate the "semantic_echo_replacements" array
2. Find EACH sentence in the document that starts with an explicit connector
3. Identify key concepts from the PREVIOUS paragraph/sentence
4. Generate a CONCRETE replacement that:
   - Removes the explicit connector completely
   - Uses a key concept from the previous content to create natural flow
   - Maintains the original meaning and academic tone
5. Example:
   - Original: "Furthermore, the experimental results demonstrate that..."
   - Prev concepts: ["temperature effects", "soil conditions"]
   - Replacement: "This temperature-driven pattern further manifests in..."
   - Explanation: 用前段"temperature"概念自然承接，无需显性连接词

## CRITICAL RULES
1. ALL Chinese content must be in proper Chinese (中文)
2. Strategies must be academically appropriate - never suggest anything that would make the paper less rigorous
3. The modification_prompt should be a complete, copy-pasteable prompt
4. Be specific - reference actual content from the document when possible
5. Provide at least 2-3 different strategies for addressing the issue
6. The diagnosis should explain WHY this pattern is problematic for AI detection
7. **For connector issues, the semantic_echo_replacements MUST contain usable, copy-pasteable replacement text**
"""

# Quick suggestion prompt for simpler analysis
# 快速建议提示词（简化版）
QUICK_ISSUE_SUGGESTION_PROMPT = """You are a De-AIGC expert. Analyze this structure issue and provide modification advice.

## ISSUE
Type: {issue_type}
Description: {issue_description}
Severity: {severity}

## DOCUMENT CONTEXT
Structure Score: {structure_score}/100
Sections: {total_sections}, Paragraphs: {total_paragraphs}

## OUTPUT (JSON)
{{
  "diagnosis": "Brief problem analysis in English (2-3 sentences)",
  "diagnosis_zh": "【问题诊断】简明扼要的问题分析（2-3句）",
  "quick_fix": "Immediately actionable modification suggestions (specific steps)",
  "quick_fix_zh": "【快速修改】立即可执行的修改建议（具体步骤）",
  "detailed_strategy": "More systematic modification approach",
  "detailed_strategy_zh": "【深度策略】更系统的修改方案",
  "prompt_snippet": "A prompt snippet the user can copy and use (in English)",
  "estimated_improvement": "Estimated improvement score"
}}

Rules:
- Provide output in both English and Chinese where applicable
- Be specific and actionable
- Keep academic standards
- The prompt_snippet MUST be in English
"""


def get_full_knowledge_base() -> str:
    """
    Get the complete De-AIGC knowledge base
    获取完整的 De-AIGC 知识库
    """
    return STRUCTURE_DEAIGC_KNOWLEDGE


def format_issue_prompt(
    issue_type: str,
    issue_description: str,
    issue_description_zh: str,
    severity: str,
    affected_positions: list,
    total_sections: int,
    total_paragraphs: int,
    structure_score: int,
    risk_level: str,
    document_excerpt: str,
    use_quick_mode: bool = False
) -> str:
    """
    Format the prompt for generating issue-specific suggestions
    格式化生成特定问题建议的提示词

    Args:
        issue_type: Type of the structure issue
        issue_description: English description of the issue
        issue_description_zh: Chinese description of the issue
        severity: Issue severity (high/medium/low)
        affected_positions: List of affected positions
        total_sections: Number of sections in document
        total_paragraphs: Number of paragraphs in document
        structure_score: Overall structure score
        risk_level: Overall risk level
        document_excerpt: Relevant excerpt from the document
        use_quick_mode: Use simplified prompt for faster response

    Returns:
        Formatted prompt string
    """
    if use_quick_mode:
        return QUICK_ISSUE_SUGGESTION_PROMPT.format(
            issue_type=issue_type,
            issue_description=issue_description,
            severity=severity,
            structure_score=structure_score,
            total_sections=total_sections,
            total_paragraphs=total_paragraphs
        )

    return ISSUE_SUGGESTION_PROMPT.format(
        knowledge_base=STRUCTURE_DEAIGC_KNOWLEDGE,
        issue_type=issue_type,
        issue_description=issue_description,
        issue_description_zh=issue_description_zh,
        severity=severity,
        affected_positions=", ".join(affected_positions) if affected_positions else "全文",
        total_sections=total_sections,
        total_paragraphs=total_paragraphs,
        structure_score=structure_score,
        risk_level=risk_level,
        document_excerpt=document_excerpt[:3000] if document_excerpt else "无文档内容"
    )
