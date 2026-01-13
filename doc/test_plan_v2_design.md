# AcademicGuard Substep 详细测试方案 V2
# AcademicGuard Substep Detailed Test Plan V2

> 设计日期: 2026-01-12
> 基于: doc/test_plan.md 的要求

---

## 一、测试目标 / Test Objectives

按照 `test_plan.md` 的要求，对每个substep进行完整的功能测试，包括：
1. 记录完整的输入/输出/提示词
2. 验证前后端一致性
3. 测试AI修改功能并对比效果
4. 分析功能是否达到预期目标

---

## 二、测试文件结构 / Test File Structure

```
test-YYYY-MM-DD-HHMM/
├── 00_test_input.txt              # 原始测试文本副本
├── 00_test_summary.md             # 测试总结报告
│
├── layer5_step1_0/                # 每个substep单独文件夹
│   ├── record.md                  # 详细记录文档
│   ├── input.txt                  # 本步骤输入文本
│   ├── output.txt                 # 本步骤输出文本(如有修改)
│   ├── api_calls.md               # API调用记录
│   ├── prompts.md                 # AI提示词记录
│   ├── analysis_result.json       # 分析结果原始数据
│   ├── screenshots/               # 截图文件夹
│   │   ├── 01_initial.png
│   │   ├── 02_analysis_result.png
│   │   ├── 03_issue_selection.png
│   │   ├── 04_ai_modification.png
│   │   └── 05_final_result.png
│   └── report.md                  # 本步骤测试报告
│
├── layer5_step1_1/
│   └── ...
│
└── final_analysis/                # 最终分析
    ├── functionality_analysis.md  # 功能分析(重叠/缺失/偏差)
    ├── effectiveness_analysis.md  # 效果分析(是否降低AIGC特征)
    └── recommendations.md         # 优化建议
```

---

## 三、每个Substep的测试流程 / Test Flow for Each Substep

### Phase 1: 准备阶段 / Preparation
1. 记录本步骤的输入文本
2. 如果是第一个步骤，输入为原始测试文本
3. 如果不是第一个步骤，验证输入是否为上一步骤的输出

### Phase 2: 分析阶段 / Analysis Phase
1. **触发分析**
   - 截图: 初始页面状态
   - 记录: 前端发送的API请求(URL, Method, Body)

2. **捕获后端处理**
   - 记录: 后端代码位置(文件:行号)
   - 记录: 规则分析逻辑(如有)
   - 记录: LLM调用的提示词(从handler文件获取)
   - 记录: 链式调用(如有多个API)

3. **记录分析结果**
   - 截图: 分析结果页面
   - 保存: 原始JSON响应
   - 记录: 检测到的问题列表
   - 记录: 风险分数和各项指标
   - 验证: 前端显示是否与后端返回一致

### Phase 3: 修改阶段 / Modification Phase
1. **问题选择**
   - 截图: 问题列表
   - 操作: 选择多个问题(测试多选功能)
   - 记录: 选择了哪些问题

2. **触发AI修改**
   - 记录: 发送给AI的合并提示词
   - 截图: 等待AI响应
   - 记录: AI返回的修改建议/文本

3. **采纳修改**
   - 操作: 选择采纳AI的修改
   - 记录: 修改后的文本
   - 截图: 采纳后的页面状态

### Phase 4: 效果评估 / Effect Evaluation
1. **指标对比**
   - 记录: 修改前的评分(CV, 风险分数等)
   - 记录: 修改后的评分
   - 分析: 评分是否改善

2. **文本对比**
   - 对比: 输入文本 vs 输出文本
   - 分析: AI是否解决了检测到的问题
   - 评估: 修改是否降低了AIGC特征

3. **数据验证**
   - 验证: 段落数、句子数、词数是否准确
   - 验证: 计算逻辑是否正确

### Phase 5: 生成报告 / Generate Report
1. 生成本步骤的详细记录文档(record.md)
2. 生成本步骤的测试报告(report.md)

---

## 四、记录文档模板 / Record Document Template

### record.md 模板

```markdown
# [Step X.X] [步骤名称] 详细记录

## 1. 基本信息
- 步骤: Layer X - Step X.X
- 功能: [功能描述]
- 测试时间: YYYY-MM-DD HH:MM

## 2. 输入
### 2.1 输入文本
\`\`\`
[完整输入文本或摘要+字数]
\`\`\`
### 2.2 输入来源
- [ ] 原始测试文本
- [ ] 上一步骤输出 (Step X.X)
- 验证结果: [是否与上一步输出一致]

## 3. API调用记录
### 3.1 前端请求
- URL: /api/v1/xxx
- Method: POST
- Body: {...}

### 3.2 后端处理
- 文件位置: src/api/routes/xxx.py:行号
- 规则分析: [描述规则逻辑]
- LLM调用: [是/否]

### 3.3 链式调用(如有)
| 序号 | API | 输入 | 输出 |
|-----|-----|-----|-----|
| 1 | /api/v1/xxx | {...} | {...} |
| 2 | /api/v1/yyy | {...} | {...} |

## 4. AI提示词
### 4.1 分析阶段提示词
\`\`\`
[从handler文件提取的prompt]
\`\`\`

### 4.2 修改阶段提示词
\`\`\`
[发送给AI的合并修改提示词]
\`\`\`

## 5. 分析结果
### 5.1 风险评估
- 风险分数: XX/100
- 风险等级: HIGH/MEDIUM/LOW

### 5.2 检测到的问题
| # | 严重程度 | 范围 | 问题描述 |
|---|---------|------|---------|
| 1 | HIGH | paragraph | xxx |
| 2 | MEDIUM | sentence | xxx |

### 5.3 指标数据
| 指标 | 值 | 阈值 | 状态 |
|-----|---|-----|-----|
| CV | 0.15 | ≥0.35 | 异常 |
| 简单句比例 | 60% | <50% | 异常 |

### 5.4 前后端一致性验证
- [ ] 问题数量一致
- [ ] 风险分数一致
- [ ] 指标数据一致
- 差异说明: [如有]

## 6. 问题选择与AI修改
### 6.1 选择的问题
- [x] 问题1: xxx
- [x] 问题3: xxx
- [ ] 问题2: xxx (未选择)

### 6.2 AI修改结果
\`\`\`
[AI返回的修改文本]
\`\`\`

### 6.3 采纳决策
- 采纳: [是/否]
- 理由: [说明]

## 7. 输出
### 7.1 输出文本
\`\`\`
[修改后的完整文本或摘要]
\`\`\`

### 7.2 修改前后对比
| 指标 | 修改前 | 修改后 | 变化 |
|-----|-------|-------|-----|
| 风险分数 | 85 | 72 | -13 |
| CV | 0.15 | 0.28 | +0.13 |

## 8. 效果评估
### 8.1 问题解决情况
| 问题 | 是否解决 | 说明 |
|-----|---------|-----|
| 句首重复 | ✅ 是 | 从43%降到25% |
| 简单句过多 | ❌ 否 | 仍为58% |

### 8.2 AIGC特征变化
- 降低的特征: [列举]
- 未改善的特征: [列举]
- 新引入的问题: [如有]

### 8.3 人类写作水平评估
- 评分: [1-10]
- 说明: [评估理由]

## 9. 数据验证
### 9.1 数量验证
| 数据项 | 系统值 | 手动验证 | 是否准确 |
|-------|-------|---------|---------|
| 段落数 | 10 | 10 | ✅ |
| 句子数 | 31 | 31 | ✅ |
| 词数 | 621 | 620 | ⚠️ 差1 |

### 9.2 计算验证
- CV计算: [验证公式是否正确]
- 比例计算: [验证百分比是否正确]

## 10. 截图列表
1. 01_initial.png - 初始页面
2. 02_analysis_result.png - 分析结果
3. 03_issue_selection.png - 问题选择
4. 04_ai_modification.png - AI修改
5. 05_final_result.png - 最终结果
```

---

## 五、测试步骤详细安排 / Detailed Test Steps

### Layer 5 (Document Level)
| Step | 名称 | 测试重点 |
|------|-----|---------|
| 1.0 | Term Lock | 术语提取准确性、锁定功能 |
| 1.1 | Structure | 结构识别、模板检测 |
| 1.2 | Uniformity | CV计算验证、长度分析 |
| 1.3 | Logic Pattern | 预测性分数计算 |
| 1.4 | Connector | 连接词检测、平滑度计算 |
| 1.5 | Substantiality | 实质性评分、具体性分析 |

### Layer 4 (Section Level)
| Step | 名称 | 测试重点 |
|------|-----|---------|
| 2.0 | Section ID | 章节识别准确性 |
| 2.1 | Section Order | 顺序逻辑验证 |
| 2.2 | Length Distribution | 长度分布CV验证 |
| 2.3 | Internal Structure | 内部结构相似度 |
| 2.4 | Transitions | 过渡词检测 |
| 2.5 | Logic Flow | 逻辑流分析 |

### Layer 3 (Paragraph Level)
| Step | 名称 | 测试重点 |
|------|-----|---------|
| 3.0 | Para ID | 段落识别与过滤 |
| 3.1 | Role Detection | 角色识别准确性 |
| 3.2 | Coherence | 连贯性指标验证 |
| 3.3 | Anchor Density | 锚点计数验证 |
| 3.4 | Sentence Length | 句长CV计算 |
| 3.5 | Transitions | 段落过渡分析 |

### Layer 2 (Sentence Level)
| Step | 名称 | 测试重点 |
|------|-----|---------|
| 4.0 | Sentence ID | 句子识别与分类 |
| 4.1 | Pattern Analysis | 模式分析、句法空洞 |
| 4.2-4.5 | Processing | AI修改效果重点测试 |

### Layer 1 (Lexical Level)
| Step | 名称 | 测试重点 |
|------|-----|---------|
| 5.0-5.5 | Lexical Analysis | (需先修复API路径bug) |

---

## 六、最终分析内容 / Final Analysis Content

### 6.1 功能分析 (functionality_analysis.md)
- 每个substep是否实现了预设功能
- 功能是否有重叠(多个步骤做类似的事)
- 功能是否有缺失(应该有但没有)
- 功能是否有偏差(做了但效果不对)

### 6.2 效果分析 (effectiveness_analysis.md)
- 整体AIGC特征降低情况
- 人类写作特征增加情况
- 一次处理是否能达到目标
- 需要多次迭代的步骤

### 6.3 优化建议 (recommendations.md)
- 提示词优化建议
- 功能调整建议
- 流程优化建议
- 优先级排序

---

## 七、执行计划 / Execution Plan

### 阶段1: 环境准备
1. 创建新的测试文件夹
2. 复制测试文本
3. 准备API监控工具

### 阶段2: 逐步测试
1. 从Layer 5 Step 1.0开始
2. 每个步骤完整执行Phase 1-5
3. 生成记录和报告
4. 验证输出作为下一步输入

### 阶段3: 汇总分析
1. 汇总所有步骤报告
2. 进行功能分析
3. 进行效果分析
4. 提出优化建议

---

## 八、关键差异点 / Key Differences from V1

| 方面 | V1测试 | V2测试 |
|-----|-------|-------|
| 记录深度 | 只记录结果 | 完整记录输入/输出/提示词 |
| API追踪 | 无 | 完整记录API调用链 |
| 修改测试 | 全部跳过 | 完整测试选择+修改+采纳 |
| 效果对比 | 无 | 修改前后指标对比 |
| 数据验证 | 无 | 手动验证数据准确性 |
| 链式验证 | 无 | 验证输入=上步输出 |
| 功能分析 | 无 | 分析重叠/缺失/偏差 |

---

## 九、预计产出 / Expected Deliverables

1. **20+ 个substep详细记录文档** (record.md)
2. **20+ 个substep测试报告** (report.md)
3. **100+ 张测试截图**
4. **原始API响应数据** (JSON)
5. **功能分析报告**
6. **效果分析报告**
7. **优化建议报告**
8. **综合测试报告**

---

*方案设计完成，等待确认后执行*
