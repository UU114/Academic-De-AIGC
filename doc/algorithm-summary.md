# AcademicGuard 算法逻辑总结
# AcademicGuard Algorithm Logic Summary

> 版本 Version: v1.0
> 最后更新 Last Updated: 2025-12-31

---

## 一、AI评分逻辑 | AI Risk Scoring Logic

### 1.1 总体评分公式 | Overall Scoring Formula

```
总分 = (PPL分数 × 权重) + (指纹分数 × 权重) + (突发性分数 × 权重) + (结构分数 × 权重) - 人类特征减分

Total Score = (PPL_Score × Weight) + (Fingerprint_Score × Weight) + (Burstiness_Score × Weight) + (Structure_Score × Weight) - Human_Deduction
```

**默认权重配置 Default Weights:**
| 维度 Dimension | 权重 Weight |
|----------------|-------------|
| 困惑度 Perplexity (PPL) | 0.35 |
| 指纹词密度 Fingerprint | 0.30 |
| 突发性 Burstiness | 0.20 |
| 结构模式 Structure | 0.15 |

### 1.2 风险等级判定 | Risk Level Thresholds

| 分数范围 Score Range | 风险等级 Risk Level | 说明 Description |
|---------------------|---------------------|------------------|
| ≥ 50 | 高风险 High | 很可能是AI生成 |
| 25 - 49 | 中风险 Medium | 有AI特征，需注意 |
| 10 - 24 | 低风险 Low | 轻微AI特征 |
| < 10 | 安全 Safe | 人类写作风格 |

---

## 二、四维度评分详解 | Four-Dimension Scoring Details

### 2.1 困惑度 (PPL) | Perplexity

**原理 Principle:**
- AI生成的文本信息密度低、模式重复，压缩率高
- 人类写作词汇更独特，压缩率较低
- AI text has lower information density and more repetitive patterns
- Human writing has more unique vocabulary and lower compression

**计算方法 Calculation Method:**
使用 zlib 压缩比作为 PPL 代理：
```python
compression_ratio = len(compressed_bytes) / len(original_bytes)

# 转换为PPL分数
if compression_ratio < 0.35:    # 高压缩率 = AI可能性高
    ppl = 15.0 + (ratio * 30)    → 高风险
elif compression_ratio < 0.50:   # 中高压缩率
    ppl = 25.0 + (ratio * 40)    → 中风险
elif compression_ratio < 0.65:   # 中等压缩率
    ppl = 45.0 + (ratio * 30)    → 不确定
else:                            # 低压缩率 = 人类可能性高
    ppl = 60.0 + (ratio * 40)    → 低风险
```

**PPL风险阈值 PPL Risk Thresholds:**
| PPL值 PPL Value | 风险 Risk |
|-----------------|-----------|
| < 25 | 高风险 High |
| 25 - 45 | 中风险 Medium |
| > 45 | 低风险 Low |

---

### 2.2 指纹词检测 | Fingerprint Detection

#### 2.2.1 分级指纹词系统 | Tiered Fingerprint System

**一级词 Level 1 (Dead Giveaways) - 每个 +40 分，上限 120 分:**

人类写作中极少使用，是AI的"确凿证据"：

```
delve, delves, delving          探究（AI最爱用词）
tapestry, tapestries            织锦/图案（过度文学化）
testament to                    证明了
in the realm of, realm of       在...领域（装腔作势）
landscape of                    ...的图景
multifaceted                    多方面的
inextricably                    不可分割地
a plethora of, plethora         大量的
myriad of                       无数的
elucidate, elucidates           阐明
henceforth                      从此以后
aforementioned                  上述的
cascading mechanisms            级联机制
interfacial                     界面的
valorization                    价值化
poses a dual threat             构成双重威胁
systemic understanding          系统性理解
remains fragmented              仍然碎片化
critically synthesizes          批判性综合
concurrent escalation           同步升级
```

**二级词 Level 2 (AI Habitual) - 每个 +15 分，上限 60 分:**

AI常用但人类也可能使用：

```
crucial, pivotal, paramount     关键的/至关重要的
underscore, underscores         强调
foster, fosters                 培养/促进
furthermore, moreover           此外
additionally, consequently      另外/因此
comprehensive, holistic         全面的/整体的
facilitate, facilitates         促进
leverage, leveraging            利用
robust, seamless                稳健的/无缝的
noteworthy, groundbreaking      值得注意的/开创性的
synergistic, synergy            协同的/协同效应
mechanisms, dynamics            机制/动态
```

#### 2.2.2 指纹短语检测 | Fingerprint Phrases

高权重短语 (0.8-1.0):
```
"it is important to note that"     → 权重 0.9
"plays a crucial/pivotal role"     → 权重 0.8-0.9
"a plethora of"                    → 权重 0.9
"is of paramount importance"       → 权重 0.9
```

中权重短语 (0.5-0.7):
```
"in the context of"                → 权重 0.6
"due to the fact that"             → 权重 0.7
"has the potential to"             → 权重 0.5
"a wide range of"                  → 权重 0.5
```

#### 2.2.3 过度使用连接词 | Overused Connectors

```
however, therefore               → 权重 0.3
moreover, furthermore            → 权重 0.4
additionally, consequently       → 权重 0.4
hence, henceforth               → 权重 0.4-0.7
whereby, wherein                → 权重 0.6
```

---

### 2.3 突发性分析 | Burstiness Analysis

**原理 Principle:**
- AI生成的文本句子长度均匀，变化小
- 人类写作句子长度参差不齐，变化大
- AI generates uniformly-lengthed sentences
- Human writing has varied sentence lengths

**计算方法 Calculation:**
```python
burstiness = std(sentence_lengths) / mean(sentence_lengths)

# 评分
if burstiness < 0.2:
    score = 80  # 非常均匀 = 高风险
elif burstiness < 0.4:
    score = 50  # 中等变化 = 中风险
else:
    score = 20  # 变化大 = 低风险（人类特征）
```

---

### 2.4 结构模式分析 | Structure Pattern Analysis

**检测的AI结构模式 Detected AI Patterns:**

| 模式 Pattern | 加分 Points |
|--------------|-------------|
| 一级指纹词命中 | +40/个，上限120 |
| 二级指纹词命中 | +15/个，上限60 |
| "not only... but also" 双重强调 | +20 |
| firstly/secondly/thirdly 列举 | +25 |
| 句子 > 40 词 | +25 |
| 句子 > 30 词 | +15 |
| 句首连接词 (Furthermore/Moreover...) | +20 |
| 空洞学术填充短语 | +15/个 |
| 超长句 (>25词) + 多逗号 (≥3) | +20 |
| AI被动结构 ("it is important to note that") | +20 |

**空洞学术填充短语 AI Academic Padding:**
```
"complex dynamics"          复杂动态
"intricate interplay"       复杂相互作用
"evolving landscape"        演变格局
"holistic approach"         整体方法
"nuanced understanding"     细致入微的理解
"multifaceted nature"       多方面性质
"cascading effects"         级联效应
"systemic approach"         系统方法
```

---

### 2.5 人类特征减分 | Human Feature Deduction

**识别人类写作标记，降低AI嫌疑：**

| 人类特征 Human Feature | 减分 Deduction |
|-----------------------|----------------|
| 带情感第一人称 ("I was surprised", "I believe") | -20 |
| 非正式括号补充 ("which was weird", "to be fair") | -15 |
| 具体非整数数字 (14.2%, p < 0.05) | -10 |
| 口语化表达 ("kind of", "honestly", "pretty much") | -10 |
| 反问句 | -10 |
| 极短句子 (< 8 词) | -5 |

**减分上限 Deduction Cap:** 50分

---

## 三、降低AIGC逻辑 | De-AIGC Logic

系统提供两个轨道来降低AIGC风险：

### 3.1 轨道A：LLM智能改写 | Track A: LLM-Powered Rewriting

使用 Claude/GPT-4/DeepSeek 进行智能改写。

**LLM Prompt 核心策略 Core Strategies:**

#### 策略1：消除AI指纹词 (高优先级)
```
delve → explore/examine
crucial/paramount/pivotal → important/key
utilize → use
facilitate → help/enable
comprehensive → full/complete
multifaceted → complex
subsequently → then/after
realm → area/field
tapestry → mix
```

#### 策略2：打破AI句式模板
```
"Not only X but also Y" → "X. Also, Y." 或 "Beyond X, Y."
"It is crucial/important to" → "We must" 或 "The X requires"
"serves as a" → "acts as" 或 "is" 或 "forms"
"In conclusion/summary" → "Ultimately" 或 "Findings suggest"
```

#### 策略3：移除连接词堆砌
```
避免句首：Furthermore, Moreover, Additionally, Consequently, Therefore, Thus, Notably, Importantly

替代方案：使用语义流 (This X..., Such Y..., The result...)
```

#### 策略4：添加人类写作标记
```
- 变化句子长度（混合短句 + 长解释句）
- 使用具体数字 ("35% increase" 而非 "significant increase")
- 主动语态 ("We found" 而非 "It was found")
- 适度hedging ("appears to", "suggests") 或确信 ("clearly shows")
```

#### 策略5：删除模糊学术填充
```
删除：complex dynamics, intricate interplay, evolving landscape, holistic approach
替换为：具体描述实际发生了什么
```

**口语化等级风格指南 Colloquialism Level Styles:**

| 等级 Level | 风格 Style | 特点 Features |
|------------|-----------|---------------|
| 0-2 | 期刊论文级 | 正式学术词汇，被动语态，无缩写 |
| 3-4 | 学位论文级 | 正式但可用第一人称复数 |
| 5-6 | 会议论文级 | 混合词汇，偶尔缩写，主动语态 |
| 7-8 | 技术博客级 | 常用词优先，鼓励缩写，简短句 |
| 9-10 | 口语讨论级 | 日常对话语言，非正式表达 |

---

### 3.2 轨道B：规则替换 | Track B: Rule-Based Replacement

确定性的词汇和短语替换，成本低、速度快。

#### 3.2.1 指纹词替换表 | Fingerprint Word Replacements

**一级词替换 Level 1 Replacements:**

| 原词 Original | 学术替换 Academic | 适中替换 Moderate | 口语替换 Casual |
|--------------|-------------------|-------------------|-----------------|
| delve | explore, examine | explore, look at | look at, check out |
| tapestry | collection, array | mix, collection | mix, bunch |
| multifaceted | complex, diverse | complex, varied | complex, mixed |
| plethora | abundance, numerous | many, lots of | lots of, a bunch of |
| elucidate | clarify, explain | explain, clarify | explain, show |
| aforementioned | previously mentioned | mentioned, these | these, this |

**二级词替换 Level 2 Replacements:**

| 原词 Original | 学术替换 Academic | 适中替换 Moderate | 口语替换 Casual |
|--------------|-------------------|-------------------|-----------------|
| crucial | essential, critical | important, key | important, big |
| furthermore | additionally, also | also, and | also, plus |
| comprehensive | thorough, extensive | full, complete | full, detailed |
| facilitate | enable, support | help, enable | help, make easier |
| leverage | employ, harness | use, apply | use |
| robust | strong, resilient | strong, solid | strong, good |

#### 3.2.2 短语替换表 | Phrase Replacements

| 原短语 Original | 学术替换 | 适中替换 | 口语替换 |
|----------------|---------|---------|---------|
| it is important to note that | notably | note that | note that |
| plays a crucial role | is essential | is important | matters a lot |
| in the context of | regarding | in | for |
| a wide range of | various | many | lots of |
| due to the fact that | because | because | since |
| in order to | to | to | to |
| holistic approach | integrated approach | complete approach | full approach |

#### 3.2.3 句法调整 | Syntax Adjustment

当检测到结构问题时，应用句法调整：

**Hedging 添加:**
```
"This shows that..." → "This seems to show that..."
"This is clear..." → "This appears to be clear..."
```

**触发条件:**
- 句子超过 35 词
- 存在 structure/burstiness 类型问题

---

## 四、双检测器视角 | Dual Detector Perspectives

### 4.1 Turnitin 视角

关注点：整体风格、结构、引用模式

| 检测项 Detection | 加分 Points |
|-----------------|-------------|
| 多个AI特征短语 (≥3) | +30 |
| 公式化句子结构 | +25 |
| 复杂但语法完美的结构 (>25词) | +15 |

### 4.2 GPTZero 视角

关注点：困惑度、突发性、词汇选择

| 检测项 Detection | 加分 Points |
|-----------------|-------------|
| PPL < 20 (非常低) | +40 |
| PPL 20-40 (较低) | +25 |
| 低突发性（句子均匀） | +25 |
| AI偏好词汇 | +20 |

---

## 五、验证机制 | Validation Mechanism

改写后需通过质量门控验证：

| 验证层 Layer | 检查内容 Check | 阈值 Threshold |
|-------------|---------------|----------------|
| 语义层 | Sentence-BERT 相似度 | ≥ 80% |
| 术语层 | 锁定术语完整性 | 100% |
| 风险层 | 改写后风险评分 | 低于原分数 |

**验证失败处理:**
1. 语义相似度 < 80% → 使用规则建议替代
2. 仍然失败 → 标记为"需人工处理"
3. 最多重试 3 次 → 超过则跳过

---

## 六、完整指纹词列表 | Complete Fingerprint Word List

### 6.1 一级指纹词 Level 1 (Dead Giveaways) - +40分/个

人类写作中极少使用，是AI的"确凿证据"：

```
delve, delves, delving              探究（AI最典型标志词）
tapestry, tapestries                织锦/图案（过度文学化修饰）
testament to                        证明了/见证了
in the realm of, realm of           在...领域（装腔作势表达）
landscape of                        ...的图景/格局
multifaceted                        多方面的/多层面的
inextricably                        不可分割地/密不可分地
a plethora of, plethora             大量的/过多的
myriad of, myriad                   无数的/各种各样的
elucidate, elucidates, elucidating  阐明/解释清楚
henceforth                          从此以后/今后
aforementioned                      上述的/前面提到的
cascading mechanisms                级联机制
interfacial                         界面的
valorization                        价值化/增值
poses a dual threat                 构成双重威胁
systemic understanding              系统性理解
remains fragmented                  仍然碎片化
critically synthesizes              批判性综合
concurrent escalation               同步升级/同时恶化
```

**总计：20+ 个一级词**

---

### 6.2 二级指纹词 Level 2 (AI Habitual) - +15分/个

AI常用但人类也可能使用的词汇：

```
# === 重要性/关键性词汇 ===
crucial                 关键的/至关重要的
pivotal                 关键的/核心的
paramount               最重要的/首要的

# === 强调动词 ===
underscore, underscores 强调/突出
foster, fosters         培养/促进
facilitate, facilitates 促进/使便利
leverage, leveraging    利用/借助

# === 连接词/过渡词 ===
furthermore             此外/而且
moreover                此外/再者
additionally            另外/此外
consequently            因此/结果
subsequently            随后/接着

# === 形容词/修饰词 ===
comprehensive           全面的/综合的
holistic                整体的/全面的
robust                  稳健的/强大的
seamless                无缝的/顺畅的
noteworthy              值得注意的
groundbreaking          开创性的/突破性的
optimal                 最佳的/最优的
intricate               复杂的/精细的
nuanced                 微妙的/细致的

# === 学科/领域词汇 ===
synergistic, synergy    协同的/协同效应
mechanisms              机制
dynamics                动态/动力学
life-cycle              生命周期
trade-offs, trade-off   权衡/取舍
circular pathway        循环途径
circular economy        循环经济
ecosystem stability     生态系统稳定性
food security           粮食安全
soil salinization       土壤盐碱化
solid waste             固体废物
integrated amendment    综合改良
amendment systems       改良系统
functional soil         功能性土壤
soil conditioner        土壤调节剂
industrial by-products  工业副产品
agricultural residues   农业残留物
remediation             修复/治理
reclamation             复垦/恢复
```

**总计：40+ 个二级词**

---

### 6.3 高频指纹词完整列表 | High-Frequency Words (权重0.5-1.0)

| 单词 Word | 权重 Weight | 推荐替换 Replacements |
|-----------|-------------|----------------------|
| delve | 1.0 | explore, examine, investigate, look at |
| delves | 1.0 | explores, examines, investigates |
| tapestry | 0.9 | mix, combination, blend |
| paramount | 0.9 | important, key, main, central |
| crucial | 0.8 | important, key, essential, critical |
| aforementioned | 0.8 | these, this, the above |
| multifaceted | 0.8 | complex, varied, diverse |
| plethora | 0.8 | many, lots of, numerous |
| elucidate | 0.8 | explain, clarify, describe |
| realm | 0.7 | area, field, domain |
| subsequently | 0.7 | then, later, after that |
| utilize | 0.7 | use, apply, employ |
| facilitate | 0.7 | help, enable, support, allow |
| pivotal | 0.7 | key, central, important |
| myriad | 0.7 | many, numerous, various |
| endeavor | 0.7 | try, attempt, effort |
| commence | 0.7 | start, begin, initiate |
| groundbreaking | 0.7 | innovative, pioneering, new |
| leverage | 0.6 | use, apply, exploit |
| seamless | 0.6 | smooth, easy, simple |
| intricate | 0.6 | complex, detailed, elaborate |
| nuanced | 0.6 | subtle, detailed, complex |
| embark | 0.6 | start, begin, set out |
| underscore | 0.6 | highlight, emphasize, stress |
| pertaining | 0.6 | about, related to, concerning |
| noteworthy | 0.6 | notable, important, significant |
| comprehensive | 0.6 | full, complete, thorough |
| robust | 0.5 | strong, solid, reliable |
| foster | 0.5 | encourage, promote, support |
| optimal | 0.5 | best, ideal, most effective |

---

### 6.4 连接词完整列表 | Connector Words (权重0.3-0.6)

| 连接词 Connector | 权重 Weight | 推荐替换 Replacements |
|-----------------|-------------|----------------------|
| whereby | 0.6 | where, by which |
| wherein | 0.6 | where, in which |
| henceforth | 0.7 | from now on, from this point |
| hence | 0.4 | so, therefore, thus |
| moreover | 0.4 | also, besides, furthermore |
| furthermore | 0.4 | also, besides, in addition |
| additionally | 0.4 | also, besides, plus |
| consequently | 0.4 | so, as a result, thus |
| nevertheless | 0.4 | but, still, yet |
| nonetheless | 0.4 | but, still, yet |
| however | 0.3 | but, yet, still |
| therefore | 0.3 | so, thus, hence |
| thus | 0.3 | so, therefore |

---

### 6.5 指纹短语完整列表 | Fingerprint Phrases (权重0.3-0.9)

| 短语 Phrase | 权重 Weight | 推荐替换 Replacement |
|-------------|-------------|---------------------|
| **高权重 (0.8-0.9)** | | |
| it is important to note that | 0.9 | note that |
| plays a pivotal role | 0.9 | is key |
| a plethora of | 0.9 | many |
| is of paramount importance | 0.9 | is very important |
| it is worth noting that | 0.8 | notably |
| it should be noted that | 0.8 | note that |
| plays a crucial role | 0.8 | is important |
| in the realm of | 0.8 | in |
| a myriad of | 0.8 | many |
| **中权重 (0.5-0.7)** | | |
| due to the fact that | 0.7 | because |
| it is evident that | 0.7 | clearly |
| the advent of | 0.6 | the arrival of |
| in the context of | 0.6 | in |
| with respect to | 0.5 | about |
| a wide range of | 0.5 | many |
| plays an important role | 0.5 | matters |
| it is clear that | 0.5 | clearly |
| serves as a | 0.5 | is a |
| can be seen as | 0.5 | is |
| has the potential to | 0.5 | can |
| **低权重 (0.3-0.4)** | | |
| in order to | 0.4 | to |
| as a result of | 0.4 | because of |
| in terms of | 0.4 | for |
| on the other hand | 0.3 | but |

---

### 6.6 规则轨道扩展短语 | Rule Track Extended Phrases

| 短语类别 Category | 原短语 Original | 学术替换 | 口语替换 |
|------------------|----------------|---------|---------|
| **重要性模式** | it is crucial to | we must | we need to |
| | it is essential to | we must | we need to |
| | plays a significant role | is significant | matters |
| | underscores the importance | shows the significance | shows how important |
| | highlights the importance | shows the significance | shows how important |
| **语境模式** | with regard to | regarding | about |
| | with respect to | regarding | about |
| **数量模式** | a multitude of | numerous | lots of |
| **因果模式** | owing to the fact that | because | since |
| | as a consequence of | because of | because of |
| **目的模式** | with the aim of | to | to |
| | for the purpose of | to | to |
| **结论模式** | in conclusion | to conclude | finally |
| | to summarize | in summary | so |
| | in summary | overall | so |
| **方法模式** | holistic approach | integrated approach | full approach |
| | comprehensive approach | thorough approach | complete approach |
| **关系模式** | testament to | evidence of | shows |
| | landscape of | field of | area of |
| **填充短语** | it can be seen that | clearly | we can see |
| | it goes without saying that | clearly | obviously |
| | needless to say | clearly | obviously |
| | complex dynamics | interactions | how things work |
| | intricate dynamics | interactions | how things work |

---

## 七、核心文件位置 | Core File Locations

| 模块 Module | 文件路径 File Path |
|-------------|-------------------|
| 风险评分器 | `src/core/analyzer/scorer.py` |
| 指纹词检测 | `src/core/analyzer/fingerprint.py` |
| LLM轨道(A) | `src/core/suggester/llm_track.py` |
| 规则轨道(B) | `src/core/suggester/rule_track.py` |
| 语义验证 | `src/core/validator/semantic.py` |
| 质量门控 | `src/core/validator/quality_gate.py` |

---

> 文档维护 | Document Maintenance:
> 本文档总结了系统的核心算法逻辑，如有算法调整需同步更新。
> This document summarizes the core algorithm logic. Update when algorithms change.
