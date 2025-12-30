# AcademicGuard 开发计划
# AcademicGuard Development Plan

> 版本 Version: v1.0
> 状态 Status: 规划中 / Planning
> 更新日期 Last Updated: 2024-12-29

---

## 一、项目概述 | Project Overview

### 1.1 项目名称 | Project Name

**AcademicGuard: 英文论文 AIGC 检测与人源化协作引擎**
**AcademicGuard: Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

### 1.2 核心定位 | Core Positioning

| 定位 | 说明 |
|------|------|
| **产品类型** | 人机协作工具（非自动改写工具） |
| **Product Type** | Human-AI Collaboration Tool (Not Auto-rewriting) |
| **核心价值** | AI教你改，而非AI替你改 |
| **Core Value** | AI guides you to revise, not revise for you |
| **目标用户** | ESL研究者、学术论文作者 |
| **Target Users** | ESL researchers, academic paper authors |

### 1.3 核心功能 | Core Features

```
输入论文 → 逐句AIGC风险分析 → 双轨建议生成 → 用户选择/修改 → 验证通过 → 输出
Input   → Sentence-by-sentence Analysis → Dual-track Suggestions → User Choice → Validation → Output
```

---

## 二、产品设计 | Product Design

### 2.1 双模式设计 | Dual Mode Design

#### YOLO模式 (自动处理模式) | YOLO Mode (Auto-processing)

| 项目 | 说明 |
|------|------|
| **适用场景** | 时间紧迫、长文档快速处理 |
| **Use Case** | Time-sensitive, quick processing of long documents |
| **处理流程** | 全文分析 → 自动应用最优建议 → 生成对比报告 → 用户审核 |
| **Process** | Full analysis → Auto-apply optimal suggestions → Generate diff report → User review |
| **用户控制** | 设置策略偏好、处理范围、阈值，最后统一审核 |
| **User Control** | Set preferences, scope, thresholds; review at end |

#### 干预模式 (逐句控制模式) | Intervention Mode (Sentence-by-sentence)

| 项目 | 说明 |
|------|------|
| **适用场景** | 重要论文、想学习AIGC特征、高质量要求 |
| **Use Case** | Important papers, learning AIGC patterns, high quality requirements |
| **处理流程** | 逐句分析 → 展示双轨建议 → 用户选择或自定义 → 实时验证 → 下一句 |
| **Process** | Analyze each sentence → Show dual suggestions → User selects/customizes → Validate → Next |
| **用户控制** | 每句完全控制，可跳过、标记、自定义修改 |
| **User Control** | Full control per sentence; skip, flag, or customize |

### 2.2 双轨建议系统 | Dual-track Suggestion System

这是核心功能，为每个风险句子提供两种来源的修改建议：
This is the core feature, providing two sources of suggestions for each risky sentence:

#### 轨道A: LLM智能建议 | Track A: LLM-powered Suggestions

| 项目 | 说明 |
|------|------|
| **技术基础** | Prompt Engineering + Claude/GPT-4 API |
| **Technology** | Prompt Engineering + Claude/GPT-4 API |
| **优势** | 语义理解深、改写自然流畅、可处理复杂句式 |
| **Strengths** | Deep semantic understanding, natural rewriting, handles complex sentences |
| **劣势** | 成本较高、输出有一定随机性 |
| **Weaknesses** | Higher cost, some output variability |
| **适用场景** | 复杂长句、需要重构逻辑的句子 |
| **Best For** | Complex sentences, sentences needing logical restructuring |

#### 轨道B: 规则建议 | Track B: Rule-based Suggestions

| 项目 | 说明 |
|------|------|
| **技术基础** | 同义词替换 + 句法重组 + BERT MLM |
| **Technology** | Synonym replacement + Syntactic restructuring + BERT MLM |
| **优势** | 速度快、成本低、可解释性强、确定性高 |
| **Strengths** | Fast, low cost, highly explainable, deterministic |
| **劣势** | 处理复杂句式能力有限 |
| **Weaknesses** | Limited capability for complex sentences |
| **适用场景** | 简单替换、指纹词清除、基础句式调整 |
| **Best For** | Simple replacements, fingerprint word removal, basic syntax adjustment |

#### 用户选择 | User Choice

```
展示界面 Display:
┌─────────────────────────────────────────┐
│ [A] LLM建议 - 预测风险: 25  语义: 94%   │  ← 用户可选
│ [B] 规则建议 - 预测风险: 40  语义: 98%  │  ← 用户可选
│ [C] 自定义输入 ___________________      │  ← 用户可自行修改
└─────────────────────────────────────────┘
```

### 2.3 口语化程度参数 | Colloquialism Level Parameter

用户可设置 0-10 的口语化程度，影响LLM改写风格和规则引擎的词汇选择：
Users can set a 0-10 colloquialism level affecting LLM style and rule engine word choices:

```
0 ─────────────────────────────────────────── 10
│                                              │
Most Academic                          Most Casual
(最学术化)                               (最口语化)
```

| 等级 Level | 名称 Name | 典型场景 Typical Use |
|------------|-----------|---------------------|
| 0-2 | 期刊论文级 Journal Paper | 顶刊投稿、正式出版 |
| 3-4 | 学位论文级 Thesis | 硕博论文、学位答辩 |
| 5-6 | 会议论文级 Conference | 会议投稿、技术报告 |
| 7-8 | 技术博客级 Tech Blog | 博客文章、内部文档 |
| 9-10 | 口语讨论级 Casual | 非正式讨论、草稿 |

#### 等级对词汇的影响示例 | Level Impact on Vocabulary

| 原词 Original | 0-2 | 3-4 | 5-6 | 7-10 |
|---------------|-----|-----|-----|------|
| utilize | utilize | use | use | use |
| demonstrate | demonstrate | show | show | show |
| subsequently | subsequently | then | then | after that |
| numerous | numerous | many | many | a lot of |
| commence | commence | begin | start | start |

### 2.4 多语言支持 | Multi-language Support

为ESL用户提供母语解释，帮助理解为什么要修改：
Provide native language explanations for ESL users to understand why changes are needed:

```
┌──────────────────────────────────────────────────────┐
│  English (Original):                                 │
│  "The methodology demonstrates significant efficacy" │
├──────────────────────────────────────────────────────┤
│  中文 (语义对照):                                     │
│  "该方法展示了显著的效果。"                           │
├──────────────────────────────────────────────────────┤
│  中文 (问题解释):                                     │
│  • "demonstrates significant efficacy" 是AI常用的     │
│    高级词堆砌模式，真人更可能写 "works well"          │
└──────────────────────────────────────────────────────┘
```

**支持语言 Supported Languages:**
- 中文 Chinese (优先 Priority)
- 日语 Japanese
- 韩语 Korean
- 西班牙语 Spanish

---

## 三、检测分析设计 | Detection Analysis Design

### 3.1 双检测器视角 | Dual Detector Perspectives

针对主流检测器的不同侧重点，提供差异化分析：
Provide differentiated analysis targeting different detector focuses:

| 检测器 Detector | 核心逻辑 Core Logic | 重点检测 Focus Areas |
|-----------------|---------------------|---------------------|
| **Turnitin** | 基于训练数据的分类器 | 整体文风、段落结构、引用模式 |
| **GPTZero** | 困惑度 + 突发性 | 句子级PPL、长度变化、词汇选择 |

### 3.2 检测维度 | Detection Dimensions

#### 维度1: 用词分析 | Dimension 1: Vocabulary Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **困惑度 PPL** | 使用LLaMA/Mistral计算，阈值<20为高风险 |
| **Perplexity** | Calculate using LLaMA/Mistral, threshold <20 is high risk |
| **AI指纹词密度** | 匹配"delve", "crucial", "paramount"等高频词库 |
| **Fingerprint Density** | Match high-frequency words like "delve", "crucial", "paramount" |
| **N-gram重复率** | 检测连续词组的重复模式 |
| **N-gram Repetition** | Detect repetitive patterns in word sequences |

#### 维度2: 结构分析 | Dimension 2: Structure Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **突发性 Burstiness** | 句子长度标准差/平均值，AI文本此值偏低 |
| **Burstiness** | Std(sentence_length)/Mean, AI text has lower values |
| **段落均质性** | 检测段落长度是否过于整齐 |
| **Paragraph Homogeneity** | Detect if paragraph lengths are too uniform |
| **段落首句模式** | AI倾向每段用"总起句"开头 |
| **Opening Sentence Pattern** | AI tends to start paragraphs with topic sentences |

#### 维度3: 逻辑分析 | Dimension 3: Logic Analysis

| 指标 Metric | 说明 Description |
|-------------|------------------|
| **连接词频率** | 统计"However/Therefore/Moreover"使用频率 |
| **Connector Frequency** | Count usage of "However/Therefore/Moreover" |
| **过渡平滑度** | 检测过度平滑的段落过渡 |
| **Transition Smoothness** | Detect overly smooth paragraph transitions |

### 3.3 风险评分 | Risk Scoring

```
综合风险分数 = Σ(维度分数 × 权重)
Overall Risk Score = Σ(Dimension Score × Weight)

风险等级 Risk Levels:
- 0-30:  低风险 Low Risk     (绿色 Green)
- 31-60: 中风险 Medium Risk  (黄色 Yellow)
- 61-100: 高风险 High Risk   (红色 Red)
```

---

## 四、技术架构 | Technical Architecture

### 4.1 系统架构图 | System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 Frontend                         │
│                    React + TailwindCSS                       │
├─────────────────────────────────────────────────────────────┤
│                        API网关 Gateway                       │
│                         FastAPI                              │
├──────────────────────┬──────────────────────────────────────┤
│    分析引擎层        │           建议生成层                   │
│  Analysis Engine     │      Suggestion Generator             │
│  ┌────────────────┐  │  ┌─────────────┬─────────────┐       │
│  │ Turnitin模拟   │  │  │  轨道A      │  轨道B      │       │
│  │ Turnitin Sim   │  │  │  LLM Engine │  Rule Engine│       │
│  ├────────────────┤  │  │  Claude/GPT │  spaCy+BERT │       │
│  │ GPTZero模拟    │  │  └─────────────┴─────────────┘       │
│  │ GPTZero Sim    │  │                                      │
│  ├────────────────┤  │  ┌─────────────────────────────┐     │
│  │ 通用AIGC检测   │  │  │    多语言解释生成器          │     │
│  │ General AIGC   │  │  │  Multilingual Explainer     │     │
│  └────────────────┘  │  └─────────────────────────────┘     │
├──────────────────────┴──────────────────────────────────────┤
│                      数据层 Data Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐     │
│  │ AI指纹词库   │ │ 同义词词典   │ │ 学术术语白名单   │     │
│  │ Fingerprint  │ │ Synonym Dict │ │ Term Whitelist   │     │
│  └──────────────┘ └──────────────┘ └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 技术栈 | Tech Stack

| 层级 Layer | 技术 Technology | 说明 Notes |
|------------|-----------------|------------|
| **前端 Frontend** | React + TailwindCSS | 复杂交互需要React |
| **后端 Backend** | FastAPI (Python) | 高性能，适合ML部署 |
| **NLP核心 NLP Core** | spaCy + Stanza | Stanza对学术文本更准 |
| **ML模型 ML Models** | Transformers (HuggingFace) | BERT MLM, Sentence-BERT |
| **LLM接口 LLM API** | Claude API / OpenAI API | 需设计fallback机制 |
| **语义相似度 Similarity** | Sentence-BERT | all-MiniLM-L6-v2 |
| **数据库 Database** | SQLite / PostgreSQL | MVP用SQLite |

### 4.3 核心模块 | Core Modules

```
src/
├── api/                    # FastAPI 路由
│   ├── routes/
│   └── middleware/
├── core/                   # 核心业务逻辑
│   ├── analyzer/           # 检测分析引擎
│   │   ├── perplexity.py   # PPL计算
│   │   ├── fingerprint.py  # 指纹词检测
│   │   ├── burstiness.py   # 突发性计算
│   │   └── scorer.py       # 综合评分
│   ├── humanizer/          # 人源化引擎
│   │   ├── llm_track.py    # 轨道A: LLM建议
│   │   ├── rule_track.py   # 轨道B: 规则建议
│   │   └── selector.py     # 建议选择器
│   ├── preprocessor/       # 预处理
│   │   ├── segmenter.py    # 分句
│   │   └── term_locker.py  # 术语锁定
│   └── validator/          # 质量验证
│       ├── semantic.py     # 语义相似度
│       └── risk_check.py   # 风险复检
├── data/                   # 数据资源
│   ├── fingerprint_words.json
│   ├── synonyms/
│   └── term_whitelist/
├── prompts/                # Prompt模板
│   ├── humanize.py
│   └── colloquialism.py
└── utils/                  # 工具函数
```

---

## 五、Prompt工程设计 | Prompt Engineering Design

### 5.1 主Prompt模板 | Main Prompt Template

```python
HUMANIZE_PROMPT = """
You are an academic writing advisor helping to make text sound more naturally human-written.

## Original Sentence
{sentence}

## Detected AIGC Issues
{issues}

## Protected Terms (DO NOT MODIFY)
{locked_terms}

## Target Colloquialism Level: {level}/10
{style_guide}

## Word Preferences for This Level
{word_preferences}

## Requirements
1. Preserve EXACT academic meaning
2. Address all detected AIGC issues
3. Match the specified colloquialism level precisely
4. Keep all protected terms unchanged
5. Output must be a single sentence (unless splitting is specifically requested)

## Response Format (JSON)
{
  "rewritten": "your rewritten sentence",
  "changes": [
    {"original": "word1", "replacement": "word2", "reason": "..."}
  ],
  "explanation_zh": "中文解释为什么这样改",
  "risk_reduction": "high/medium/low"
}
"""
```

### 5.2 口语化等级Prompt | Colloquialism Level Prompts

```python
STYLE_GUIDES = {
    "0-2": """
    Style: Most Academic (Journal Paper Level)
    - Use formal academic register exclusively
    - Prefer Latinate vocabulary (utilize, demonstrate, indicate)
    - Use passive voice where appropriate
    - Avoid contractions entirely
    - Use hedging language (it appears that, evidence suggests)
    - Complex sentence structures with subordinate clauses
    """,

    "3-4": """
    Style: Academic Moderate (Thesis Level)
    - Use formal academic vocabulary
    - First person plural acceptable (we found, our results)
    - Avoid contractions in main text
    - Balance passive and active voice
    - Clear but sophisticated sentence structures
    """,

    "5-6": """
    Style: Semi-formal (Conference Paper Level)
    - Mix of academic and common vocabulary
    - Contractions acceptable occasionally
    - Prefer active voice for clarity
    - Varied sentence length
    - Direct statements preferred
    """,

    "7-8": """
    Style: Casual Professional (Tech Blog Level)
    - Prefer common words over academic jargon
    - Contractions encouraged
    - Active voice strongly preferred
    - Short, punchy sentences
    - Conversational but professional
    """,

    "9-10": """
    Style: Casual Informal (Discussion Level)
    - Everyday conversational language
    - Contractions always preferred
    - Informal expressions acceptable
    - Very short sentences, fragments okay
    - Colloquialisms and mild slang okay
    """
}
```

---

## 六、规则引擎设计 | Rule Engine Design

### 6.1 同义词替换模块 | Synonym Replacement Module

```python
# AI指纹词 → 人类常用词 映射表
# AI Fingerprint → Human-preferred Word Mapping
FINGERPRINT_REPLACEMENTS = {
    "delve": ["explore", "examine", "look at", "investigate"],
    "paramount": ["important", "key", "main", "central"],
    "utilize": ["use", "apply", "employ"],
    "facilitate": ["help", "enable", "support"],
    "comprehensive": ["full", "complete", "thorough"],
    "subsequently": ["then", "later", "after that"],
    "aforementioned": ["these", "this", "the above"],
    "pertaining to": ["about", "regarding", "on"],
    "in order to": ["to"],
    "due to the fact that": ["because", "since"],
    "it is important to note that": ["note that", "importantly"],
    "a wide range of": ["many", "various"],
    "in the context of": ["in", "for", "regarding"],
    "plays a crucial role": ["is important", "matters", "helps"],
}
```

### 6.2 句法重组模块 | Syntactic Restructuring Module

| 重组类型 Type | 说明 Description | 示例 Example |
|--------------|------------------|--------------|
| **主动↔被动** Active↔Passive | 语态转换 | "We analyzed..." ↔ "The data was analyzed..." |
| **句子拆分** Split | 长句变短句 | 30+词句子拆为两句 |
| **句子合并** Merge | 短句变复合句 | 两个相关短句合并 |
| **从句移位** Clause Move | 调整从句位置 | 后置从句移到句首 |
| **插入语添加** Parenthetical | 增加节奏变化 | 添加"in fact", "arguably" |

### 6.3 BERT MLM上下文感知替换 | BERT MLM Context-aware Replacement

```python
def context_aware_synonym(sentence: str, target_word: str) -> list:
    """
    Use BERT MLM to find contextually appropriate synonyms
    使用BERT MLM找到上下文合适的同义词
    """
    # 1. Mask target word
    masked = sentence.replace(target_word, "[MASK]")

    # 2. Get BERT predictions
    predictions = bert_mlm(masked, top_k=10)

    # 3. Filter: keep only human-preferred words
    filtered = [p for p in predictions
                if p not in AI_FINGERPRINT_WORDS]

    return filtered[:5]
```

---

## 七、质量控制 | Quality Control

### 7.1 多层验证 | Multi-layer Validation

| 层级 Layer | 检查内容 Check | 阈值 Threshold |
|------------|---------------|----------------|
| **语义层** Semantic | Sentence-BERT相似度 | ≥ 0.80 |
| **事实层** Factual | 关键实体保留检查 | 100% |
| **术语层** Term | 锁定术语完整性 | 100% |
| **风险层** Risk | 改写后风险评分 | 目标值以下 |

### 7.2 回滚机制 | Rollback Mechanism

```
如果验证失败 If validation fails:
1. 语义相似度 < 0.80 → 使用规则建议替代 / Use rule suggestion instead
2. 仍然失败 → 标记为"需人工处理" / Flag as "needs manual review"
3. 最多重试3次 → 超过则跳过 / Max 3 retries, then skip
```

---

## 八、开发阶段 | Development Phases

### Phase 1: MVP核心闭环 | MVP Core Loop

**目标 Goal:** 跑通"输入→检测→建议→验证→输出"基础流程
**Run through basic "input→detect→suggest→validate→output" flow**

| 任务 Task | 优先级 Priority |
|-----------|-----------------|
| 文本分句模块 Text segmentation | P0 |
| 基础PPL计算 Basic PPL calculation | P0 |
| AI指纹词检测 Fingerprint detection | P0 |
| 风险评分系统 Risk scoring system | P0 |
| LLM建议生成(轨道A) LLM suggestions (Track A) | P0 |
| 基础同义词替换(轨道B) Basic synonym replacement (Track B) | P0 |
| 语义相似度验证 Semantic similarity validation | P0 |
| 干预模式基础UI Intervention mode basic UI | P0 |

### Phase 2: 双轨完善 | Dual-track Enhancement

**目标 Goal:** 完善双轨建议系统，增加口语化参数
**Enhance dual-track system, add colloquialism parameter**

| 任务 Task | 优先级 Priority |
|-----------|-----------------|
| 句法重组模块 Syntactic restructuring | P1 |
| BERT MLM上下文替换 BERT MLM context replacement | P1 |
| 口语化等级参数(0-10) Colloquialism level (0-10) | P1 |
| 口语化Prompt模板库 Colloquialism prompt templates | P1 |
| 术语锁定功能 Term locking feature | P1 |
| YOLO模式实现 YOLO mode implementation | P1 |
| 双检测器视角(Turnitin/GPTZero) Dual detector views | P1 |

### Phase 3: 多语言与体验优化 | Multilingual & UX

**目标 Goal:** 多语言支持，优化用户体验
**Multilingual support, optimize user experience**

| 任务 Task | 优先级 Priority |
|-----------|-----------------|
| 中文解释生成 Chinese explanation generation | P2 |
| 日/韩/西语支持 Japanese/Korean/Spanish support | P2 |
| 批量处理相似问题句子 Batch process similar sentences | P2 |
| 进度可视化优化 Progress visualization | P2 |
| 修改历史与对比报告 Edit history & diff report | P2 |

### Phase 4: 测试与部署 | Testing & Deployment

**目标 Goal:** 系统测试，部署上线
**System testing, deployment**

| 任务 Task | 优先级 Priority |
|-----------|-----------------|
| 单元测试覆盖 Unit test coverage | P3 |
| 100篇AI论文对抗测试 Test with 100 AI papers | P3 |
| 性能优化 Performance optimization | P3 |
| 部署配置 Deployment configuration | P3 |

---

## 九、风险与应对 | Risks & Mitigation

| 风险 Risk | 等级 Level | 应对策略 Mitigation |
|-----------|-----------|---------------------|
| LLM输出不稳定 LLM output instability | 高 High | 规则建议作为fallback |
| API成本过高 High API cost | 中 Medium | 优先规则建议，LLM按需调用 |
| 检测器更新导致失效 Detector updates | 中 Medium | 定期更新指纹词库 |
| 术语误改 Term modification errors | 高 High | 强制术语锁定机制 |
| 语义漂移 Semantic drift | 中 Medium | 严格语义相似度阈值 |

---

## 十、成功指标 | Success Metrics

| 指标 Metric | 目标 Target |
|-------------|-------------|
| 高风险句转低风险率 High→Low risk conversion | ≥ 80% |
| 平均语义保持度 Average semantic similarity | ≥ 85% |
| 单句处理时间 Per-sentence processing time | ≤ 3s |
| 用户满意度 User satisfaction | ≥ 4.0/5.0 |

---

## 附录 | Appendix

### A. AI指纹词库(部分) | AI Fingerprint Words (Partial)

```
高频词 High-frequency:
delve, crucial, paramount, utilize, facilitate, comprehensive,
subsequently, aforementioned, pertaining, realm, tapestry,
multifaceted, leverage, robust, seamless, cutting-edge

高频短语 High-frequency phrases:
"it is important to note", "plays a crucial role",
"in the context of", "a wide range of", "due to the fact that",
"in order to", "as a result of", "with respect to"
```

### B. 参考资源 | References

- GPTZero Detection Methodology
- Turnitin AI Writing Detection
- Perplexity and Burstiness in AI Text Detection
- Academic Writing Style Guides

---

> 文档维护 Document Maintenance:
> 本文档为项目唯一计划文档，所有规划变更需同步更新此文件。
> This is the sole planning document. All planning changes must be synced here.
