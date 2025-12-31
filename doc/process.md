# AcademicGuard 开发进度
# AcademicGuard Development Progress

> 最后更新 Last Updated: 2025-12-31

---

## 开发阶段概览 | Development Phase Overview

| Phase | 状态 Status | 完成度 Progress |
|-------|-------------|-----------------|
| Phase 1: MVP核心闭环 | 进行中 In Progress | 98% |
| Phase 2: 双轨完善 | 待开始 Pending | 0% |
| Phase 3: 多语言与体验优化 | 待开始 Pending | 0% |
| Phase 4: 测试与部署 | 待开始 Pending | 0% |

---

## Phase 1: MVP核心闭环 | MVP Core Loop

### 2024-12-29 - 初始开发 | Initial Development

#### 完成的功能 | Completed Features

| 功能 Feature | 文件 Files | 状态 Status |
|--------------|-----------|-------------|
| 项目结构创建 | 全部目录 | ✅ 完成 |
| FastAPI后端框架 | `src/main.py`, `src/config.py` | ✅ 完成 |
| 数据库模型 | `src/db/models.py`, `src/db/database.py` | ✅ 完成 |
| API路由框架 | `src/api/routes/*.py` | ✅ 完成 |
| API数据模式 | `src/api/schemas.py` | ✅ 完成 |
| 文本分句模块 | `src/core/preprocessor/segmenter.py` | ✅ 完成 |
| 术语锁定模块 | `src/core/preprocessor/term_locker.py` | ✅ 完成 |
| 指纹词检测 | `src/core/analyzer/fingerprint.py` | ✅ 完成 |
| 风险评分系统 | `src/core/analyzer/scorer.py` | ✅ 完成 |
| LLM建议轨道(A) | `src/core/suggester/llm_track.py` | ✅ 完成 |
| 规则建议轨道(B) | `src/core/suggester/rule_track.py` | ✅ 完成 |
| 语义相似度验证 | `src/core/validator/semantic.py` | ✅ 完成 |
| 质量门控 | `src/core/validator/quality_gate.py` | ✅ 完成 |
| 指纹词数据 | `data/fingerprints/*.json` | ✅ 完成 |
| 术语白名单 | `data/terms/whitelist.json` | ✅ 完成 |

#### 代码摘要 | Code Summary

**核心模块实现：**

1. **SentenceSegmenter** (`preprocessor/segmenter.py`)
   - 支持学术文本的智能分句
   - 处理缩写、引用、小数等特殊情况
   - 支持段落信息保留

2. **TermLocker** (`preprocessor/term_locker.py`)
   - 白名单术语识别
   - 统计模式识别 (p < 0.05, R² = 0.89)
   - 引用保护 ([1], (Smith, 2020))

3. **FingerprintDetector** (`analyzer/fingerprint.py`)
   - 40+ AI高频词检测
   - 20+ AI偏好短语检测
   - 12+ 过度使用连接词检测
   - 密度计算与风险权重

4. **RiskScorer** (`analyzer/scorer.py`)
   - 4维度风险评分 (PPL/指纹/突发性/结构)
   - Turnitin视角分析
   - GPTZero视角分析
   - 综合风险等级判定

5. **LLMTrack** (`suggester/llm_track.py`)
   - Anthropic/OpenAI API支持
   - 5级口语化风格提示词
   - 词汇偏好映射
   - Fallback机制

6. **RuleTrack** (`suggester/rule_track.py`)
   - 指纹词替换 (按等级)
   - 短语替换
   - 句法调整
   - 相似度计算

7. **SemanticValidator** (`validator/semantic.py`)
   - Sentence-BERT支持
   - 备用相似度算法
   - 批量验证

8. **QualityGate** (`validator/quality_gate.py`)
   - 语义层验证
   - 术语层验证
   - 风险层验证
   - 动作决策

#### 待完成 | Pending

| 任务 Task | 优先级 Priority |
|-----------|-----------------|
| ~~前端UI开发~~ | ✅ 完成 |
| 完整API测试 | P1 |
| LLM API集成测试 | P1 |
| 数据库初始化脚本 | P2 |

---

### 2024-12-30 - 前端开发 | Frontend Development

#### 完成的功能 | Completed Features

| 功能 Feature | 文件 Files | 状态 Status |
|--------------|-----------|-------------|
| React + Vite 项目初始化 | `frontend/package.json`, `frontend/vite.config.ts` | ✅ 完成 |
| TailwindCSS 配置 | `frontend/tailwind.config.js`, `frontend/src/index.css` | ✅ 完成 |
| TypeScript 类型定义 | `frontend/src/types/index.ts` | ✅ 完成 |
| API 服务层 | `frontend/src/services/api.ts` | ✅ 完成 |
| 会话状态管理 (Zustand) | `frontend/src/stores/sessionStore.ts` | ✅ 完成 |
| 配置状态管理 | `frontend/src/stores/configStore.ts` | ✅ 完成 |
| 布局组件 | `frontend/src/components/common/Layout.tsx` | ✅ 完成 |
| 按钮组件 | `frontend/src/components/common/Button.tsx` | ✅ 完成 |
| 风险徽章组件 | `frontend/src/components/common/RiskBadge.tsx` | ✅ 完成 |
| 进度条组件 | `frontend/src/components/common/ProgressBar.tsx` | ✅ 完成 |
| 口语化滑块组件 | `frontend/src/components/settings/ColloquialismSlider.tsx` | ✅ 完成 |
| 句子卡片组件 | `frontend/src/components/editor/SentenceCard.tsx` | ✅ 完成 |
| 建议面板组件 | `frontend/src/components/editor/SuggestionPanel.tsx` | ✅ 完成 |
| 首页 | `frontend/src/pages/Home.tsx` | ✅ 完成 |
| 上传页面 | `frontend/src/pages/Upload.tsx` | ✅ 完成 |
| 干预模式页面 | `frontend/src/pages/Intervention.tsx` | ✅ 完成 |
| YOLO模式页面 | `frontend/src/pages/Yolo.tsx` | ✅ 完成 |
| 审核结果页面 | `frontend/src/pages/Review.tsx` | ✅ 完成 |

#### 代码摘要 | Code Summary

**前端架构实现：**

1. **技术栈**
   - React 18 + TypeScript
   - Vite 构建工具
   - TailwindCSS 样式框架
   - Zustand 状态管理
   - React Router DOM 路由
   - Axios HTTP客户端
   - Lucide React 图标库

2. **组件设计**
   - 通用组件: Button, RiskBadge, ProgressBar, Layout
   - 编辑器组件: SentenceCard (指纹词高亮), SuggestionPanel (双轨建议展示)
   - 设置组件: ColloquialismSlider (0-10口语化程度)

3. **页面功能**
   - Home: 产品介绍和快速入口
   - Upload: 文件上传/文本粘贴，处理设置
   - Intervention: 逐句处理，双轨建议选择
   - Yolo: 自动处理，实时进度显示
   - Review: 结果查看，导出功能

4. **状态管理**
   - sessionStore: 会话状态、建议加载、验证结果
   - configStore: 口语化等级、目标语言、处理等级 (持久化)

---

## 变更日志 | Change Log

### 2025-12-31 (Update 23)

**新增 Gemini API 支持 Add Gemini API Support:**
- 用户需求：增加调用 Gemini 的功能，将默认模型换成 Gemini 的最新 Flash 模型
- 环境变量：`GEMINI_API_KEY`
- 修改内容：
  - `src/config.py:43-45`
    - 新增 `gemini_api_key` 配置项
    - 将 `llm_provider` 默认值改为 `"gemini"`
    - 将 `llm_model` 默认值改为 `"gemini-2.5-flash"`
  - `src/core/suggester/llm_track.py:252-263`
    - 在 `generate_suggestion` 方法中添加 Gemini provider 支持
    - Gemini 作为首选 provider，DeepSeek 作为 fallback
  - `src/core/suggester/llm_track.py:360-390`
    - 新增 `_call_gemini` 异步方法
    - 使用 `google-genai` 库的异步 API (`client.aio.models.generate_content`)
  - `src/api/routes/suggest.py:498-511`
    - 在 `analyze_sentence` 端点添加 Gemini API 调用
  - `src/api/routes/suggest.py:766-779`
    - 在 `_translate_sentence` 函数添加 Gemini API 调用
  - `requirements.txt:29`
    - 新增 `google-genai>=1.0.0` 依赖

**效果**:
- 默认使用 Gemini 2.5 Flash 模型（最新版本，速度快、成本低）
- 保持对 DeepSeek、Anthropic、OpenAI 的兼容支持
- 支持通过 `llm_provider` 环境变量切换 LLM 提供商

---

### 2025-12-31 (Update 22)

**新增项目总结文档 Add Project Summary Document:**
- 用户需求：总结项目结构和运行逻辑
- 新增文件：`doc/project-summary.md`
- 内容包括：
  - 项目概述和核心理念
  - 完整技术栈（后端Python + 前端TypeScript/React）
  - 项目目录结构
  - 四大核心功能模块详解（预处理、分析、建议、验证）
  - 双模式架构（干预模式 + YOLO模式）
  - API接口设计
  - 数据流与运行逻辑图
  - 数据库设计
  - 项目创新点
  - 与竞品对比
  - 启动与运行说明
  - 开发进度现状
- 文档格式：中英双语

---

### 2025-12-31 (Update 21)

**多项UX优化 Multiple UX Improvements:**

1. **修复句子列表滚动位置重置 Fix Sidebar Scroll Position Reset:**
   - 问题：点击选择方案后，左侧句子列表会刷新到最顶端
   - 修复：`frontend/src/pages/Intervention.tsx:74-76, 210-230`
     - 新增 `sidebarScrollRef` 保存滚动容器引用
     - 在 `loadAllSentences` 中保存滚动位置
     - 使用 `requestAnimationFrame` 在状态更新后恢复滚动位置

2. **默认展开轨道A Default Expand Track A:**
   - 问题：切换句子后保持上一个句子的轨道展开状态
   - 修复：`frontend/src/components/editor/SuggestionPanel.tsx:65-69`
     - 监听 `sentenceId` 变化，重置 `expandedTrack` 为 'llm'

3. **统一句子序号显示 Unified Sentence Index Display:**
   - 问题：句子列表显示 #12，当前句子页面显示 #33（数据库索引）
   - 修复：
     - `frontend/src/components/editor/SentenceCard.tsx:14, 27-31, 85`
       - 新增 `displayIndex` 属性覆盖显示序号
       - 使用 `indexToShow` 变量统一处理
     - `frontend/src/pages/Intervention.tsx:618`
       - 传递 `displayIndex={(session?.currentIndex ?? 0) + 1}`

4. **进度条显示已完成/总共比例 Progress Bar Shows Completed/Total Ratio:**
   - 问题：进度条显示当前选中位置而非已完成比例
   - 修复：`frontend/src/pages/Intervention.tsx:572-582`
     - 改用 `completedCount / totalSentences * 100` 计算进度

5. **已处理句子不重新调用LLM Processed Sentences Don't Reload LLM:**
   - 问题：重新登录后，选择已处理句子仍会调用LLM生成建议
   - 修复：
     - `frontend/src/pages/Intervention.tsx:292-299`
       - 新增 `isCurrentSentenceProcessed` 检查当前句子状态
     - `frontend/src/pages/Intervention.tsx:266-277`
       - 在加载建议前检查句子是否已处理
       - 已处理则跳过LLM调用，直接显示已处理状态
     - `frontend/src/components/editor/SuggestionPanel.tsx:25, 54, 119-158`
       - 新增 `sentenceProcessedType` 属性
       - 根据处理类型显示不同图标和消息（处理✓/跳过⏭/标记🚩）

**效果**:
- 选择方案后侧边栏保持滚动位置
- 切换句子时自动展开轨道A
- 当前句子序号与侧边栏一致
- 进度条准确反映已完成比例
- 已处理句子直接显示状态，不浪费LLM调用

---

### 2025-12-31 (Update 20)

**修复快速切换句子导致建议面板跳动 Fix Suggestions Panel Jumping on Fast Sentence Switching:**
- 用户需求：快速切换句子时，修改建议页面会来回跳动，显示之前点击句子的修改意见
- 问题分析：
  - 这是典型的竞态条件 (race condition) 问题
  - 用户快速切换句子时，多个 API 请求同时发出
  - 由于网络延迟不确定，先发出的请求可能比后发出的请求更晚返回
  - 导致显示旧请求的结果，而不是当前选中句子的建议
- 修复内容：
  - `frontend/src/stores/sessionStore.ts:29-31`
    - 新增 `suggestionRequestCounter` 模块级计数器
  - `frontend/src/stores/sessionStore.ts:50`
    - 新增 `currentSuggestionRequestId` 状态追踪当前请求ID
  - `frontend/src/stores/sessionStore.ts:130-188`
    - `loadSuggestions` 函数使用请求ID验证机制：
    - 发起请求前生成新的 requestId 并存入状态
    - 请求返回后检查 requestId 是否仍是最新
    - 如果不是最新则丢弃结果，避免覆盖当前句子的建议
  - `frontend/src/pages/Intervention.tsx:1`
    - 导入 `useRef` hook
  - `frontend/src/pages/Intervention.tsx:70-72`
    - 新增 `analysisRequestIdRef` 用于追踪分析请求ID
  - `frontend/src/pages/Intervention.tsx:100-187`
    - `handleAnalysisToggle` 函数增加竞态条件保护：
    - 使用 ref 追踪分析请求ID
    - 请求返回后验证是否为最新请求
    - 过期请求的结果和错误都会被丢弃

**效果**:
- 快速切换句子时，只有最后点击句子的建议会被显示
- 过期的请求结果会被静默丢弃，控制台会输出日志便于调试
- 建议面板不再来回跳动，用户体验显著提升

---

### 2025-12-31 (Update 19)

**新增算法逻辑总结文档 Add Algorithm Summary Document:**
- 用户需求：总结AI评分逻辑和降低AIGC的逻辑
- 新增文件：`doc/algorithm-summary.md`
- 内容包括：
  - 四维度评分系统详解（PPL、指纹词、突发性、结构模式）
  - 分级指纹词系统（一级+40分/个，二级+15分/个）
  - 人类特征减分机制
  - 双轨道降AIGC策略（LLM改写 + 规则替换）
  - 双检测器视角（Turnitin/GPTZero）
  - 验证机制和质量门控

---

### 2025-12-30 (Update 18)

**修复轨道C检测风险500错误 Fix Track C Validate Risk 500 Error:**
- 问题：点击"检测风险"按钮时返回 500 Internal Server Error
- 原因：`src/api/routes/suggest.py:237` 使用 `sentence.text` 但模型属性是 `original_text`
- 修复内容：
  - `src/api/routes/suggest.py:237`
    - `sentence.text` → `sentence.original_text`

---

### 2025-12-30 (Update 17)

**修复轨道C分析卡在加载状态 Fix Track C Analysis Stuck in Loading:**
- 问题：点击"分析"按钮后，分析结果返回成功但UI一直显示加载中
- 原因：`SuggestionPanel` 组件使用 `getAnalysisForSentence()` 获取缓存，但不是响应式的
  - 当缓存更新时，组件没有重新渲染
  - `loadingAnalysis` 变为 `false`，但 `analysisResult` 仍为 `null`
- 修复内容：
  - `frontend/src/components/editor/SuggestionPanel.tsx:65-71`
    - 使用 `useSessionStore(state => state.analysisCache)` 直接订阅缓存
    - 使 `analysisResult` 对缓存更新具有响应性

---

### 2025-12-30 (Update 16)

**修复DOM嵌套警告 Fix DOM Nesting Warning:**
- 问题：`<button> cannot appear as a descendant of <button>` 警告
- 原因：`InfoTooltip` 组件使用 `<button>` 被嵌套在 `SuggestionTrack` 的 `<button>` 内
- 修复内容：
  - `frontend/src/components/common/InfoTooltip.tsx:74-95`
    - 将内部 `<button>` 改为 `<span role="button">`
    - 添加 `tabIndex={0}` 保持键盘可访问性
    - 添加 `onKeyDown` 处理 Enter/Space 键
    - 添加 `e.stopPropagation()` 防止触发父按钮

---

### 2025-12-30 (Update 15)

**修复风险变化显示问题 Fix Risk Change Display Issues:**

1. **修复已有数据缺少new_risk_score的问题 Fix Missing new_risk_score for Existing Data:**
   - 问题：之前创建的修改记录没有`new_risk_score`，导致UI无法显示风险变化
   - 解决：编写脚本重新计算并更新8条已有修改记录的`new_risk_score`
   - 更新后的分数：4, 12, 12, 39, 27, 22, 12, 29

2. **修复RiskLevel枚举大小写错误 Fix RiskLevel Enum Case Error:**
   - 问题：`/session/{id}/sentences` API 返回 500 Internal Server Error
   - 原因：`src/api/routes/session.py:412-419` 使用 `RiskLevel.safe` 而非 `RiskLevel.SAFE`
   - Python枚举成员名称为大写（SAFE, LOW, MEDIUM, HIGH），值为小写字符串
   - 修复内容：
     - `src/api/routes/session.py:412-419`
       - `RiskLevel.safe` → `RiskLevel.SAFE`
       - `RiskLevel.low` → `RiskLevel.LOW`
       - `RiskLevel.medium` → `RiskLevel.MEDIUM`
       - `RiskLevel.high` → `RiskLevel.HIGH`

**效果**:
- `/session/{id}/sentences` API 正常返回数据
- 已处理句子包含 `new_risk_score` 和 `new_risk_level`
- 前端侧边栏可正确显示风险变化箭头（如 "56 高风险 → 4 安全"）

---

### 2025-12-30 (Update 14)

**UI与数据显示优化 UI and Data Display Improvements:**

1. **PPL提示信息修正 Fix PPL Tooltip:**
   - 用户需求：PPL所有句子显示100.0
   - 分析：PPL计算逻辑正确，但tooltip描述有误
   - 修改内容：
     - `frontend/src/components/editor/SentenceCard.tsx:188-192`
     - 更正tooltip：PPL越低表示文本越可预测，AI特征越明显
     - 阈值说明：<25高风险，25-45中风险，>45低风险

2. **指纹词指标改用数量+emoji显示 Fingerprint Count with Emoji:**
   - 用户需求：不要用密度，用数量和emoji表示（0=😊,1=😐,2=😰,3+=😡）
   - 修改内容：
     - `frontend/src/components/editor/SentenceCard.tsx:199-230`
     - 新增 `FingerprintIndicator` 组件
     - 根据数量显示不同emoji和颜色：
       - 0个：😊 绿色 - 未检测到AI指纹词
       - 1个：😐 黄色 - 建议替换
       - 2个：😰 橙色 - 需要修改
       - 3+个：😡 红色 - 强烈建议改写
     - 移除旧的密度显示

3. **句子列表风险变化显示 Risk Change Display in Sentence List:**
   - 用户需求：已修改句子应显示"原风险指数 → 新风险指数"
   - 问题分析：
     - 前端UI代码已存在 (`Intervention.tsx:429-442`)
     - 后端 `/apply` 接口没有计算和存储 `new_risk_score`
   - 修改内容：
     - `src/api/routes/suggest.py:165-201`
       - 在 `/apply` 端点添加 `RiskScorer` 计算新风险分数
       - 保存到 `Modification.new_risk_score` 字段
       - 返回 `new_risk_score` 到前端
     - `src/api/routes/session.py:408-419`
       - `/sentences` 端点已包含 `new_risk_score` 和 `new_risk_level` 返回逻辑

**效果**:
- PPL提示信息准确描述低值=高风险
- 指纹词显示直观的数量+emoji，用户一目了然
- 应用修改后，侧边栏显示 `原风险分数 → 新风险分数` 变化

---

### 2025-12-30 (Update 13)

**自定义输入语义相似度0%修复 Fix Custom Input Semantic Similarity 0%:**
- 用户需求：用户改写后点击"检测风险"，语义相似度显示0%，明显不正确
- 问题分析：
  - `src/api/routes/suggest.py:213` 代码中 `original=""` 被硬编码为空字符串
  - 注释写着 "Will be fetched from DB" 但从未实现
  - 用户改写与空字符串比较，语义相似度始终为0%
- 修复内容：
  - `src/api/routes/suggest.py:193-239`
    - 从数据库获取原始句子：`select(Sentence).where(Sentence.id == request.sentence_id)`
    - 提取原文：`original_text = sentence.text`
    - 提取锁定术语：`locked_terms = sentence.locked_terms_json or []`
    - 正确调用质量门控验证

**效果**: 语义相似度验证现在正确比较用户改写与原句，能正确判断语义保持程度

---

### 2025-12-30 (Update 12)

**句子分析长时间无响应修复 Fix Sentence Analysis No Response:**
- 用户需求：点击"分析"按钮后长时间无反应，需调查原因
- 问题分析：
  1. API本身正常，响应时间约5-10秒
  2. 前端 `analysisState.expandedTrack` 没有在点击分析时同步为 'custom'，导致布局状态不一致
  3. 错误处理没有给用户显示反馈
- 修复内容：
  - `frontend/src/pages/Intervention.tsx:72-84`
    - `analysisState` 新增 `error?: string` 字段追踪错误状态
  - `frontend/src/pages/Intervention.tsx:98-150`
    - `handleAnalysisToggle` 增强：
    - 验证 `sentenceId` 和 `originalText` 存在，否则显示错误
    - 设置 `expandedTrack: 'custom'` 确保布局正确更新
    - 添加console.log调试信息
    - 捕获错误并显示到 `analysisState.error`
  - `frontend/src/components/editor/SuggestionPanel.tsx:12-18`
    - `AnalysisState` 接口新增 `error?: string` 字段
  - `frontend/src/components/editor/SuggestionPanel.tsx:256-291`
    - 加载状态新增提示：首次分析可能需要10-30秒
    - 错误状态显示具体错误消息和重试按钮
    - 失败状态也显示重试按钮

**效果**:
- 用户点击分析后能立即看到加载状态
- 分析失败时显示具体错误消息，可一键重试
- 状态同步问题修复，布局能正确切换

---

### 2025-12-30 (Update 11)

**轨道C自定义输入布局优化 Track C Custom Input Layout:**
- 用户需求：轨道C点击"分析"按钮后，输入框应显示在左侧"当前句子"下方，右侧只显示分析面板，便于左上看原文、左下输入修改、右边看分析
- 修改内容：
  - 新增 `frontend/src/components/editor/CustomInputSection.tsx`
    - 独立的自定义输入组件，包含写作提示、输入框、验证结果和操作按钮
    - 支持分析状态的切换回调
  - `frontend/src/components/editor/SuggestionPanel.tsx`
    - 轨道C展开时：
      - 分析未显示：在右侧显示CustomInputSection（正常位置）
      - 分析已显示：只显示分析面板，输入框移到左侧
    - 分析状态由父组件管理，通过 `analysisState` props传入
    - 新增 `handleCloseAnalysis` 处理关闭分析
  - `frontend/src/pages/Intervention.tsx:70-131`
    - 新增 `analysisState` 状态管理分析面板显示
    - 新增 `handleAnalysisToggle` 处理分析加载和切换
    - 条件：`expandedTrack === 'custom' && showAnalysis` 时，左侧显示CustomInputSection
  - `frontend/src/components/editor/SentenceAnalysisPanel.tsx:15-18,44-63`
    - 新增 `hideCloseButton` 属性，内嵌时隐藏标题栏

**效果**:
- 轨道C展开时：输入框在右侧（正常位置）
- 点击"分析"后：输入框移到左侧，右侧显示分析面板
- 左上原句、左下输入、右边分析，三区并列对照，改写体验大幅提升

---

### 2025-12-30 (Update 10)

**当前句子区域固定布局 Fixed Current Sentence Area:**
- 用户需求：红框里的"当前句子"部分不应随右边修改建议的滚动而滚动，当句子较长时可更好对照原句与修改意见
- 修改内容：
  - `frontend/src/pages/Intervention.tsx:458-527`
    - 将主内容区域从 `overflow-y-auto` 改为 `overflow-hidden`（禁止整体滚动）
    - 将两列布局从 `grid lg:grid-cols-2` 改为 `flex flex-col lg:flex-row`
    - 左侧"当前句子"区域使用 `lg:w-1/2 flex-shrink-0` 固定宽度且不收缩
    - 右侧"修改建议"区域使用 `lg:w-1/2 flex flex-col min-h-0`
    - 右侧内部新增 `overflow-y-auto` 容器，使建议列表独立滚动
    - 添加 `pr-2` 为滚动条预留空间

**InfoTooltip组件改用Portal InfoTooltip Using React Portal:**
- 用户需求：PPL信息提示框左边显示不全，被overflow:hidden裁剪
- 修改内容：
  - `frontend/src/components/common/InfoTooltip.tsx`
    - 使用 React Portal (`createPortal`) 将tooltip渲染到 `document.body`
    - 彻底解决被父容器 `overflow:hidden` 裁剪的问题
    - 使用 `z-index: 9999` 确保始终在最顶层

**效果**:
- 左侧当前句子固定显示，不随右侧内容滚动
- 右侧修改建议区域独立滚动
- 长句子对照修改建议时体验更佳
- 信息提示框不再被裁剪，始终完整显示

---

### 2025-12-30 (Update 9)

**侧边栏状态标记改进 Sidebar Status Indicators:**
- 用户需求：侧边栏状态标记需要区分：灰色（未查看）、黄色（已查看有缓存）、绿色（已处理）、跳过图标、小旗子
- 修改内容：
  - `frontend/src/pages/Intervention.tsx:159-200`
    - 更新 `getStatusIndicator` 函数，使用 `suggestionsCache` 判断是否已查看
    - 灰色圆点 (Circle fill-gray-300): 未查看
    - 黄色圆点 (Circle fill-amber-400): 已查看有缓存但未处理
    - 绿色对勾 (CheckCircle): 已应用修改
    - 跳过图标 (SkipForward): 已跳过
    - 旗子图标 (Flag): 已标记
    - 蓝色脉冲点: 当前正在编辑
  - `frontend/src/pages/Intervention.tsx:47`
    - 从 store 导入 `suggestionsCache`

**跳过/标记不自动跳转 Skip/Flag No Auto-Jump:**
- 用户需求：选择"跳过"或"标记"后不应自动跳转到下一句
- 修改内容：
  - `src/api/routes/session.py:252-303`
    - `skip_sentence` 端点不再调用 `next_sentence`
    - 改为调用 `get_current_state` 返回当前状态
    - 新增重复修改记录检查，支持覆盖更新
  - `src/api/routes/session.py:306-357`
    - `flag_sentence` 端点同样修改
  - `frontend/src/stores/sessionStore.ts:160-200`
    - 更新注释说明不自动跳转
    - 添加 `validationResult: null` 清理

**效果**:
- 侧边栏状态标记可视化更清晰
- 跳过/标记后保持在当前句子，用户可手动选择下一句

---

### 2025-12-30 (Update 8)

**规则轨道增强 Rule Track Enhancement:**
- 问题：规则轨道(Track B)大多数情况显示"无需修改"，没有实际作用
- 原因：规则轨道只有约20个指纹词，而评分器有60+个
- 修复内容：
  - `src/core/suggester/rule_track.py:47-319`
    - 扩展 `FINGERPRINT_REPLACEMENTS` 从20个词到50+个词
    - 包含一级词：delve, tapestry, multifaceted, inextricably, plethora, myriad, elucidate, henceforth, aforementioned等
    - 包含二级词：crucial, pivotal, underscore, foster, furthermore, moreover, additionally, consequently, comprehensive, holistic, facilitate, leverage, robust, seamless, noteworthy, groundbreaking, dynamics, mechanisms, notably, importantly, hence, thereby等
  - `src/core/suggester/rule_track.py:321-531`
    - 扩展 `PHRASE_REPLACEMENTS` 从10个短语到40+个短语
    - 新增类别：Important/Note模式、Role/Importance模式、Emphasis模式、Context模式、Quantity模式、Cause/Result模式、Purpose模式、Conclusion模式、Approach模式、AI padding短语等

**效果**: 规则轨道现在能有效替换AI指纹词
- 示例："Furthermore, the study facilitates understanding."
- 改写："Also, the study helps understanding."
- 风险：55 → 0

---

### 2025-12-30 (Update 7)

**建议缓存功能 Suggestions Caching:**
- 新增建议缓存机制，避免切换句子时重复调用LLM
- 修改内容：
  - `frontend/src/stores/sessionStore.ts:18,34,59,73`
    - 新增 `SuggestionsCache` 类型 (`Map<string, SuggestResponse>`)
    - 新增 `suggestionsCache` 状态存储句子ID到建议的映射
    - 新增 `clearSuggestionsCache` 接口声明
  - `frontend/src/stores/sessionStore.ts:101-141`
    - `loadSuggestions` 方法支持缓存检查
    - 可选 `forceRefresh` 参数强制刷新缓存
    - 成功获取建议后存入缓存
  - `frontend/src/stores/sessionStore.ts:77-80`
    - 开始新会话时自动清除缓存
  - `frontend/src/stores/sessionStore.ts:311-313`
    - 新增 `clearSuggestionsCache` 方法实现
  - `frontend/src/stores/sessionStore.ts:317-327`
    - `reset` 方法清除缓存

**效果**: 用户在不同句子间切换时，已生成的建议会被缓存，无需重复调用LLM

---

### 2025-12-30 (Update 6)

**修复：选择建议后不再跳转和重复调用LLM**
- 问题：选择建议后，系统会自动跳转到下一句并重新调用LLM生成新建议
- 原因：
  1. `useEffect` 监听 `session?.currentSentence` 对象变化，每次调用 `getCurrent` 都会触发
  2. 后端 `/apply` 端点没有真正保存修改到数据库
  3. 前端使用 `sentence.index` 作为ID，但后端期望的是数据库UUID

- 修复内容：
  - `frontend/src/pages/Intervention.tsx:99-121`
    - 新增 `lastLoadedIndex` 状态追踪已加载的句子索引
    - 只在 `currentIndex` 变化时才重新加载建议
  - `src/api/routes/suggest.py:140-190`
    - `/apply` 端点现在正确保存修改到数据库
    - 不更新 `session.current_index`，保持用户手动导航
  - `src/api/schemas.py:146`
    - `SentenceAnalysis` 新增 `id` 字段返回数据库ID
  - `src/api/routes/session.py:454`
    - `_build_sentence_analysis` 返回句子的数据库ID
  - `frontend/src/types/index.ts:59`
    - `SentenceAnalysis` 接口新增 `id` 字段
  - `frontend/src/stores/sessionStore.ts:174,213,248`
    - 使用 `sentence.id` 替代 `sentence.index.toString()` 调用API

---

### 2025-12-30 (Update 5)

**句子分析功能 Sentence Analysis Feature:**
- 新增后端分析API (`src/api/routes/suggest.py:334-640`)
  - `/api/v1/suggest/analyze` 端点
  - 使用LLM进行深度句法分析
  - 备用分析机制（LLM失败时使用规则）

- 分析内容包括:
  - **语法结构**: 主语/谓语/宾语 + 定语/状语/补语
  - **从句分析**: 关系从句、名词从句、状语从句及作用
  - **代词指代**: 识别代词指向的具体对象
  - **AI词汇检测**: 一级词（+40分）、二级词（+15分）及替换建议
  - **改写建议**: 被动转主动、拆分长句、简化表达等

- 新增前端类型定义 (`frontend/src/types/index.ts:196-265`)
  - GrammarModifier, GrammarStructure, ClauseInfo
  - PronounReference, AIWordSuggestion, RewriteSuggestion
  - DetailedSentenceAnalysis

- 新增分析结果面板 (`frontend/src/components/editor/SentenceAnalysisPanel.tsx`)
  - 可折叠的分析区块
  - 语法结构可视化
  - AI词汇替换建议（点击可复制）
  - 改写示例展示

- 更新建议面板 (`frontend/src/components/editor/SuggestionPanel.tsx`)
  - 自定义修改区域新增"分析"按钮
  - 根据口语化程度生成替换建议
  - 分析面板内嵌显示

---

### 2025-12-30 (Update 4)

**信息提示优化 Info Tooltip Improvements:**
- 新增InfoTooltip通用组件 (`frontend/src/components/common/InfoTooltip.tsx`)
  - 支持点击/悬停显示提示
  - 支持四个方向定位（top/bottom/left/right）
  - 自动点击外部关闭

- PPL信息提示 (`frontend/src/components/editor/SentenceCard.tsx:188-192`)
  - 说明：使用zlib压缩比计算，AI文本压缩率高=信息密度低
  - 阈值说明：>2.5可疑，>3.0高风险

- 指纹词密度信息提示 (`frontend/src/components/editor/SentenceCard.tsx:196-200`)
  - 说明：指纹词数量占总词数的比例
  - 举例：delve、tapestry、multifaceted等

- 语义相似度信息提示 (`frontend/src/components/editor/SuggestionPanel.tsx:344-349`)
  - 说明：改写后与原文的语义相似程度
  - 阈值说明：>85%语义良好，<70%存在偏移风险

---

### 2025-12-30 (Update 3)

**交互优化 UX Improvements:**
- 新增DE-AIGC导航标签 (`frontend/src/components/common/Layout.tsx:5,29-32,62-71`)
  - 当用户在干预模式页面时，导航栏显示"DE-AIGC"标签
  - 使用Wand2图标，蓝色高亮边框
  - 防止用户误点其他导航后无法返回当前会话

- 移除修改后自动跳转 (`frontend/src/stores/sessionStore.ts:179-194,218-227`)
  - 应用建议后不再自动跳转到下一句
  - 清空suggestions状态表示当前句子已处理
  - 用户需点击左侧列表选择下一句（节省LLM token）

- 句子已处理视觉提示 (`frontend/src/components/editor/SuggestionPanel.tsx:84-104`)
  - 当前句子处理完成后显示绿色对勾图标
  - 提示"当前句子已处理"+"请从左侧列表选择下一个句子"
  - 引导用户使用侧边栏导航

- ProgressBar组件增强 (`frontend/src/components/common/ProgressBar.tsx:10,37,42`)
  - 新增className属性支持自定义样式

- Upload页面类型修复 (`frontend/src/pages/Upload.tsx:304-309`)
  - 补充RiskLevel的'safe'类型定义

---

### 2025-12-30 (Update 2)

**重大改进 Major Improvements:**
- 风险评分系统重构 (`src/core/analyzer/scorer.py`)
  - 基于学术写作专家分析进行全面改进
  - 新增分级指纹词检测：
    - 一级词 (Dead Giveaways): delve, tapestry, realm, multifaceted 等 (+40分/个)
    - 二级词 (AI Habitual): crucial, furthermore, comprehensive 等 (+15分/个)
  - 使用zlib压缩比作为PPL代理（AI文本压缩率高=信息密度低）
  - 新增人类特征减分机制 (`_calculate_human_deduction`):
    - 带情感第一人称 ("I was surprised"): -20分
    - 非正式括号补充 ("which was weird"): -15分
    - 具体非整数数字 (14.2%, p<0.05): -10分
    - 口语化表达 (kind of, honestly): -10分
    - 反问句: -10分
  - 移除错误规则：
    - 犹豫词 (suggests, indicates) 不再惩罚 - 学术写作规范
    - 引号不再惩罚 - 引用是人类特征
  - 增强AI模式检测：
    - "not only...but also" 双重强调 (+20)
    - 空洞学术填充 ("complex dynamics", "holistic approach") (+15/个)
    - 句首连接词 (Furthermore, Moreover) (+20)

**测试结果 Test Results:**
```
Super AI (Level 1 fingerprints): Score=51 (high) ✓
Moderate AI (Level 2 only): Score=42 (medium) ✓
Academic Human: Score=0 (safe) ✓ (无假阳性)
Casual Human: Score=0 (safe) ✓
```

---

### 2025-12-30

**新增 Added:**
- 内容类型检测与过滤功能 (`src/core/preprocessor/segmenter.py:14-600`)
  - 自动识别标题 (title)、章节标题 (section)、表格说明 (table_header)、图片说明 (figure)、参考文献 (reference)、元数据 (metadata)、短片段 (fragment)
  - 过滤参考文献部分 (References section)：检测到"References"后自动标记后续内容为参考文献
  - 识别编号章节 (1. Introduction, 1.1 Background)
  - 识别表格/图片说明 (Table 1:, Figure 2.)
  - 识别作者信息、单位信息、关键词等元数据
  - 短于15字符或4词的片段自动过滤
- 数据库模型更新 (`src/db/models.py:75-76`)
  - Sentence模型新增 `content_type` 和 `should_process` 字段
- Session路由更新 (`src/api/routes/session.py:50-57`)
  - 干预模式只处理 `should_process=True` 的句子
- 安全风险等级 (`src/api/schemas.py:16`)
  - 新增 "safe" 风险等级 (score < 10)
- 历史任务页面 (`frontend/src/pages/History.tsx`)
  - 会话列表和文档列表双标签页
  - 恢复/继续会话功能
  - 删除文档功能
- 历史列表API (`src/api/routes/session.py`, `src/api/routes/documents.py`)
  - `GET /api/v1/session/list` - 获取所有会话列表
  - `GET /api/v1/documents/` - 获取所有文档列表
- 导航栏更新 (`frontend/src/components/common/Layout.tsx`)
  - 新增"历史"导航项
- 标题/章节识别增强 (`src/core/preprocessor/segmenter.py:418-453`)
  - 新增 `_looks_like_header` 方法识别类似标题的文本
  - 检测：编号章节、已知章节关键词、首字母大写模式、含冒号的学术标题
- 干预模式页面重构 (`frontend/src/pages/Intervention.tsx`)
  - 左侧可折叠句子列表侧边栏
  - 支持点击跳转到任意句子
  - 显示句子状态（待处理/当前/已处理/跳过/标记）
  - 风险等级颜色指示
- 句子列表API (`src/api/routes/session.py:320-400`)
  - `GET /api/v1/session/{id}/sentences` - 获取会话所有句子
  - `POST /api/v1/session/{id}/goto/{index}` - 跳转到指定句子
- 自定义修改建议 (`src/api/routes/suggest.py:186-323`)
  - `POST /api/v1/suggest/hints` - 获取3点写作建议
  - 基于suggestions.md分析原句并提供针对性建议
  - 检测：AI高频词、AI句式模板、连接词过度使用、被动语态、空洞修饰
- 建议面板优化 (`frontend/src/components/editor/SuggestionPanel.tsx`)
  - 展开自定义修改时显示3点写作建议
  - 风险分数变化差值显示（+/-）
- 实际风险评分计算 (`src/api/routes/suggest.py:47-99`)
  - 使用RiskScorer计算原始和改写后的实际风险分数
  - 替换原来的假分数（40/70等）

**修复 Fixed:**
- 标题与正文内容合并问题 (`src/core/preprocessor/segmenter.py:323-344, 386-453`)
  - 问题：标题 "Turning Waste into Soil Wealth: ..." 与 "Abstract\r\nThe concurrent..." 被合并为一句
  - 原因1：`_split_sentences` 只在双换行符处分割，单个换行符被忽略
  - 原因2：`_merge_fragments` 将无句号结尾的短文本视为片段并与下一句合并
  - 解决1：修改 `_split_sentences` 在任意换行符 (`\r?\n`) 处分割
  - 解决2：新增 `_looks_like_header` 方法，`_is_fragment` 调用时排除类似标题的文本
- API响应snake_case到camelCase转换 (`frontend/src/services/api.ts`)
  - 问题：session_id (后端) vs sessionId (前端) 命名不匹配
  - 解决：添加 transformKeys 函数自动转换所有API响应键名
- 翻译功能实现 (`src/api/routes/suggest.py`)
  - 问题：翻译显示占位符 "[Translation to zh]"
  - 解决：使用DeepSeek API实现实际翻译
- 风险阈值调整 (`src/core/analyzer/scorer.py`)
  - 问题：文档210句中207句为低风险，只有3句被识别
  - 解决：调整阈值 - high: ≥50 (原61), medium: ≥25 (原31), low: ≥10, safe: <10
  - 增强AI结构模式检测 (学术过渡词、犹豫词、长句等)
- LLM改写提示词优化 (`src/core/suggester/llm_track.py:173-214`)
  - 问题：LLM生成新内容而非改写原句，导致风险反而升高
  - 解决：强化提示词强调"改写"而非"生成"，添加STRICT Requirements

**依赖 Dependencies:**
- 安装 pydantic-settings, aiosqlite, python-multipart

---

### 2025-12-30 - 缓存与UX优化 | Caching and UX Improvements

**新增 Added:**
- 分析结果缓存 (`frontend/src/stores/sessionStore.ts:21-24, 44-45, 66-78`)
  - `analysisCache: Map<string, DetailedSentenceAnalysis>` - 每句子的分析结果缓存
  - `setAnalysisForSentence` / `getAnalysisForSentence` - 缓存读写方法
  - 避免重复API调用，提升响应速度
- 自定义文本草稿缓存 (`frontend/src/stores/sessionStore.ts:25-28, 67-68`)
  - `customTextCache: Map<string, string>` - 每句子的用户输入草稿缓存
  - `setCustomTextForSentence` / `getCustomTextForSentence` - 缓存读写方法
  - 切换句子时保留用户输入，避免丢失
- 自动保存功能 (`frontend/src/components/editor/SuggestionPanel.tsx:86-106`)
  - 每15秒自动将用户输入保存到缓存
  - 使用useRef管理定时器，防止内存泄漏
- Sticky布局优化 (`frontend/src/components/editor/SuggestionPanel.tsx:256-431`)
  - 点击分析后，原文+输入框固定在顶部
  - 分析面板在下方独立滚动，高度限制`max-h-[70vh]`
  - 用户可同时参考原文和分析内容进行改写
- 侧边栏状态指示器增强 (`frontend/src/pages/Intervention.tsx:159-200`)
  - 灰色圆点 - 未查看
  - 黄色圆点 - 已查看有缓存但未处理
  - 绿色对勾 - 已确定修改方案
  - 跳过图标 - 标记为跳过
  - 小旗子 - 标记需审核
- 跳过/标记不自动跳转 (`src/api/routes/session.py:252-357`)
  - 修改`skip_sentence`和`flag_sentence`不再调用`next_sentence`
  - 返回当前状态，用户通过侧边栏手动导航
  - 支持修改记录的更新（upsert逻辑）

**修改 Modified:**
- `frontend/src/stores/sessionStore.ts` - 新增三个缓存Map和对应方法
- `frontend/src/components/editor/SuggestionPanel.tsx` - 缓存集成和sticky布局
- `frontend/src/pages/Intervention.tsx` - 传递sentenceId，状态指示器使用缓存
- `src/api/routes/session.py` - skip/flag不自动跳转

**修复 Fixed:**
- TypeScript类型错误：移除未使用的`DetailedSentenceAnalysis`导入
- TypeScript类型错误：`NodeJS.Timeout`改为`ReturnType<typeof setTimeout>`

---

### 2025-12-30 - 计数器与完成按钮优化 | Counter and Complete Button Improvements

**新增 Added:**
- 进度计数器优化 (`frontend/src/pages/Intervention.tsx:146-149, 378-382`)
  - 计数器显示"已完成 X 句"而非"第 X 句"
  - 已完成数 = 已处理(processed) + 已跳过(skipped)
  - 更准确反映实际处理进度
- 完成按钮始终可用 (`frontend/src/pages/Intervention.tsx:516-522`)
  - 移除 `disabled` 条件，按钮始终可点击
  - 用户可随时选择结束处理
- 中断确认对话框 (`frontend/src/pages/Intervention.tsx:527-558`)
  - 当未完成所有句子时点击"完成处理"，弹出确认对话框
  - 显示剩余未处理句子数量
  - 提供"继续处理"和"确认中断"两个选项
  - 确认后跳转到结果页面
- 侧边栏风险变化显示 (`frontend/src/pages/Intervention.tsx:326-348`)
  - 已处理句子显示风险变化：`54 高风险 → 14 低风险`
  - 原风险和新风险均使用 RiskBadge 组件显示
  - 底色保持红/黄/绿区分

**修改 Modified:**
- `frontend/src/pages/Intervention.tsx` - 计数器逻辑、完成按钮、确认对话框、风险变化显示
- `frontend/src/types/index.ts` - SentenceAnalysis 新增 newRiskScore, newRiskLevel 字段
- `src/api/schemas.py` - SentenceAnalysis 新增 new_risk_score, new_risk_level 字段
- `src/api/routes/session.py` - get_all_sentences 返回处理后的新风险分数

---

### 2024-12-30

**新增 Added:**
- React + Vite + TypeScript 前端项目
- TailwindCSS 配置及自定义主题
- Zustand 状态管理 (sessionStore, configStore)
- 全部UI组件实现 (Button, RiskBadge, ProgressBar, Layout)
- 编辑器组件 (SentenceCard, SuggestionPanel)
- 设置组件 (ColloquialismSlider)
- 全部页面实现 (Home, Upload, Intervention, Yolo, Review)
- API服务层及类型定义
- 开发启动脚本 (scripts/dev.bat, scripts/dev.sh)
- 环境配置模板 (.env.example)

**测试 Tested:**
- 前端构建测试 ✅ (npm run build)
- 后端启动测试 ✅ (uvicorn)
- 健康检查端点 ✅ (/health)
- DeepSeek API 集成测试 ✅ (LLM Track A)

**修改 Modified:**
- 更新README.md (完整安装和使用说明)
- 更新process.md进度记录

**删除 Removed:**
- N/A

### 2024-12-29

**新增 Added:**
- 项目初始化，创建完整目录结构
- FastAPI后端框架搭建
- 全部核心模块实现
- 数据资源文件创建
- 文档系统建立 (plan.md, structure.md, process.md)

**修改 Modified:**
- N/A

**删除 Removed:**
- N/A

---

## 技术债务 | Technical Debt

| 问题 Issue | 严重程度 Severity | 计划解决 Planned |
|-----------|-------------------|-----------------|
| PPL计算使用简化算法 | 中 Medium | Phase 2 |
| 语义相似度备用算法精度有限 | 低 Low | Phase 2 |
| 无单元测试覆盖 | 高 High | Phase 1 |

---

## 下一步计划 | Next Steps

1. **完成Phase 1:**
   - [x] 创建前端基础UI (React + TailwindCSS)
   - [ ] 编写API集成测试
   - [ ] 配置LLM API密钥并测试
   - [ ] 安装依赖并进行端到端测试

2. **准备Phase 2:**
   - [ ] 集成真实PPL计算模型
   - [ ] 实现BERT MLM上下文替换
   - [ ] 完善YOLO模式后端逻辑

---

> 文档维护 | Document Maintenance:
> 每次功能开发完成后更新此文档
> Update this document after each feature completion
