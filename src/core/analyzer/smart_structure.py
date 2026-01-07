"""
Smart Document Structure Analyzer using LLM
智能文档结构分析器（基于 LLM）

Uses LangChain for intelligent document parsing:
1. Identify paper section structure (1, 1.1, 1.2, 2, 2.1...)
2. Filter non-paragraph content (titles, tables, figures, bullet points)
3. Generate meaningful summaries for each paragraph
4. Label paragraphs with section positions (e.g., "3.2(1)")

使用 LangChain 进行智能文档解析：
1. 识别论文章节结构
2. 过滤非段落内容（标题、表格、图片、要点）
3. 为每个段落生成有意义的摘要
4. 用章节位置标注段落
"""

import json
import re
import httpx
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from src.config import get_settings

# Get settings instance
settings = get_settings()


# =============================================================================
# Pydantic Models for structured output
# 用于结构化输出的 Pydantic 模型
# =============================================================================

class ParagraphAnalysis(BaseModel):
    """Analysis of a single paragraph 单个段落的分析"""
    position: str = Field(description="Section position like '3.2(1)' meaning Section 3.2, paragraph 1")
    summary: str = Field(description="10-20 word summary of what this paragraph discusses")
    summary_zh: str = Field(description="10-20字的段落要点总结")
    first_sentence: str = Field(description="First sentence of the paragraph")
    last_sentence: str = Field(description="Last sentence of the paragraph")
    word_count: int = Field(description="Approximate word count")
    ai_risk: str = Field(description="AI detection risk: high/medium/low")
    ai_risk_reason: str = Field(description="Brief reason for the risk level")


class SectionInfo(BaseModel):
    """Information about a document section 文档章节信息"""
    number: str = Field(description="Section number like '1', '1.1', '2.3.1'")
    title: str = Field(description="Section title")
    paragraphs: List[ParagraphAnalysis] = Field(description="Paragraphs in this section")


class StructureIssueInfo(BaseModel):
    """Detected structure issue 检测到的结构问题"""
    type: str = Field(description="Issue type: linear_flow, repetitive_pattern, uniform_length, etc.")
    description: str = Field(description="Description of the issue")
    description_zh: str = Field(description="问题描述")
    severity: str = Field(description="high/medium/low")
    affected_positions: List[str] = Field(description="Affected paragraph positions")


class StyleAnalysis(BaseModel):
    """Document style analysis result 文档风格分析结果"""
    detected_style: int = Field(description="Detected formality level 0-10 (0=most academic, 10=most casual)")
    style_name: str = Field(description="Style name in English")
    style_name_zh: str = Field(description="风格名称（中文）")
    style_indicators: List[str] = Field(description="Indicators that led to this style classification")
    style_indicators_zh: List[str] = Field(description="风格判断依据（中文）")
    mismatch_warning: Optional[str] = Field(default=None, description="Warning if style mismatches user expectation")
    mismatch_warning_zh: Optional[str] = Field(default=None, description="风格不匹配警告（中文）")


class SmartStructureAnalysis(BaseModel):
    """Complete smart structure analysis result 完整的智能结构分析结果"""
    sections: List[SectionInfo] = Field(description="Document sections with paragraphs")
    total_paragraphs: int = Field(description="Total number of real paragraphs")
    total_sections: int = Field(description="Total number of sections")
    structure_score: int = Field(description="AI detection risk score 0-100, higher = more AI-like")
    risk_level: str = Field(description="Overall risk: high/medium/low")
    issues: List[StructureIssueInfo] = Field(description="Detected structural issues")
    score_breakdown: Dict[str, int] = Field(description="Score breakdown by category")
    recommendation: str = Field(description="Recommended action")
    recommendation_zh: str = Field(description="建议采取的行动")
    # Style analysis fields (added for colloquialism level support)
    # 风格分析字段（为支持口语化级别而添加）
    style_analysis: Optional[StyleAnalysis] = Field(default=None, description="Document style analysis")


# =============================================================================
# Prompts
# 提示词
# =============================================================================

# Step 1-1: Document Structure Analysis Prompt
# 步骤 1-1：全文结构分析提示词
STRUCTURE_ANALYSIS_PROMPT = """You are an expert academic document analyzer. Analyze this document's STRUCTURE only (not paragraph relationships).

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

### 1. IDENTIFY REAL PARAGRAPHS
Filter OUT these non-paragraph elements:
- Section titles/headings (e.g., "1. Introduction", "2.1 Methods")
- Table headers and table content
- Figure captions (e.g., "Figure 1: ...")
- Bullet point lists
- Short fragments (< 30 words)
- References/citations blocks
- Author information
- Abstract headings

KEEP ONLY: Continuous prose paragraphs with complete sentences (typically > 50 words).

### 2. IDENTIFY SECTION STRUCTURE
Detect the paper's section numbering system:
- Could be "1, 2, 3" or "1.1, 1.2" or "I, II, III" or "A, B, C"
- If no clear numbering, use inferred sections like "Intro(1)", "Method(1)", etc.

### 3. FOR EACH REAL PARAGRAPH, PROVIDE:
- **position**: Section-based position like "3.2(1)" meaning "Section 3.2, paragraph 1"
- **summary**: 10-20 word summary of the SPECIFIC TOPIC (not generic labels)
- **summary_zh**: Chinese version of summary
- **first_sentence**: First sentence (truncate if > 100 chars)
- **last_sentence**: Last sentence (truncate if > 100 chars)
- **word_count**: Approximate word count

### 4. DETECT STRUCTURE ISSUES (GLOBAL PATTERNS)
Look for AI-typical structural patterns:
- **linear_flow**: "First...Second...Third" enumeration pattern across sections
- **repetitive_pattern**: Similar section structures repeated
- **uniform_length**: All paragraphs have similar word counts (low variance)
- **predictable_order**: Formulaic intro-body-conclusion structure
- **symmetry**: Perfectly balanced sections (equal paragraphs per section)

### 5. CALCULATE STRUCTURE SCORE (0-100, higher = more AI-like)
- linear_flow: +20 if detected
- repetitive_pattern: +15 if detected
- uniform_length: +10 if detected
- predictable_order: +10 if detected
- symmetry: +15 if detected

### 6. ANALYZE DOCUMENT STYLE/FORMALITY (CRITICAL!)
Determine the document's actual formality level (0-10 scale):
- **0-2 (Academic)**: Formal academic writing with citations, passive voice, technical terminology, structured arguments, hedging language ("may suggest", "appears to indicate")
- **3-4 (Thesis Level)**: Semi-formal academic, organized structure, some personal pronouns allowed
- **5-6 (Semi-formal)**: Conference paper or technical report style, mix of formal and accessible language
- **7-8 (Technical Blog)**: Casual professional, conversational tone, first-person allowed, some contractions
- **9-10 (Casual/Diary)**: Very informal, personal narrative, subjective opinions, colloquial expressions, emotional language

**Style Indicators to Check:**
- Personal pronouns frequency (I/my/we vs. impersonal)
- Contractions presence (don't, can't, it's)
- Emotional/subjective language ("I was bored", "surprisingly", "honestly")
- Citation/reference style
- Sentence complexity and length variation
- Use of hedging vs. absolute statements
- Narrative vs. argumentative structure

{style_context}

## OUTPUT FORMAT (JSON):
{{
  "sections": [
    {{
      "number": "1",
      "title": "Introduction",
      "paragraphs": [
        {{
          "position": "1(1)",
          "summary": "Background on protein structure prediction challenges",
          "summary_zh": "蛋白质结构预测的背景与挑战",
          "first_sentence": "Protein structure prediction remains...",
          "last_sentence": "...this study addresses.",
          "word_count": 120
        }}
      ]
    }}
  ],
  "total_paragraphs": 12,
  "total_sections": 5,
  "structure_score": 45,
  "risk_level": "medium",
  "structure_issues": [
    {{
      "type": "linear_flow",
      "description": "Found linear progression pattern in methodology",
      "description_zh": "在方法论部分发现线性推进模式",
      "severity": "high",
      "affected_positions": ["2(1)", "2(2)", "2(3)"]
    }}
  ],
  "score_breakdown": {{
    "linear_flow": 20,
    "repetitive_pattern": 0,
    "uniform_length": 10,
    "predictable_order": 10,
    "symmetry": 5
  }},
  "recommendation_zh": "文档结构过于规整，建议打破段落的对称分布",
  "style_analysis": {{
    "detected_style": 8,
    "style_name": "Casual/Personal Narrative",
    "style_name_zh": "休闲/个人叙事",
    "style_indicators": [
      "Heavy use of first person (I, my)",
      "Emotional language (was bored, surprisingly)",
      "Narrative structure rather than argumentative",
      "No citations or references",
      "Casual expressions and colloquialisms"
    ],
    "style_indicators_zh": [
      "大量使用第一人称（I, my）",
      "情感化语言（was bored, surprisingly）",
      "叙事结构而非论证结构",
      "无引用或参考文献",
      "口语化表达"
    ]
  }}
}}

CRITICAL RULES:
- Only include REAL paragraphs (continuous prose > 50 words)
- Use SPECIFIC topic summaries, not generic labels like "body/conclusion"
- Position format must be "SectionNum(ParaNum)"
- Focus on GLOBAL structure patterns, NOT paragraph-level connections
"""


# Step 1-2: Paragraph Relationship Analysis Prompt
# 步骤 1-2：段落关系分析提示词
RELATIONSHIP_ANALYSIS_PROMPT = """You are an expert De-AIGC analyst. Analyze the RELATIONSHIPS between paragraphs in this document.

## DOCUMENT TEXT:
{document_text}

## PARAGRAPH POSITIONS (from Step 1-1):
{paragraph_positions}

## YOUR TASKS:

### 1. DETECT EXPLICIT CONNECTOR WORDS AND GENERATE SEMANTIC ECHO REPLACEMENTS (CRITICAL!)
Identify ALL instances of explicit connector words at paragraph or sentence starts:

**English Connectors (AI fingerprints):**
- "Furthermore", "Moreover", "Additionally", "Consequently", "Therefore", "Thus", "Hence"
- "Notably", "Importantly", "However", "Nevertheless", "In addition"
- "First/Firstly", "Second/Secondly", "Third/Thirdly", "Finally"
- "In conclusion", "To summarize", "In summary"

**Chinese Connectors (AI fingerprints):**
- "首先", "其次", "再次", "此外", "另外", "总之", "综上所述"
- "另一方面", "因此", "所以", "然而", "但是", "不过", "同时", "与此同时"

For each connector found, you MUST:
1. Record the connector word, position, location (paragraph_start/sentence_start), severity
2. **Extract the ending of the PREVIOUS paragraph** (last 1-2 sentences)
3. **Identify 1-3 KEY CONCEPTS from the previous paragraph** that can be echoed
4. **Record the current opening sentence** (the one with the connector)
5. **Generate a CONCRETE semantic echo replacement** - rewrite the opening WITHOUT the connector, using the key concepts from the previous paragraph
6. **Explain in Chinese why this replacement works**

**Semantic Echo Strategy:**
- Remove the explicit connector completely
- Start with a reference to a key concept from the previous paragraph
- Create natural flow through meaning, not through connector words

**Example:**
- Previous ending: "...the statistical significance reached p<0.05."
- Current opening: "Furthermore, the results demonstrate that..."
- Key concepts: ["statistical significance", "p-value"]
- Semantic echo replacement: "This pattern of statistical significance extends to..."
- Explanation: 用前段'statistical significance'概念自然承接，无需显性连接词

### 2. DETECT LOGIC BREAK POINTS (段落间逻辑断裂点)
For each consecutive paragraph pair (Para N → Para N+1):
- Check semantic continuity: Does N+1 naturally follow N?
- Identify transition type: "smooth" / "abrupt" / "glue_word_only" / "ai_perfect_linear"
- A "glue_word_only" transition = connection relies ONLY on explicit connectors without semantic echo
- A "ai_perfect_linear" transition = TOO PERFECT linear flow, typical AI pattern (e.g., "Introduction → Overview → Details → Conclusion" flow)

**IMPORTANT**: The `issue_zh` field MUST describe what is WRONG with this transition, NOT what is good about it!
- BAD example: "从阐明综述目标，自然过渡到具体分类阐述..." (This sounds positive!)
- GOOD example: "具有典型AI生成的'完美线性过渡'特征，从综述目标过于直接地过渡到分类阐述，缺乏人类写作的自然跳跃和思维转折"
- The issue description should highlight the AI PATTERN being detected, not describe the content flow

### 3. ANALYZE AI RISK FOR EACH PARAGRAPH
For each paragraph, determine:
- ai_risk: "high" / "medium" / "low"
- ai_risk_reason: Specific reason in Chinese, quoting original text
- opening_connector: If starts with connector word
- rewrite_suggestion_zh: For medium/high risk paragraphs, provide specific rewrite advice including:
  - 【问题诊断】具体指出AI痕迹
  - 【修改策略】针对性修改方法
  - 【改写提示】如何改写开头

### 4. CALCULATE RELATIONSHIP SCORE (0-100)
- connector_overuse: +5 per 10% of paragraphs starting with connectors (max +25)
- missing_semantic_echo: +10 if paragraphs lack semantic continuity
- glue_word_transitions: +15 if more than 30% transitions are glue_word_only

## OUTPUT FORMAT (JSON):
{{
  "explicit_connectors": [
    {{
      "word": "Furthermore",
      "position": "1(2)",
      "location": "paragraph_start",
      "severity": "high",
      "prev_paragraph_ending": "...the statistical significance reached p<0.05.",
      "prev_key_concepts": ["statistical significance", "p-value threshold"],
      "current_opening": "Furthermore, the results demonstrate...",
      "semantic_echo_replacement": "This pattern of statistical significance extends to...",
      "replacement_explanation_zh": "用前段关键概念'statistical significance'自然承接，避免使用显性连接词"
    }},
    {{
      "word": "此外",
      "position": "2(3)",
      "location": "sentence_start",
      "severity": "medium",
      "prev_paragraph_ending": "...土壤盐分累积问题日益严重。",
      "prev_key_concepts": ["土壤盐分", "累积问题"],
      "current_opening": "此外，灌溉方式也会影响...",
      "semantic_echo_replacement": "盐分累积的这一趋势在不同灌溉方式下呈现出...",
      "replacement_explanation_zh": "用前段'盐分累积'概念自然引出灌溉方式的讨论"
    }}
  ],
  "logic_breaks": [
    {{
      "from_position": "2(1)",
      "to_position": "2(2)",
      "transition_type": "glue_word_only",
      "issue": "Connected only by 'Moreover', no semantic continuity",
      "issue_zh": "仅靠显性连接词'此外'连接，缺乏语义连贯性，属于典型AI写作模式",
      "suggestion": "Use semantic echo - repeat key concept from previous paragraph",
      "suggestion_zh": "建议使用语义回声，用前段关键概念自然承接",
      "prev_key_concepts": ["concept1", "concept2"],
      "semantic_echo_example": "Example of how to rewrite using key concepts"
    }},
    {{
      "from_position": "1(1)",
      "to_position": "1(2)",
      "transition_type": "ai_perfect_linear",
      "issue": "Too perfect linear flow from introduction to classification, typical AI pattern",
      "issue_zh": "具有典型AI生成的'完美线性过渡'特征，从引言直接过渡到分类阐述过于顺畅，缺乏人类写作自然的思维跳跃",
      "suggestion": "Break the perfect linearity by adding a question, contrast, or unexpected angle",
      "suggestion_zh": "打破线性结构，可在过渡处加入疑问、对比或意外视角",
      "prev_key_concepts": ["research background", "problem statement"],
      "semantic_echo_example": "Instead of direct flow, insert a rhetorical question or contrast"
    }}
  ],
  "paragraph_risks": [
    {{
      "position": "1(2)",
      "ai_risk": "high",
      "ai_risk_reason": "段首使用显性连接词'Furthermore'，属于典型AI写作痕迹",
      "opening_connector": "Furthermore",
      "prev_key_concepts": ["key concept from previous paragraph"],
      "rewrite_suggestion_zh": "【问题诊断】段首使用显性连接词'Furthermore'。\\n【修改策略】删除连接词，使用语义回声承接上段关键概念。\\n【改写提示】可改为直接引用前段概念，如将'Furthermore, the results...'改为'This pattern of [前段概念]...'"
    }}
  ],
  "relationship_score": 35,
  "relationship_issues": [
    {{
      "type": "connector_overuse",
      "description": "40% of paragraphs start with explicit connectors",
      "description_zh": "40%的段落以显性连接词开头",
      "severity": "high",
      "affected_positions": ["1(2)", "2(1)", "2(3)"]
    }}
  ],
  "score_breakdown": {{
    "connector_overuse": 20,
    "missing_semantic_echo": 10,
    "glue_word_transitions": 5
  }}
}}

CRITICAL RULES:
- MUST detect ALL explicit connector words - this is the primary AI signal
- MUST generate semantic echo replacement for EACH explicit connector found
- MUST extract key concepts from the previous paragraph for each connector
- MUST analyze transitions between ALL consecutive paragraph pairs
- Provide specific Chinese explanations with original text quotes
- The semantic_echo_replacement must be a COMPLETE, USABLE sentence that can directly replace the original opening
"""


# Combined prompt (legacy - for backward compatibility)
# 组合提示词（遗留 - 向后兼容）
SMART_STRUCTURE_PROMPT = """You are an expert academic document analyzer specializing in De-AIGC (detecting AI-generated text patterns). Analyze this document's structure intelligently.

## DOCUMENT TEXT:
{document_text}

## YOUR TASKS:

### 1. IDENTIFY REAL PARAGRAPHS
Filter OUT these non-paragraph elements:
- Section titles/headings (e.g., "1. Introduction", "2.1 Methods")
- Table headers and table content
- Figure captions (e.g., "Figure 1: ...")
- Bullet point lists
- Short fragments (< 30 words)
- References/citations blocks
- Author information
- Abstract headings

KEEP ONLY: Continuous prose paragraphs with complete sentences (typically > 50 words).

### 2. IDENTIFY SECTION STRUCTURE
Detect the paper's section numbering system:
- Could be "1, 2, 3" or "1.1, 1.2" or "I, II, III" or "A, B, C"
- If no clear numbering, use inferred sections like "Intro(1)", "Method(1)", etc.

### 3. FOR EACH REAL PARAGRAPH, PROVIDE:
- **position**: Section-based position like "3.2(1)" meaning "Section 3.2, paragraph 1"
  - Format: "SectionNumber(ParagraphNumber)" e.g., "1(1)", "2.1(2)", "3(1)"
- **summary**: 10-20 word summary of the SPECIFIC TOPIC (not generic labels)
  - GOOD: "蛋白质折叠预测中的深度学习方法比较"
  - BAD: "body", "evidence", "discussion" (DO NOT USE THESE)
- **summary_zh**: Chinese version of summary
- **first_sentence**: First sentence (truncate if > 100 chars)
- **last_sentence**: Last sentence (truncate if > 100 chars)
- **word_count**: Approximate word count
- **ai_risk**: "high"/"medium"/"low" based on AI-typical patterns
- **ai_risk_reason**: Brief Chinese reason describing the AI pattern detected (引用原文时保留原文语言)
  - Format: "问题描述 + '原文引用'" e.g., "段首使用显性连接词'Furthermore'，采用公式化结构"
- **opening_connector**: If paragraph starts with explicit connector word, list it (e.g., "Furthermore", "此外")
- **ending_connector**: If paragraph ends with transition phrase, list it

- **rewrite_suggestion_zh** (CRITICAL - Required for medium/high risk paragraphs):
  Provide SPECIFIC, ACTIONABLE Chinese rewriting advice. Must include:
  1. 问题诊断：具体指出段落中的AI痕迹（引用原文）
  2. 修改策略：针对性的修改方法
  3. 示例提示：如何改写开头或关键句

  Example format:
  "【问题诊断】段首使用显性连接词'Furthermore'，属于典型AI写作痕迹。段落结构采用'问题-分析-结论'公式化模式。
   【修改策略】1. 删除段首连接词，改用语义回声承接上段关键概念'salt accumulation'；2. 打散公式化结构，将结论提前或融入论述中。
   【改写提示】可将开头改为直接承接上段内容，如'土壤盐分累积的这一趋势在...'或引入具体案例开头。"

- **rewrite_example** (IMPORTANT - same language as original):
  A rewritten version of the first 1-2 sentences showing how to improve.
  MUST be in the SAME LANGUAGE as the original paragraph text.
  If original is English, write in English. If original is Chinese, write in Chinese.
  Example (English original): "The escalating trend of soil salinization poses new challenges to traditional agriculture. In the North China Plain, monitoring data from the past decade reveals..."
  Example (Chinese original): "土壤盐渍化的加剧趋势对传统农业提出了新挑战。根据华北平原过去十年的监测数据显示..."

### 4. DETECT EXPLICIT CONNECTOR WORDS (CRITICAL!)
This is the most important AI detection signal. Identify ALL instances of:

**English Connectors (AI fingerprints):**
- Sentence starters: "Furthermore", "Moreover", "Additionally", "Consequently", "Therefore", "Thus", "Hence", "Notably", "Importantly", "However", "Nevertheless", "In addition", "First/Firstly", "Second/Secondly", "Third/Thirdly", "Finally", "In conclusion", "To summarize"

**Chinese Connectors (AI fingerprints):**
- "首先", "其次", "再次", "此外", "另外", "总之", "综上所述", "另一方面", "因此", "所以", "然而", "但是", "不过", "同时", "与此同时"

For each connector found, record:
- The connector word
- Which paragraph position it appears in
- Whether it's at paragraph start or sentence start

### 5. DETECT LOGIC BREAK POINTS (段落间逻辑断裂点)
Analyze transitions BETWEEN consecutive paragraphs. For each pair (Para N, Para N+1):
- Does Para N+1 logically follow from Para N?
- Is there a semantic connection or just a "glue word"?
- Rate the transition: "smooth" / "abrupt" / "glue_word_only"

A "glue_word_only" transition means: the connection relies ONLY on explicit connectors like "Moreover/此外" without semantic continuity.

### 6. DETECT STRUCTURE ISSUES
Look for AI-typical patterns:
- **linear_flow**: "First...Second...Third" enumeration pattern
- **repetitive_pattern**: Similar sentence structures repeated across paragraphs
- **uniform_length**: All paragraphs have similar word counts (low variance)
- **predictable_order**: Formulaic intro-body-conclusion structure
- **connector_overuse**: More than 30% of paragraphs start with explicit connectors
- **missing_semantic_echo**: Paragraphs don't echo key concepts from previous paragraph

### 7. CALCULATE SCORE (0-100, higher = more AI-like)
- linear_flow: +20 if detected
- repetitive_pattern: +15 if detected
- uniform_length: +10 if detected
- predictable_order: +10 if detected
- connector_overuse: +5 per 10% above threshold (max +25)
- missing_semantic_echo: +10 if no semantic continuity between paragraphs

## OUTPUT FORMAT (JSON):
{{
  "sections": [
    {{
      "number": "1",
      "title": "Introduction",
      "paragraphs": [
        {{
          "position": "1(1)",
          "summary": "Background on protein structure prediction challenges",
          "summary_zh": "蛋白质结构预测的背景与挑战",
          "first_sentence": "Protein structure prediction remains...",
          "last_sentence": "...this study addresses.",
          "word_count": 120,
          "ai_risk": "medium",
          "ai_risk_reason": "标准学术问题框架，使用隐喻修辞，关联SDGs目标",
          "opening_connector": null,
          "ending_connector": null,
          "rewrite_suggestion_zh": "【问题诊断】段落采用标准学术问题框架，使用隐喻修辞（如'Edaphic Cancer'），并关联SDGs目标，属于AI常见的宏大叙事开篇模式。\n【修改策略】1. 减少抽象概念堆砌，增加具体数据或案例支撑；2. 避免过度使用学术流行词汇；3. 开篇可从具体现象或数据切入。\n【改写提示】可考虑直接引入具体研究区域或数据，如'根据2020-2023年华北平原土壤监测数据，盐渍化面积年增长率达3.2%...'",
          "rewrite_example": "According to FAO 2023 data, global agricultural losses from soil salinization exceed $27 billion annually. In northwest China, this problem is particularly acute..."
        }},
        {{
          "position": "1(2)",
          "summary": "Previous approaches and their limitations",
          "summary_zh": "先前方法及其局限性",
          "first_sentence": "Furthermore, existing methods...",
          "last_sentence": "...remain unsolved.",
          "word_count": 95,
          "ai_risk": "high",
          "ai_risk_reason": "段首使用显性连接词'Furthermore'，采用公式化'问题-批评'结构",
          "opening_connector": "Furthermore",
          "ending_connector": null,
          "rewrite_suggestion_zh": "【问题诊断】段首使用显性连接词'Furthermore'，这是典型的AI写作指纹。段落结构遵循'现有方法-批评-局限性'的公式化模式。\n【修改策略】1. 删除段首连接词'Furthermore'；2. 使用语义回声承接上段关键概念；3. 打散公式化结构，可以先抛出核心问题再展开。\n【改写提示】删除'Furthermore'，改为承接上段具体内容，如'传统方法在处理高浓度盐分时表现出明显局限'或'这一挑战促使研究者探索新的技术路径'",
          "rewrite_example": "Traditional chemical remediation methods, despite decades of application, often prove ineffective against severely salinized soils. Taking gypsum amendment as an example, its cost-effectiveness ratio drops sharply in soils exceeding 15dS/m..."
        }}
      ]
    }}
  ],
  "total_paragraphs": 12,
  "total_sections": 5,
  "structure_score": 55,
  "risk_level": "medium",
  "explicit_connectors": [
    {{
      "word": "Furthermore",
      "position": "1(2)",
      "location": "paragraph_start",
      "severity": "high"
    }},
    {{
      "word": "此外",
      "position": "2(3)",
      "location": "sentence_start",
      "severity": "high"
    }}
  ],
  "logic_breaks": [
    {{
      "from_position": "2(1)",
      "to_position": "2(2)",
      "transition_type": "glue_word_only",
      "issue": "Connected only by 'Moreover', no semantic continuity",
      "issue_zh": "仅靠'此外'连接，缺乏语义连贯性",
      "suggestion": "Use semantic echo - repeat key concept from previous paragraph",
      "suggestion_zh": "建议使用语义回声 - 在下一段开头重复上一段的关键概念"
    }}
  ],
  "issues": [
    {{
      "type": "connector_overuse",
      "description": "40% of paragraphs start with explicit connectors",
      "description_zh": "40%的段落以显性连接词开头",
      "severity": "high",
      "affected_positions": ["1(2)", "2(1)", "2(3)", "3(1)"]
    }},
    {{
      "type": "linear_flow",
      "description": "Found First/Second/Third enumeration pattern",
      "description_zh": "发现第一/第二/第三枚举模式",
      "severity": "high",
      "affected_positions": ["2(1)", "2(2)", "2(3)"]
    }}
  ],
  "score_breakdown": {{
    "linear_flow": 20,
    "repetitive_pattern": 0,
    "uniform_length": 0,
    "predictable_order": 10,
    "connector_overuse": 15,
    "missing_semantic_echo": 10
  }},
  "recommendation": "1. Remove explicit connectors (Furthermore, Moreover, 此外) and use semantic echoing instead. 2. Break the linear enumeration pattern.",
  "recommendation_zh": "1. 移除显性连接词（Furthermore, Moreover, 此外），改用语义回声承接。2. 打破线性枚举模式。",
  "detailed_suggestions": {{
    "abstract_suggestions": [
      "摘要应提到第2章(方法论)中的核心技术如何在第4章(结果)中得到验证",
      "建议在摘要中明确指出研究的局限性，对应第5章(讨论)的内容"
    ],
    "logic_suggestions": [
      "建议将第3章(实验设计)与第4章(数据收集)合并，因为内容高度相关",
      "第5章(讨论)应移至第4章(结果)之后，当前顺序打断了论证链条"
    ],
    "section_suggestions": [
      {{
        "section_number": "1",
        "section_title": "Introduction",
        "severity": "high",
        "suggestion_type": "add_content",
        "suggestion_zh": "引言部分需要补充研究背景，增加领域文献引用",
        "suggestion_en": "Introduction needs more background context and literature citations",
        "details": [
          "补充3-5篇2020年后的相关文献引用",
          "增加研究问题的实际应用场景描述",
          "添加研究假设的明确陈述"
        ],
        "affected_paragraphs": ["1(1)", "1(2)"]
      }},
      {{
        "section_number": "3",
        "section_title": "Results",
        "severity": "medium",
        "suggestion_type": "split",
        "suggestion_zh": "结果部分内容过长，建议拆分为4个小节",
        "suggestion_en": "Results section is too long, suggest splitting into 4 subsections",
        "details": [
          "3.1 数据概述与预处理结果",
          "3.2 主要实验结果分析",
          "3.3 对比实验结果",
          "3.4 统计显著性分析"
        ],
        "affected_paragraphs": ["3(1)", "3(2)", "3(3)", "3(4)"]
      }},
      {{
        "section_number": "5,6",
        "section_title": "Discussion & Conclusion",
        "severity": "medium",
        "suggestion_type": "merge",
        "suggestion_zh": "讨论和结论章节内容重复，建议合并整合",
        "suggestion_en": "Discussion and Conclusion have overlapping content, suggest merging",
        "details": [
          "将第6章的研究局限性讨论并入第5章",
          "合并后统一命名为'讨论与结论'",
          "删除两章中重复的未来研究方向描述"
        ],
        "affected_paragraphs": ["5(1)", "5(2)", "6(1)"]
      }}
    ],
    "priority_order": ["1", "3", "5,6"],
    "overall_assessment_zh": "文档整体结构符合学术规范，但存在AI写作的典型特征：章节对称性过高、段落长度过于均匀。建议按优先级依次修改引言部分、结果部分和讨论结论部分。",
    "overall_assessment_en": "Document structure follows academic norms but shows typical AI writing patterns: high section symmetry and uniform paragraph lengths."
  }}
}}

CRITICAL RULES:
- Only include REAL paragraphs (continuous prose > 50 words)
- Use SPECIFIC topic summaries, not generic labels like "body/conclusion"
- Position format must be "SectionNum(ParaNum)"
- MUST detect and list ALL explicit connector words - this is the primary AI signal
- MUST analyze logic breaks between consecutive paragraphs
- MUST provide detailed_suggestions with specific, actionable advice for EACH section
- Section suggestions MUST be specific: cite paragraph positions, give concrete examples
- suggestion_type MUST be one of: add_content, restructure, merge, split, reorder, remove_connector, add_citation
"""


# =============================================================================
# Smart Structure Analyzer Class
# 智能结构分析器类
# =============================================================================

class SmartStructureAnalyzer:
    """
    LLM-powered document structure analyzer
    基于 LLM 的文档结构分析器
    """

    def __init__(self, model: str = None, temperature: float = 0.1):
        """
        Initialize the smart structure analyzer
        初始化智能结构分析器

        Args:
            model: LLM model name (defaults to settings)
            temperature: LLM temperature for consistency
        """
        self.model = model or settings.llm_model
        self.temperature = temperature

    async def analyze(self, document_text: str) -> Dict[str, Any]:
        """
        Analyze document structure using LLM (legacy combined analysis)
        使用 LLM 分析文档结构（遗留的组合分析）

        Args:
            document_text: Full document text

        Returns:
            SmartStructureAnalysis as dict
        """
        try:
            # Truncate if too long (keep first 15000 chars for context window)
            # 如果太长则截断
            if len(document_text) > 15000:
                document_text = document_text[:15000] + "\n\n[... document truncated for analysis ...]"

            # Build prompt
            # 构建提示词
            prompt = SMART_STRUCTURE_PROMPT.format(document_text=document_text)

            # Call LLM directly using httpx (bypassing proxy)
            # 直接使用httpx调用LLM（绕过代理）
            response_text = await self._call_llm(prompt)

            # Parse JSON response
            # 解析JSON响应
            result = self._parse_llm_response(response_text)

            # Validate and clean up result
            # 验证并清理结果
            return self._validate_result(result)

        except Exception as e:
            # Log the error for debugging
            # 记录错误以便调试
            import traceback
            logger.error(f"[SmartStructureAnalyzer] LLM Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[SmartStructureAnalyzer] Traceback: {traceback.format_exc()}")
            # Return fallback result on error
            # 错误时返回后备结果
            return self._fallback_analysis(document_text, str(e))

    async def analyze_structure(self, document_text: str, target_colloquialism: int = None) -> Dict[str, Any]:
        """
        Step 1-1: Analyze document STRUCTURE only (global patterns)
        步骤 1-1：仅分析文档结构（全局模式）

        This is the first phase of analysis focusing on:
        - Section structure identification
        - Paragraph identification
        - Global structural patterns (linear flow, symmetry, etc.)
        - Document style/formality detection (added for colloquialism support)

        Args:
            document_text: Full document text
            target_colloquialism: User's target colloquialism level (0-10), if provided will check for mismatch

        Returns:
            Structure analysis result with sections, paragraphs, structure issues, and style analysis
        """
        try:
            logger.info(f"[SmartStructureAnalyzer] Starting Step 1-1: Structure Analysis (target_colloquialism={target_colloquialism})")

            # Truncate if too long
            # 如果太长则截断
            if len(document_text) > 15000:
                document_text = document_text[:15000] + "\n\n[... document truncated for analysis ...]"

            # Build style context based on target colloquialism level
            # 根据目标口语化级别构建风格上下文
            style_context = self._build_style_context(target_colloquialism)

            # Build prompt for structure analysis
            # 构建结构分析提示词
            prompt = STRUCTURE_ANALYSIS_PROMPT.format(
                document_text=document_text,
                style_context=style_context
            )

            # Call LLM
            # 调用 LLM
            response_text = await self._call_llm(prompt)

            # Parse response
            # 解析响应
            result = self._parse_llm_response(response_text)

            # Validate structure-specific fields
            # 验证结构特定字段
            result = self._validate_structure_result(result)

            # Check for style mismatch and add warning if needed
            # 检查风格不匹配并在需要时添加警告
            result = self._check_style_mismatch(result, target_colloquialism)

            logger.info(f"[SmartStructureAnalyzer] Step 1-1 completed: {result.get('total_paragraphs', 0)} paragraphs, score={result.get('structure_score', 0)}")
            return result

        except Exception as e:
            import traceback
            logger.error(f"[SmartStructureAnalyzer] Step 1-1 Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[SmartStructureAnalyzer] Traceback: {traceback.format_exc()}")
            return self._fallback_structure_analysis(document_text, str(e))

    async def analyze_relationships(self, document_text: str, structure_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1-2: Analyze paragraph RELATIONSHIPS (connections, transitions)
        步骤 1-2：分析段落关系（连接、过渡）

        This is the second phase of analysis focusing on:
        - Explicit connector word detection
        - Logic break points between paragraphs
        - AI risk assessment for each paragraph
        - Rewrite suggestions

        Args:
            document_text: Full document text
            structure_result: Result from analyze_structure (Step 1-1)

        Returns:
            Relationship analysis result with connectors, logic breaks, and risks
        """
        try:
            logger.info("[SmartStructureAnalyzer] Starting Step 1-2: Relationship Analysis")

            # Truncate if too long
            # 如果太长则截断
            if len(document_text) > 15000:
                document_text = document_text[:15000] + "\n\n[... document truncated for analysis ...]"

            # Extract paragraph positions from structure result
            # 从结构结果中提取段落位置
            paragraph_positions = []
            for section in structure_result.get("sections", []):
                for para in section.get("paragraphs", []):
                    pos = para.get("position", "?")
                    summary = para.get("summary_zh", para.get("summary", ""))
                    paragraph_positions.append(f"{pos}: {summary}")

            positions_text = "\n".join(paragraph_positions) if paragraph_positions else "No paragraphs identified"

            # Build prompt for relationship analysis
            # 构建关系分析提示词
            prompt = RELATIONSHIP_ANALYSIS_PROMPT.format(
                document_text=document_text,
                paragraph_positions=positions_text
            )

            # Call LLM
            # 调用 LLM
            response_text = await self._call_llm(prompt)

            # Parse response
            # 解析响应
            result = self._parse_llm_response(response_text)

            # Validate relationship-specific fields
            # 验证关系特定字段
            result = self._validate_relationship_result(result)

            logger.info(f"[SmartStructureAnalyzer] Step 1-2 completed: {len(result.get('explicit_connectors', []))} connectors, {len(result.get('logic_breaks', []))} breaks")
            return result

        except Exception as e:
            import traceback
            logger.error(f"[SmartStructureAnalyzer] Step 1-2 Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[SmartStructureAnalyzer] Traceback: {traceback.format_exc()}")
            return self._fallback_relationship_analysis(str(e))

    def _validate_structure_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Step 1-1 structure result
        验证步骤 1-1 结构结果
        """
        if "sections" not in result:
            result["sections"] = []
        if "total_paragraphs" not in result:
            result["total_paragraphs"] = sum(
                len(s.get("paragraphs", [])) for s in result.get("sections", [])
            )
        if "total_sections" not in result:
            result["total_sections"] = len(result.get("sections", []))
        if "structure_score" not in result:
            result["structure_score"] = 0
        if "risk_level" not in result:
            result["risk_level"] = self._score_to_level(result["structure_score"])
        if "structure_issues" not in result:
            result["structure_issues"] = result.get("issues", [])
        if "score_breakdown" not in result:
            result["score_breakdown"] = {}
        if "recommendation_zh" not in result:
            result["recommendation_zh"] = ""
        return result

    def _validate_relationship_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Step 1-2 relationship result
        验证步骤 1-2 关系结果
        """
        if "explicit_connectors" not in result:
            result["explicit_connectors"] = []
        if "logic_breaks" not in result:
            result["logic_breaks"] = []
        if "paragraph_risks" not in result:
            result["paragraph_risks"] = []
        if "relationship_score" not in result:
            result["relationship_score"] = 0
        if "relationship_issues" not in result:
            result["relationship_issues"] = result.get("issues", [])
        if "score_breakdown" not in result:
            result["score_breakdown"] = {}
        return result

    def _fallback_structure_analysis(self, document_text: str, error: str) -> Dict[str, Any]:
        """
        Fallback for Step 1-1 when LLM fails
        LLM 失败时的步骤 1-1 后备
        """
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', document_text) if p.strip() and len(p.strip()) > 50]

        paragraph_analyses = []
        for i, p in enumerate(paragraphs[:20]):
            sentences = re.split(r'(?<=[.!?])\s+', p)
            paragraph_analyses.append({
                "position": f"?(${i+1})",
                "summary": f"Paragraph {i+1}",
                "summary_zh": f"第{i+1}段",
                "first_sentence": sentences[0][:100] if sentences else "",
                "last_sentence": sentences[-1][:100] if sentences else "",
                "word_count": len(p.split())
            })

        return {
            "sections": [{"number": "?", "title": "Document", "paragraphs": paragraph_analyses}],
            "total_paragraphs": len(paragraph_analyses),
            "total_sections": 1,
            "structure_score": 0,
            "risk_level": "unknown",
            "structure_issues": [{"type": "analysis_error", "description": f"LLM analysis failed: {error}", "description_zh": f"分析失败: {error}", "severity": "high", "affected_positions": []}],
            "score_breakdown": {},
            "recommendation_zh": "请重试分析"
        }

    def _fallback_relationship_analysis(self, error: str) -> Dict[str, Any]:
        """
        Fallback for Step 1-2 when LLM fails
        LLM 失败时的步骤 1-2 后备
        """
        return {
            "explicit_connectors": [],
            "logic_breaks": [],
            "paragraph_risks": [],
            "relationship_score": 0,
            "relationship_issues": [{"type": "analysis_error", "description": f"LLM analysis failed: {error}", "description_zh": f"分析失败: {error}", "severity": "high", "affected_positions": []}],
            "score_breakdown": {}
        }

    # =============================================================================
    # Style Analysis Helper Methods
    # 风格分析辅助方法
    # =============================================================================

    # Colloquialism level names mapping
    # 口语化级别名称映射
    COLLOQUIALISM_LEVELS = {
        0: ("Most Academic", "最学术化"),
        1: ("Very Academic", "非常学术"),
        2: ("Academic", "学术化"),
        3: ("Thesis Level", "论文级"),
        4: ("Moderate Academic", "适度学术"),
        5: ("Semi-formal", "半正式"),
        6: ("Conference Level", "会议级"),
        7: ("Technical Blog", "技术博客"),
        8: ("Casual Professional", "休闲专业"),
        9: ("Casual", "休闲"),
        10: ("Most Casual", "最口语化"),
    }

    def _build_style_context(self, target_colloquialism: int = None) -> str:
        """
        Build style context for the prompt based on user's target colloquialism level
        根据用户的目标口语化级别为提示词构建风格上下文

        Args:
            target_colloquialism: User's target colloquialism level (0-10)

        Returns:
            Style context string to insert into prompt
        """
        if target_colloquialism is None:
            return ""

        level_name, level_name_zh = self.COLLOQUIALISM_LEVELS.get(
            target_colloquialism, ("Unknown", "未知")
        )

        return f"""
**USER'S TARGET STYLE**: Level {target_colloquialism}/10 ({level_name} / {level_name_zh})

IMPORTANT: Compare the document's actual style against the user's target style.
If there is a significant mismatch (difference >= 3 levels), include a warning in your analysis.

For example:
- If user targets level 1 (Very Academic) but document is casual/diary-like (level 8-10), this is a CRITICAL mismatch
- If user targets level 7 (Technical Blog) but document is too formal (level 0-2), this is also a mismatch
"""

    def _check_style_mismatch(self, result: Dict[str, Any], target_colloquialism: int = None) -> Dict[str, Any]:
        """
        Check if detected style mismatches user's target and add warning
        检查检测到的风格是否与用户目标不匹配，并添加警告

        Args:
            result: Analysis result from LLM
            target_colloquialism: User's target colloquialism level (0-10)

        Returns:
            Updated result with mismatch warning if needed
        """
        if target_colloquialism is None:
            return result

        style_analysis = result.get("style_analysis", {})
        if not style_analysis:
            return result

        detected_style = style_analysis.get("detected_style")
        if detected_style is None:
            return result

        # Calculate style difference
        # 计算风格差异
        style_diff = abs(detected_style - target_colloquialism)

        # Add mismatch warning if significant difference (>= 3 levels)
        # 如果差异显著（>= 3级），添加不匹配警告
        if style_diff >= 3:
            target_name, target_name_zh = self.COLLOQUIALISM_LEVELS.get(
                target_colloquialism, ("Unknown", "未知")
            )
            detected_name = style_analysis.get("style_name", "Unknown")
            detected_name_zh = style_analysis.get("style_name_zh", "未知")

            # Determine mismatch direction
            # 确定不匹配方向
            if detected_style > target_colloquialism:
                # Document is more casual than expected
                # 文档比预期更口语化
                mismatch_warning = (
                    f"⚠️ STYLE MISMATCH: Your target style is Level {target_colloquialism} ({target_name}), "
                    f"but this document's actual style is Level {detected_style} ({detected_name}). "
                    f"The document is significantly MORE CASUAL/INFORMAL than your target. "
                    f"Consider: Is this document suitable for academic submission? "
                    f"The analysis and suggestions will use your target level {target_colloquialism}."
                )
                mismatch_warning_zh = (
                    f"⚠️ 风格不匹配警告：您的目标风格是 {target_colloquialism} 级（{target_name_zh}），"
                    f"但本文档的实际风格是 {detected_style} 级（{detected_name_zh}）。"
                    f"文档比您的目标风格显著更加口语化/非正式。"
                    f"请考虑：这篇文档是否适合学术提交？"
                    f"后续分析和建议将按照您的目标级别 {target_colloquialism} 进行。"
                )
            else:
                # Document is more formal than expected
                # 文档比预期更正式
                mismatch_warning = (
                    f"⚠️ STYLE MISMATCH: Your target style is Level {target_colloquialism} ({target_name}), "
                    f"but this document's actual style is Level {detected_style} ({detected_name}). "
                    f"The document is significantly MORE FORMAL/ACADEMIC than your target. "
                    f"The analysis and suggestions will use your target level {target_colloquialism}."
                )
                mismatch_warning_zh = (
                    f"⚠️ 风格不匹配警告：您的目标风格是 {target_colloquialism} 级（{target_name_zh}），"
                    f"但本文档的实际风格是 {detected_style} 级（{detected_name_zh}）。"
                    f"文档比您的目标风格显著更加正式/学术化。"
                    f"后续分析和建议将按照您的目标级别 {target_colloquialism} 进行。"
                )

            # Update style_analysis with warning
            # 更新 style_analysis 添加警告
            style_analysis["mismatch_warning"] = mismatch_warning
            style_analysis["mismatch_warning_zh"] = mismatch_warning_zh
            style_analysis["target_colloquialism"] = target_colloquialism
            style_analysis["style_mismatch_level"] = style_diff
            result["style_analysis"] = style_analysis

            # Also add as a structure issue for visibility
            # 同时作为结构问题添加以提高可见性
            if "structure_issues" not in result:
                result["structure_issues"] = []
            result["structure_issues"].insert(0, {
                "type": "style_mismatch",
                "description": mismatch_warning,
                "description_zh": mismatch_warning_zh,
                "severity": "high" if style_diff >= 5 else "medium",
                "affected_positions": ["全文"]
            })

        return result

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API directly using httpx with trust_env=False to bypass proxy
        直接使用httpx调用LLM API，设置trust_env=False以绕过代理
        """
        # DashScope (阿里云灵积) - Qwen models
        # 阿里云灵积 - 通义千问模型
        if settings.llm_provider == "dashscope" and settings.dashscope_api_key:
            return await self._call_dashscope(prompt)
        # Volcengine (火山引擎) - preferred for faster DeepSeek access
        # 火山引擎 - 更快的 DeepSeek 访问
        elif settings.llm_provider == "volcengine" and settings.volcengine_api_key:
            return await self._call_volcengine(prompt)
        # DeepSeek official (commented out - slower)
        # DeepSeek 官方（已注释 - 较慢）
        elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
            return await self._call_deepseek(prompt)
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            return await self._call_gemini(prompt)
        elif settings.openai_api_key:
            return await self._call_openai(prompt)
        else:
            raise ValueError("No LLM API configured. Please set DASHSCOPE_API_KEY or other LLM API key in .env")

    async def _call_dashscope(self, prompt: str) -> str:
        """
        Call DashScope (阿里云灵积) API - OpenAI compatible format
        调用阿里云灵积 API - OpenAI 兼容格式
        """
        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url,
            headers={
                "Authorization": f"Bearer {settings.dashscope_api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0,  # 5 minutes timeout for long documents
            trust_env=False  # Ignore system proxy settings
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.dashscope_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8192,  # Increased for longer documents
                "temperature": self.temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_volcengine(self, prompt: str) -> str:
        """
        Call Volcengine (火山引擎) DeepSeek API - OpenAI compatible format
        调用火山引擎 DeepSeek API - OpenAI 兼容格式
        """
        async with httpx.AsyncClient(
            base_url=settings.volcengine_base_url,
            headers={
                "Authorization": f"Bearer {settings.volcengine_api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0,  # 5 minutes timeout for long documents
            trust_env=False  # Ignore system proxy settings
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": settings.volcengine_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8192,  # Increased for longer documents
                "temperature": self.temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_deepseek(self, prompt: str) -> str:
        """
        Call DeepSeek API directly (official - slower than Volcengine)
        直接调用DeepSeek API（官方 - 比火山引擎慢）
        """
        async with httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0,  # 5 minutes timeout for long documents
            trust_env=False  # Ignore system proxy settings
        ) as client:
            response = await client.post("/chat/completions", json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8192,  # Increased for longer documents
                "temperature": self.temperature
            })
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API
        调用Gemini API
        """
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "max_output_tokens": 4096,
                "temperature": self.temperature
            }
        )
        return response.text

    async def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API
        调用OpenAI API
        """
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to JSON
        解析LLM响应为JSON
        """
        # Clean response (remove markdown code blocks if present)
        # 清理响应（如果存在则移除markdown代码块）
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            response = "\n".join(lines)
        response = response.strip()

        # Try to parse JSON, with truncation repair if needed
        # 尝试解析 JSON，如果需要则修复截断
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to repair truncated JSON
            # 尝试修复截断的 JSON
            logger.warning(f"[SmartStructureAnalyzer] Attempting to repair truncated JSON: {str(e)[:100]}")
            repaired = self._repair_truncated_json(response)
            if repaired:
                return json.loads(repaired)
            raise

    def _repair_truncated_json(self, response: str) -> Optional[str]:
        """
        Attempt to repair truncated JSON by adding missing closing brackets
        尝试通过添加缺失的闭合括号来修复截断的 JSON
        """
        # Count open brackets
        # 统计未闭合的括号
        open_braces = 0
        open_brackets = 0
        in_string = False
        escape_next = False

        for char in response:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
            elif char == '[':
                open_brackets += 1
            elif char == ']':
                open_brackets -= 1

        # If we're in a string, try to close it
        # 如果在字符串中，尝试关闭它
        if in_string:
            response = response.rstrip()
            # Remove incomplete escape sequence
            if response.endswith('\\'):
                response = response[:-1]
            response += '"'

        # Add missing closing brackets
        # 添加缺失的闭合括号
        response += ']' * open_brackets
        response += '}' * open_braces

        # Verify it's valid JSON now
        # 验证现在是否为有效 JSON
        try:
            json.loads(response)
            logger.info("[SmartStructureAnalyzer] JSON repair successful")
            return response
        except json.JSONDecodeError:
            logger.error("[SmartStructureAnalyzer] JSON repair failed")
            return None

    def analyze_sync(self, document_text: str) -> Dict[str, Any]:
        """
        Synchronous version of analyze
        同步版本的分析
        """
        import asyncio
        return asyncio.run(self.analyze(document_text))

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the LLM result
        验证并清理 LLM 结果
        """
        # Ensure required fields exist
        # 确保必需字段存在
        if "sections" not in result:
            result["sections"] = []
        if "total_paragraphs" not in result:
            result["total_paragraphs"] = sum(
                len(s.get("paragraphs", [])) for s in result.get("sections", [])
            )
        if "total_sections" not in result:
            result["total_sections"] = len(result.get("sections", []))
        if "structure_score" not in result:
            result["structure_score"] = 0
        if "risk_level" not in result:
            result["risk_level"] = self._score_to_level(result["structure_score"])
        if "issues" not in result:
            result["issues"] = []
        if "score_breakdown" not in result:
            result["score_breakdown"] = {}
        if "recommendation" not in result:
            result["recommendation"] = ""
        if "recommendation_zh" not in result:
            result["recommendation_zh"] = ""

        return result

    def _score_to_level(self, score: int) -> str:
        """Convert score to risk level 将分数转换为风险等级"""
        if score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        return "low"

    def _fallback_analysis(self, document_text: str, error: str) -> Dict[str, Any]:
        """
        Fallback analysis when LLM fails
        LLM 失败时的后备分析
        """
        # Simple paragraph split
        # 简单段落分割
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', document_text) if p.strip() and len(p.strip()) > 50]

        paragraph_analyses = []
        for i, p in enumerate(paragraphs[:20]):  # Limit to 20
            sentences = re.split(r'(?<=[.!?])\s+', p)
            paragraph_analyses.append({
                "position": f"?(${i+1})",
                "summary": f"Paragraph {i+1} content",
                "summary_zh": f"第{i+1}段内容",
                "first_sentence": sentences[0][:100] if sentences else "",
                "last_sentence": sentences[-1][:100] if sentences else "",
                "word_count": len(p.split()),
                "ai_risk": "unknown",
                "ai_risk_reason": "LLM analysis failed"
            })

        return {
            "sections": [{
                "number": "?",
                "title": "Document",
                "paragraphs": paragraph_analyses
            }],
            "total_paragraphs": len(paragraph_analyses),
            "total_sections": 1,
            "structure_score": 0,
            "risk_level": "unknown",
            "issues": [{
                "type": "analysis_error",
                "description": f"LLM analysis failed: {error}",
                "description_zh": f"LLM分析失败: {error}",
                "severity": "high",
                "affected_positions": []
            }],
            "score_breakdown": {},
            "recommendation": "Please retry analysis",
            "recommendation_zh": "请重试分析"
        }


# =============================================================================
# Paragraph Length Distribution Analysis (Step 1-2 Phase 1)
# 段落长度分布分析（Step 1-2 阶段1）
# =============================================================================

# LLM Prompt for semantic-based paragraph length strategy generation
# 基于语义的段落长度策略生成LLM提示词
PARAGRAPH_LENGTH_STRATEGY_PROMPT = """You are an expert academic writing analyst. Analyze the paragraph structure and generate strategies to improve length variation (CV).

## CURRENT SITUATION:
- Mean paragraph length: {mean_length:.1f} words
- Standard deviation: {std_dev:.1f}
- Coefficient of Variation (CV): {cv:.2f}
- Target CV: > 0.30 (human-like writing typically has CV 0.35-0.50)
- Problem: Paragraph lengths are TOO UNIFORM, which is a typical AI writing pattern

## PARAGRAPH LIST:
{paragraph_list}

## YOUR TASKS:

### 1. IDENTIFY EXPANDABLE PARAGRAPHS
Look for paragraphs that can be meaningfully expanded:
- **Introduction paragraphs**: Can add more background, motivation, research gaps
- **Methodology paragraphs**: Can add implementation details, parameter justification, algorithm steps
- **Analysis/Results paragraphs**: Can add more data interpretation, comparison with baselines, statistical details
- **Discussion paragraphs**: Can add implications, limitations, connections to prior work

For each expandable paragraph, explain WHAT SPECIFIC CONTENT to add.

### 2. IDENTIFY MERGEABLE PARAGRAPH PAIRS
Look for adjacent paragraphs that:
- Discuss the same topic/concept from different angles
- Have a clear cause-effect relationship
- Are both short and semantically tightly connected
- One provides context and the other provides details

Explain WHY they should be merged (semantic relationship).

### 3. IDENTIFY SPLITTABLE/COMPRESSIBLE PARAGRAPHS
Look for paragraphs that:
- Contain multiple distinct ideas or arguments
- Mix different topics (e.g., methods AND results)
- Are overly dense with information
- Have redundant content that can be compressed

Specify WHERE to split or WHAT to compress.

## OUTPUT FORMAT (JSON):
{{
  "strategies": [
    {{
      "strategy_type": "expand",
      "target_positions": ["1(1)"],
      "description": "Expand introduction with more research background",
      "description_zh": "扩展引言部分，增加更多研究背景",
      "reason": "Introduction paragraph is too brief, lacks context for the research problem",
      "reason_zh": "引言段落过于简短，缺乏研究问题的背景铺垫",
      "priority": 1,
      "expand_suggestion": "Add 2-3 sentences about: 1) Historical context of the problem, 2) Recent developments in the field, 3) Gap this research addresses",
      "expand_suggestion_zh": "建议添加2-3句话：1) 问题的历史背景 2) 领域近期发展 3) 本研究填补的空白"
    }},
    {{
      "strategy_type": "merge",
      "target_positions": ["2(1)", "2(2)"],
      "description": "Merge two methodology paragraphs discussing the same technique",
      "description_zh": "合并两个讨论相同技术的方法论段落",
      "reason": "Both paragraphs discuss data preprocessing, creating fragmented reading experience",
      "reason_zh": "两个段落都讨论数据预处理，造成阅读体验碎片化",
      "priority": 2,
      "semantic_relation": "Both describe sequential steps of the same preprocessing pipeline",
      "semantic_relation_zh": "两者描述同一预处理流程的连续步骤"
    }},
    {{
      "strategy_type": "split",
      "target_positions": ["3(2)"],
      "description": "Split paragraph containing both results and interpretation",
      "description_zh": "拆分同时包含结果和解释的段落",
      "reason": "Paragraph mixes data presentation with discussion, should be separated for clarity",
      "reason_zh": "段落混合了数据呈现和讨论，应分开以提高清晰度",
      "priority": 2,
      "split_points": ["After presenting the numerical results", "Before 'This suggests that...'"],
      "split_points_zh": ["在呈现数值结果之后", "在'这表明...'之前"]
    }},
    {{
      "strategy_type": "compress",
      "target_positions": ["4(1)"],
      "description": "Compress redundant discussion paragraph",
      "description_zh": "压缩冗余的讨论段落",
      "reason": "Paragraph repeats information already stated in results section",
      "reason_zh": "段落重复了结果部分已陈述的信息",
      "priority": 3,
      "split_points": ["Remove sentences 2-3 which repeat Table 1 data"],
      "split_points_zh": ["删除重复表1数据的第2-3句"]
    }}
  ],
  "analysis_summary": "Document has 12 paragraphs with very uniform lengths. Recommend 2 expansions, 1 merge, and 1 split to achieve natural variation.",
  "analysis_summary_zh": "文档有12个段落，长度非常均匀。建议2处扩展、1处合并、1处拆分以实现自然变化。"
}}

CRITICAL RULES:
- Generate AT LEAST 2-4 strategies, prioritizing those with highest impact on CV
- Each strategy must have SPECIFIC, ACTIONABLE suggestions (not generic advice)
- Priority 1 = highest priority, 5 = lowest
- Focus on strategies that will INCREASE length variation (some longer, some shorter)
- Consider the SEMANTIC CONTENT of paragraphs, not just their length
"""


class ParagraphLengthStrategy(BaseModel):
    """Strategy suggestion for paragraph length optimization 段落长度优化策略建议"""
    strategy_type: str = Field(description="merge|expand|split|compress")
    target_positions: List[str] = Field(description="Affected paragraph positions")
    description: str = Field(description="Strategy description")
    description_zh: str = Field(description="策略描述")
    reason: str = Field(description="Why this strategy is suggested")
    reason_zh: str = Field(description="建议原因")
    priority: int = Field(description="Priority 1-5, lower = more important")
    # For expand strategy, what kind of content to add
    # 对于扩展策略，建议添加什么类型的内容
    expand_suggestion: Optional[str] = Field(default=None, description="Suggestion for what to expand")
    expand_suggestion_zh: Optional[str] = Field(default=None, description="扩展建议")
    # For merge strategy, semantic relationship between paragraphs
    # 对于合并策略，段落间的语义关系
    semantic_relation: Optional[str] = Field(default=None, description="Semantic relationship for merge")
    semantic_relation_zh: Optional[str] = Field(default=None, description="合并的语义关系说明")
    # For split/compress strategy, what aspects to separate or remove
    # 对于拆分/压缩策略，应分离或删除哪些方面
    split_points: Optional[List[str]] = Field(default=None, description="Points where to split")
    split_points_zh: Optional[List[str]] = Field(default=None, description="建议拆分点")


class ParagraphLengthAnalysis(BaseModel):
    """Analysis of paragraph length distribution 段落长度分布分析"""
    paragraph_lengths: List[Dict[str, Any]] = Field(description="List of {position, word_count, section}")
    mean_length: float = Field(description="Mean paragraph length")
    std_dev: float = Field(description="Standard deviation")
    cv: float = Field(description="Coefficient of variation")
    is_uniform: bool = Field(description="Whether lengths are too uniform (CV < 0.3)")
    human_like_cv_target: float = Field(default=0.4, description="Target CV for human-like distribution")
    strategies: List[ParagraphLengthStrategy] = Field(description="Suggested strategies")
    summary: str = Field(description="Summary of length distribution")
    summary_zh: str = Field(description="长度分布摘要")


async def generate_semantic_strategies(
    paragraph_lengths: List[Dict[str, Any]],
    mean_length: float,
    std_dev: float,
    cv: float
) -> List[ParagraphLengthStrategy]:
    """
    Use LLM to generate semantic-aware strategies for paragraph length optimization
    使用LLM生成基于语义的段落长度优化策略

    Args:
        paragraph_lengths: List of paragraph info with position, word_count, section, summary
        mean_length: Mean paragraph length
        std_dev: Standard deviation
        cv: Coefficient of variation

    Returns:
        List of ParagraphLengthStrategy with semantic-aware suggestions
    """
    # Build paragraph list for prompt
    # 构建段落列表用于提示词
    paragraph_list_lines = []
    for para in paragraph_lengths:
        position = para.get("position", "?")
        word_count = para.get("word_count", 0)
        section = para.get("section", "?")
        summary_zh = para.get("summary_zh", "")
        summary = para.get("summary", "")
        display_summary = summary_zh if summary_zh else summary
        paragraph_list_lines.append(
            f"- {position} (Section {section}): {word_count} words - {display_summary}"
        )

    paragraph_list = "\n".join(paragraph_list_lines)

    # Build prompt
    # 构建提示词
    prompt = PARAGRAPH_LENGTH_STRATEGY_PROMPT.format(
        mean_length=mean_length,
        std_dev=std_dev,
        cv=cv,
        paragraph_list=paragraph_list
    )

    try:
        # Call LLM using SmartStructureAnalyzer's method
        # 使用SmartStructureAnalyzer的方法调用LLM
        analyzer = SmartStructureAnalyzer()
        response_text = await analyzer._call_llm(prompt)

        # Parse response
        # 解析响应
        result = analyzer._parse_llm_response(response_text)

        # Convert to ParagraphLengthStrategy objects
        # 转换为ParagraphLengthStrategy对象
        strategies = []
        for s in result.get("strategies", []):
            strategy = ParagraphLengthStrategy(
                strategy_type=s.get("strategy_type", "expand"),
                target_positions=s.get("target_positions", []),
                description=s.get("description", ""),
                description_zh=s.get("description_zh", ""),
                reason=s.get("reason", ""),
                reason_zh=s.get("reason_zh", ""),
                priority=s.get("priority", 3),
                expand_suggestion=s.get("expand_suggestion"),
                expand_suggestion_zh=s.get("expand_suggestion_zh"),
                semantic_relation=s.get("semantic_relation"),
                semantic_relation_zh=s.get("semantic_relation_zh"),
                split_points=s.get("split_points"),
                split_points_zh=s.get("split_points_zh")
            )
            strategies.append(strategy)

        # Sort by priority
        # 按优先级排序
        strategies.sort(key=lambda x: x.priority)

        logger.info(f"[SemanticStrategies] Generated {len(strategies)} strategies via LLM")
        return strategies

    except Exception as e:
        logger.error(f"[SemanticStrategies] LLM call failed: {e}")
        # Return empty list on failure, caller will handle fallback
        # 失败时返回空列表，调用者会处理后备逻辑
        return []


def analyze_paragraph_length_distribution(
    structure_result: Dict[str, Any]
) -> ParagraphLengthAnalysis:
    """
    Analyze paragraph length distribution and suggest strategies for improvement
    分析段落长度分布并建议改进策略

    This is Phase 1 of the enhanced Step 1-2 process.
    这是增强版 Step 1-2 的第一阶段。

    Args:
        structure_result: Result from Step 1-1 structure analysis

    Returns:
        ParagraphLengthAnalysis with strategies
    """
    import statistics

    # Extract paragraph lengths from structure result
    # 从结构结果中提取段落长度
    paragraph_lengths = []
    sections = structure_result.get("sections", [])

    for section in sections:
        section_num = section.get("number", "?")
        paragraphs = section.get("paragraphs", [])
        for para in paragraphs:
            paragraph_lengths.append({
                "position": para.get("position", "?"),
                "word_count": para.get("word_count", 0),
                "section": section_num,
                "summary": para.get("summary", ""),
                "summary_zh": para.get("summary_zh", "")
            })

    if not paragraph_lengths:
        return ParagraphLengthAnalysis(
            paragraph_lengths=[],
            mean_length=0,
            std_dev=0,
            cv=0,
            is_uniform=False,
            strategies=[],
            summary="No paragraphs found",
            summary_zh="未找到段落"
        )

    # Calculate statistics
    # 计算统计数据
    lengths = [p["word_count"] for p in paragraph_lengths]
    mean_len = statistics.mean(lengths)
    std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv = std_dev / mean_len if mean_len > 0 else 0

    is_uniform = cv < 0.30  # Human academic writing typically has CV > 0.35

    # Generate strategies
    # 生成策略
    strategies = []

    if is_uniform:
        # Sort by word count to find candidates for merging/splitting
        # 按字数排序以找到合并/拆分候选
        sorted_paras = sorted(paragraph_lengths, key=lambda x: x["word_count"])

        # Find short paragraphs that could be merged
        # 找到可以合并的短段落
        short_threshold = mean_len * 0.6  # Paragraphs below 60% of mean
        long_threshold = mean_len * 1.4   # Paragraphs above 140% of mean

        short_paras = [p for p in paragraph_lengths if p["word_count"] < short_threshold]
        long_paras = [p for p in paragraph_lengths if p["word_count"] > long_threshold]
        medium_paras = [p for p in paragraph_lengths if short_threshold <= p["word_count"] <= long_threshold]

        # Strategy 1: Merge adjacent short paragraphs
        # 策略1：合并相邻的短段落
        for i, para in enumerate(paragraph_lengths[:-1]):
            next_para = paragraph_lengths[i + 1]
            if para["word_count"] < short_threshold and next_para["word_count"] < short_threshold:
                # Check if same section
                if para["section"] == next_para["section"]:
                    strategies.append(ParagraphLengthStrategy(
                        strategy_type="merge",
                        target_positions=[para["position"], next_para["position"]],
                        description=f"Merge {para['position']} and {next_para['position']} (both short: {para['word_count']} + {next_para['word_count']} words)",
                        description_zh=f"合并 {para['position']} 和 {next_para['position']}（均较短：{para['word_count']} + {next_para['word_count']} 词）",
                        reason="Adjacent short paragraphs can be combined to create natural variation",
                        reason_zh="相邻的短段落可以合并以创造自然的长度变化",
                        priority=2
                    ))

        # Strategy 2: Expand medium paragraphs in expandable sections
        # 策略2：在可扩展的章节中扩展中等段落
        expandable_sections = ["introduction", "method", "result", "discussion", "data", "analysis"]
        for para in medium_paras:
            section_lower = para.get("section", "").lower()
            summary_lower = (para.get("summary", "") + " " + para.get("summary_zh", "")).lower()

            # Check if this is an expandable section
            is_expandable = any(kw in section_lower or kw in summary_lower for kw in expandable_sections)

            if is_expandable:
                expand_hint = ""
                expand_hint_zh = ""

                if "data" in summary_lower or "result" in summary_lower:
                    expand_hint = "Consider adding more data points, statistical details, or comparison with baseline"
                    expand_hint_zh = "考虑添加更多数据点、统计细节或与基线的比较"
                elif "method" in summary_lower or "analysis" in summary_lower:
                    expand_hint = "Consider adding implementation details, parameter choices, or methodological justification"
                    expand_hint_zh = "考虑添加实现细节、参数选择或方法论证"
                elif "introduction" in section_lower:
                    expand_hint = "Consider adding more background context or motivation"
                    expand_hint_zh = "考虑添加更多背景上下文或动机"
                else:
                    expand_hint = "Consider adding supporting details or examples"
                    expand_hint_zh = "考虑添加支持性细节或示例"

                strategies.append(ParagraphLengthStrategy(
                    strategy_type="expand",
                    target_positions=[para["position"]],
                    description=f"Expand {para['position']} ({para['word_count']} words)",
                    description_zh=f"扩展 {para['position']}（{para['word_count']} 词）",
                    reason="Expanding this paragraph will increase length variation",
                    reason_zh="扩展此段落将增加长度变化",
                    priority=3,
                    expand_suggestion=expand_hint,
                    expand_suggestion_zh=expand_hint_zh
                ))

        # Strategy 3: Split very long paragraphs
        # 策略3：拆分超长段落
        very_long_threshold = mean_len * 1.8
        for para in paragraph_lengths:
            if para["word_count"] > very_long_threshold:
                strategies.append(ParagraphLengthStrategy(
                    strategy_type="split",
                    target_positions=[para["position"]],
                    description=f"Split {para['position']} into 2 paragraphs ({para['word_count']} words, very long)",
                    description_zh=f"将 {para['position']} 拆分为2个段落（{para['word_count']} 词，过长）",
                    reason="Very long paragraphs can be split to create variation",
                    reason_zh="超长段落可以拆分以创造变化",
                    priority=2
                ))

    # Sort strategies by priority
    # 按优先级排序策略
    strategies.sort(key=lambda x: x.priority)

    # Generate summary
    # 生成摘要
    if is_uniform:
        summary = f"Paragraph lengths are too uniform (CV={cv:.2f}, target>0.30). {len(strategies)} strategies suggested."
        summary_zh = f"段落长度过于均匀（CV={cv:.2f}，目标>0.30）。建议{len(strategies)}种策略。"
    else:
        summary = f"Paragraph length distribution is acceptable (CV={cv:.2f})."
        summary_zh = f"段落长度分布可接受（CV={cv:.2f}）。"

    return ParagraphLengthAnalysis(
        paragraph_lengths=paragraph_lengths,
        mean_length=mean_len,
        std_dev=std_dev,
        cv=cv,
        is_uniform=is_uniform,
        strategies=strategies,
        summary=summary,
        summary_zh=summary_zh
    )


async def analyze_paragraph_length_distribution_async(
    structure_result: Dict[str, Any]
) -> ParagraphLengthAnalysis:
    """
    Async version: Analyze paragraph length distribution with LLM-based semantic analysis
    异步版本：使用LLM语义分析进行段落长度分布分析

    When simple statistical analysis doesn't generate strategies (because paragraphs are
    uniformly medium-length), this function calls LLM to analyze semantic relationships
    and generate intelligent merge/expand/split/compress suggestions.

    当简单统计分析无法生成策略时（因为段落长度均匀且都是中等长度），
    此函数调用LLM分析语义关系并生成智能的合并/扩展/拆分/压缩建议。

    Args:
        structure_result: Result from Step 1-1 structure analysis

    Returns:
        ParagraphLengthAnalysis with semantic-aware strategies
    """
    import statistics

    # First, run the basic statistical analysis
    # 首先，运行基本统计分析
    paragraph_lengths = []
    sections = structure_result.get("sections", [])

    for section in sections:
        section_num = section.get("number", "?")
        section_title = section.get("title", "")
        paragraphs = section.get("paragraphs", [])
        for para in paragraphs:
            paragraph_lengths.append({
                "position": para.get("position", "?"),
                "word_count": para.get("word_count", 0),
                "section": section_num,
                "section_title": section_title,
                "summary": para.get("summary", ""),
                "summary_zh": para.get("summary_zh", ""),
                "first_sentence": para.get("first_sentence", ""),
                "last_sentence": para.get("last_sentence", "")
            })

    if not paragraph_lengths:
        return ParagraphLengthAnalysis(
            paragraph_lengths=[],
            mean_length=0,
            std_dev=0,
            cv=0,
            is_uniform=False,
            strategies=[],
            summary="No paragraphs found",
            summary_zh="未找到段落"
        )

    # Calculate statistics
    # 计算统计数据
    lengths = [p["word_count"] for p in paragraph_lengths]
    mean_len = statistics.mean(lengths)
    std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv = std_dev / mean_len if mean_len > 0 else 0

    is_uniform = cv < 0.30

    # If uniform, use LLM to generate semantic-aware strategies
    # 如果均匀，使用LLM生成基于语义的策略
    strategies = []

    if is_uniform:
        logger.info(f"[ParagraphLengthAsync] CV={cv:.2f} < 0.30, calling LLM for semantic analysis")

        # Call LLM for semantic-aware strategies
        # 调用LLM进行语义分析
        llm_strategies = await generate_semantic_strategies(
            paragraph_lengths=paragraph_lengths,
            mean_length=mean_len,
            std_dev=std_dev,
            cv=cv
        )

        if llm_strategies:
            strategies = llm_strategies
            logger.info(f"[ParagraphLengthAsync] LLM generated {len(strategies)} strategies")
        else:
            # Fallback: Generate basic strategies if LLM fails
            # 后备：如果LLM失败，生成基本策略
            logger.warning("[ParagraphLengthAsync] LLM failed, generating fallback strategies")
            strategies = _generate_fallback_strategies(paragraph_lengths, mean_len, cv)

    # Generate summary
    # 生成摘要
    if is_uniform:
        summary = f"Paragraph lengths are too uniform (CV={cv:.2f}, target>0.30). {len(strategies)} strategies suggested."
        summary_zh = f"段落长度过于均匀（CV={cv:.2f}，目标>0.30）。建议{len(strategies)}种策略。"
    else:
        summary = f"Paragraph length distribution is acceptable (CV={cv:.2f})."
        summary_zh = f"段落长度分布可接受（CV={cv:.2f}）。"

    return ParagraphLengthAnalysis(
        paragraph_lengths=paragraph_lengths,
        mean_length=mean_len,
        std_dev=std_dev,
        cv=cv,
        is_uniform=is_uniform,
        strategies=strategies,
        summary=summary,
        summary_zh=summary_zh
    )


def _generate_fallback_strategies(
    paragraph_lengths: List[Dict[str, Any]],
    mean_len: float,
    cv: float
) -> List[ParagraphLengthStrategy]:
    """
    Generate fallback strategies when LLM is unavailable
    当LLM不可用时生成后备策略

    Args:
        paragraph_lengths: List of paragraph info
        mean_len: Mean paragraph length
        cv: Coefficient of variation

    Returns:
        List of basic strategies
    """
    strategies = []

    if not paragraph_lengths:
        return strategies

    # Strategy 1: Identify introduction paragraphs to expand
    # 策略1：识别可扩展的引言段落
    intro_paras = [p for p in paragraph_lengths if
                   p.get("section", "").lower() in ["1", "intro", "introduction"] or
                   "introduction" in p.get("section_title", "").lower() or
                   "引言" in p.get("summary_zh", "") or
                   "背景" in p.get("summary_zh", "")]

    for para in intro_paras[:1]:  # Only first intro paragraph
        strategies.append(ParagraphLengthStrategy(
            strategy_type="expand",
            target_positions=[para["position"]],
            description=f"Expand introduction paragraph {para['position']}",
            description_zh=f"扩展引言段落 {para['position']}",
            reason="Introduction paragraphs typically benefit from more context and background",
            reason_zh="引言段落通常需要更多的背景和上下文铺垫",
            priority=1,
            expand_suggestion="Add research background, motivation, and gap analysis",
            expand_suggestion_zh="添加研究背景、动机和研究空白分析"
        ))

    # Strategy 2: Identify methodology paragraphs to expand
    # 策略2：识别可扩展的方法论段落
    method_paras = [p for p in paragraph_lengths if
                    "method" in p.get("section_title", "").lower() or
                    "方法" in p.get("summary_zh", "") or
                    "实验" in p.get("summary_zh", "")]

    for para in method_paras[:1]:  # Only first method paragraph
        strategies.append(ParagraphLengthStrategy(
            strategy_type="expand",
            target_positions=[para["position"]],
            description=f"Expand methodology paragraph {para['position']}",
            description_zh=f"扩展方法论段落 {para['position']}",
            reason="Methodology paragraphs often need more implementation details",
            reason_zh="方法论段落通常需要更多的实现细节",
            priority=2,
            expand_suggestion="Add parameter justification, algorithm steps, or implementation details",
            expand_suggestion_zh="添加参数说明、算法步骤或实现细节"
        ))

    # Strategy 3: Suggest merging adjacent short paragraphs in same section
    # 策略3：建议合并同一章节内相邻的短段落
    for i in range(len(paragraph_lengths) - 1):
        para1 = paragraph_lengths[i]
        para2 = paragraph_lengths[i + 1]
        if (para1["section"] == para2["section"] and
            para1["word_count"] < mean_len * 0.8 and
            para2["word_count"] < mean_len * 0.8):
            strategies.append(ParagraphLengthStrategy(
                strategy_type="merge",
                target_positions=[para1["position"], para2["position"]],
                description=f"Consider merging {para1['position']} and {para2['position']}",
                description_zh=f"考虑合并 {para1['position']} 和 {para2['position']}",
                reason="Adjacent paragraphs in same section may have related content",
                reason_zh="同一章节内相邻段落可能有相关内容",
                priority=3,
                semantic_relation="Adjacent paragraphs in same section",
                semantic_relation_zh="同一章节内相邻段落"
            ))
            break  # Only suggest one merge

    # Strategy 4: Suggest splitting a long-ish paragraph
    # 策略4：建议拆分较长的段落
    long_paras = [p for p in paragraph_lengths if p["word_count"] > mean_len * 1.3]
    if long_paras:
        para = max(long_paras, key=lambda x: x["word_count"])
        strategies.append(ParagraphLengthStrategy(
            strategy_type="split",
            target_positions=[para["position"]],
            description=f"Consider splitting {para['position']} ({para['word_count']} words)",
            description_zh=f"考虑拆分 {para['position']}（{para['word_count']} 词）",
            reason="Longer paragraphs may contain multiple ideas that could be separated",
            reason_zh="较长的段落可能包含多个可以分开的观点",
            priority=3,
            split_points=["Look for topic shifts or transitional phrases"],
            split_points_zh=["寻找主题转换或过渡性短语"]
        ))

    # If still no strategies, add a general suggestion
    # 如果仍然没有策略，添加一个通用建议
    if not strategies and paragraph_lengths:
        # Pick a random middle paragraph to expand
        mid_idx = len(paragraph_lengths) // 2
        para = paragraph_lengths[mid_idx]
        strategies.append(ParagraphLengthStrategy(
            strategy_type="expand",
            target_positions=[para["position"]],
            description=f"Expand paragraph {para['position']} with more details",
            description_zh=f"扩展段落 {para['position']}，添加更多细节",
            reason=f"To increase length variation (current CV={cv:.2f}), some paragraphs need expansion",
            reason_zh=f"为增加长度变化（当前CV={cv:.2f}），部分段落需要扩展",
            priority=2,
            expand_suggestion="Add supporting examples, data, or analysis",
            expand_suggestion_zh="添加支持性示例、数据或分析"
        ))

    return strategies


# =============================================================================
# Convenience function
# 便捷函数
# =============================================================================

async def analyze_document_structure(document_text: str) -> Dict[str, Any]:
    """
    Convenience function to analyze document structure
    分析文档结构的便捷函数

    Args:
        document_text: Full document text

    Returns:
        Structure analysis result
    """
    analyzer = SmartStructureAnalyzer()
    return await analyzer.analyze(document_text)
