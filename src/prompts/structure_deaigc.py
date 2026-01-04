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
# 学术论文结构层面 De-AIGC 方法大全

## 核心原则

AI生成文本在结构上的最大特征是"过度完美"——逻辑过于线性、对称过于完美、过渡过于显式。
人类写作的特点是"有序中带有自然的不规则性"。

**重要：所有修改必须保持学术论文的严谨性和专业性，不能为了降低AI检测而牺牲学术质量。**

---

## 一、宏观结构优化方法

### 1.1 打破线性叙事（Linear Flow Breaking）

**问题**：AI倾向于使用"引言→方法→结果→讨论"的严格线性结构

**学术友好的解决方案**：
- **问题前置法**：在引言中先呈现一个具体的研究悖论或反常现象，再引出研究背景
- **案例开局法**：以一个具体的实验失败案例或研究困境开篇，增加叙事张力
- **结果闪回法**：在方法部分适当预告关键发现，创建非线性阅读体验
- **对话嵌入法**：在适当位置插入与其他研究者观点的"对话"，打破单一叙事线

**示例**：
原文：This paper investigates the effects of climate change on agriculture. First, we review existing literature...
改后：A 40% crop failure in the North China Plain in 2022 defied all predictive models. This anomaly—the focus of our investigation—challenges fundamental assumptions about...

### 1.2 章节功能重组（Section Function Reorganization）

**问题**：AI生成的各章节功能划分过于清晰，每章只做一件事

**学术友好的解决方案**：
- **功能融合**：在方法章节中融入部分结果预览，在结果中嵌入方法调整说明
- **论证交织**：让理论框架和实证分析在同一章节中交替出现
- **深浅搭配**：同一章节内安排不同深度的内容，如概述性段落与深入分析段落交替

**注意**：融合不能损害论文的可读性，必须保持逻辑的可追踪性

### 1.3 打破完美对称（Breaking Perfect Symmetry）

**问题**：AI倾向于生成对称结构，如每章段落数相近、每段字数均匀

**学术友好的解决方案**：
- **有意的不均衡**：重点章节可以是其他章节的2-3倍长度
- **段落长度变化**：关键论证用长段落深入展开，过渡性内容用短段落简洁处理
- **层级深度变化**：某些章节有3级子标题，某些只有2级，反映内容本身的复杂度差异

---

## 二、段落层面优化方法

### 2.1 移除显性连接词（Removing Explicit Connectors）

**问题**：AI过度使用"Furthermore", "Moreover", "Additionally", "In conclusion"等连接词

**学术友好的替代策略**：

#### 2.1.1 语义回声法（Semantic Echo）
用重复上段关键概念的方式自然承接，不需要显性连接词
- 原文：Furthermore, the temperature increase affects soil moisture.
- 改后：Soil moisture—directly impacted by these temperature shifts—demonstrates...

#### 2.1.2 代词承接法（Pronoun Bridge）
使用"This", "Such", "These findings"等代词自然过渡
- 原文：Moreover, our analysis reveals that...
- 改后：This pattern suggests that...

#### 2.1.3 问题引导法（Question-driven Transition）
用设问方式引入新内容
- 原文：Additionally, we examined the role of...
- 改后：How does this relate to agricultural output? Our examination of...

#### 2.1.4 对比引入法（Contrast Introduction）
通过对比自然过渡
- 原文：However, some researchers disagree.
- 改后：Smith (2020) challenges this interpretation, arguing that...

### 2.2 打破段落公式化模式（Breaking Formulaic Paragraph Patterns）

**问题**：AI段落常遵循"主题句→支持证据→小结"的公式

**学术友好的变体**：
- **证据先行**：先呈现数据或引用，再解释其意义
- **递进展开**：从具体到抽象，或从抽象到具体
- **反驳-修正结构**：先呈现可能的反对意见，再给出回应
- **类比开局**：用类比或隐喻开始段落

### 2.3 增加句子长度变化（Sentence Length Variation）

**问题**：AI句子长度过于均匀

**学术友好的方法**：
- 复杂论证用长句，结论性陈述用短句
- 在一组长句后插入一个简短有力的判断句
- 使用括号补充信息增加句子复杂度变化

---

## 三、衔接层面优化方法

### 3.1 隐性逻辑衔接（Implicit Logical Connection）

**目标**：让读者能感受到逻辑但看不到明显的逻辑标记

**方法**：
- **时间顺序隐含**：用时态变化暗示时间推移
- **因果关系隐含**：通过句子排列暗示因果，而非使用"because", "therefore"
- **对比关系隐含**：并置对比内容，不用"however", "on the contrary"

### 3.2 学术引用作为衔接（Citations as Transitions）

**方法**：
- 用不同学者观点的对话串联段落
- 用"X argued..., but Y later demonstrated..."的方式自然过渡
- 引用本身携带的时间线或逻辑关系作为衔接

### 3.3 主题词回环（Thematic Word Cycling）

**方法**：
- 段落首句重复上段末句的关键词
- 在不同段落中用同义词或近义词指代同一概念，创造"词汇回声"
- 使用指示代词（this phenomenon, such effects）建立连接

---

## 四、开头与结尾优化方法

### 4.1 避免公式化开头

**AI常见模式**：
- "This paper aims to..."
- "In recent years, there has been growing interest in..."
- "The purpose of this study is to..."

**学术友好的替代**：
- 以研究悖论或反常现象开篇
- 以具体数据或案例开篇
- 以学术争议开篇
- 以研究者的"困惑"开篇（第一人称适度使用）

### 4.2 避免过度闭合的结尾

**AI常见模式**：
- "In conclusion, this study has demonstrated..."
- "To summarize, the findings indicate..."
- 完美回应所有研究问题

**学术友好的替代**：
- **开放式结尾**：指出尚未解决的问题或新的研究方向
- **审慎结尾**：使用hedging语言（"may suggest", "appears to indicate"）
- **问题式结尾**：以新的研究问题收尾
- **局限性承认**：坦诚讨论研究局限，留下探索空间

---

## 五、跨段落优化方法

### 5.1 建立回指结构（Cross-Reference Structure）

**问题**：AI文本往往是线性的，缺少前后呼应

**方法**：
- 在后文中明确回指前文的论点或数据（"As noted in Section 2..."）
- 创建"论证循环"：在结论中呼应引言中提出的问题
- 使用脚注或括号建立跨段落连接

### 5.2 制造有控制的"不完美"

**方法**：
- 允许某些论点只是初步探讨，不必完全证明
- 保留一些"悬而未决"的讨论
- 承认数据的模糊性或解释的多样性

---

## 六、特定问题的解决方案

### 6.1 线性流程过于明显
**诊断**：Document follows a strict, linear progression: Introduction -> Methodology -> Results -> Conclusion
**解决方案**：
1. 在方法部分插入预期结果的简短讨论
2. 在结果部分回顾方法调整
3. 考虑使用"研究故事"叙事法，记录研究过程中的曲折

### 6.2 IMRaD结构过于公式化
**诊断**：Structure is a highly formulaic IMRaD format
**解决方案**：
1. 在标准章节外增加"研究背景"或"概念框架"章节
2. 将讨论和结论合并，或将方法和结果部分交织
3. 添加独立的"研究局限"章节

### 6.3 完美对称结构
**诊断**：Perfect symmetry: each section contains exactly one paragraph
**解决方案**：
1. 根据内容实际需要调整段落数量
2. 重点章节应该有更多段落
3. 某些章节可以只有概述性内容

### 6.4 段落长度过于均匀
**诊断**：All paragraphs are extremely short and uniform in length
**解决方案**：
1. 合并相关的短段落
2. 扩展关键论证段落
3. 创造长短段落交替的节奏感

### 6.5 显性连接词过度使用
**诊断**：Explicit AI-fingerprint connectors detected (Furthermore, Moreover, etc.)
**解决方案**：
1. 使用语义回声替代
2. 使用代词承接替代
3. 使用引用或数据作为过渡

### 6.6 缺乏回指结构
**诊断**：No cross-references between sections
**解决方案**：
1. 添加"如前所述"、"正如第X节讨论的"等回指
2. 在结论中呼应引言
3. 在讨论中引用之前的数据

---

## 重要提醒

1. **学术优先**：所有修改必须服务于学术表达，不能为降低AI检测而牺牲清晰度
2. **保持一致性**：选择的风格应在全文保持一致
3. **领域惯例**：不同学科有不同的写作惯例，修改应符合目标领域的规范
4. **参考文献**：所有引用和数据必须真实可查
5. **适度原则**：不需要使用所有方法，选择最适合的2-3种即可
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
Description: {issue_description_zh}
Severity: {severity}

## DOCUMENT CONTEXT
Structure Score: {structure_score}/100
Sections: {total_sections}, Paragraphs: {total_paragraphs}

## OUTPUT (JSON)
{{
  "diagnosis_zh": "【问题诊断】简明扼要的问题分析（2-3句）",
  "quick_fix_zh": "【快速修改】立即可执行的修改建议（具体步骤）",
  "detailed_strategy_zh": "【深度策略】更系统的修改方案",
  "prompt_snippet": "用户可以复制使用的提示词片段（中文）",
  "estimated_improvement": "预估改进幅度（分数）"
}}

Rules:
- All output in Chinese
- Be specific and actionable
- Keep academic standards
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
            issue_description_zh=issue_description_zh,
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
