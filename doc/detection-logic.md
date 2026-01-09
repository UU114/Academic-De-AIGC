# DEAI 检测逻辑完整文档
# DEAI Detection Logic Complete Documentation

> 版本 Version: 2.0
> 更新日期 Last Updated: 2026-01-07
> 目的 Purpose: 梳理所有检测逻辑，明确层级关系和集成状态

---

## 目录 Table of Contents

1. [总体架构](#一总体架构)
2. [Level 1 - 文章/结构层级](#二level-1---文章结构层级检测)
3. [Level 2 - 段落/衔接层级](#三level-2---段落衔接层级检测)
4. [Level 3 - 句子/用词层级](#四level-3---句子用词层级检测)
5. [未集成模块分析](#五未集成模块分析与建议插入位置)
6. [双轨建议系统](#六双轨建议系统)
7. [模块依赖关系](#七模块依赖关系)
8. [集成状态汇总](#八集成状态汇总)

---

## 一、总体架构

### 1.1 三层级 De-AIGC 处理流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      三层级 De-AIGC 检测与处理流程                         │
│                   Three-Level De-AIGC Detection Flow                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Level 1: 骨架重组 (Macro Structure) - Step 1-1, 1-2            │    │
│  │  ├── 全文逻辑诊断 (SmartStructureAnalyzer)                       │    │
│  │  ├── 段落长度分布分析 (CV检测)                                    │    │
│  │  ├── 段落关系分析                                                │    │
│  │  ├── [待集成] 结构预测性评分 (StructurePredictabilityAnalyzer)   │    │
│  │  └── [待集成] 学术锚点密度 (AnchorDensityAnalyzer)               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    ↓                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Level 2: 关节润滑 (Paragraph Transition) - Step 2              │    │
│  │  ├── 段落衔接分析 (TransitionAnalyzer)                          │    │
│  │  ├── 段落内逻辑框架分析 (ParagraphLogicAnalyzer)                 │    │
│  │  ├── 句子角色检测 (10种角色, LLM驱动)                            │    │
│  │  └── 句子融合策略                                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    ↓                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Level 3: 皮肤精修 (Sentence Polish) - Step 3                   │    │
│  │  ├── CAASS v2.0 综合风险评分 (RiskScorer)                        │    │
│  │  ├── 指纹词检测 (FingerprintDetector)                           │    │
│  │  ├── PPL困惑度计算 (ONNX distilgpt2)                            │    │
│  │  ├── 突发性分析 (BurstinessAnalyzer)                            │    │
│  │  ├── 显性连接词检测 (ConnectorDetector)                         │    │
│  │  └── [待集成] 句法空洞检测 (SyntacticVoidDetector)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 处理顺序原则

| 原则 Principle | 说明 Description |
|----------------|------------------|
| **顺序强制** | 必须按 Level 1 → 2 → 3 顺序处理 |
| **Order Enforced** | Must process in Level 1 → 2 → 3 order |
| **原因** | 如果先改句子(L3)再调结构(L1)，结构调整可能导致句子级修改失效 |
| **Reason** | If L3 done before L1, structure changes may invalidate sentence edits |

---

## 二、Level 1 - 文章/结构层级检测

### 2.1 智能结构分析 (SmartStructureAnalyzer) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/smart_structure.py` |
| **API端点** | `POST /api/v1/structure/analyze-step1` |
| **模型依赖** | LLM (Claude/GPT/DashScope) |
| **集成状态** | ✅ 已集成 |

#### 检测维度

| 问题类型 | 英文 | 加分 | 说明 |
|---------|------|------|------|
| 线性流动 | linear_flow | +20 | First...Second...Third 枚举模式 |
| 重复模式 | repetitive_pattern | +15 | 章节结构重复 |
| 均匀长度 | uniform_length | +10 | 段落长度均匀 |
| 可预测顺序 | predictable_order | +10 | 公式化 intro-body-conclusion |
| 对称结构 | symmetry | +15 | 完美对称的章节结构 |

#### 风格分析 (0-10等级)

| 等级 Level | 名称 Name | 特征 Characteristics |
|------------|-----------|----------------------|
| 0-2 | 学术 Academic | 被动语态、引用、hedging语言 |
| 3-4 | 论文级 Thesis | 半正式、允许第一人称复数 |
| 5-6 | 半正式 Semi-formal | 会议论文/技术报告风格 |
| 7-8 | 技术博客 Tech Blog | 对话式、允许缩写 |
| 9-10 | 休闲 Casual | 非正式、口语化表达 |

#### 输出数据结构

```python
SmartStructureAnalysis:
  - sections: List[SectionInfo]           # 章节列表
  - total_paragraphs: int                  # 总段落数
  - total_sections: int                    # 总章节数
  - structure_score: int                   # 结构分数 0-100
  - risk_level: str                        # 风险等级 high/medium/low
  - issues: List[StructureIssueInfo]       # 检测到的问题
  - style_analysis: Optional[StyleAnalysis] # 风格分析
```

---

### 2.2 段落长度分布分析 ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/smart_structure.py` |
| **API端点** | `POST /api/v1/structure/paragraph-length/analyze` |
| **模型依赖** | LLM (语义分析时) |
| **集成状态** | ✅ 已集成 |

#### 检测指标

| 指标 Metric | 阈值 Threshold | 说明 Description |
|-------------|----------------|------------------|
| CV (变异系数) | < 0.30 | 过于均匀 = AI特征 |
| Coefficient of Variation | < 0.30 | Too uniform = AI characteristic |
| 目标 CV | ≥ 0.40 | 人类学术写作的目标 |
| Target CV | ≥ 0.40 | Target for human academic writing |
| 短段落阈值 | 平均长度的 60% | 可合并 |
| Short paragraph | 60% of average | Can be merged |
| 超长段落阈值 | 平均长度的 180% | 建议拆分 |
| Long paragraph | 180% of average | Suggest split |

#### 策略类型

| 策略 Strategy | 图标 | 说明 Description |
|---------------|------|------------------|
| merge | 🔗 | 合并相邻短段落 Merge adjacent short paragraphs |
| expand | 📈 | 扩展中等长度段落 Expand medium paragraphs |
| split | ✂️ | 拆分过长段落 Split long paragraphs |
| compress | 📉 | 删除冗余内容 Remove redundant content |

#### 输出数据结构

```python
ParagraphLengthAnalysis:
  - cv: float                              # 变异系数
  - mean_length: float                     # 平均长度
  - std_length: float                      # 标准差
  - is_too_uniform: bool                   # 是否过于均匀
  - paragraphs: List[ParagraphLengthInfo]  # 段落信息
  - strategies: List[ParagraphLengthStrategy] # 建议策略
```

---

### 2.3 结构预测性评分 (StructurePredictabilityAnalyzer) ⚠️ 未集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/structure_predictability.py` |
| **API端点** | 无 (未集成) |
| **模型依赖** | 无 (纯规则) |
| **集成状态** | ⚠️ 代码存在但未被调用 |

#### 核心洞察

> "AI的核心特征不是线性，而是结构高度可预测"
> "AI's key feature is not linearity, but high structural predictability"

#### 五维度评分体系

| 维度 Dimension | 权重 Weight | AI特征 AI-like | 人类特征 Human-like |
|----------------|-------------|----------------|---------------------|
| 推进可预测性 Progression | 25% | First/Second/Third单调递进 | 回溯、条件、局部反转 |
| 功能均匀性 Function | 20% | 每段落功能相似 | 非对称：深入一点，扫过其他 |
| 闭合强度 Closure | 20% | "In conclusion" 明确总结 | 开放问题、未解决张力 |
| 长度规律性 Length | 15% | 段落长度均匀(CV<0.2) | 段落长度参差(CV>0.5) |
| 连接词显性度 Connector | 20% | Furthermore/Moreover显性连接 | 词汇回声隐性连接 |

#### 单调推进标记词 (AI模式)

```
顺序 Sequential: first, second, third, firstly, secondly, finally
累加 Additive: furthermore, moreover, additionally, in addition
因果 Causal: therefore, thus, hence, consequently, as a result
```

#### 非单调标记词 (人类模式)

```
回溯 Return: as noted earlier, returning to, recall that
条件 Conditional: if, when, unless, provided that
对比 Contrastive: however, but, yet, nevertheless, on the other hand
让步 Concessive: although, though, despite, even though
```

#### 输出数据结构

```python
PredictabilityScore:
  - total_score: int                      # 总分 0-100
  - progression_predictability: int       # 推进可预测性
  - function_uniformity: int              # 功能均匀性
  - closure_strength: int                 # 闭合强度
  - length_regularity: int                # 长度规律性
  - connector_explicitness: int           # 连接词显性度
  - progression_type: str                 # "monotonic" | "non_monotonic" | "mixed"
  - function_distribution: str            # "uniform" | "asymmetric" | "balanced"
  - closure_type: str                     # "strong" | "moderate" | "weak" | "open"
  - lexical_echo_score: float             # 词汇回声分数 0-1
  - risk_level: str                       # "low" | "medium" | "high"
```

---

### 2.4 学术锚点密度分析 (AnchorDensityAnalyzer) ⚠️ 未集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/anchor_density.py` |
| **API端点** | 无 (未集成) |
| **模型依赖** | 无 (纯规则) |
| **集成状态** | ⚠️ 代码存在但未被调用 |

#### 核心功能

检测"幻觉风险" - 长段落中缺乏具体证据的AI填充物
Detect "hallucination risk" - AI-generated filler lacking concrete evidence in long paragraphs

#### 锚点类型 (13种)

| 类型 Type | 示例 Example | 权重 Weight |
|-----------|--------------|-------------|
| DECIMAL_NUMBER | 14.2, 3.5 | 1.0 |
| PERCENTAGE | 50%, 14.2% | 1.2 |
| STATISTICAL_VALUE | p < 0.05, r = 0.82 | 1.5 |
| SAMPLE_SIZE | n=500, N=1000 | 1.3 |
| CITATION_BRACKET | [1], [2,3] | 1.5 |
| CITATION_AUTHOR | (Smith, 2020) | 1.5 |
| UNIT_MEASUREMENT | 5mL, 20°C, 3.5kg | 1.3 |
| CHEMICAL_FORMULA | H2O, CO2, NaCl | 1.2 |
| SPECIFIC_COUNT | 500 samples, 3 groups | 1.4 |
| SCIENTIFIC_NOTATION | 1.5e-3, 2.0×10^6 | 1.3 |
| ACRONYM | ANOVA, CNN, LSTM | 1.0 |
| EQUATION_REF | Eq. 1, Equation (2) | 1.4 |
| FIGURE_TABLE_REF | Fig. 1, Table 2 | 1.4 |

#### 幻觉风险判定

| 密度阈值 (每100词) | 风险等级 | 说明 |
|-------------------|---------|------|
| < 5.0 | 高风险 High | 可能是AI填充物 Possible AI filler |
| 5.0 - 10.0 | 中等风险 Medium | 需要更多具体证据 May need more evidence |
| > 10.0 | 低风险 Low | 内容有实质性 Content has substance |

#### 输出数据结构

```python
AnchorDensityResult:
  - overall_density: float                    # 整体密度
  - total_anchors: int                        # 总锚点数
  - total_words: int                          # 总词数
  - paragraph_analyses: List[ParagraphAnchorAnalysis]  # 段落分析
  - high_risk_paragraphs: List[int]           # 高风险段落索引
  - anchor_type_distribution: Dict[str, int]  # 锚点类型分布
  - document_hallucination_risk: str          # 文档级风险 low/medium/high
```

---

## 三、Level 2 - 段落/衔接层级检测

### 3.1 段落衔接分析 (TransitionAnalyzer) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/transition.py` |
| **API端点** | `POST /api/v1/transition/analyze` |
| **模型依赖** | LLM (生成建议时) |
| **集成状态** | ✅ 已集成 |

#### 衔接问题类型

| 类型 Type | 说明 Description | 措施 Action |
|-----------|------------------|-------------|
| explicit_connector | 显性连接词过多 Too many explicit connectors | 使用隐性衔接 Use implicit connection |
| too_smooth | 过度平滑过渡 Overly smooth transition | 添加节奏变化 Add rhythm variation |
| abrupt | 突兀过渡 Abrupt transition | 添加语义桥接 Add semantic bridge |
| repetitive_opener | 重复开头 Repetitive opening | 变换开头方式 Vary opening style |
| ai_perfect_linear | AI式完美线性过渡 AI-like perfect linear | 打破线性 Break linearity |

#### 过渡策略

| 策略 Strategy | 英文 | 说明 Description |
|---------------|------|------------------|
| 语义回声 | SEMANTIC_ECHO | 在下段开头自然引用上段关键词 |
| 逻辑设问 | LOGICAL_HOOK | 用问题引导到下一段 |
| 节奏打断 | RHYTHM_BREAK | 用短句或转折打断单调节奏 |

#### 输出数据结构

```python
TransitionAnalysisResult:
  - risk_score: int                        # 风险分数 0-100
  - risk_level: str                        # 风险等级
  - issues: List[TransitionIssue]          # 检测到的问题
  - suggestions: List[TransitionSuggestion] # 建议
```

---

### 3.2 段落逻辑分析 (ParagraphLogicAnalyzer) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/paragraph_logic.py` |
| **API端点** | `POST /api/v1/paragraph/analyze` |
| **模型依赖** | 无 (纯规则) |
| **集成状态** | ✅ 已集成 |

#### 检测AI模式

| 问题类型 Type | 说明 Description | 严重度 Severity |
|---------------|------------------|-----------------|
| linear_structure | 线性/同质结构 Linear/homogeneous structure | high |
| subject_repetition | 主语重复 (The X... The X...) Subject repetition | medium |
| uniform_length | 句长均匀 (CV过低) Uniform sentence length | medium |
| first_person_overuse | 第一人称过多 (We... We...) First person overuse | low |
| weak_logic | 逻辑连接薄弱 Weak logic connection | medium |
| citation_pattern | AI式括号引用堆砌 AI-like citation stacking | medium |

#### 引用模式检测

```python
CITATION_PATTERNS = [
    # 标准APA格式: (Smith, 2023), (Smith & Jones, 2023), (Smith et al., 2023)
    r'\(([A-Z][a-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][a-z]+)?),?\s*(\d{4}[a-z]?)\)',
    # 多引用: (Smith, 2023; Jones, 2022)
    r'\((?:[A-Z][a-z]+...;\s*)+...\)',
    # 带页码: (Smith, 2023, p. 45)
    r'\([A-Z][a-z]+...,\s*p+\.\s*\d+(?:-\d+)?\)',
]
```

#### 输出数据结构

```python
ParagraphLogicResult:
  - issues: List[LogicIssue]              # 检测到的问题
  - subject_diversity_score: float        # 主语多样性 0-1
  - length_variation_cv: float            # 句长变异系数
  - logic_structure: str                  # 逻辑结构类型
  - first_person_ratio: float             # 第一人称比例
  - connector_density: float              # 连接词密度
  - overall_risk: int                     # 总体风险 0-100
```

---

### 3.3 句子角色检测 (LLM驱动) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/paragraph_logic.py` + `src/prompts/paragraph_logic.py` |
| **API端点** | `POST /api/v1/paragraph/analyze-logic-framework` |
| **模型依赖** | LLM |
| **集成状态** | ✅ 已集成 |

#### 10种句子角色

| 角色 Role | 英文 English | 说明 Description |
|-----------|--------------|------------------|
| 论点 | CLAIM | 陈述主要论点或立场 State main argument or position |
| 证据 | EVIDENCE | 数据、引用或事实支持 Data, citations, or factual support |
| 分析 | ANALYSIS | 解释数据或阐述关系 Interpret data or explain relationships |
| 批判 | CRITIQUE | 质疑、挑战或识别局限性 Question, challenge, or identify limitations |
| 让步 | CONCESSION | 承认反论点或复杂性 Acknowledge counterarguments or complexity |
| 综合 | SYNTHESIS | 整合多个观点或视角 Integrate multiple viewpoints |
| 过渡 | TRANSITION | 连接不同想法或章节 Connect different ideas or sections |
| 背景 | CONTEXT | 提供背景或定位主题 Provide background or position topic |
| 含义推导 | IMPLICATION | 得出更广泛结论或意义 Draw broader conclusions or significance |
| 展开细化 | ELABORATION | 对前一点添加细节 Add details to previous point |

#### 逻辑框架模式

| AI式刚性模式 (高风险) | 人类化动态模式 (低风险) |
|----------------------|----------------------|
| LINEAR_TEMPLATE 线性模板 | ANI_STRUCTURE ANI结构 |
| ADDITIVE_STACK 叠加堆砌 | CRITICAL_DEPTH 批判深度 |
| UNIFORM_RHYTHM 均匀节奏 | NON_LINEAR 非线性 |
| | VARIED_RHYTHM 变化节奏 |

#### 输出数据结构

```python
ParagraphLogicFrameworkResult:
  - sentence_roles: List[SentenceRole]    # 句子角色列表
  - logic_framework: LogicFramework       # 逻辑框架
  - burstiness_analysis: BurstinessAnalysis # 爆发度分析
  - missing_elements: List[str]           # 缺失元素
  - suggestions: List[str]                # 改进建议
```

---

### 3.4 句子融合策略 ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/prompts/paragraph_logic.py` |
| **API端点** | `POST /api/v1/paragraph/restructure` (strategy="sentence_fusion") |
| **模型依赖** | LLM |
| **集成状态** | ✅ 已集成 |

#### 语义关系分析

| 关系类型 Type | 决策 Decision | 融合技术 Fusion Technique |
|---------------|---------------|---------------------------|
| CAUSE_EFFECT | 考虑合并 Consider merge | because, since从句 |
| ELABORATION | 考虑合并 Consider merge | which, that关系从句 |
| DEFINITION_EXAMPLE | 考虑合并 Consider merge | 同位语结构 Appositive |
| CONDITION_RESULT | 考虑合并 Consider merge | provided that, given that |
| TOPIC_SHIFT | 保持分离 Keep separate | - |
| CONTRAST | 保持分离 Keep separate | - |

#### 平衡要求

```
- 长句 (25-40+ 词) 1-2 句（来自合并）
- 短句 (8-14 词) 1-2 句（用于强调）
- 目标 CV > 0.30
```

---

## 四、Level 3 - 句子/用词层级检测

### 4.1 CAASS v2.0 综合风险评分 (RiskScorer) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/scorer.py` |
| **API端点** | `POST /api/v1/analyze/` |
| **模型依赖** | ONNX distilgpt2 (PPL计算) |
| **集成状态** | ✅ 已集成 |

#### CAASS v2.0 Phase 2 评分公式

```
总风险分 = 上下文基准分(0-25)
         + 指纹词绝对分(0-80)
         + 结构模式分(0-40)
         + PPL贡献分(0-20)
         - 人类特征减分(0-50)

Total Risk = Context Baseline (0-25)
           + Fingerprint Absolute (0-80)
           + Structure Pattern (0-40)
           + PPL Contribution (0-20)
           - Human Feature Deduction (0-50)
```

#### 指纹词三级分类 + 语气适配

| 类型 Type | 词汇示例 Examples | 语气0-2 | 语气3-4 | 语气5 |
|-----------|-------------------|---------|---------|-------|
| **A类 (确凿证据)** Type A (Dead Giveaways) | delve, tapestry, plethora | +40 | +40-45 | +50 |
| **B类 (学术套话)** Type B (Academic Clichés) | crucial, paramount | +5-10 | +15-18 | +25 |
| **C类 (连接词)** Type C (Connectors) | furthermore, moreover | +10-15 | +18-22 | +30 |

#### A类确凿证据词表 (Level 1 Fingerprints)

```
delve, delves, delving
tapestry, tapestries
testament to
in the realm of, realm of
landscape of
multifaceted
inextricably
a plethora of, plethora
myriad of
elucidate, elucidates, elucidating
henceforth
aforementioned
cascading mechanisms
interfacial
valorization
poses a dual threat
systemic understanding
remains fragmented
critically synthesizes
concurrent escalation
```

#### B类学术套话词表 (Level 2 Fingerprints)

```
crucial, pivotal, paramount
it is crucial to, it is important to note
underscores the importance, underscore, underscores
plays a pivotal role, plays a crucial role
foster a culture, foster, fosters
comprehensive, holistic approach, holistic
facilitate, facilitates, facilitating
leverage, leveraging
robust, seamless
noteworthy, groundbreaking
furthermore, moreover, additionally
in conclusion, to summarize, in summary
```

#### 风险等级映射

| 分数范围 Score Range | 等级 Level | 颜色 Color |
|---------------------|------------|------------|
| 0-9 | safe 安全 | 绿色 Green |
| 10-24 | low 低风险 | 蓝色 Blue |
| 25-49 | medium 中风险 | 橙色 Orange |
| 50-100 | high 高风险 | 红色 Red |

#### 输出数据结构

```python
SentenceAnalysisResult:
  - risk_score: int                       # 风险分数 0-100
  - risk_level: str                       # 风险等级
  - ppl: float                            # 困惑度值
  - ppl_risk: str                         # 困惑度风险等级
  - fingerprints: List[FingerprintMatch]  # 指纹词匹配
  - fingerprint_density: float            # 指纹词密度
  - issues: List[IssueDetail]             # 问题详情
  - turnitin_view: DetectorView           # Turnitin视角
  - gptzero_view: DetectorView            # GPTZero视角
  - burstiness_value: float               # 突发性值
  - burstiness_risk: str                  # 突发性风险
  - connector_count: int                  # 连接词数量
  - context_baseline: int                 # 上下文基准分
```

---

### 4.2 指纹词检测 (FingerprintDetector) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/fingerprint.py` |
| **API端点** | 通过 `/api/v1/analyze/` 调用 |
| **模型依赖** | 无 (纯规则) |
| **集成状态** | ✅ 已集成 |

#### 高频AI词汇 (HIGH_FREQ_WORDS)

每个词配有：
- 风险权重 (0.4-1.0)
- 替换建议列表
- 支持活用形式 (delves, utilizing等)

#### AI偏好短语 (32个模式)

| 短语 Phrase | 权重 Weight |
|-------------|-------------|
| it is important to note that | 0.8 |
| plays a crucial role in | 0.9 |
| a wide range of | 0.6 |
| in the context of | 0.5 |
| due to the fact that | 0.7 |
| in order to | 0.4 |
| ... (共32个) | 0.4-0.9 |

#### 学术锚点免疫 (DEAI 2.0)

```
检测学术特征:
- 数字 (14.2%)
- 统计值 (p<0.05)
- 单位 (mL)
- 化学式 (H2O)
- 引用

规则: 若指纹词靠近锚点, 权重降低50%
```

---

### 4.3 困惑度计算 (PPL Calculator) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/ppl_calculator.py` |
| **API端点** | 通过 `/api/v1/analyze/` 调用 |
| **模型依赖** | ONNX distilgpt2 (真实PPL) / zlib压缩比 (备用) |
| **集成状态** | ✅ 已集成 |

#### PPL风险映射

| PPL值 | 风险等级 | 评分贡献 |
|-------|---------|---------|
| < 20 | 高风险 High | +15-20分 |
| 20-40 | 中风险 Medium | +5-15分 |
| > 40 | 低风险 Low | 0分 |

#### 技术路线

```
1. 优先使用: ONNX模型 (distilgpt2) 真实PPL计算
2. 备选方案: zlib压缩比代理
3. 原理: 低PPL(易压缩) = 高AI风险; 高PPL(难压缩) = 人类特征
```

---

### 4.4 突发性分析 (BurstinessAnalyzer) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/burstiness.py` |
| **API端点** | 通过 `/api/v1/analyze/` 调用 |
| **模型依赖** | 无 (纯计算) |
| **集成状态** | ✅ 已集成 |

#### 计算公式

```
突发性 Burstiness = 句长标准差 / 句长平均值
Burstiness = Std(sentence_length) / Mean(sentence_length)
```

#### 风险映射

| 突发性值 | 风险等级 | 说明 |
|---------|---------|------|
| < 0.3 | 高风险 High | 句长极均匀 = AI特征 Very uniform = AI-like |
| 0.3-0.5 | 中等风险 Medium | 适中 Moderate |
| > 0.5 | 低风险 Low | 人类特征 Human-like |

#### 输出数据结构

```python
BurstinessResult:
  - burstiness_score: float              # 突发性值 0-1
  - risk_score: int                      # 风险贡献 0-30
  - risk_level: str                      # 风险等级
  - sentence_lengths: List[int]          # 各句词数
  - mean_length: float                   # 平均句长
  - std_length: float                    # 句长标准差
```

---

### 4.5 显性连接词检测 (ConnectorDetector) ✅ 已集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/connector_detector.py` |
| **API端点** | 通过 `/api/v1/analyze/` 调用 |
| **模型依赖** | 无 (纯规则) |
| **集成状态** | ✅ 已集成 |

#### 连接词分级

| 严重级别 Severity | 示例 Examples | 建议 Suggestion |
|-------------------|---------------|-----------------|
| 高 High | Furthermore, Therefore, However | 删除或自然融合 Delete or naturally integrate |
| 中 Medium | It is important to note that, In particular | 删除或简化 Delete or simplify |
| 段首特殊 Paragraph-start | Firstly, Secondly, Finally | 仅在段落开头检测 Only at paragraph start |

#### 输出数据结构

```python
ConnectorAnalysisResult:
  - total_connectors: int                # 总数
  - high_severity_count: int             # 高严重性数量
  - medium_severity_count: int           # 中严重性数量
  - risk_score: int                      # 风险贡献 0-30
  - matches: List[ConnectorMatch]        # 匹配列表
```

---

### 4.6 句法空洞检测 (SyntacticVoidDetector) ⚠️ 未集成

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/analyzer/syntactic_void.py` |
| **API端点** | 无 (未集成) |
| **模型依赖** | spaCy en_core_web_md (依存句法分析) |
| **集成状态** | ⚠️ 代码存在但未被调用 |

#### 核心功能

检测"语法正确但语义空洞"的AI华丽结构
Detect "grammatically correct but semantically empty" flowery AI structures

#### 空洞模式类型 (7种)

| 模式 Pattern | 示例 Example | 严重度 Severity | 建议 Suggestion |
|--------------|--------------|-----------------|-----------------|
| ABSTRACT_VERB_NOUN | "underscores the significance of" | high | 用 "shows" 替代 |
| TESTAMENT_PHRASE | "serves as a testament to" | high | 直接陈述证据 |
| PIVOTAL_ROLE | "plays a pivotal role in" | high | 用 "X enables Y" 替代 |
| LANDSCAPE_PHRASE | "in the comprehensive landscape of" | high | 删除隐喻性短语 |
| EMPTY_FILLER | "it is important to note that" | medium | 删除填充短语 |
| CHARACTERIZED_BY | "is characterized by" | medium | 用 "X has/includes" 替代 |
| OFFERS_PATHWAY | "offers a novel pathway" | medium | 陈述方法实际做什么 |

#### 抽象动词词库 (ABSTRACT_VERBS)

```
underscore, underscores, underscoring, underscored
highlight, highlights, highlighting, highlighted
exemplify, exemplifies, exemplifying, exemplified
demonstrate, demonstrates, demonstrating, demonstrated
illustrate, illustrates, illustrating, illustrated
showcase, showcases, showcasing, showcased
emphasize, emphasizes, emphasizing, emphasized
signify, signifies, signifying, signified
epitomize, epitomizes, epitomizing, epitomized
encapsulate, encapsulates, encapsulating, encapsulated
embody, embodies, embodying, embodied
```

#### 抽象名词词库 (ABSTRACT_NOUNS)

```
significance, importance, relevance, nuance, nuances
complexity, complexities, intricacy, intricacies
landscape, tapestry, framework, paradigm
dynamic, dynamics, interplay, intersection
trajectory, evolution, transformation, dimension
facet, facets, aspect, aspects
essence, nature, character, fabric
realm, domain, sphere, scope
magnitude, scale, extent, depth
```

#### 输出数据结构

```python
SyntacticVoidResult:
  - void_score: int                      # 空洞分数 0-100
  - matches: List[VoidMatch]             # 匹配列表
  - has_critical_void: bool              # 是否有高严重度空洞
  - void_density: float                  # 每100词的空洞数
  - sentence_count: int                  # 句子数
  - void_sentence_count: int             # 含空洞的句子数
```

---

## 五、未集成模块分析与建议插入位置

### 5.1 模块概览

| 模块 Module | 文件 File | 依赖 Dependency | 当前状态 Status |
|-------------|-----------|-----------------|-----------------|
| 结构预测性评分 | structure_predictability.py | 无 (纯规则) | 代码存在未调用 |
| 学术锚点密度 | anchor_density.py | 无 (纯规则) | 代码存在未调用 |
| 句法空洞检测 | syntactic_void.py | spaCy en_core_web_md | 代码存在未调用 |

### 5.2 结构预测性评分 - 建议插入位置

#### 最佳位置: Level 1 Step 1-1 结构分析

```
建议集成点 Suggested Integration Point:
  文件: src/api/routes/structure.py
  端点: POST /api/v1/structure/analyze-step1
  位置: SmartStructureAnalyzer.analyze_structure() 之后

调用时机 When to Call:
  在智能结构分析完成后，作为补充维度
  After SmartStructureAnalyzer completes, as supplementary dimensions

集成方式 Integration Method:
  1. 在 structure.py 中导入 StructurePredictabilityAnalyzer
  2. 在 analyze_document_structure_step1 函数中调用
  3. 将结果合并到 SmartStructureAnalysis 响应中
```

#### 价值分析

| 维度 | 与现有功能的互补性 |
|-----|-------------------|
| 推进可预测性 | 补充 SmartStructure 的 linear_flow 检测 |
| 功能均匀性 | 新维度，现有功能未覆盖 |
| 闭合强度 | 新维度，检测结论公式化程度 |
| 长度规律性 | 与段落长度CV分析部分重叠，可合并 |
| 连接词显性度 | 补充 ConnectorDetector，增加段落级视角 |
| 词汇回声 | 新维度，检测隐性语义连接 |

#### 建议集成代码

```python
# 在 src/api/routes/structure.py 中添加

from src.core.analyzer.structure_predictability import (
    StructurePredictabilityAnalyzer,
    PredictabilityScore
)

# 在 analyze_document_structure_step1 函数中:
async def analyze_document_structure_step1(...):
    # 现有智能结构分析
    smart_result = await analyzer.analyze_structure(...)

    # 新增: 结构预测性分析
    predictability_analyzer = StructurePredictabilityAnalyzer()
    predictability_result = predictability_analyzer.analyze(paragraphs)

    # 合并结果
    combined_score = (smart_result.structure_score * 0.6 +
                     predictability_result.total_score * 0.4)
```

---

### 5.3 学术锚点密度 - 建议插入位置

#### 最佳位置: Level 1 Step 1-2 段落关系分析

```
建议集成点 Suggested Integration Point:
  文件: src/api/routes/structure.py
  端点: POST /api/v1/structure/analyze-relationships-step2
  位置: 段落关系分析时

调用时机 When to Call:
  在分析段落关系时，为每个段落计算锚点密度
  When analyzing paragraph relationships, calculate anchor density for each

集成方式 Integration Method:
  1. 在 structure.py 中导入 AnchorDensityAnalyzer
  2. 为每个段落计算锚点密度
  3. 标记高风险段落（可能是AI填充物）
  4. 将结果添加到段落关系分析响应中
```

#### 价值分析

| 场景 | 价值 |
|-----|------|
| 长段落无数据 | 识别可能的AI填充段落 |
| 引用分布不均 | 检测引用堆砌 vs 真实论证 |
| 论证空洞 | 提示用户添加具体证据 |

#### 建议集成代码

```python
# 在 src/api/routes/structure.py 中添加

from src.core.analyzer.anchor_density import (
    AnchorDensityAnalyzer,
    AnchorDensityResult
)

# 在 analyze_document_relationships_step2 函数中:
async def analyze_document_relationships_step2(...):
    # 新增: 锚点密度分析
    anchor_analyzer = AnchorDensityAnalyzer()
    anchor_result = anchor_analyzer.analyze_document(paragraphs)

    # 标记高风险段落
    for para_analysis in anchor_result.paragraph_analyses:
        if para_analysis.has_hallucination_risk:
            # 添加到问题列表
            issues.append({
                "type": "low_anchor_density",
                "paragraph_index": para_analysis.paragraph_index,
                "description": f"Low evidence density ({para_analysis.anchor_density:.1f}%)",
                "description_zh": f"证据密度过低 ({para_analysis.anchor_density:.1f}%)",
                "severity": "medium"
            })
```

---

### 5.4 句法空洞检测 - 建议插入位置

#### 最佳位置: Level 3 Step 3 句子精修

```
建议集成点 Suggested Integration Point:
  文件: src/core/analyzer/scorer.py 或 src/api/routes/analyze.py
  端点: POST /api/v1/analyze/
  位置: RiskScorer.analyze() 内部或之后

调用时机 When to Call:
  在句子级风险评分时，作为额外检测维度
  During sentence-level risk scoring, as additional detection dimension

集成方式 Integration Method:
  1. 在 scorer.py 中导入 SyntacticVoidDetector
  2. 在 analyze() 方法中调用空洞检测
  3. 将空洞分数加入总风险分
  4. 将匹配的空洞模式添加到 issues 列表
```

#### 价值分析

| 场景 | 价值 |
|-----|------|
| 华丽但空洞的句子 | 检测 "underscores the significance" 类模式 |
| 指纹词之外的AI特征 | 补充指纹词检测的盲区 |
| 依存句法分析 | 比纯正则更准确地检测复杂模式 |

#### 建议集成代码

```python
# 在 src/core/analyzer/scorer.py 中添加

from src.core.analyzer.syntactic_void import (
    SyntacticVoidDetector,
    SyntacticVoidResult,
    VoidPatternType
)

class RiskScorer:
    def __init__(self):
        # 现有初始化
        self.fingerprint_detector = FingerprintDetector()
        self.burstiness_analyzer = BurstinessAnalyzer()
        self.connector_detector = ConnectorDetector()
        # 新增
        self.void_detector = SyntacticVoidDetector(use_spacy=True)

    def analyze(self, text, ...):
        # 现有分析
        fingerprints = self.fingerprint_detector.detect(text)
        burstiness = self.burstiness_analyzer.analyze(text)

        # 新增: 句法空洞检测
        void_result = self.void_detector.detect(text)

        # 将空洞分数加入总分
        # Add void score contribution (0-15 points)
        void_contribution = min(15, void_result.void_score // 7)

        total_score = (context_baseline + fingerprint_score +
                      structure_score + ppl_contribution +
                      void_contribution - human_deduction)

        # 将空洞匹配添加到 issues
        for vm in void_result.matches:
            issues.append(IssueDetail(
                type="syntactic_void",
                description=f"Empty pattern: {vm.matched_text}",
                description_zh=f"空洞表达: {vm.matched_text}",
                severity=vm.severity,
                position=vm.position,
                word=vm.matched_text
            ))
```

---

### 5.5 集成优先级建议

| 优先级 | 模块 | 原因 |
|--------|------|------|
| **P1 (高)** | 句法空洞检测 | 直接补充Level 3检测盲区，价值最高 |
| **P2 (中)** | 学术锚点密度 | 识别AI填充段落，用户反馈价值高 |
| **P3 (低)** | 结构预测性评分 | 与现有功能部分重叠，可渐进集成 |

---

## 六、双轨建议系统

### 6.1 轨道A: LLM智能建议 (Track A: LLM Suggestions)

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/suggester/llm_track.py` |
| **API端点** | `POST /api/v1/suggest/` |
| **模型依赖** | Claude / GPT / DashScope |

#### 18点改写技术

| 序号 | 技术 Technique | 说明 Description |
|------|----------------|------------------|
| 1 | 指纹词替换 | A/B/C三类分级替换 |
| 2 | 句式重构 | 拆分长句/合并短句 |
| 3 | 语态转换 | 主动↔被动 |
| 4 | 从句移位 | 后置从句移到句首 |
| 5 | 插入语添加 | 增加 "in fact", "arguably" |
| 6 | 主语多样化 | 避免 The X... The X... |
| 7 | 连接方式调整 | 显性→隐性 |
| 8 | 人类特征注入 | 第一人称、不完整句 |
| 9 | 口语化等级调整 | 按0-10等级选择词汇 |
| 10 | 学术hedging | "may suggest", "appears to" |
| 11 | 具体化替换 | 抽象→具体表达 |
| 12 | 节奏变化 | 长短句交替 |
| 13 | 语义回声 | 引用上文关键词 |
| 14 | 逻辑设问 | 用问题引导 |
| 15 | 批判性补充 | 添加limitation提及 |
| 16 | 数据锚点强化 | 补充具体数据 |
| 17 | 引用重组 | 调整引用位置 |
| 18 | 转折添加 | 打破线性流动 |

### 6.2 轨道B: 规则建议 (Track B: Rule Suggestions)

| 属性 | 值 |
|-----|-----|
| **文件位置** | `src/core/suggester/rule_track.py` |
| **API端点** | `POST /api/v1/suggest/` |
| **模型依赖** | BERT MLM (可选) |

#### 技术手段

| 技术 | 说明 |
|------|------|
| 同义词替换 | 基于规则库的确定性替换 |
| BERT MLM | 上下文感知的词汇选择 |
| 语态转换 | 被动↔主动规则转换 |
| 短语简化 | 冗长短语→简洁表达 |

### 6.3 验证机制

| 验证层 | 检查内容 | 阈值 |
|--------|---------|------|
| 语义层 | Sentence-BERT相似度 | ≥ 0.80 |
| 事实层 | 关键实体保留检查 | 100% |
| 术语层 | 锁定术语完整性 | 100% |
| 风险层 | 改写后风险评分 | 低于原分数 |

---

## 七、模块依赖关系

### 7.1 模型依赖汇总

| 模块 Module | 模型 Model | 用途 Purpose | 必需 Required |
|-------------|------------|--------------|---------------|
| PPL Calculator | ONNX distilgpt2 | 真实困惑度计算 | 可选 (有zlib备用) |
| Syntactic Void | spaCy en_core_web_md | 依存句法分析 | 可选 (有正则备用) |
| LLM Track | Claude/GPT/DashScope | 智能改写 | 是 |
| Rule Track | BERT MLM | 上下文感知替换 | 可选 |
| Semantic Validator | Sentence-BERT | 语义相似度 | 是 |

### 7.2 模块调用关系图

```
analyze_text (API)
    ├── SentenceSegmenter.segment()
    ├── TermLocker.identify_terms()
    ├── FingerprintDetector.detect()
    └── RiskScorer.analyze()
            ├── FingerprintDetector.detect_with_context_immunity()
            ├── BurstinessAnalyzer.analyze()
            ├── ConnectorDetector.analyze_single_sentence()
            ├── calculate_onnx_ppl()
            └── [待集成] SyntacticVoidDetector.detect()

analyze_structure (API)
    ├── SmartStructureAnalyzer.analyze_structure()
    │       └── LLM API call
    ├── analyze_paragraph_length_distribution()
    ├── [待集成] StructurePredictabilityAnalyzer.analyze()
    └── [待集成] AnchorDensityAnalyzer.analyze_document()

analyze_transition (API)
    └── TransitionAnalyzer.analyze()
            └── LLM API call (for suggestions)

analyze_paragraph (API)
    └── ParagraphLogicAnalyzer.analyze()
            └── LLM API call (for sentence roles)
```

---

## 八、集成状态汇总

### 8.1 已集成模块 (Integrated Modules) ✅

| 层级 | 模块 | 文件 | API端点 |
|------|------|------|--------|
| L1 | 智能结构分析 | smart_structure.py | /structure/analyze-step1 |
| L1 | 段落长度分析 | smart_structure.py | /structure/paragraph-length/analyze |
| L1 | 段落关系分析 | smart_structure.py | /structure/analyze-relationships-step2 |
| L2 | 段落衔接分析 | transition.py | /transition/analyze |
| L2 | 段落逻辑分析 | paragraph_logic.py | /paragraph/analyze |
| L2 | 句子角色检测 | paragraph_logic.py | /paragraph/analyze-logic-framework |
| L3 | CAASS评分 | scorer.py | /analyze |
| L3 | 指纹词检测 | fingerprint.py | /analyze |
| L3 | PPL计算 | ppl_calculator.py | /analyze |
| L3 | 突发性分析 | burstiness.py | /analyze |
| L3 | 连接词检测 | connector_detector.py | /analyze |

### 8.2 未集成模块 (Not Integrated) ⚠️

| 层级 | 模块 | 文件 | 建议集成点 | 优先级 |
|------|------|------|-----------|--------|
| L1 | 结构预测性评分 | structure_predictability.py | /structure/analyze-step1 | P3 |
| L1 | 学术锚点密度 | anchor_density.py | /structure/analyze-relationships-step2 | P2 |
| L3 | 句法空洞检测 | syntactic_void.py | /analyze | P1 |

### 8.3 功能重叠分析

| 重叠点 | 涉及模块 | 建议处理 |
|--------|---------|---------|
| 指纹词检测 | scorer.py + fingerprint.py | 保持现状，scorer调用fingerprint |
| CV计算 | smart_structure.py + structure_predictability.py | 可合并，使用统一方法 |
| 连接词密度 | connector_detector.py + paragraph_logic.py + structure_predictability.py | 统一到connector_detector |
| 段落长度均匀性 | smart_structure.py (CV) + structure_predictability.py (length_regularity) | 考虑合并 |

---

## 附录 A: API端点速查表

| 端点 Endpoint | 方法 | 功能 Function |
|---------------|------|---------------|
| `/api/v1/analyze/` | POST | 句子级AIGC分析 |
| `/api/v1/structure/analyze-step1` | POST | Level 1 结构分析 |
| `/api/v1/structure/analyze-relationships-step2` | POST | Level 1 段落关系 |
| `/api/v1/structure/paragraph-length/analyze` | POST | 段落长度分析 |
| `/api/v1/structure/paragraph-length/apply` | POST | 应用段落策略 |
| `/api/v1/transition/analyze` | POST | Level 2 衔接分析 |
| `/api/v1/paragraph/analyze` | POST | 段落逻辑分析 |
| `/api/v1/paragraph/analyze-logic-framework` | POST | 句子角色分析 |
| `/api/v1/paragraph/restructure` | POST | 段落重构 |
| `/api/v1/suggest/` | POST | 双轨建议生成 |

---

## 附录 B: 关键文件路径速查表

| 功能 Function | 文件路径 File Path |
|---------------|-------------------|
| 指纹词检测 | `src/core/analyzer/fingerprint.py` |
| PPL计算 | `src/core/analyzer/ppl_calculator.py` |
| 突发性分析 | `src/core/analyzer/burstiness.py` |
| 连接词检测 | `src/core/analyzer/connector_detector.py` |
| 综合评分 | `src/core/analyzer/scorer.py` |
| 智能结构分析 | `src/core/analyzer/smart_structure.py` |
| 结构预测性 | `src/core/analyzer/structure_predictability.py` |
| 锚点密度 | `src/core/analyzer/anchor_density.py` |
| 句法空洞 | `src/core/analyzer/syntactic_void.py` |
| 衔接分析 | `src/core/analyzer/transition.py` |
| 段落逻辑 | `src/core/analyzer/paragraph_logic.py` |
| LLM轨道 | `src/core/suggester/llm_track.py` |
| 规则轨道 | `src/core/suggester/rule_track.py` |
| 分析API | `src/api/routes/analyze.py` |
| 结构API | `src/api/routes/structure.py` |
| 衔接API | `src/api/routes/transition.py` |
| 段落API | `src/api/routes/paragraph.py` |
| 建议API | `src/api/routes/suggest.py` |

---

> 文档维护 Document Maintenance:
> 本文档为检测逻辑唯一技术文档，所有检测相关变更需同步更新此文件。
> This is the sole detection logic documentation. All detection-related changes must be synced here.
