# AcademicGuard 开发进度
# AcademicGuard Development Progress

> 最后更新 Last Updated: 2026-01-04

---

## 最近更新 | Recent Updates

### 2026-01-04 - 双模式系统实现 | Dual-Mode System Implementation

#### 需求 | Requirements
实现调试模式(DEBUG)和运营模式(OPERATIONAL)的双模式切换系统，支持：
1. 调试模式：不需要用户注册，不需要支付，用于开发测试
2. 运营模式：需要用户登录和支付，连接中央平台
3. 所有预留接口需文档化，便于后续中央平台对接

Implement dual-mode system with DEBUG and OPERATIONAL modes:
1. Debug mode: No registration/payment required, for development/testing
2. Operational mode: Full login and payment flow, connects to central platform
3. All reserved interfaces documented for future platform integration

#### 新增文件 | New Files

| 文件 File | 说明 Description |
|----------|-----------------|
| `src/services/__init__.py` | 服务层初始化 Service layer init |
| `src/services/auth_service.py` | 认证服务（含IAuthProvider接口）Auth service with IAuthProvider interface |
| `src/services/payment_service.py` | 支付服务（含IPaymentProvider接口）Payment service with IPaymentProvider interface |
| `src/services/word_counter.py` | 字数统计服务 Word counting service |
| `src/services/task_service.py` | 任务管理服务 Task management service |
| `src/middleware/__init__.py` | 中间件层初始化 Middleware layer init |
| `src/middleware/mode_checker.py` | 模式检查中间件 Mode checker middleware |
| `src/middleware/auth_middleware.py` | 认证中间件 Auth middleware |
| `src/api/routes/auth.py` | 认证API路由 Auth API routes |
| `src/api/routes/payment.py` | 支付API路由 Payment API routes |
| `src/api/routes/task.py` | 任务API路由 Task API routes |
| `frontend/src/stores/authStore.ts` | 前端认证状态管理 Frontend auth state |
| `frontend/src/stores/modeStore.ts` | 前端模式状态管理 Frontend mode state |
| `frontend/src/components/auth/LoginModal.tsx` | 登录弹窗组件 Login modal |
| `frontend/src/components/auth/AuthGuard.tsx` | 认证守卫组件 Auth guard |
| `frontend/src/components/auth/ModeIndicator.tsx` | 模式指示器组件 Mode indicator |
| `frontend/src/components/payment/QuoteModal.tsx` | 报价弹窗组件 Quote modal |
| `frontend/src/components/payment/PaymentStatus.tsx` | 支付状态组件 Payment status |

#### 修改文件 | Modified Files

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/config.py` | 添加SystemMode枚举、平台配置、定价配置、JWT配置 Add SystemMode enum, platform/pricing/JWT config |
| `src/db/models.py` | 添加User、Task模型和状态枚举 Add User, Task models and status enums |
| `src/main.py` | 添加ModeCheckerMiddleware和新路由 Add ModeCheckerMiddleware and new routes |
| `src/api/schemas.py` | 添加认证/支付相关Schema Add auth/payment schemas |
| `frontend/src/App.tsx` | 添加模式初始化和浮动模式徽章 Add mode init and floating mode badge |
| `frontend/src/pages/Home.tsx` | 添加模式指示器和定价信息显示 Add mode indicator and pricing info |
| `frontend/src/pages/Upload.tsx` | 添加认证检查和支付流程 Add auth check and payment flow |
| `frontend/src/services/api.ts` | 添加taskApi和paymentApi Add taskApi and paymentApi |
| `README.md` | 添加双模式说明和完整预留接口文档 Add dual-mode docs and reserved interface specs |

#### 架构设计 | Architecture Design

1. **策略模式 Strategy Pattern**: 认证和支付服务使用接口+实现类，便于切换：
   - `IAuthProvider` → `DebugAuthProvider` / `PlatformAuthProvider`
   - `IPaymentProvider` → `DebugPaymentProvider` / `PlatformPaymentProvider`

2. **任务生命周期 Task Lifecycle**: CREATED → QUOTED → PAYING → PAID → PROCESSING → COMPLETED

3. **安全机制 Security**:
   - 防偷梁换柱：上传时计算content_hash并锁定
   - 防重放攻击：状态机幂等性设计
   - JWT令牌认证

#### 预留接口 | Reserved Interfaces

完整的接口规范已记录在 README.md 中，包括：

- **认证接口 Auth Interfaces**:
  - `POST /api/v1/auth/send-sms` - 发送验证码
  - `POST /api/v1/auth/verify-sms` - 验证码登录
  - `GET /api/v1/users/{user_id}` - 获取用户信息
  - `POST /api/v1/auth/refresh` - 刷新令牌

- **支付接口 Payment Interfaces**:
  - `POST /api/v1/payments/create` - 创建支付订单
  - `GET /api/v1/payments/{order_id}/status` - 查询订单状态
  - `POST /api/v1/payments/{order_id}/refund` - 申请退款
  - `POST /api/v1/payment/callback` - 支付回调(Webhook)

#### 环境变量 | Environment Variables

```env
SYSTEM_MODE=debug  # debug | operational
PLATFORM_BASE_URL=https://api.yourplatform.com
PLATFORM_API_KEY=your_api_key
PLATFORM_APP_ID=academicguard
PRICE_PER_100_WORDS=2.0
MINIMUM_CHARGE=50.0
JWT_SECRET_KEY=your-secret-key
```

#### 结果 | Result
双模式系统完整实现，默认为调试模式（免登录、免支付），可通过环境变量切换为运营模式。所有中央平台预留接口已完整文档化，便于后续对接。

Dual-mode system fully implemented. Default debug mode (no login/payment), switchable to operational mode via env var. All platform interfaces documented for future integration.

---

### 2026-01-04 - 禁止学术写作中使用第一人称代词 | Prohibit First-Person Pronouns in Academic Writing

#### 需求 | Requirements
用户反馈：在学术化级别(Level 0-5)的LLM建议中，生成了过多的第一人称代词(I, we, my, our, us, me)。学术论文不应使用第一人称代词，需要使用被动语态或非人称结构(如"this study", "the analysis")。

User feedback: LLM suggestions in academic levels (0-5) contained too many first-person pronouns. Academic papers should avoid first-person pronouns and use passive voice or impersonal constructs instead.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/suggester/llm_track.py` | 在STYLE_GUIDES中为每个学术级别(0-5)添加"STRICTLY FORBIDDEN: First-person pronouns"规则；添加专门的FIRST-PERSON PRONOUN RULES section (行211-217) |
| `src/core/validator/quality_gate.py` | 新增ACADEMIC_LEVEL_THRESHOLD=5常量；新增FIRST_PERSON_PRONOUNS集合；新增`_check_first_person_pronouns()`方法；修改`verify_suggestion()`增加人称检查 |
| `src/api/routes/session.py` | 在`yolo_auto_process()`中集成QualityGate验证，拒绝包含第一人称代词的LLM建议 |

#### 技术细节 | Technical Details

```python
# quality_gate.py
ACADEMIC_LEVEL_THRESHOLD = 5  # Level 0-5 prohibits first-person pronouns
FIRST_PERSON_PRONOUNS = {"i", "we", "my", "our", "us", "me", "myself", "ourselves"}

def verify_suggestion(self, original, suggestion, colloquialism_level=4):
    if colloquialism_level <= ACADEMIC_LEVEL_THRESHOLD:
        pronouns_found = self._check_first_person_pronouns(suggestion)
        if pronouns_found:
            return SuggestionValidationResult(passed=False, action="retry_without_pronouns", ...)
```

#### 结果 | Result
测试验证：原始文本包含多个第一人称代词(Our research, we have demonstrated, We believe)，修改后的文本全部使用非人称结构：
- "Our research examines..." → "This research examines..."
- "we have demonstrated..." → "Deep learning models demonstrate..."
- "Our comprehensive analysis..." → "The analysis highlights..."
- "We believe..." → "These findings may encourage..."

所有4个句子成功消除第一人称代词，风险分数平均降低51.2分。

---

### 2026-01-04 - 修复缓存持久化问题 | Fix Cache Persistence Issue

#### 问题 | Problem
服务器重启后，Step 1-1 的分析缓存丢失，导致 Step 1-2 报错 "Step 1-1 (structure analysis) must be completed first"。

After server restart, Step 1-1 analysis cache was lost, causing Step 1-2 to fail with "Step 1-1 (structure analysis) must be completed first".

#### 原因 | Cause
SQLAlchemy 的 JSON 字段在原地修改时不会自动检测变化。需要使用 `flag_modified()` 显式标记字段已修改。

SQLAlchemy JSON fields don't automatically detect in-place modifications. Need to use `flag_modified()` to explicitly mark fields as modified.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/api/routes/structure.py` | 添加 `flag_modified` 导入；在所有缓存写入处添加 `flag_modified(document, 'structure_analysis_cache')` |
| `src/api/routes/structure_guidance.py` | 添加 `flag_modified` 导入；在缓存写入处添加 `flag_modified()` |

#### 技术细节 | Technical Details

```python
from sqlalchemy.orm.attributes import flag_modified

# 修改 JSON 字段后必须调用
document.structure_analysis_cache[cache_key] = result
flag_modified(document, 'structure_analysis_cache')
await db.commit()
```

#### 结果 | Result
现在所有分析缓存都会正确保存到 SQLite 数据库，服务器重启后数据不会丢失。

All analysis caches are now correctly persisted to SQLite database and survive server restarts.

---

### 2026-01-04 - Step1-1 合并修改功能 | Step1-1 Merge Modify Feature

#### 需求 | Requirements
在 Step1-1 的上传文件与改进建议之间，增加"合并修改"功能：
1. 在分析出的问题前面加上复选框，用户可以选择多个问题
2. 提供两个选项：AI直接修改 和 AI生成修改提示词
3. 点击按钮后确认选定的问题，让用户补充注意事项（可选）
4. 合并所选问题生成提示词，注意用户选择的口语化等级
5. AI直接修改可重新生成，限制3次

Add "Merge Modify" feature between file upload and improvement suggestions in Step1-1:
1. Add checkboxes before each issue for multi-selection
2. Two options: AI Direct Modify and Generate Prompt
3. Confirm selected issues and allow user notes (optional)
4. Generate combined prompt respecting colloquialism level
5. AI Direct Modify can regenerate up to 3 times

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/api/schemas.py` | 新增 `SelectedIssue`, `MergeModifyRequest`, `MergeModifyPromptResponse`, `MergeModifyApplyResponse` 模型 |
| `src/api/routes/structure.py` | 新增 `POST /merge-modify/prompt` 和 `POST /merge-modify/apply` 端点；添加 `MERGE_MODIFY_PROMPT_TEMPLATE`、`MERGE_MODIFY_APPLY_TEMPLATE` 和 `STYLE_LEVEL_DESCRIPTIONS` |
| `frontend/src/services/api.ts` | `structureApi` 新增 `mergeModifyPrompt()` 和 `mergeModifyApply()` 方法 |
| `frontend/src/pages/Step1_1.tsx` | 添加问题复选框、全选功能、合并修改按钮、确认对话框、结果展示、重新生成和采纳功能 |

#### 技术细节 | Technical Details

**后端 API:**
- `POST /structure/merge-modify/prompt`: 生成合并修改提示词
  - 输入：documentId, sessionId, selectedIssues, userNotes
  - 输出：prompt, promptZh, issuesSummaryZh, colloquialismLevel, estimatedChanges
- `POST /structure/merge-modify/apply`: 直接调用 LLM 修改文档
  - 输入：同上
  - 输出：modifiedText, changesSummaryZh, changesCount, issuesAddressed, remainingAttempts

**口语化级别集成:**
- 从 session 获取用户设置的 colloquialism_level
- 使用 STYLE_LEVEL_DESCRIPTIONS (0-10级) 描述目标风格
- LLM 提示词要求保持目标风格级别

**前端交互流程:**
1. 用户勾选要修改的问题（支持全选）
2. 点击"生成修改提示词"或"AI直接修改"
3. 弹出确认对话框，显示选中的问题，允许输入注意事项
4. 确认后调用相应 API
5. 显示结果：
   - 提示词模式：显示可复制的提示词
   - 直接修改模式：显示修改后的文本，可重新生成（最多3次），点击"采纳修改"将文本填入修改区域

#### 结果 | Result
用户现在可以在 Step1-1 页面选择多个结构问题，使用AI批量生成修改提示词或直接获得修改后的文档，显著提高修改效率。

Users can now select multiple structure issues in Step1-1, use AI to batch generate modification prompts or directly get modified documents, significantly improving modification efficiency.

---

### 2026-01-04 - 改写示例语言一致性 | Rewrite Example Language Consistency

#### 需求 | Requirements
修改后的部分应与原文语言保持一致。即如果原文是英文，改写示例也应该是英文；如果原文是中文，改写示例也应该是中文。

Rewritten examples should match the language of the original text. If original is English, rewrite in English. If original is Chinese, rewrite in Chinese.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/smart_structure.py` | 修改 `rewrite_example` 字段说明，要求与原文语言保持一致；添加中英文示例 |

#### 技术细节 | Technical Details

**修改前:**
```
- **rewrite_example** (Optional - in English):
  A rewritten version of the first 1-2 sentences in English showing how to improve.
```

**修改后:**
```
- **rewrite_example** (IMPORTANT - same language as original):
  A rewritten version of the first 1-2 sentences showing how to improve.
  MUST be in the SAME LANGUAGE as the original paragraph text.
  If original is English, write in English. If original is Chinese, write in Chinese.
```

#### 结果 | Result
LLM 生成的改写示例现在会与原文语言保持一致，提升用户体验。

LLM-generated rewrite examples now match the language of the original text, improving user experience.

---

### 2026-01-03 - ONNX PPL 集成与口语化级别贯穿 | ONNX PPL Integration & Colloquialism Level Throughout

#### 需求 | Requirements
1. 将 ONNX 模型计算的 PPL（困惑度）真正用于风险评分公式
2. 在前端 UI 显示 PPL 分析结果，包括风险等级着色和 emoji
3. 口语化级别选择要贯穿全部步骤，不仅是结构分析

User requirements:
1. Use ONNX model PPL (perplexity) in the risk scoring formula
2. Display PPL analysis results in frontend UI with risk-based coloring and emoji
3. Colloquialism level selection should be applied throughout all steps, not just structure analysis

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/scorer.py` | 添加 `ppl_contribution` 到评分公式 (0-20分)；高风险 PPL 加15-20分，中风险加5-15分 |
| `frontend/src/components/editor/SentenceCard.tsx` | 新增 `PPLIndicator` 组件，显示 PPL 值、风险着色和 emoji (🤖/⚠️/👍) |
| `src/core/analyzer/smart_structure.py` | 添加 `StyleAnalysis` 模型和风格分析功能，检测文档实际风格与目标口语化级别的不匹配 |
| `src/api/routes/structure.py` | 接收 session_id 参数，获取用户的 colloquialism_level 进行风格分析 |
| `src/api/schemas.py` | `DocumentStructureRequest` 添加 `session_id` 字段 |
| `src/api/routes/suggest.py` | 修复硬编码的 `tone_level=4`，改为使用用户设置的 `colloquialism_level` |
| `frontend/src/services/api.ts` | `analyzeStep1_1` 添加 `sessionId` 参数 |
| `frontend/src/pages/Step1_1.tsx` | 传递 sessionId 到结构分析，显示风格不匹配警告 |

#### 技术细节 | Technical Details

**CAASS v2.0 Phase 2 评分公式:**
```
raw_score = context_baseline + fingerprint_score + structure_score + ppl_contribution
total_score = raw_score - human_deduction
```

**PPL 贡献分计算:**
- `ppl_risk == "high"` (PPL < 20): 加 15-20 分
- `ppl_risk == "medium"` (PPL 20-40): 加 5-15 分
- `ppl_risk == "low"` (PPL > 40): 不加分

**PPL 来源优先级:**
1. ONNX 模型 (distilgpt2): 真实 token 级困惑度
2. zlib 压缩比: 后备方案

**风格分析:**
- 检测文档实际风格等级 (0-10)
- 与用户选择的 colloquialism_level 比较
- 差距超过 3 级则生成不匹配警告

**PPLIndicator 组件:**
- 高风险 (🤖): 红色，表示强 AI 特征
- 中风险 (⚠️): 橙色，表示有 AI 特征
- 低风险 (👍): 绿色，表示文本自然

#### 结果 | Result
- PPL 现在真正参与风险评分，AI 特征文本会获得更高分数
- 前端清晰显示 PPL 风险等级，帮助用户理解评分依据
- 口语化级别选择现在贯穿 Level 1 结构分析和 Level 3 句子改写

PPL now contributes to risk scoring, AI-like text receives higher scores. Frontend clearly displays PPL risk levels, helping users understand scoring rationale. Colloquialism level now applies throughout Level 1 structure analysis and Level 3 sentence rewriting.

---

### 2026-01-03 - Step1-1 文档修改功能 | Step1-1 Document Modification

#### 需求 | Requirements
在 Step1-1 分析结果下面，提供上传新文件或输入新内容的功能，用户可以根据建议修改文档后上传继续处理。

Add document upload/input functionality below Step1-1 analysis results, allowing users to modify and upload revised documents based on suggestions.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/Step1_1.tsx` | 新增文档修改区域：上传文件/粘贴文本；"确定修改并继续"和"跳过"按钮；移除原有的"跳过此步"和"继续 Step1-2"按钮 |

#### 技术细节 | Technical Details

**新增功能:**
- 文件上传模式：支持 TXT/DOCX 格式
- 文本粘贴模式：直接输入修改后的内容
- "确定修改并继续"：上传新文档，用新文档 ID 继续 step1-2
- "跳过，使用原文档继续"：使用原文档继续 step1-2

**交互流程:**
1. 用户查看结构分析结果和建议
2. 如果需要修改：上传修改后的文件或粘贴文本 → 点击"确定修改并继续"
3. 如果不需要修改：点击"跳过，使用原文档继续"

#### 结果 | Result
用户现在可以在 Step1-1 页面根据分析建议修改文档，并上传修改后的版本继续后续处理流程。

Users can now modify their document based on Step1-1 analysis suggestions and upload the revised version to continue processing.

---

### 2026-01-03 - 任务步骤持久化与恢复 | Task Step Persistence & Resume

#### 需求 | Requirements
实现历史任务的步骤状态持久化，用户从历史页面恢复任务时能跳转到正确的步骤，并保留之前的分析结果和建议。

Implement task step state persistence so users can resume from the correct step when restoring tasks from history, preserving previous analysis results and suggestions.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/db/models.py` | Session 模型新增 `current_step` 字段 (step1-1, step1-2, level2, level3, review) |
| `src/api/schemas.py` | SessionInfo 新增 `current_step` 字段 |
| `src/api/routes/session.py` | 新增 `POST /{session_id}/step/{step}` API；list 接口返回 current_step；complete 时自动设为 review |
| `frontend/src/types/index.ts` | 新增 `SessionStep` 类型；SessionInfo 新增 currentStep |
| `frontend/src/services/api.ts` | sessionApi 新增 `updateStep()` 方法 |
| `frontend/src/pages/History.tsx` | 根据 currentStep 导航到正确页面；显示当前步骤标签 |
| `frontend/src/pages/Upload.tsx` | 上传后创建 session 并传递 sessionId 到后续流程 |
| `frontend/src/pages/Step1_1.tsx` | 加载时更新 step；导航传递 sessionId |
| `frontend/src/pages/Step1_2.tsx` | 加载时更新 step；导航传递 sessionId |
| `frontend/src/pages/Level2.tsx` | 加载时更新 step；根据 mode 导航到 intervention/yolo |
| `frontend/src/pages/Intervention.tsx` | 加载时更新 step 为 level3 |
| `frontend/src/pages/Yolo.tsx` | 加载时更新 step 为 level3 |

#### 技术细节 | Technical Details

**步骤流转:**
- Upload -> step1-1 (创建 session，开始跟踪)
- step1-1 -> step1-2 -> level2 -> level3 (intervention/yolo) -> review
- 每个页面加载时调用 `sessionApi.updateStep()` 更新当前步骤

**历史恢复逻辑:**
- 任务卡片显示当前步骤标签 (L1-结构分析, L1-段落分析, L2-衔接优化, L3-句子处理, 审核完成)
- 点击恢复根据 currentStep 导航到对应页面

**数据保留:**
- 文档内容: `Document.original_text`
- 分析结果: `Document.structure_analysis_cache`, `transition_analysis_cache`
- 会话状态: `Session.current_step`, `current_index`, `config_json`

#### 结果 | Result
用户现在可以从历史页面恢复任务到正确的步骤，所有之前的分析结果和进度都会保留。

Users can now resume tasks from history to the correct step, with all previous analysis results and progress preserved.

---

### 2026-01-03 - 历史页面重构为统一任务列表 | History Page Refactored to Unified Task List

#### 需求 | Requirements
将历史页面的"会话列表"和"文档列表"两个 tabs 合并为一个统一的"任务列表"，展示所有任务的状态、文档、进度等信息。

Merge "Session List" and "Document List" tabs in the history page into a unified "Task List" that displays all task status, documents, progress, and other information.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/History.tsx` | 完全重构：移除 tabs 切换，创建统一的 TaskItem 接口合并会话和文档信息，任务卡片显示状态、模式、风险等级、处理进度，添加刷新按钮 |

#### 技术细节 | Technical Details

**TaskItem 统一数据结构:**
- 合并 SessionInfo 和 DocumentInfo 的关键字段
- 包含：sessionId, documentId, documentName, mode, status, progress, risk counts

**任务卡片布局:**
- 顶部：文档名、状态图标、模式标签、创建时间、删除按钮
- 中部：风险等级徽章（高/中/低风险数量）
- 底部：处理进度条、继续/查看按钮

**视觉优化:**
- 左侧边框颜色编码（绿=完成，蓝=进行中，黄=暂停，灰=待处理）
- 刷新按钮便于重新加载数据

#### 结果 | Result
历史页面现在展示统一的任务列表，用户可以一目了然地查看所有任务的完整状态和进度。

History page now displays a unified task list where users can see the complete status and progress of all tasks at a glance.

---

### 2026-01-03 - 上传页面模式提示 | Upload Page Mode Hint

#### 需求 | Requirements
在文件上传页面的模式选择区域添加提示信息，说明 YOLO 模式和干预模式的适用场景。

Add hint text in the mode selection area on the upload page to explain the applicable scenarios for YOLO mode and Intervention mode.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/Upload.tsx:292-294` | 新增：模式选择下方添加提示"💡 YOLO模式仅适用于灌水文章，想认真改的请用干预模式" |

#### 结果 | Result
上传页面现在会在模式选择区域显示提示信息，帮助用户选择合适的处理模式。

Upload page now displays a hint in the mode selection area to help users choose the appropriate processing mode.

---

### 2026-01-03 - 僵尸代码激活与清理 | Zombie Code Activation & Cleanup

#### 需求 | Requirements
对代码库进行审计，发现多处"僵尸代码"（已编写但未集成使用的功能）。根据价值评估完成三项任务：
1. 激活 ParagraphLogicPanel 段落级分析组件（填补分析层级空白，价值最高）
2. 清理 `_analyze_document_task` 空函数（消除技术债务）
3. 为 `/risk-card` API 开发前端组件 StructuralRiskCard（提升可视化效果）

Audit codebase for zombie code (written but not integrated features). Based on value assessment, complete 3 tasks:
1. Activate ParagraphLogicPanel paragraph-level analysis component (fills analysis gap, highest value)
2. Clean up `_analyze_document_task` empty function (eliminate tech debt)
3. Develop StructuralRiskCard frontend component for `/risk-card` API (enhance visualization)

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/types/index.ts` | 新增：`StructuralIndicator`, `StructuralRiskCardResponse` 类型；`citation_entanglement` 添加到策略类型 |
| `frontend/src/services/api.ts` | 新增：`structureApi.getRiskCard()` 方法调用 `/structure/risk-card` API |
| `frontend/src/components/editor/ParagraphLogicPanel.tsx` | 修改：添加 `citation_entanglement` 策略信息和 UI 支持 |
| `frontend/src/components/editor/StructuralRiskCard.tsx` | 新增：7 指标风险卡片可视化组件，含 emoji、星级评分、详情展开 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 修改：集成 ParagraphLogicPanel（段落选择、分析、重构）和 StructuralRiskCard（风险卡片获取和展示） |
| `src/api/routes/analyze.py` | 修改：`_analyze_document_task` 添加弃用说明和日志警告 |

#### 技术细节 | Technical Details

**ParagraphLogicPanel 集成:**
- 新增段落选择 UI：用户可选择要分析的段落范围
- 调用 `/api/v1/paragraph/analyze` 进行逻辑分析
- 调用 `/api/v1/paragraph/restructure` 应用重构策略
- 支持 6 种策略：subject_diversity, sentence_variation, non_linear, citation_entanglement, combined, custom

**StructuralRiskCard 组件:**
- 7 个 AI 结构指标可视化：对称性、均匀性、连接词依赖、线性化、节奏、闭合、回指
- 触发状态徽章（触发/OK）
- 风险等级星级显示（★★☆）
- 整体风险颜色编码（红/黄/绿）
- 可展开详情说明

**弃用函数处理:**
- `_analyze_document_task` 标记为 DEPRECATED
- 添加日志警告，记录调用情况
- 保留函数但不实现，便于未来决策

#### 结果 | Result
- 段落级分析：ThreeLevelFlow 页面支持段落选择和 6 种重构策略
- 风险可视化：一键获取 7 指标结构风险卡片
- 技术债务：弃用函数已标记，不影响正常功能
- 代码质量：消除了三处主要的僵尸代码问题

---

### 2026-01-03 - 引用句法纠缠功能激活 | Citation Entanglement Activation

#### 需求 | Requirements
修复引用句法纠缠 (Citation Entanglement) 功能的三个问题，使其从"僵尸代码"变为可用功能：
1. 问题A：分析器未检测引用 - ParagraphLogicAnalyzer 缺少引用检测逻辑
2. 问题B：API未暴露策略 - `restructure_paragraph` 接口的 strategy 参数缺少 "citation_entanglement"
3. 问题C：句子级改写未集成 - `llm_track.py` 缺少引用处理指令

Fix three issues in Citation Entanglement feature to make it functional:
1. Issue A: Analyzer not detecting citations - ParagraphLogicAnalyzer missing citation detection
2. Issue B: API not exposing strategy - restructure_paragraph endpoint missing "citation_entanglement" strategy
3. Issue C: Sentence-level rewrite not integrated - llm_track.py missing citation handling instructions

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/paragraph_logic.py` | 新增：CITATION_PATTERNS 正则表达式，`_check_citation_pattern()` 方法检测括号引用，`get_citations_for_entanglement()` 便捷方法 |
| `src/api/routes/paragraph.py` | 修改：`ParagraphRestructureRequest.strategy` 类型新增 "citation_entanglement"，新增 `citations_found` 参数，添加策略处理逻辑和响应解析 |
| `src/prompts/paragraph_logic.py` | 修改：`STRATEGY_DESCRIPTIONS` 新增 citation_entanglement 描述 |
| `src/core/suggester/llm_track.py` | 新增：第12条 DE-AIGC 技巧 "CITATION ENTANGLEMENT (引用句法纠缠)" 到 Prompt 中 |

#### 结果 | Result
- 引用检测：自动识别括号引用 (Author, Year) 模式，检测是否为 AI 式写作
- API 可用：`/api/v1/paragraph/restructure` 接口支持 `strategy: "citation_entanglement"`
- 句子级改写：单句润色时也会考虑引用格式的优化
- 测试验证：`POST /analyze` 成功检测出 `citation_pattern` 问题类型

---

### 2026-01-02 - 改进报告实施 | Improvement Report Implementation

#### 需求 | Requirements
根据 `doc/improve-analysis-report.md` 审计报告实施四项优化：
1. [HIGH] PPL 检测内核升级 - 从 zlib 压缩比升级到 ONNX 真实困惑度
2. [MEDIUM] 有意的不完美 - 在 Prompt 中增加人类化瑕疵指令
3. [MEDIUM] 引用句法纠缠 - 将 30% 括号引用转换为叙述引用
4. [LOW] 指纹词库扩充 - 添加报告建议的短语检测项

Based on `doc/improve-analysis-report.md` audit report, implementing 4 optimizations:
1. [HIGH] PPL detection core upgrade - from zlib compression ratio to ONNX true perplexity
2. [MEDIUM] Intentional imperfection - add human-like flaw instructions to Prompts
3. [MEDIUM] Citation entanglement - transform 30% parenthetical citations to narrative form
4. [LOW] Fingerprint dictionary expansion - add suggested phrase patterns from report

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/ppl_calculator.py` | 新增：ONNX PPL 计算器模块，使用 distilgpt2 计算真实 token 级困惑度 |
| `src/core/analyzer/scorer.py` | 修改：`_calculate_ppl()` 优先使用 ONNX，失败回退 zlib；新增 `_calculate_ppl_zlib()` |
| `src/core/analyzer/fingerprint.py` | 修改：PHRASE_PATTERNS 新增 10 个 AI 特征短语 |
| `src/prompts/paragraph_logic.py` | 修改：新增 "有意的不完美" 策略；新增 `get_citation_entanglement_prompt()` 函数 |
| `src/core/suggester/llm_track.py` | 修改：`_build_prompt()` 新增第 11 条 INTENTIONAL IMPERFECTION 技术 |
| `scripts/download_onnx_model.py` | 新增：ONNX 模型下载和转换脚本 |
| `requirements.txt` | 修改：添加 onnxruntime、tokenizers 可选依赖 |

#### 技术细节 | Technical Details

**PPL 检测升级 PPL Detection Upgrade:**
- 使用 distilgpt2 ONNX 模型计算 token 级困惑度
- 懒加载模式：首次调用时加载模型，后续复用
- 优雅降级：ONNX 不可用时自动回退 zlib 压缩比
- 可检测 "语义平庸但词汇丰富" 的高级 AI 文本

**有意的不完美 Intentional Imperfection:**
- 偶尔以连词开头 (And, But, So) - 约 10-15% 句子
- 使用破折号打断思路
- 允许略松散语法 ("Which is why this matters.")
- 添加口语化学术表达 ("frankly", "to put it simply")

**引用句法纠缠 Citation Entanglement:**
- 新策略: `citation_entanglement`
- 叙述引用: "Smith (2023) argues that..."
- 权威引用: "According to Smith (2023),..."
- 嵌入引用: "Smith's (2023) groundbreaking study..."
- 保留约 70% 括号引用以保持自然变化

**指纹词库扩充 Fingerprint Expansion:**
- "is characterized by" → "features / involves"
- "can be described as" → "is effectively"
- "with regard to" → "concerning"
- "in light of" → "given / considering"
- 以及 6 个其他 AI 特征短语

#### 使用说明 | Usage

**启用 ONNX PPL Enable ONNX PPL:**
```bash
# 1. 安装依赖 Install dependencies
pip install onnxruntime tokenizers

# 2. 下载模型 Download model
python scripts/download_onnx_model.py

# 3. 重启服务 Restart server
# 系统会自动检测并使用 ONNX 模型
```

#### 结果 | Results
- 检测端能力提升：可检测高质量 AI 文本（GPT-4 等）
- 改写策略增强：6 种新技术/策略添加
- 指纹词库扩充：10 个新短语模式

### 2026-01-03 - ONNX 模型安装完成 | ONNX Model Installation Complete

#### 安装内容 | Installed Components
- `onnxruntime 1.16.3` - ONNX 运行时
- `tokenizers 0.13.3` - Hugging Face 分词器
- `distilgpt2.onnx` (313 MB) - 预转换 ONNX 模型 (from Xenova/distilgpt2)
- `tokenizer.json` (1.3 MB) - GPT-2 分词器配置

#### 修改内容 | Changes
| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/ppl_calculator.py` | 更新：支持 Transformers.js 风格 ONNX 模型输入（添加 attention_mask, position_ids, past_key_values） |

#### 测试结果 | Test Results
```
AI-like text PPL: 25.26 (lower = more predictable)
Human-like text PPL: 50.61 (higher = more surprising)
[OK] ONNX PPL correctly identifies AI text as more predictable!
```

#### 状态 | Status
所有四项改进报告任务已完成：
All four improvement report tasks completed:

| Task | Status |
|------|--------|
| Task 1: PPL 内核升级 (ONNX) | ✅ 完成 |
| Task 2: 有意的不完美 | ✅ 完成 |
| Task 3: 引用句法纠缠 | ✅ 完成 |
| Task 4: 指纹词库扩充 | ✅ 完成 |

---

### 2026-01-02 - 4步独立页面架构 | 4-Step Independent Page Architecture

#### 需求 | Requirements
将处理流程拆分为4个独立页面，每步单独一个页面：
- Step 1-1: 全文结构分析页面
- Step 1-2: 段落关系分析页面
- Level 2: 段落衔接分析页面
- Level 3: 跳转到句子精修页面（Intervention）

Split the processing flow into 4 independent pages, one page per step:
- Step 1-1: Document Structure Analysis page
- Step 1-2: Paragraph Relationship Analysis page
- Level 2: Transition Analysis page
- Level 3: Jump to Sentence Polish page (Intervention)

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/Step1_1.tsx` | 新增：Step 1-1 独立页面，调用 structureApi.analyzeStep1_1()，显示结构分数和问题 |
| `frontend/src/pages/Step1_2.tsx` | 新增：Step 1-2 独立页面，调用 structureApi.analyzeStep1_2()，显示连接词、逻辑断层、高风险段落 |
| `frontend/src/pages/Level2.tsx` | 新增：Level 2 独立页面，调用 transitionApi.analyzeDocument()，显示衔接分析和修复选项 |
| `frontend/src/App.tsx` | 新增路由：/flow/step1-1/:documentId, /flow/step1-2/:documentId, /flow/level2/:documentId |
| `frontend/src/pages/Upload.tsx` | 修改：上传后导航到 /flow/step1-1/:documentId 而非旧的 /flow/:documentId |

#### 功能说明 | Feature Description

**新路由结构 New Routing Structure:**
```
Upload → /flow/step1-1/:documentId?mode=intervention|yolo
         → /flow/step1-2/:documentId?mode=intervention|yolo
         → /flow/level2/:documentId?mode=intervention|yolo
         → /intervention/:documentId?mode=intervention|yolo
```

**页面导航 Page Navigation:**
- Step 1-1: 返回上传 / 继续到 Step 1-2
- Step 1-2: 返回 Step 1-1 / 继续到 Level 2
- Level 2: 返回 Step 1-2 / 继续到 Level 3 (Intervention)

**进度指示器 Progress Indicator:**
每个页面顶部显示流程进度：Step 1-1 → Step 1-2 → Level 2 → Level 3

---

### 2026-01-02 - Step 1 拆分为 Step 1-1 和 Step 1-2 | Split Step 1 into Step 1-1 and Step 1-2

#### 需求 | Requirements
将 Step 1 (Level 1) 拆分为两个独立的子步骤，每步单独调用 LLM：
- Step 1-1: 全文结构分析（章节划分、段落结构、全局模式）
- Step 1-2: 段落关系分析（显性连接词、逻辑断层、段落AI风险）

Split Step 1 (Level 1) into two independent sub-steps, each calling LLM separately:
- Step 1-1: Document Structure Analysis (sections, paragraphs, global patterns)
- Step 1-2: Paragraph Relationship Analysis (explicit connectors, logic breaks, paragraph AI risks)

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/analyzer/smart_structure.py` | 新增：STRUCTURE_ANALYSIS_PROMPT 和 RELATIONSHIP_ANALYSIS_PROMPT 提示词；新增 analyze_structure() 和 analyze_relationships() 方法 |
| `src/api/routes/structure.py` | 新增：/document/step1-1 和 /document/step1-2 两个 API 端点 |
| `frontend/src/services/api.ts` | 新增：analyzeStep1_1() 和 analyzeStep1_2() 方法 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 重构：ProcessingLevel 类型改为 4 步 (step1_1/step1_2/level_2/level_3)；新增 step1_1Result/step1_2Result 状态；新增 Step 1-1 和 Step 1-2 UI 区域；更新 YOLO 模式处理逻辑 |

#### 功能说明 | Feature Description

**处理流程 Processing Flow:**
```
Step 1-1: 全文结构分析 → Step 1-2: 段落关系分析 → Level 2: 段落衔接 → Level 3: 句子精修
```

**Step 1-1 输出 Step 1-1 Output:**
- 章节划分 (sections)
- 段落信息 (paragraphs)
- 结构风险分数 (structureScore)
- 结构问题列表 (structureIssues)
- 改进建议 (recommendationZh)

**Step 1-2 输出 Step 1-2 Output:**
- 显性连接词 (explicitConnectors)
- 逻辑断层 (logicBreaks)
- 段落AI风险 (paragraphRisks)
- 关系风险分数 (relationshipScore)
- 关系问题列表 (relationshipIssues)

**YOLO 模式更新 YOLO Mode Updates:**
- 自动执行 Step 1-1 结构分析
- 自动执行 Step 1-2 关系分析
- 继续 Level 2 和 Level 3 处理
- 处理日志显示 4 个步骤进度

---

### 2026-01-02 - 流程重组：统一三层级处理入口 | Flow Refactor: Unified Three-Level Entry

#### 需求 | Requirements
重新组织处理流程关系：
- 论文降AIGC默认从 Step 1 (Level 1) 开始
- 移除直接跳到干预模式(Level 3)的选项
- YOLO模式也从 Step 1 开始，链式自动处理
- 文本级联：每一步使用上一步处理后的文本

Refactor processing flow:
- Paper de-AIGC starts from Step 1 (Level 1) by default
- Remove option to jump directly to intervention mode (Level 3)
- YOLO mode also starts from Step 1 with chained auto-processing
- Text cascading: each step uses text from previous step

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/Upload.tsx` | 移除"深度模式"选项，保留"干预模式"和"YOLO模式"两个选项，两者都导航到 /flow/:documentId |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 新增：支持 mode URL 参数 (intervention/yolo)；新增 YOLO 警告弹窗；新增 YOLO 自动处理逻辑和处理日志显示 |
| 多个组件文件 | 清理未使用的导入和变量 |

#### 功能说明 | Feature Description

**处理模式 Processing Modes:**
- **干预模式 Intervention Mode**: 三级流程 L1→L2→L3，每一步手动选择方案
- **YOLO模式 YOLO Mode**: 三级流程 L1→L2→L3，全自动处理，最后统一审核

**YOLO 模式特性 YOLO Mode Features:**
- 开始前显示警告弹窗，提示 AI 自动处理不保证完全可靠
- 实时处理日志显示各层级处理进度
- 自动选择最佳方案并应用
- 处理完 L1/L2 后自动跳转到句子级处理页面 (L3)

**流程架构 Flow Architecture:**
```
Upload → /flow/:documentId?mode=intervention|yolo
         ├── Level 1: 结构分析（自动/手动）
         ├── Level 2: 衔接分析（自动/手动）
         └── Level 3: 句子精修
             ├── 干预模式 → /intervention/:sessionId
             └── YOLO模式 → /yolo/:sessionId
```

---

### 2026-01-02 - Level 1 指引式交互实现 | Level 1 Guided Interaction Implementation

#### 需求 | Requirements
将 Level 1（骨架重组）从"仅给意见"改为"指引式交互"：
- 针对具体问题提供详细改进意见
- 可以给出参考版本时提供参考版本（如替换显性连接词）
- 类似 Level 3 Track C 的用户输入框
- 不适合给参考版本的问题只提供建议（如扩展段落）
- 结构问题优先显示，段落关系问题其次
- 展开具体问题时按需调用 LLM

Transform Level 1 (Structure Analysis) from "opinion-only" to "guided interaction":
- Detailed improvement suggestions for specific issues
- Reference versions when feasible (e.g., replacing explicit connectors)
- User input box similar to Level 3 Track C
- Advice-only for issues where references aren't practical (e.g., expand paragraph)
- Structure issues displayed first, then transition issues
- LLM called on-demand when expanding specific issues

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/prompts/structure_guidance.py` | 新增：结构指引提示词模板，定义可参考/仅建议的问题类型 |
| `src/api/schemas.py` | 新增：StructureIssueItem, IssueGuidanceRequest/Response, ApplyStructureFixRequest/Response, ReorderSuggestionRequest/Response 等 schemas |
| `src/api/routes/structure_guidance.py` | 新增：/issues, /guidance, /apply-fix, /reorder-suggestion 四个 API 端点 |
| `src/api/routes/__init__.py` | 添加 structure_guidance 模块导入 |
| `src/main.py` | 注册 structure-guidance 路由 |
| `frontend/src/types/index.ts` | 新增：StructureIssueItem, IssueGuidanceResponse 等 TypeScript 类型 |
| `frontend/src/services/api.ts` | 新增：structureGuidanceApi 服务（getIssues, getGuidance, applyFix, getReorderSuggestion） |
| `frontend/src/components/editor/StructureIssueCard.tsx` | 新增：可展开的问题卡片组件，支持获取指引、显示参考版本、用户输入 |
| `frontend/src/components/editor/StructureGuidedPanel.tsx` | 新增：Level 1 指引面板主组件，分类显示结构/衔接问题 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 修改：Level 1 部分使用 StructureGuidedPanel 替换原 StructurePanel |

#### 功能说明 | Feature Description

**问题分类 Issue Categories:**
- **结构问题 Structure Issues**: linear_flow (线性流程), uniform_length (均匀长度), predictable_structure (可预测结构)
- **衔接问题 Transition Issues**: explicit_connector (显性连接词), missing_semantic_echo (缺少语义回声), logic_gap (逻辑断裂), paragraph_too_short/long (段落长度)

**可生成参考版本 Can Generate Reference:**
- explicit_connector: 用语义回声替换显性连接词
- linear_flow: 打乱顺序建议
- predictable_structure: 结构变化建议
- missing_semantic_echo: 添加语义连接
- formulaic_opening: 改写开头
- weak_transition: 增强过渡

**仅提供建议 Advice Only:**
- uniform_length: 需要用户决定扩展/精简哪些段落
- paragraph_too_short/long: 需要用户领域知识
- logic_gap: 需要理解内容上下文

**API 端点 API Endpoints:**
- `POST /api/v1/structure-guidance/issues` - 获取分类问题列表（轻量级，不调用LLM）
- `POST /api/v1/structure-guidance/guidance` - 获取具体问题的详细指引（调用LLM）
- `POST /api/v1/structure-guidance/apply-fix` - 应用修复
- `POST /api/v1/structure-guidance/reorder-suggestion` - 获取段落重排建议

#### 结果 | Result
✅ 完成 Completed - API 和前端组件均已实现并通过测试

---

### 2026-01-01 - UX优化与国际化改进 | UX Optimization & i18n Improvements

#### 需求 | Requirements
1. 在等待界面添加预估等待时间显示（根据文档字数）
2. ai_risk_reason 字段改为中文输出（引用原文保留原语言）
3. rewrite_example 字段改为英文输出

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/utils/loadingMessages.ts` | 新增 `estimateWaitTime()` 和 `useCountdownTimer()` 函数用于计算预估时间和倒计时 |
| `frontend/src/components/common/LoadingMessage.tsx` | 添加 `charCount` 和 `showCountdown` 参数，显示预估等待时间 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 集成预估等待时间显示，先获取文档信息用于时间估算 |
| `frontend/src/types/index.ts` | 修改 `ParagraphInfo.rewriteExampleZh` → `rewriteExample` |
| `frontend/src/components/editor/StructurePanel.tsx` | 更新字段名和显示标签 |
| `frontend/src/services/api.ts` | 更新API返回类型定义 |
| `src/core/analyzer/smart_structure.py` | 修改prompt：ai_risk_reason输出中文，rewrite_example输出英文 |
| `src/api/schemas.py` | 修改字段名：`rewrite_example_zh` → `rewrite_example` |
| `src/api/routes/structure.py` | 更新字段映射和prompt模板 |

#### 功能说明 | Feature Description
- **预估等待时间**：基于文档字符数计算（约14字符/秒），显示倒计时
- **时间估算公式**：`估计秒数 = 字符数 / 14 * 1.2`（20%缓冲）
- **超时动态设置**：`超时时间 = 估计秒数 * 1.5`
- **ai_risk_reason**：中文描述AI风险原因，引用原文时保留原语言
- **rewrite_example**：英文改写示例

#### 结果 | Result
✅ 完成 Completed

---

## 开发阶段概览 | Development Phase Overview

> 基于三层级 De-AIGC 架构重新规划 Replanned based on Three-Level De-AIGC Architecture

| Phase | 状态 Status | 完成度 Progress |
|-------|-------------|-----------------|
| Phase 1: Level 3 核心闭环 | ✅ 已完成 Completed | 100% |
| Phase 2: Level 3 增强 | ✅ 已完成 Completed | 100% |
| Phase 3: Level 2 实现 | ✅ 已完成 Completed | 100% |
| Phase 4: Level 1 实现 | ✅ 已完成 Completed | 100% |
| Phase 5: 全流程整合 | ✅ 已完成 Completed | 100% |
| Phase 6: 测试与部署 | ✅ 已完成 Completed | 100% |

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

### 2025-12-31 (Update 29)

**Phase 2: Level 3 增强完成 Phase 2: Level 3 Enhancement Completed:**

- 用户需求：持续开发，完成 Phase 2 后进行测试
- 核心变更：

**1. 新增 Burstiness 检测模块:**
- `src/core/analyzer/burstiness.py`
  - `BurstinessAnalyzer` 类计算句子长度变化
  - 公式：burstiness = std(sentence_length) / mean(sentence_length)
  - 阈值：<0.3 高风险，0.3-0.5 中等风险，>0.5 低风险
  - `BurstinessResult` 数据类包含完整分析结果

**2. 新增显性连接词检测模块:**
- `src/core/analyzer/connector_detector.py`
  - `ConnectorDetector` 类检测 AI 风格连接词
  - 高严重性词：Furthermore, Moreover, Additionally, Consequently 等
  - 中等严重性词：It is important to note, In conclusion 等
  - 提供替换建议

**3. 集成到评分系统:**
- `src/core/analyzer/scorer.py`
  - 导入并初始化 BurstinessAnalyzer 和 ConnectorDetector
  - `SentenceAnalysisResult` 新增字段：burstiness_value, burstiness_risk, connector_count, connector_match
  - `analyze()` 方法集成两个新检测器

**4. 更新 API schemas:**
- `src/api/schemas.py:166-173`
  - `SentenceAnalysis` 新增字段：burstiness_value, burstiness_risk, connector_count, connector_word

**5. 更新后端 API:**
- `src/api/routes/documents.py` - 保存新字段到 analysis_json
- `src/api/routes/session.py:626-632` - 从 analysis_json 读取新字段

**6. 更新前端:**
- `frontend/src/types/index.ts:79-84` - 新增类型字段
- `frontend/src/components/editor/SentenceCard.tsx:240-248` - 新增 ConnectorIndicator 组件

**测试结果 Test Results:**
```
Burstiness: 0.59 (low risk), Score: 0 ✓
Connectors: 3 detected (Furthermore, Moreover, It is important to note) ✓
Frontend build: ✓
```

---

### 2025-12-31 (Update 28)

**三层级 De-AIGC 架构规划 Three-Level De-AIGC Architecture Planning:**

- 用户需求：基于 `improve.md` 分析报告进行后续开发规划，项目仅针对英文学术论文
- 核心变更：

**1. 更新 plan.md 开发计划:**
- 版本升级至 v2.0，明确目标语言为 English Academic Papers Only
- 新增"二、三层级 De-AIGC 架构"章节
  - Level 1: 骨架重组 (Macro Structure) - 全文逻辑诊断、重构方案
  - Level 2: 关节润滑 (Paragraph Transition) - 段落衔接、消灭显性连接词
  - Level 3: 皮肤精修 (Sentence Polish) - 已实现 (CAASS v2.0)
- 定义处理顺序原则：必须按 Level 1 → 2 → 3 顺序处理
- 更新开发阶段规划为 6 个 Phase：
  - Phase 1: Level 3 核心闭环 ✅ 已完成
  - Phase 2: Level 3 增强 (Burstiness 检测、显性连接词检测)
  - Phase 3: Level 2 实现 (滑动窗口段落分析、接缝修补 UI)
  - Phase 4: Level 1 实现 (全文逻辑诊断、逻辑诊断卡 UI)
  - Phase 5: 全流程整合
  - Phase 6: 测试与部署
- 新增 API 设计规范：`/api/v1/analyze/transition`、`/api/v1/analyze/structure`
- 开发周期预估：21-40 天

**2. 更新 process.md 开发进度:**
- 重新规划开发阶段概览表格
- Phase 1 (Level 3 核心闭环) 标记为已完成 100%

**3. 简化 ESL 辅助解释:**
- 移除日语、韩语、西班牙语支持计划
- 保留中文解释作为 ESL 用户辅助
- 明确项目仅处理英文学术论文

**相关文档 Related Documents:**
- `doc/plan.md` - 更新开发计划
- `doc/improve-analysis-report.md` - 分析报告 (已完成)
- `doc/improve.md` - 用户改进建议 (参考)

---

### 2025-01-01 (Update 27)

**修复 Review 页面假数据和 Track B 分数不一致 Fix Review Page Fake Data and Track B Score Inconsistency:**

**1. Review 页面假数据问题 Review Page Fake Data Issue:**
- 问题：用户没有进行任何修改，但 Review 页面显示"72降低到了28"
- 原因：`frontend/src/pages/Review.tsx` 硬编码了假数据
- 解决：
  - 新增后端 API `GET /session/{id}/review-stats`
    - `src/api/routes/session.py:520-580`
    - 返回：总句子数、修改数、平均风险降低分、来源分布
  - 新增前端 API 方法 `sessionApi.getReviewStats()`
    - `frontend/src/services/api.ts:369-377`
  - 更新 Review 页面使用真实数据
    - `frontend/src/pages/Review.tsx:63-77`
    - 简化显示：修改数量 + 平均风险降低分

**2. Track B 分数不一致问题 Track B Score Inconsistency:**
- 问题：相同文本，原文分数34，Track B 分数10
- 原因：
  - 上传时使用 `tone_level=4`（hardcoded in `documents.py:139-144`）
  - 建议生成时使用 `tone_level = colloquialism_level // 2`（variable in `suggest.py:69`）
- 解决：
  - `src/api/routes/suggest.py:65-71`
  - 将 `tone_level` 固定为 4，与文档上传时保持一致
  - 确保评分前后一致

**3. 跨平台日志兼容 Cross-Platform Logging Compatibility:**
- 问题：Windows 控制台 GBK 编码无法显示特殊字符导致 `UnicodeEncodeError`
- 解决：
  - `src/api/routes/suggest.py:6-9,141` - 使用 `logger` 替代 `print`
  - `src/core/analyzer/scorer.py:450-453` - 使用 `logger` 替代 `print`
  - 兼容 Windows GBK 和 Linux UTF-8

**效果 Effects:**
- ✅ Review 页面显示真实统计数据
- ✅ Track A/B 评分与原文评分一致
- ✅ 跨平台日志兼容

---

### 2025-01-01 (Update 26)

**调查轨道B分数问题 Investigate Track B Score Issue:**

- 用户反馈：轨道B显示"无需修改"但分数为0，而原文分数为42
- 用户询问：轨道A/B的分数是否按照原文规则计算

**分析 Analysis:**
1. **轨道A/B评分机制确认**：是的，轨道A和B的分数都使用相同的评分器（RiskScorer）计算
   - `src/api/routes/suggest.py:67-73` - 原文评分
   - `src/api/routes/suggest.py:88-94` - 轨道A评分（对改写后的文本）
   - `src/api/routes/suggest.py:126-132` - 轨道B评分（对改写后的文本）
   - 三者使用相同的参数：tone_level, whitelist, context_baseline

2. **问题根源**：如果轨道B未做修改，rewritten应该等于原文，分数也应该相同。显示0分是一个bug

**修改内容 Changes Made:**
1. **添加调试日志** - `src/api/routes/suggest.py:134-142`
   - 记录轨道B的修改数量
   - 检查文本是否真的相同
   - 比较原文和轨道B的分数

2. **添加评分器调试日志** - `src/core/analyzer/scorer.py:450-453`
   - 打印每次评分的详细组成：上下文基准、指纹分、结构分、人类减分、总分
   - 输出文本预览便于对比

**下一步 Next Steps:**
- 用户需要重启后端，然后查看控制台输出以确定问题根源
- 根据调试输出确定是文本变化问题还是评分器问题

---

### 2025-01-01 (Update 25)

**CAASS v2.0 Phase 2: 上下文感知与白名单机制 Context-Aware and Whitelist Mechanism:**

- 用户需求：实现 CAASS v2.0 第二阶段功能
- 核心变更：

**1. 段落级 PPL 上下文基准 Paragraph-Level PPL Context Baseline:**
- `src/core/analyzer/scorer.py:166-263`
  - 新增 `calculate_text_ppl()` 函数计算文本 PPL（使用 zlib 压缩比作为代理）
  - 新增 `calculate_context_baseline()` 函数返回段落上下文基准分 (0-25分)
    - PPL < 20: 强 AI 信号，+25 分
    - PPL 20-30: 中等 AI 信号，+15 分
    - PPL 30-40: 弱 AI 信号，+8 分
    - PPL > 40: 人类特征，+0 分
  - 新增 `ParagraphContext` 数据类，包含段落文本、PPL、基准分、句子数

**2. 智能白名单提取 Smart Whitelist Extraction:**
- 新增 `src/core/preprocessor/whitelist_extractor.py`
  - `WhitelistExtractor` 类从 Abstract 提取学科特定术语
  - 检测技术复合词、缩写定义、带技术后缀的词汇
  - 内置已知学科术语（remediation, circular economy, biodiversity 等）
  - `extract_from_abstract()` 和 `extract_from_document()` 方法
  - 支持用户自定义白名单合并

**3. 文档处理集成 Document Processing Integration:**
- `src/api/routes/documents.py:68-244, 310-426`
  - 导入 `ParagraphContext`, `calculate_context_baseline`, `WhitelistExtractor`
  - 文档上传时自动提取白名单
  - 使用 `segment_with_paragraphs()` 保留段落信息
  - 新增 `_build_paragraph_contexts()` 函数构建段落上下文
  - `analysis_json` 现在包含 `paragraph_index` 和 `context_baseline`

**4. 会话配置存储 Session Config Storage:**
- `src/api/routes/session.py:84-169, 490-518`
  - 会话启动时提取并存储白名单到 `config_json`
  - 新增 `GET /session/{id}/config` 端点返回白名单和语气等级
  - `config_json` 现在包含 `whitelist` 和 `tone_level`

**5. 建议 API 支持 Suggest API Support:**
- `src/api/schemas.py:55-68`
  - `SuggestRequest` 新增 `whitelist` 和 `context_baseline` 字段
- `src/api/routes/suggest.py:41-162`
  - `get_suggestions()` 端点使用白名单和上下文基准评分
  - 所有 `_scorer.analyze()` 调用现在传递白名单和上下文基准

**6. 前端集成 Frontend Integration:**
- `frontend/src/types/index.ts:75-78`
  - `SentenceAnalysis` 新增 `contextBaseline` 和 `paragraphIndex` 字段
- `frontend/src/services/api.ts:191-212, 347-363`
  - `suggestApi.getSuggestions()` 新增 `whitelist` 和 `contextBaseline` 参数
  - 新增 `sessionApi.getConfig()` 获取会话配置
- `frontend/src/stores/sessionStore.ts:29-35, 92-161, 444-453`
  - 新增 `SessionConfigCache` 接口和 `sessionConfig` 状态
  - `startSession()` 和 `loadCurrentState()` 自动加载会话配置
  - `loadSuggestions()` 传递白名单和上下文基准

**效果 Effects:**
- ✅ 段落级上下文感知，低 PPL 段落中的句子获得额外基准分
- ✅ 智能白名单自动提取，学科术语不再被误判
- ✅ 前后端完整集成，白名单随会话存储和使用
- ✅ 实时 Delta 反馈已存在（SuggestionPanel 第 363-399 行显示风险变化）

**CAASS v2.0 Phase 2 评分公式 Scoring Formula:**
```
Score_Final = Clamp(Context_baseline + Score_fp + Score_st - Bonus_hu, 0, 100)

其中 Where:
- Context_baseline = 段落 PPL 基准分 (0-25)
- Score_fp = 指纹词绝对权重分 (白名单术语豁免)
- Score_st = 结构模式分数
- Bonus_hu = 人类特征减分
```

---

### 2025-12-31 (Update 30)

**Phase 3: Level 2 实现 - 段落衔接分析 | Level 2 Implementation - Paragraph Transition Analysis**

- 用户需求：实现 Level 2 "关节润滑" 功能，分析段落衔接并提供修复建议
- User Request: Implement Level 2 "Joint Lubrication" feature for paragraph transition analysis

**1. 段落衔接分析器 Transition Analyzer:**
- `src/core/analyzer/transition.py` (新增)
  - `TransitionAnalyzer` 类分析相邻段落衔接
  - 检测显性连接词 (Furthermore, Moreover, Additionally 等)
  - 检测主题句模式和总结结尾模式
  - 计算语义重叠率
  - 返回平滑度分数 (0-100, 越高越像AI)
  - 支持批量文档分析

**2. 过渡策略 Prompt Transition Strategy Prompts:**
- `src/prompts/__init__.py` (新增)
- `src/prompts/transition.py` (新增)
  - 三种过渡策略:
    - 语义回声 (Semantic Echo): 移除连接词，回应前段关键概念
    - 逻辑设问 (Logical Hook): 在段落末制造隐含问题，下段回应
    - 节奏打断 (Rhythm Break): 变化句长和结构，打破均匀AI节奏
  - 支持单策略和全策略 Prompt 生成
  - `get_transition_prompt()` 统一入口

**3. API 端点 API Endpoints:**
- `src/api/routes/transition.py` (新增)
  - `POST /api/v1/transition/` - 分析两段落衔接
  - `POST /api/v1/transition/with-suggestions` - 分析并生成修复建议
  - `POST /api/v1/transition/suggest/{strategy}` - 获取特定策略建议
  - `GET /api/v1/transition/strategies` - 列出可用策略
  - `POST /api/v1/transition/document` - 分析文档所有衔接
- `src/main.py:12,61` - 注册 transition 路由
- `src/api/routes/__init__.py:2` - 导入 transition 模块

**4. API Schemas:**
- `src/api/schemas.py:397-501` (新增)
  - `TransitionStrategy` 枚举 (semantic_echo, logical_hook, rhythm_break)
  - `TransitionAnalysisRequest` 请求模型
  - `TransitionIssue` 问题详情
  - `TransitionOption` 修复选项
  - `TransitionAnalysisResponse` 完整响应
  - `DocumentTransitionSummary` 文档衔接摘要

**5. 前端类型 Frontend Types:**
- `frontend/src/types/index.ts:280-341` (新增)
  - `TransitionStrategy` 类型
  - `TransitionIssue` 接口
  - `TransitionOption` 接口
  - `TransitionAnalysisResponse` 接口
  - `DocumentTransitionSummary` 接口

**6. 前端 API Frontend API:**
- `frontend/src/services/api.ts:17-19,440-526` (新增)
  - `transitionApi.analyze()` - 分析衔接
  - `transitionApi.analyzeWithSuggestions()` - 分析并获取建议
  - `transitionApi.getSuggestion()` - 获取特定策略建议
  - `transitionApi.getStrategies()` - 获取策略列表
  - `transitionApi.analyzeDocument()` - 分析文档所有衔接

**7. 前端 UI组件 Frontend UI Components:**
- `frontend/src/components/editor/TransitionPanel.tsx` (新增)
  - `TransitionPanel` 主组件：显示衔接分析和三种修复策略
  - `TransitionCard` 紧凑卡片：用于文档概览
  - 支持策略选择和预览
  - 显示检测问题和连接词标记

**测试结果 Test Results:**
```
Transition Analysis Test:
- Input: Para A (summary ending) → Para B ("Moreover, it is important to note...")
- Smoothness Score: 40 (medium risk)
- Issues Found: 2
  - [high] explicit_connector: "Moreover" 开头
  - [medium] summary_ending: 段落以总结结尾
- Explicit Connectors: ['Moreover']
- All strategies available: semantic_echo, logical_hook, rhythm_break
- Frontend build: ✓ Success
```

**效果 Effects:**
- ✅ 检测段落间显性连接词和公式化模式
- ✅ 提供三种过渡策略选择
- ✅ 支持单个衔接和全文档批量分析
- ✅ 前后端完整集成

---

### 2025-12-31 (Update 31)

**Phase 4: Level 1 实现 - 文档结构分析 | Level 1 Implementation - Document Structure Analysis**

- 用户需求：实现 Level 1 "骨架重组" 功能，分析全文宏观结构并提供重组策略
- User Request: Implement Level 1 "Skeleton Restructure" feature for document structure analysis

**1. 文档结构分析器 Structure Analyzer:**
- `src/core/analyzer/structure.py` (新增)
  - `StructureAnalyzer` 类分析全文结构
  - 检测线性流程模式 (First, Second, Third 等)
  - 检测重复段落结构 (topic sentence 模式)
  - 检测均匀段落长度
  - 检测可预测的引言-正文-结论结构
  - 提取核心论点和关键论据
  - 识别逻辑断点
  - 返回结构分数 (0-100, 越高越像AI)
  - 数据类: `ParagraphInfo`, `StructureIssue`, `BreakPoint`, `StructureOption`

**2. 结构重组 Prompts Structure Restructuring Prompts:**
- `src/prompts/structure.py` (新增)
  - 两种重组策略:
    - 优化连接 (Optimize Connection): 保持顺序，改善段落衔接
    - 深度重组 (Deep Restructure): 重新排序和组织内容
  - 支持逻辑诊断卡 Prompt 生成
  - `get_structure_prompt()` 统一入口
  - `get_logic_diagnosis_prompt()` 生成逻辑诊断卡

**3. API 端点 API Endpoints:**
- `src/api/routes/structure.py` (新增)
  - `POST /api/v1/structure/` - 分析文档结构
  - `POST /api/v1/structure/with-suggestions` - 分析并生成重组建议
  - `POST /api/v1/structure/suggest/{strategy}` - 获取特定策略建议
  - `POST /api/v1/structure/diagnosis` - 获取逻辑诊断卡
  - `POST /api/v1/structure/document` - 按ID分析文档结构
  - `GET /api/v1/structure/strategies` - 列出可用策略
- `src/main.py:12,62` - 注册 structure 路由
- `src/api/routes/__init__.py:2` - 导入 structure 模块

**4. API Schemas:**
- `src/api/schemas.py:504-711` (新增)
  - `StructureStrategy` 枚举 (optimize_connection, deep_restructure)
  - `ParagraphInfo` 段落信息
  - `StructureIssue` 结构问题
  - `BreakPoint` 逻辑断点
  - `FlowRelation` 流关系
  - `RiskArea` 风险区域
  - `StructureModification` 结构修改
  - `StructureChange` 结构变化
  - `StructureOption` 重组选项
  - `StructureAnalysisResponse` 完整响应
  - `LogicDiagnosisResponse` 逻辑诊断卡响应

**5. 前端类型 Frontend Types:**
- `frontend/src/types/index.ts:343-493` (新增)
  - `StructureStrategy` 类型
  - `ParagraphInfo` 接口
  - `StructureIssue` 接口
  - `BreakPoint` 接口
  - `FlowRelation` 接口
  - `RiskArea` 接口
  - `StructureModification` 接口
  - `StructureChange` 接口
  - `StructureOption` 接口
  - `StructureAnalysisResponse` 接口
  - `LogicDiagnosisResponse` 接口

**6. 前端 API Frontend API:**
- `frontend/src/services/api.ts:20-23,572-667` (新增)
  - `structureApi.analyze()` - 分析结构
  - `structureApi.analyzeWithSuggestions()` - 分析并获取建议
  - `structureApi.getSuggestion()` - 获取特定策略建议
  - `structureApi.getDiagnosis()` - 获取逻辑诊断卡
  - `structureApi.analyzeDocument()` - 按ID分析文档
  - `structureApi.getStrategies()` - 获取策略列表

**7. 前端 UI组件 Frontend UI Components:**
- `frontend/src/components/editor/StructurePanel.tsx` (新增)
  - `StructurePanel` 主组件：显示逻辑诊断卡和两种重组策略
  - `StructureCard` 紧凑卡片：用于文档概览
  - 显示流程图可视化 (→, ↔, ⤵, ⟳, ✗)
  - 显示结构模式 (线性/并列/嵌套/环形)
  - 显示核心论点和关键论据
  - 支持策略选择和大纲预览

**测试结果 Test Results:**
```
Structure Analysis Test:
- Input: 5 paragraphs with "First, Second, Third, Fourth, Finally" pattern
- Structure Score: 60 (high risk)
- Risk Level: high
- Pattern Flags:
  - Has Linear Flow: True
  - Has Repetitive Pattern: True
- Issues Found: 3
  - [high] linear_flow: 检测到4个线性过渡标记 (First, Second 等)
  - [medium] repetitive_pattern: 4/5个段落以主题句开头
  - [medium] uniform_length: 段落长度均匀 (平均26词，5/5相似)
- Backend imports: ✓ Success
- Frontend build: ✓ Success
```

**效果 Effects:**
- ✅ 检测全文线性流程和重复模式
- ✅ 检测均匀段落长度和可预测结构
- ✅ 提取核心论点和关键论据
- ✅ 提供两种重组策略选择
- ✅ 生成可视化逻辑诊断卡
- ✅ 前后端完整集成

---

### 2025-12-31 (Update 32)

**Phase 5: 全流程整合 - 三层级处理协调 | Full Flow Integration - Three-Level Processing Coordination**

- 用户需求：整合三层级处理流程，实现 L1→L2→L3 强制顺序
- User Request: Integrate three-level processing flow with forced L1→L2→L3 order

**1. 流程协调器 Flow Coordinator:**
- `src/core/coordinator/__init__.py` (新增)
- `src/core/coordinator/flow_coordinator.py` (新增)
  - `FlowCoordinator` 类协调三层级处理流程
  - `FlowContext` 数据类存储处理上下文
  - `LevelResult` 数据类存储层级结果
  - 支持 Quick 模式（跳过 L1/L2）和 Deep 模式（完整流程）
  - 自动根据文档大小决定是否跳过层级
  - 上下文在层级间传递（L1→L2→L3）

**2. 流程 API 端点 Flow API Endpoints:**
- `src/api/routes/flow.py` (新增)
  - `POST /api/v1/flow/start` - 开始新处理流程
  - `GET /api/v1/flow/{id}/progress` - 获取流程进度
  - `POST /api/v1/flow/{id}/complete-level` - 完成层级
  - `POST /api/v1/flow/{id}/skip-level` - 跳过层级
  - `GET /api/v1/flow/{id}/context/{level}` - 获取层级上下文
  - `POST /api/v1/flow/{id}/update-context` - 更新上下文
  - `GET /api/v1/flow/{id}/current-text` - 获取当前文本
  - `DELETE /api/v1/flow/{id}` - 取消流程
- `src/main.py:12,63` - 注册 flow 路由
- `src/api/routes/__init__.py:2` - 导入 flow 模块

**3. 前端类型 Frontend Types:**
- `frontend/src/types/index.ts:495-573` (新增)
  - `ProcessingLevel` 类型
  - `ProcessingMode` 类型
  - `StepStatus` 类型
  - `LevelInfo` 接口
  - `FlowSummary` 接口
  - `FlowProgress` 接口
  - `FlowStartResponse` 接口
  - `LevelContext` 接口

**4. 前端 API Frontend API:**
- `frontend/src/services/api.ts:669-837` (新增)
  - `flowApi.start()` - 开始流程
  - `flowApi.getProgress()` - 获取进度
  - `flowApi.completeLevel()` - 完成层级
  - `flowApi.skipLevel()` - 跳过层级
  - `flowApi.getLevelContext()` - 获取层级上下文
  - `flowApi.updateContext()` - 更新上下文
  - `flowApi.getCurrentText()` - 获取当前文本
  - `flowApi.cancel()` - 取消流程

**测试结果 Test Results:**
```
Flow Coordinator Test:
- Context creation: ✓
- Level tracking: L1(in_progress) → L2(pending) → L3(pending)
- Mode support: quick/deep ✓
- Paragraph detection: 3 paragraphs detected ✓
- Backend imports: ✓ Success
- Frontend build: ✓ Success
```

**效果 Effects:**
- ✅ 强制 L1→L2→L3 处理顺序
- ✅ 上下文在层级间自动传递
- ✅ 支持 Quick/Deep 两种处理模式
- ✅ 自动根据文档大小决定跳过策略
- ✅ 流程进度实时追踪
- ✅ 前后端完整集成

---

### 2025-12-31 (Update 33)

**Phase 6: 测试与部署 - 集成测试完成 | Testing & Deployment - Integration Tests Complete**

- 用户需求：完成三层级系统集成测试
- User Request: Complete three-level system integration testing

**集成测试结果 Integration Test Results:**

```
============================================================
Phase 6: Three-Level De-AIGC Integration Test
============================================================

[Test 1] Level 3: Sentence Analysis
  Fingerprints Detected: 4
  Risk Score: 100 (high risk sentence)
  [PASS] Level 3

[Test 2] Level 2: Transition Analysis
  Smoothness Score: 40
  Risk Level: medium
  Connectors Found: ['Moreover']
  [PASS] Level 2

[Test 3] Level 1: Structure Analysis
  Paragraphs: 4
  Structure Score: 60
  Risk Level: high
  Linear Flow Detected: True
  Issues Found: 3
  [PASS] Level 1

[Test 4] Flow Coordinator
  Mode: deep
  Flow: L1 -> L2 -> L3 -> Done
  Score Reduction: 60 -> 15 (-45)
  [PASS] Flow Coordinator

[Test 5] API Module Imports
  structure.router: OK
  transition.router: OK
  flow.router: OK
  [PASS] API Modules

============================================================
ALL TESTS PASSED - Three-Level De-AIGC Ready!
============================================================
```

**前端构建结果 Frontend Build Results:**
```
vite v5.4.21 building for production...
✓ 1446 modules transformed
dist/index.html           0.49 kB
dist/assets/index.css    34.35 kB
dist/assets/index.js    310.31 kB
✓ built in 2.80s
```

**效果 Effects:**
- ✅ 三层级分析器全部通过测试
- ✅ 流程协调器正常工作
- ✅ API模块正确导入
- ✅ 前端构建成功
- ✅ 系统就绪

---

## 项目完成总结 | Project Completion Summary

**三层级 De-AIGC 架构已完整实现 Three-Level De-AIGC Architecture Fully Implemented:**

| 层级 Level | 功能 Function | 状态 Status |
|------------|---------------|-------------|
| Level 1 骨架重组 | 全文结构分析，检测线性模式 | ✅ 完成 |
| Level 2 关节润滑 | 段落衔接分析，消灭显性连接词 | ✅ 完成 |
| Level 3 皮肤精修 | 指纹词检测，句式重构建议 | ✅ 完成 |
| Flow Coordinator | L1→L2→L3 流程协调 | ✅ 完成 |

**API 端点汇总 API Endpoints Summary:**
- `/api/v1/structure/*` - Level 1 结构分析
- `/api/v1/transition/*` - Level 2 衔接分析
- `/api/v1/suggest/*` - Level 3 建议生成
- `/api/v1/flow/*` - 流程协调
- `/api/v1/session/*` - 会话管理
- `/api/v1/documents/*` - 文档管理
- `/api/v1/analyze/*` - 分析服务
- `/api/v1/export/*` - 导出服务

---

### 2025-01-01 (Update 24)

**CAASS v2.0 评分系统重构 CAASS v2.0 Scoring System Refactor:**

- 用户需求：根据优化报告实现 CAASS v2.0 (Context-Aware Absolute Scoring System)
- 核心变更：

**1. 清理指纹词库 Clean Fingerprint Dictionary:**
- `src/core/analyzer/scorer.py:57-78`
  - 从 Level 2 移除所有学科特定术语 (remediation, circular economy, soil salinization 等)
  - 仅保留真正的 AI 惯用词（学术套话和结构连接词）

**2. 语气自适应权重矩阵 Tone-Adaptive Weight Matrix:**
- `src/core/analyzer/scorer.py:81-163`
  - 新增 `TONE_WEIGHT_MATRIX` 常量，定义三类词汇在不同语气等级下的权重
  - Type A (死罪词): 始终高惩罚 (40-50分)，如 delve, tapestry
  - Type B (学术套话): 语气相关 (5-25分)，如 crucial, utilize
  - Type C (连接词): 语气相关 (10-30分)，如 furthermore, moreover
  - 新增 `get_tone_adjusted_weight()` 和 `classify_fingerprint_type()` 函数

**3. 绝对权重评分算法 Absolute Weight Scoring:**
- `src/core/analyzer/scorer.py:499-527`
  - 新增 `_score_fingerprint_caass()` 方法
  - 使用绝对权重累加替代密度计算，解决短句评分失真问题
  - 公式: `Score = Σ(word_weight × tone_modifier)`

**4. 结构模式评分重构 Structure Pattern Scoring Refactor:**
- `src/core/analyzer/scorer.py:724-791`
  - 新增 `_score_structure_caass()` 方法
  - 仅检测结构模式（非指纹词），消除重复计算问题
  - 结构分数上限 40 分，为指纹分数留出空间

**5. 白名单支持 Whitelist Support:**
- `src/core/analyzer/scorer.py:238-288`
  - `analyze()` 方法新增 `whitelist` 参数
  - 白名单术语自动豁免，不参与评分

**6. API 端点更新 API Endpoint Updates:**
- `src/api/routes/suggest.py:55-110` - 传递 tone_level
- `src/api/routes/analyze.py:59-67` - 使用默认 tone_level=4
- `src/api/routes/documents.py:117-120, 287-290` - 使用默认 tone_level=4
- `src/core/validator/quality_gate.py:198-204` - 支持 tone_level 参数

**效果 Effects:**
- ✅ 解决短句评分失真问题（不再使用密度计算）
- ✅ 解决学科术语误判问题（清理词库 + 白名单机制）
- ✅ Tone Level 真正生效（语气自适应权重矩阵）
- ✅ 消除评分重复计算（分离指纹词和结构模式评分）

**CAASS v2.0 评分公式 Scoring Formula:**
```
Score_Final = Clamp(Score_fp + Score_st - Bonus_hu, 0, 100)

其中 Where:
- Score_fp = Σ(fingerprint_weight × tone_modifier), 上限 80
- Score_st = 结构模式分数, 上限 40
- Bonus_hu = 人类特征减分, 上限 50
```

---

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

### 2025-12-31 (Update 10)

**三级流程前端集成 Three-Level Flow Frontend Integration:**
- 用户需求：前端缺少 Level 1 和 Level 2 的工作流程入口
- 修改内容：
  - `frontend/src/pages/ThreeLevelFlow.tsx` (新建)
    - 三级流程页面，集成全部三个处理层级
    - Step 1: 使用 StructurePanel 进行结构分析 (Level 1)
    - Step 2: 使用 TransitionPanel 进行衔接分析 (Level 2)
    - Step 3: 跳转到 Intervention 页面进行句子精修 (Level 3)
    - 包含进度指示器和层级状态管理
  - `frontend/src/App.tsx:9,23`
    - 导入 ThreeLevelFlow 组件
    - 添加路由 `/flow/:documentId`
  - `frontend/src/pages/Upload.tsx:29-30,121-142,266-312`
    - 新增"深度模式"(Deep Mode) 选项
    - 三种处理模式：深度(三级流程)、干预(直接)、YOLO(自动)
    - 深度模式导航到 `/flow/:documentId`
  - `src/api/routes/structure.py:533`
    - 修复 `document.content` → `document.original_text`

**效果**:
- 用户可选择"深度模式"进入完整三级流程
- 三级流程页面提供 L1 → L2 → L3 的完整处理体验
- 每个层级有独立的展开/折叠面板和状态指示

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

### 2024-12-31 - Track C分析功能修复 | Track C Analysis Fix

**用户需求 User Request:**
- 修复轨道C的分析句子功能卡住的问题
- Track C sentence analysis feature was stuck

**问题分析 Issue Analysis:**
- 当用户切换句子时，`analysisState` 没有被正确重置
- 导致API返回结果时，当前句子已变化，但状态更新针对的是旧句子
- 表现为加载状态永远不结束或显示错误

**方法 Approach:**
1. 在 `Intervention.tsx` 中添加 effect，当句子变化时重置 `analysisState`
2. 在 `handleAnalysisToggle` 中添加句子ID变化检查
3. 即使句子变化也缓存API结果供将来使用

**修改 Modified:**
- `frontend/src/pages/Intervention.tsx`:
  - 添加 `analysisStartSentenceIdRef` ref 追踪分析起始句子ID (line 104-106)
  - 添加句子变化时重置 `analysisState` 的 effect (line 227-253)
  - 在 API 返回时检查当前句子是否仍为发起请求的句子 (line 182-191, 204-210)
  - 即使句子变化也缓存结果 (line 175-179, 186-190)

**结果 Result:**
- 切换句子时分析状态正确重置
- 避免了竞态条件导致的状态混乱
- 分析结果仍会被缓存，下次访问同一句子时可直接使用

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

> 基于三层级 De-AIGC 架构规划

### 已完成：Phase 2 - 5

**Phase 2: Level 3 增强 ✅**
- [x] Burstiness 检测 (`src/core/analyzer/burstiness.py`)
- [x] 显性连接词检测 (`src/core/analyzer/connector_detector.py`)
- [x] 前端显示增强指标

**Phase 3: Level 2 实现 ✅**
- [x] 段落衔接分析器 (`src/core/analyzer/transition.py`)
- [x] 三种过渡策略 Prompt (`src/prompts/transition.py`)
- [x] Transition API 端点 (`src/api/routes/transition.py`)
- [x] TransitionPanel UI 组件

**Phase 4: Level 1 实现 ✅**
- [x] 全文结构分析器 (`src/core/analyzer/structure.py`)
- [x] 两种重构策略 Prompt (`src/prompts/structure.py`)
- [x] Structure API 端点 (`src/api/routes/structure.py`)
- [x] StructurePanel UI 组件
- [x] 逻辑诊断卡 API (`/structure/diagnosis`)
- [x] 核心论点提取

**Phase 5: 全流程整合 ✅**
- [x] FlowCoordinator 协调器 (`src/core/coordinator/flow_coordinator.py`)
- [x] Flow API 端点 (`src/api/routes/flow.py`)
- [x] 三级流程页面 (`frontend/src/pages/ThreeLevelFlow.tsx`)
- [x] 深度模式入口 (Upload 页面)
- [x] L1 → L2 → L3 流程引导

### 下一阶段：Phase 6 - 生产优化

1. **性能优化**
   - [ ] LLM 调用缓存
   - [ ] 批量处理优化

2. **用户体验增强**
   - [ ] 进度保存和恢复
   - [ ] 导出处理结果
   - [ ] 历史记录管理

3. **测试覆盖**
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] E2E 测试

---

## Bug Fixes - 2025-12-31

### Step 2 段落数不匹配问题 | Step 2 Paragraph Count Mismatch

**问题描述 | Problem:**
- Step 1 正确显示 21 段或 88 段，但 Step 2 始终只显示 2 段
- User reported: "step1显示21段，step显示2段，step1显示88段，step2依旧是2段"

**原因分析 | Root Cause:**
- `ThreeLevelFlow.tsx` 中的 `analyzeTransitions` 函数手动从重构的 `documentText` 分割段落
- `documentText` 是从 Step 1 结果中重构的摘要文本（首句...尾句），而非原始文档

**修复方案 | Fix:**
- 修改 `analyzeTransitions` 函数，调用 `transitionApi.analyzeDocument(documentId)` 直接从后端获取衔接分析
- 后端 `/transition/document` 端点使用原始文档文本 `doc.original_text` 正确解析段落

**修改文件 | Modified Files:**
- `frontend/src/pages/ThreeLevelFlow.tsx` (lines 144-167)

**代码变更 | Code Changes:**
```typescript
// OLD (错误)
const paragraphs = documentText.split(/\n\s*\n/).filter(p => p.trim());
// 手动构建 transitionAnalyses

// NEW (正确)
const summary = await transitionApi.analyzeDocument(documentId);
if (summary.transitions && summary.transitions.length > 0) {
  setTransitionAnalyses(summary.transitions);
}
```

### 智能结构分析改进 | Smart Structure Analysis Enhancement

**用户需求 | User Requirements:**
1. 分段逻辑要智能 - 过滤掉标题、表头、图名等非正文内容
2. 大纲标注要用论文结构编号（如 3.2(1)），不要用"段落N"
3. 每段要有具体的要点总结，不要用 body/conclusion 等标签

**实现方案 | Implementation:**
使用 LangChain + LLM 实现智能文档结构分析：

1. **智能段落识别**：
   - LLM 自动过滤标题、表头、图名、要点列表等非正文内容
   - 只保留真正的连续散文段落（> 50 词）

2. **章节结构识别**：
   - 识别论文章节编号（1, 1.1, 2.3.1 等）
   - 用位置标签标注段落（如 "3.2(1)" = 第3.2节第1段）

3. **要点生成**：
   - 为每段生成 10-20 词的具体内容摘要
   - 同时生成中英文版本

4. **AI 风险评估**：
   - 为每段评估 AI 检测风险（high/medium/low）
   - 给出具体原因

**新增文件 | New Files:**
- `src/core/analyzer/smart_structure.py` - LangChain 智能结构分析器

**修改文件 | Modified Files:**
- `src/api/schemas.py` - 新增 SmartStructureResponse, SectionInfo, SmartParagraphInfo 等类型
- `src/api/routes/structure.py` - `/document` 端点改用智能分析器
- `frontend/src/types/index.ts` - 对应的前端类型定义
- `frontend/src/components/editor/StructurePanel.tsx` - 显示章节位置和要点摘要

**用户体验改进 | UX Improvements:**
- 显示论文结构位置（如 "3.2(1)"）而非简单的段落编号
- 显示每段的具体内容摘要而非功能标签
- 显示每段的 AI 风险等级和原因
- 支持展开/收起完整段落列表

### 显性连接词检测与逻辑断裂点分析 | Explicit Connector Detection & Logic Break Analysis

**用户需求 | User Requirements:**
- Step 1 和 Step 2 的分析逻辑过于简单
- 没有分析前后段、前后句的连接词或承接句子
- 需要按照 improve-analysis-report.md 中的内容增强分析能力

**实现方案 | Implementation:**

1. **显性连接词检测 (AI 指纹)**：
   - 检测英文连接词：Furthermore, Moreover, Additionally, Consequently, Therefore, Thus, Hence, Notably, Importantly, However, Nevertheless, In addition, First/Firstly, Second/Secondly, Third/Thirdly, Finally, In conclusion, To summarize
   - 检测中文连接词：首先, 其次, 再次, 此外, 另外, 总之, 综上所述, 另一方面, 因此, 所以, 然而, 但是, 不过, 同时, 与此同时
   - 记录每个连接词的位置（段落位置）和严重程度

2. **逻辑断裂点分析 (段落间)**：
   - 分析相邻段落之间的过渡质量
   - 识别过渡类型：smooth (流畅), abrupt (突兀), glue_word_only (仅靠连接词)
   - 提供具体的修复建议（使用语义回声替代显性连接词）

3. **评分增强**：
   - connector_overuse: 连接词过度使用评分
   - missing_semantic_echo: 缺少语义回声评分

**修改文件 | Modified Files:**
- `src/core/analyzer/smart_structure.py` - 增强 SMART_STRUCTURE_PROMPT，添加连接词和逻辑断裂点检测
- `src/core/analyzer/transition.py` - 添加中文高严重度连接词列表 HIGH_SEVERITY_CONNECTORS_ZH
- `src/api/schemas.py` - 新增 ExplicitConnector, LogicBreak 类型，更新 SmartStructureResponse
- `src/api/routes/structure.py` - `/document` 端点返回 explicit_connectors 和 logic_breaks
- `frontend/src/types/index.ts` - 添加 ExplicitConnector, LogicBreak 接口
- `frontend/src/components/editor/StructurePanel.tsx` - 显示检测到的连接词和逻辑断裂点

**前端 UI 增强 | Frontend UI Enhancement:**
- 显示检测到的显性连接词列表，标注位置和严重程度
- 显示逻辑断裂点，标注过渡类型和修复建议
- 评分说明增加 connector_overuse 和 missing_semantic_echo 指标

**代码示例 | Code Examples:**
```typescript
// ExplicitConnector 类型
interface ExplicitConnector {
  word: string;       // 连接词
  position: string;   // 段落位置如 "3.2(1)"
  location: string;   // "paragraph_start" or "sentence_start"
  severity: string;   // "high" or "medium"
}

// LogicBreak 类型
interface LogicBreak {
  from_position: string;     // 起始段落
  to_position: string;       // 目标段落
  transition_type: string;   // "smooth", "abrupt", "glue_word_only"
  issue: string;             // 问题描述
  issue_zh: string;          // 中文描述
  suggestion: string;        // 建议
  suggestion_zh: string;     // 中文建议
}
```

---

## 2025-12-31 - Level 3 段落内逻辑增强 | Level 3 Intra-paragraph Logic Enhancement

### 用户需求 | User Requirements

根据 `doc/段落内分析.md` 文档，增强段落内句子之间的逻辑关系处理能力，重点关注：
1. 句子之间的逻辑关系（递进、推导、转折、强调等，不要平铺，不要均质化）
2. 隐性连接替代连接词
3. 主语多样性，第一人称使用被动句式替代
4. 打破线性结构：Assertion + Nuance + Deep Implication (ANI结构)
5. 长短句搭配使用
6. 语气词（may, possible等）的策略性使用

### 完成的功能 | Completed Features

| 优先级 | 功能 Feature | 文件 Files | 状态 Status |
|--------|--------------|-----------|-------------|
| P0 | 增强LLM Prompt (策略6-10) | `src/core/suggester/llm_track.py` | ✅ 完成 |
| P1 | 段落逻辑分析器 | `src/core/analyzer/paragraph_logic.py` | ✅ 完成 |
| P1 | 段落逻辑Prompt模板 | `src/prompts/paragraph_logic.py` | ✅ 完成 |
| P2 | 评分系统集成 | `src/core/analyzer/scorer.py` | ✅ 完成 |
| P2 | 段落级API | `src/api/routes/paragraph.py` | ✅ 完成 |
| P3 | 前端UI组件 | `frontend/src/components/editor/ParagraphLogicPanel.tsx` | ✅ 完成 |

### 新增/修改的文件 | New/Modified Files

**新增文件 New Files:**
- `src/core/analyzer/paragraph_logic.py` - 段落逻辑分析器，检测主语重复、句长均匀、线性结构等AI模式
- `src/prompts/paragraph_logic.py` - 段落重组Prompt模板（ANI结构、主语多样性、隐性连接、节奏变化）
- `src/api/routes/paragraph.py` - 段落分析与重组API端点
- `frontend/src/components/editor/ParagraphLogicPanel.tsx` - 段落逻辑分析UI组件

**修改文件 Modified Files:**
- `src/core/suggester/llm_track.py` - 增加策略6-10（隐性连接、主语多样性、ANI结构、节奏变化、语气词）
- `src/core/analyzer/scorer.py` - 新增 `analyze_paragraph_logic()` 方法
- `src/main.py` - 注册 paragraph 路由
- `src/api/routes/__init__.py` - 导入 paragraph 模块
- `frontend/src/types/index.ts` - 新增段落逻辑相关类型定义
- `frontend/src/services/api.ts` - 新增 `paragraphApi` 服务

### 实现细节 | Implementation Details

**1. 段落逻辑分析器 (`paragraph_logic.py`):**

检测4类AI模式问题：
- `subject_repetition`: 主语重复（同一主语出现>40%）
- `uniform_length`: 句长均匀（CV<0.25视为AI模式）
- `linear_structure`: 线性叠加结构（>=3个叠加连接词）
- `first_person_overuse`: 第一人称过度使用（>50%）

输出指标：
- `subject_diversity_score`: 主语多样性分数 (0-1)
- `length_variation_cv`: 句长变异系数
- `logic_structure`: linear/mixed/varied
- `paragraph_risk_adjustment`: 风险调整值 (0-50)

**2. 重组策略 (`paragraph_logic.py` prompts):**

| 策略 Strategy | 用途 Use Case |
|---------------|---------------|
| `ani` | 将平铺结构转为 断言→细微差别→深层含义 |
| `subject_diversity` | 变换主语（指示代词、名词化、被动替代）|
| `implicit_connector` | 显性连接词→语义回声、嵌入式转折 |
| `rhythm` | 创造长短句节奏感（Long→Short→Medium）|
| `all` | 综合应用所有相关策略 |

**3. LLM Prompt增强 (`llm_track.py`):**

新增5项De-AIGC技术：
- 策略6: 隐性连接（语义回声、嵌入式转折、蕴含流）
- 策略7: 主语多样性（指示代词、名词化、被动替代）
- 策略8: ANI结构（断言-细微-深意）
- 策略9: 句长节奏变化（Long-Short-Medium模式）
- 策略10: 语气词策略（hedging vs conviction 平衡）

### API端点 | API Endpoints

| 端点 Endpoint | 方法 Method | 描述 Description |
|---------------|-------------|------------------|
| `/api/v1/paragraph/strategies` | GET | 获取可用重组策略 |
| `/api/v1/paragraph/analyze` | POST | 分析段落逻辑问题 |
| `/api/v1/paragraph/restructure` | POST | 使用指定策略重组段落 |

### 代码示例 | Code Examples

```python
# 段落逻辑分析
from src.core.analyzer.paragraph_logic import ParagraphLogicAnalyzer

analyzer = ParagraphLogicAnalyzer()
result = analyzer.analyze_paragraph([
    "The model improves accuracy.",
    "Furthermore, the model reduces errors.",
    "Additionally, the model enhances performance.",
])

# result.issues: [LogicIssue(type="linear_structure", ...)]
# result.logic_structure: "linear"
# result.connector_density: 0.67
```

```typescript
// 前端组件使用
import ParagraphLogicPanel from '@/components/editor/ParagraphLogicPanel';
import { paragraphApi } from '@/services/api';

<ParagraphLogicPanel
  paragraph={currentParagraph}
  onAnalyze={(p) => paragraphApi.analyze(p, toneLevel)}
  onRestructure={(p, s) => paragraphApi.restructure(p, s, toneLevel)}
  onApply={(restructured) => handleApply(restructured)}
  toneLevel={4}
  paragraphIndex={1}
/>
```

---

## 2024-12-31: Level 1 结构增强 | Level 1 Structure Enhancement

### 需求描述 | Requirements

基于`文章结构分析.md`的分析报告，增强Level 1（Step 1 - 结构重组）的De-AIGC能力：
- 核心洞察：破坏"结构预测性"，而非"清晰性"
- 创建结构预测性评分模型
- 参数化扰动等级（轻度/中度/强度）
- 实现六大扰动策略
- 允许人类特征（功能重叠、未解决张力、开放式结尾）

Based on the analysis report in `文章结构分析.md`, enhance Level 1 (Step 1 - Structure Restructuring) De-AIGC capabilities:
- Core insight: break "structural predictability" not "clarity"
- Create structure predictability scoring model
- Parameterize disruption levels (light/medium/strong)
- Implement six disruption strategies
- Allow human features (function overlap, unresolved tension, open endings)

### 技术要点 | Technical Details

**1. 结构预测性评分模型 (`structure_predictability.py`):**

五个维度的预测性检测：
- `progression_predictability`: 推进预测性（单调 vs 非单调）
- `function_uniformity`: 功能均匀度（均匀 vs 非对称）
- `closure_strength`: 闭合强度（强 vs 弱/开放）
- `length_regularity`: 长度规则性
- `connector_explicitness`: 连接词显性度

权重配置：
```python
DIMENSION_WEIGHTS = {
    "progression": 0.25,
    "function": 0.20,
    "closure": 0.20,
    "length": 0.15,
    "connector": 0.20
}
```

**2. 扰动等级参数化 (`prompts/structure.py`):**

| 等级 Level | 允许策略 Allowed | 目标降分 Target |
|------------|------------------|-----------------|
| `light` | rewrite_opening, remove_connector, lexical_echo | 15% |
| `medium` | + local_reorder, asymmetry, non_monotonic | 25% |
| `strong` | + full_reorder, inversion, conflict_injection, weak_closure | 40% |

**3. 六大扰动策略 (`prompts/structure.py`):**

| 策略 Strategy | 名称 Name | 作用 Effect |
|---------------|-----------|-------------|
| `inversion` | 结构倒置 | 交换定义↔问题、方法↔失败案例 |
| `conflict_injection` | 冲突引入 | 主论述前插入反对意见/边界条件 |
| `induction` | 归纳式推进 | 从数据切入，延迟显式结论 |
| `asymmetry` | 非对称布局 | 深入一点(150%)，简扫其他(60%) |
| `weak_closure` | 弱闭合 | 开放问题替代"In conclusion" |
| `lexical_echo` | 词汇回声 | 语义桥接替代显性连接词 |

**4. 检测增强 (`structure.py`):**

新增数据类：
- `ProgressionAnalysis`: 推进类型分析（monotonic/non_monotonic/mixed）
- `FunctionDistribution`: 功能分布分析（uniform/asymmetric/balanced）
- `ClosureAnalysis`: 闭合模式分析（strong/moderate/weak/open）
- `LexicalEchoAnalysis`: 词汇回声分析

新增检测模式：
- 回指模式: `as mentioned earlier`, `returning to`, `recall that`
- 条件模式: `if...then`, `assuming...`, `given...`
- 公式化结论: `in conclusion`, `to summarize`, `this study demonstrates`
- 开放式结尾: `remains unclear`, `further research needed`, `what remains`

**5. 专用策略Prompt函数 (`prompts/structure.py`):**

| 函数 Function | 用途 Use Case |
|---------------|---------------|
| `get_disruption_restructure_prompt()` | 核心扰动重组（使用等级参数） |
| `get_single_strategy_prompt()` | 单策略应用于单段落 |
| `get_lexical_echo_prompt()` | 创建段落间词汇回声 |
| `get_weak_closure_prompt()` | 转换公式化结论为开放式 |
| `get_asymmetry_prompt()` | 创建非对称段落深度 |

### API端点 | API Endpoints

| 端点 Endpoint | 方法 Method | 描述 Description |
|---------------|-------------|------------------|
| `/api/v1/structure/predictability` | POST | 分析结构预测性（5维度） |
| `/api/v1/structure/disruption-levels` | GET | 获取扰动等级配置 |
| `/api/v1/structure/disruption-strategies` | GET | 获取六大扰动策略 |

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/core/analyzer/structure_predictability.py` | NEW | 结构预测性评分模型 |
| `src/prompts/structure.py` | MODIFY | 添加扰动等级、策略、Prompt函数 |
| `src/core/analyzer/structure.py` | MODIFY | 添加4种新检测方法和数据类 |
| `src/api/routes/structure.py` | MODIFY | 添加3个新API端点 |
| `src/api/schemas.py` | MODIFY | 添加增强分析请求/响应模式 |

### 代码示例 | Code Examples

```python
# 结构预测性分析
from src.core.analyzer.structure import StructureAnalyzer

analyzer = StructureAnalyzer()
result = analyzer.analyze(document_text)

# 访问增强分析结果
print(result.progression_analysis.progression_type)  # "monotonic" / "non_monotonic" / "mixed"
print(result.function_distribution.distribution_type)  # "uniform" / "asymmetric" / "balanced"
print(result.closure_analysis.closure_type)  # "strong" / "moderate" / "weak" / "open"
print(result.lexical_echo_analysis.echo_ratio)  # 0.0-1.0
```

```python
# 使用扰动重组Prompt
from src.prompts.structure import get_disruption_restructure_prompt, DISRUPTION_LEVELS

prompt = get_disruption_restructure_prompt(
    paragraphs=paragraph_list,
    disruption_level="medium",  # light/medium/strong
    selected_strategies=["lexical_echo", "asymmetry"],
    predictability_score={"total_score": 65, "progression_type": "monotonic"},
    extracted_thesis="This study demonstrates..."
)
```

### 设计原则 | Design Principles

1. **破坏可预测性，不是清晰性**: De-AIGC目标是让结构"非最优"但仍逻辑连贯
2. **参数化扰动**: 避免"一刀切"，根据风险等级选择适当策略
3. **允许人类特征**: 功能重叠、未解决张力、开放式结尾都是正常的人类写作特征
4. **层级递进**: light→medium→strong，逐步增加扰动强度
5. **向后兼容**: 保留原有`optimize_connection`和`deep_restructure`策略

---

## 7指征风险卡片系统 | 7-Indicator Structural Risk Card System

**日期 | Date**: 2025-12-31

### 用户需求 | User Requirements

用户要求：
1. 增强第7条（回指结构检测）
2. 让用户真正看到自己的文章触发了哪些文章结构层面的AI指征
3. 使用emoji或颜色来表示，一目了然

User requirements:
1. Enhance the 7th indicator (cross-reference detection)
2. Let users see which structural AI indicators their article triggers
3. Use emoji and colors for clear visualization

### 方法 | Method

基于`文章结构分析改进.md`中定义的7大结构性AI指征，创建可视化风险卡片系统：

Based on the 7 structural AI indicators defined in `文章结构分析改进.md`, create a visual risk card system:

**7大指征配置 | 7-Indicator Configuration:**

| ID | 指征 Indicator | 风险等级 Risk | Emoji | 描述 Description |
|----|----------------|---------------|-------|------------------|
| `symmetry` | 逻辑推进对称 | ★★★ | ⚖️ | 完美三段式结构 |
| `uniform_function` | 段落功能均匀 | ★★☆ | 📊 | 每段功能过于单一 |
| `explicit_connectors` | 连接词依赖 | ★★★ | 🔗 | 过度依赖显性连接词 |
| `linear_progression` | 单一线性推进 | ★★★ | 📝 | 纯粹的线性枚举 |
| `rhythmic_regularity` | 段落节奏均衡 | ★★☆ | 📏 | 段落长度过于均匀 |
| `over_conclusive` | 结尾过度闭合 | ★★☆ | 🔒 | 公式化总结结尾 |
| `no_cross_reference` | 缺乏回指结构 | ★★☆ | 🔄 | 只有前向引用 |

**颜色方案 | Color Scheme:**
- 触发(Triggered): `#ef4444` (红色/Red)
- 安全(Safe): `#22c55e` (绿色/Green)

### 修改/新增的内容 | Modified/Added Content

**1. 新增数据类 (`src/core/analyzer/structure.py`):**

```python
@dataclass
class CrossReferenceAnalysis:
    has_cross_references: bool      # Has cross-reference patterns
    cross_reference_count: int       # Count of cross-references
    concept_callbacks: int           # Count of concept callbacks
    forward_only_ratio: float        # Ratio of forward-only references
    score: int                       # Overall score
    detected_references: List[Dict]  # Detected reference patterns
    core_concepts: List[str]         # Core concepts from text

@dataclass
class StructuralIndicator:
    id: str                    # Indicator ID
    name: str                  # English name
    name_zh: str               # Chinese name
    triggered: bool            # Whether triggered
    risk_level: int            # Risk level (1-3 stars)
    emoji: str                 # Display emoji
    color: str                 # Hex color code
    description: str           # English description
    description_zh: str        # Chinese description
    details: str               # English details
    details_zh: str            # Chinese details

@dataclass
class StructuralRiskCard:
    indicators: List[StructuralIndicator]  # All 7 indicators
    triggered_count: int                    # Count of triggered indicators
    overall_risk: str                       # low/medium/high
    overall_risk_zh: str                    # Chinese risk level
    summary: str                            # English summary
    summary_zh: str                         # Chinese summary
    total_score: int                        # Total risk score
```

**2. 新增检测模式 (`src/core/analyzer/structure.py`):**

```python
CROSS_REFERENCE_PATTERNS = [
    r'\bas\s+(mentioned|noted|discussed|stated|described)\s+(earlier|above|previously|before)',
    r'\b(returning|going back|referring back)\s+to',
    r'\b(recall|remember|recalling)\s+(that|how|when)',
    r'\b(this|these)\s+(relates?|connects?|links?)\s+(back\s+)?to',
    r'\bearlier\s+(we|I)\s+(saw|mentioned|discussed|noted)',
    r'\bwe\'ve\s+(already\s+)?(seen|discussed|established)',
    r'\b(as|like)\s+we\s+(saw|mentioned|discussed)\s+(in|earlier)',
]

CONCEPT_CALLBACK_PATTERNS = [
    r'this\s+(concept|idea|point|notion|theme)',
    r'the\s+(aforementioned|previously\s+discussed)',
    r'(echoing|mirroring|reflecting)\s+(earlier|previous)',
]
```

**3. 新增方法 (`src/core/analyzer/structure.py`):**

- `analyze_cross_references(paragraphs)`: 检测回指结构和概念回调
- `generate_risk_card(result)`: 生成7指征风险卡片

**4. 新增API Schema (`src/api/schemas.py`):**

```python
class StructuralIndicatorResponse(BaseModel):
    id: str
    name: str
    name_zh: str
    triggered: bool
    risk_level: int
    emoji: str
    color: str
    description: str
    description_zh: str
    details: str = ""
    details_zh: str = ""

class StructuralRiskCardResponse(BaseModel):
    indicators: List[StructuralIndicatorResponse]
    triggered_count: int
    overall_risk: str
    overall_risk_zh: str
    summary: str
    summary_zh: str
    total_score: int

class RiskCardRequest(BaseModel):
    text: str = Field(..., description="Full document text to analyze")
```

**5. 新增API端点 (`src/api/routes/structure.py`):**

| 端点 Endpoint | 方法 Method | 描述 Description |
|---------------|-------------|------------------|
| `/api/v1/structure/risk-card` | POST | 获取7指征风险卡片 |
| `/api/v1/structure/indicator-config` | GET | 获取指征配置（用于UI渲染） |

### 代码示例 | Code Examples

```python
# 分析文档并获取风险卡片
from src.core.analyzer.structure import StructureAnalyzer

analyzer = StructureAnalyzer()
result = analyzer.analyze(document_text)

# 访问风险卡片
risk_card = result.risk_card
print(f"触发指征数: {risk_card.triggered_count}/7")
print(f"整体风险: {risk_card.overall_risk_zh}")

# 遍历各指征
for indicator in risk_card.indicators:
    status = indicator.emoji if indicator.triggered else "✓"
    print(f"{status} {indicator.name_zh}: {'触发' if indicator.triggered else '安全'}")
```

```python
# API调用示例
import requests

# 获取风险卡片
response = requests.post(
    "http://localhost:8000/api/v1/structure/risk-card",
    json={"text": document_text}
)
risk_card = response.json()

# 前端渲染
for indicator in risk_card["indicators"]:
    color = indicator["color"]  # #ef4444 (red) or #22c55e (green)
    emoji = indicator["emoji"]
    # 渲染带颜色的指征卡片
```

### 结果 | Result

实现了7指征结构性AI风险可视化系统：
- 支持emoji和颜色编码的风险卡片
- 增强的回指结构检测（第7条指征）
- 整体风险评估（低/中/高）
- 中英双语支持
- API端点支持前端集成

Implemented 7-indicator structural AI risk visualization system:
- Risk card with emoji and color coding
- Enhanced cross-reference detection (7th indicator)
- Overall risk assessment (low/medium/high)
- Bilingual support (Chinese/English)
- API endpoints for frontend integration

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/core/analyzer/structure.py` | MODIFY | 添加回指检测、7指征配置、风险卡片生成 |
| `src/api/schemas.py` | MODIFY | 添加风险卡片响应模式 |
| `src/api/routes/structure.py` | MODIFY | 添加风险卡片API端点 |

---

> 文档维护 | Document Maintenance:
> 每次功能开发完成后更新此文档
> Update this document after each feature completion

---

## 2026-01-01: 修复前端结构分析超时问题 | Fix Frontend Structure Analysis Timeout

### 需求 | Requirement

用户上传文档后点击开始处理，在 ThreeLevelFlow 页面出现超时错误：`timeout of 120000ms exceeded`

User encountered timeout error on ThreeLevelFlow page after uploading document: `timeout of 120000ms exceeded`

### 分析 | Analysis

**问题根源 | Root Cause:**
- 前端 axios 全局超时设置为 120 秒
- `/structure/document` API 调用 DeepSeek LLM 进行智能结构分析
- 处理长文档（311句）需要约 119 秒，接近超时边界
- 网络延迟或 API 响应略慢时触发超时

**调用链 | Call Chain:**
```
前端 ThreeLevelFlow.tsx → axios (120s timeout)
→ 后端 /api/v1/structure/document
→ SmartStructureAnalyzer.analyze()
→ httpx → DeepSeek API (实际耗时 ~119s)
```

### 方法 | Method

增加前端 axios 全局超时时间，从 120 秒增加到 300 秒（5分钟），以确保长文档 LLM 分析有足够时间完成。

Increased frontend axios global timeout from 120s to 300s (5 minutes) to allow sufficient time for LLM analysis of long documents.

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `frontend/src/services/api.ts:53` | MODIFY | axios timeout: 120000 → 300000 |

### 结果 | Result

前端请求超时时间延长到 5 分钟，解决了长文档结构分析超时问题。

Frontend request timeout extended to 5 minutes, resolving the timeout issue for long document structure analysis.


---

## 2026-01-01: 切换 LLM 提供商从 DeepSeek 官方到火山引擎 | Switch LLM Provider from DeepSeek Official to Volcengine

### 需求 | Requirement

DeepSeek 官方 API 速度太慢，切换到火山引擎提供的 DeepSeek 模型。

DeepSeek official API is too slow, switch to Volcengine-hosted DeepSeek model.

### 方法 | Method

1. 在 config.py 中添加火山引擎配置（API key、base URL、model）
2. 修改 .env 文件，将 LLM_PROVIDER 从 deepseek 改为 volcengine
3. 在所有 LLM 调用位置添加火山引擎支持，保留 DeepSeek 官方作为备选

Added Volcengine configuration to config.py and updated all LLM call locations to support Volcengine while keeping DeepSeek official as fallback.

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/config.py` | MODIFY | 添加火山引擎配置项 (volcengine_api_key, volcengine_base_url, volcengine_model) |
| `.env` | MODIFY | LLM_PROVIDER=volcengine, 添加 VOLCENGINE_* 变量，注释 DeepSeek 官方 |
| `src/core/analyzer/smart_structure.py` | MODIFY | 添加 _call_volcengine 方法，更新 _call_llm 逻辑 |
| `src/core/suggester/llm_track.py` | MODIFY | 添加 _call_volcengine 方法，更新 generate_suggestion 逻辑 |
| `src/api/routes/paragraph.py` | MODIFY | 添加火山引擎 LLM 调用支持 |
| `src/api/routes/suggest.py` | MODIFY | 添加火山引擎 LLM 调用支持（2处） |

### 配置说明 | Configuration

火山引擎 DeepSeek API 配置：
```env
LLM_PROVIDER=volcengine
VOLCENGINE_API_KEY=your-api-key
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=deepseek-v3-250324
```

### 结果 | Result

系统现在优先使用火山引擎的 DeepSeek API，预期响应速度会更快。用户需要在 .env 文件中填入火山引擎的 API key。

System now prioritizes Volcengine DeepSeek API for faster response. User needs to fill in Volcengine API key in .env file.



---

## 2026-01-01: 修复 LogicBreak Pydantic v2 验证错误 | Fix LogicBreak Pydantic v2 Validation Error

### 需求 | Requirement

三层级 De-AIGC 处理页面在结构分析完成后约 2 秒出现错误：
`2 validation errors for LogicBreak suggestion Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]`

Three-level De-AIGC processing page shows error ~2 seconds after structure analysis completion.

### 原因分析 | Root Cause

Pydantic v2 对 `Optional[str]` 的处理方式与 v1 不同。当 LLM 返回 JSON 中 `suggestion` 字段为 `null` 时，代码显式传递 `None` 值给 Pydantic 模型。在 Pydantic v2 中，即使字段定义为 `Optional[str] = None`，显式传递 `None` 时仍会验证其是否为 `str` 类型。

Pydantic v2 handles `Optional[str]` differently from v1. When explicitly passing `None`, it validates against `str` type even if field is defined as `Optional[str] = None`.

### 方法 | Method

将 `LogicBreak` 模型中的类型注解从 `Optional[str]` 改为 `str | None`（Python 3.10+ union type syntax），明确告诉 Pydantic v2 接受 `None` 值。

Changed type annotation in `LogicBreak` model from `Optional[str]` to `str | None` (Python 3.10+ union type syntax).

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/api/schemas.py:597-600` | MODIFY | 将 `suggestion: Optional[str] = None` 改为 `suggestion: str \| None = None` |

### 代码变更 | Code Change

```python
# Before 修改前
suggestion: Optional[str] = None
suggestion_zh: Optional[str] = None

# After 修改后
suggestion: str | None = None  # Use str | None for Pydantic v2 compatibility
suggestion_zh: str | None = None
```

### 结果 | Result

修复了 Pydantic v2 验证错误，三层级 De-AIGC 处理页面的结构分析功能现在可以正常工作。

Fixed Pydantic v2 validation error, Three-level De-AIGC processing structure analysis now works correctly.


---

## 2026-01-01: 添加 Step 1 和 Step 2 分析结果缓存 | Add Analysis Caching for Step 1 and Step 2

### 需求 | Requirement

三层级 De-AIGC 处理页面每次打开都会调用 LLM 进行分析，导致不必要的 API 调用和等待时间。需要缓存 Step 1 (结构分析) 和 Step 2 (衔接分析) 的结果。

Three-level De-AIGC processing page calls LLM for analysis every time it opens, causing unnecessary API calls and wait time. Need to cache Step 1 (structure analysis) and Step 2 (transition analysis) results.

### 方法 | Method

1. 在 Document 模型中添加两个 JSON 缓存字段
2. 修改 structure 和 transition API 端点，先检查缓存
3. 首次分析后将结果保存到数据库缓存

Added JSON cache fields to Document model and modified API endpoints to check cache before analysis.

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/db/models.py:33-36` | MODIFY | 在 Document 模型中添加 `structure_analysis_cache` 和 `transition_analysis_cache` JSON 字段 |
| `src/api/routes/structure.py:562-578` | MODIFY | `/document` 端点添加缓存检查和保存逻辑 |
| `src/api/routes/transition.py:198-327` | MODIFY | `/document` 端点添加缓存检查和保存逻辑 |

### 缓存机制 | Caching Mechanism

```
首次访问:
1. 检查 document.structure_analysis_cache / transition_analysis_cache
2. 缓存为空 → 调用 LLM 分析
3. 分析完成 → 保存结果到数据库
4. 返回响应

再次访问:
1. 检查缓存 → 发现有数据
2. 直接从缓存构建响应
3. 跳过 LLM 调用
```

### 数据库变更 | Database Changes

新增字段（SQLite JSON 类型，自动迁移）：
- `documents.structure_analysis_cache`: Step 1 结构分析缓存
- `documents.transition_analysis_cache`: Step 2 衔接分析缓存

### 结果 | Result

- 同一文档第二次打开三层级处理页面时，Step 1 和 Step 2 分析将从缓存加载，无需等待 LLM 响应
- 大幅减少 API 调用次数和用户等待时间
- 缓存与文档绑定，文档删除时缓存自动清除

When reopening the three-level processing page for the same document, Step 1 and Step 2 analysis will load from cache, eliminating LLM wait time. Significantly reduces API calls and user wait time.


---

## 2026-01-01: 修复 React StrictMode 导致的重复 API 调用 | Fix Duplicate API Calls from React StrictMode

### 问题 | Problem

三层级处理页面打开后，Step 1 结构分析 API 被调用两次：
- 第一次成功返回正确结果（65分，12段落）
- 第二次返回 fallback 结果（0分，unknown风险），覆盖了正确结果

React StrictMode in development mode causes useEffect to run twice, triggering duplicate API calls.

### 原因分析 | Root Cause

React.StrictMode 在开发模式下会故意执行两次渲染来检测副作用问题。这导致 `useEffect` 中的 `analyzeDocumentStructure` 被调用两次。

### 修复方法 | Solution

在 ThreeLevelFlow.tsx 中添加 `useRef` 来追踪分析状态，防止重复调用：

```typescript
// Ref to prevent duplicate API calls
const isAnalyzingRef = useRef(false);
const analyzedDocIdRef = useRef<string | null>(null);

// In useEffect check
if (documentId && !isAnalyzingRef.current && analyzedDocIdRef.current !== documentId) {
  analyzeDocumentStructure(documentId);
}

// In function, set flag at start and clear at end
if (isAnalyzingRef.current) return;
isAnalyzingRef.current = true;
// ... after success
analyzedDocIdRef.current = docId;
// ... in finally
isAnalyzingRef.current = false;
```

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `frontend/src/pages/ThreeLevelFlow.tsx:1` | MODIFY | 导入 `useRef` |
| `frontend/src/pages/ThreeLevelFlow.tsx:91-94` | MODIFY | 添加 `isAnalyzingRef` 和 `analyzedDocIdRef` |
| `frontend/src/pages/ThreeLevelFlow.tsx:98-102` | MODIFY | useEffect 中添加重复调用检查 |
| `frontend/src/pages/ThreeLevelFlow.tsx:107-156` | MODIFY | `analyzeDocumentStructure` 函数中添加防重复逻辑 |

### 结果 | Result

修复后，即使在 React StrictMode 下，结构分析 API 也只会被调用一次，正确的分析结果不会被覆盖。

After fix, structure analysis API is called only once even in React StrictMode, correct analysis result is preserved.


---

## 2026-01-01: 增强结构分析 - 添加每段具体修改建议 | Enhance Structure Analysis - Add Paragraph-Level Rewrite Suggestions

### 需求 | Requirement

结构分析只显示问题诊断不够，需要针对每一段的内容给出具体的修改意见：
1. 中文写的具体修改建议（引用原文内容可保留）
2. 用户点击某一段可展开详细的解释和修改建议
3. 包含【问题诊断】【修改策略】【改写提示】三部分

Structure analysis needs to provide specific rewrite suggestions for each paragraph, not just problem diagnosis.

### 方法 | Method

1. 增强 LLM prompt，为每个段落生成详细的中文修改建议
2. 更新 API schemas 添加新字段
3. 更新前端组件，添加可展开的详细建议面板

Enhanced LLM prompt to generate detailed Chinese rewrite suggestions with three sections: problem diagnosis, modification strategy, and rewrite hints.

### 修改的文件 | Modified Files

| 文件 File | 操作 Action | 描述 Description |
|-----------|-------------|------------------|
| `src/core/analyzer/smart_structure.py:126-139` | MODIFY | Prompt 中添加 `rewrite_suggestion_zh` 和 `rewrite_example_zh` 字段要求 |
| `src/core/analyzer/smart_structure.py:180-214` | MODIFY | JSON 输出示例中添加详细修改建议示例 |
| `src/api/schemas.py:552-557` | MODIFY | `SmartParagraphInfo` 添加 `rewrite_suggestion_zh`, `rewrite_example_zh` 字段 |
| `src/api/schemas.py:537-540` | MODIFY | `ParagraphInfo` 添加相同字段 |
| `src/api/routes/structure.py:596-599` | MODIFY | 传递新字段到响应 |
| `src/api/routes/structure.py:650-653` | MODIFY | 兼容段落列表也添加新字段 |
| `frontend/src/types/index.ts:371-374` | MODIFY | `ParagraphInfo` 类型添加新字段 |
| `frontend/src/types/index.ts:388-391` | MODIFY | `SmartParagraphInfo` 类型添加新字段 |
| `frontend/src/components/editor/StructurePanel.tsx:62-78` | MODIFY | 添加展开段落状态管理和切换函数 |
| `frontend/src/components/editor/StructurePanel.tsx:414-536` | MODIFY | 段落卡片改为可点击展开，添加详细建议面板 |

### 新增功能说明 | New Feature Description

**LLM 生成的修改建议格式：**
```
【问题诊断】段首使用显性连接词'Furthermore'，属于典型AI写作痕迹。段落结构遵循'现有方法-批评-局限性'的公式化模式。
【修改策略】1. 删除段首连接词'Furthermore'；2. 使用语义回声承接上段关键概念；3. 打散公式化结构。
【改写提示】删除'Furthermore'，改为承接上段具体内容，如'传统方法在处理高浓度盐分时表现出明显局限'。
```

**前端交互：**
- 中/高风险段落卡片右侧显示展开箭头
- 点击段落卡片可展开/收起详细建议
- 展开后显示三部分结构化建议（不同颜色高亮）
- 如有改写示例，显示在绿色框中

### 缓存注意事项 | Cache Notice

由于增加了新字段，旧的缓存数据不包含修改建议。需要清除文档的 `structure_analysis_cache` 才能获取新的分析结果。

Due to new fields, old cached data won't have rewrite suggestions. Clear `structure_analysis_cache` to get new analysis.

### 结果 | Result

用户现在可以：
1. 点击任意中/高风险段落查看详细修改建议
2. 建议包含具体的问题诊断、修改策略和改写提示
3. 建议全部使用中文，但引用原文内容保留原语言
4. 部分段落还会提供改写示例供参考

Users can now click on medium/high risk paragraphs to see detailed Chinese rewrite suggestions with problem diagnosis, modification strategy, and rewrite hints.

---

## 2026-01-01: 修复0词段落显示和自动获取段落建议 | Fix 0-Word Paragraph Display and Auto-Fetch Suggestions

### 需求 | Requirements

用户报告两个问题：
1. 某些段落显示 "0词" - 这些非内容元素不应该显示
2. 点击展开段落时显示 "请重试分析以获取详细修改建议" 而不是自动获取建议

Two issues reported:
1. Some paragraphs show "0 words" - these non-content elements shouldn't be displayed
2. Clicking to expand shows "Please retry..." instead of auto-fetching suggestions

### 方法 | Method

1. **前端过滤0词段落** / Frontend filter 0-word paragraphs:
   - 修改 `StructurePanel.tsx` 中的段落渲染逻辑
   - 使用 `filter(p => p.wordCount > 0)` 过滤掉0词段落
   - 更新 "+更多段落" 按钮显示正确的剩余数量

2. **创建单段落建议API** / Create single paragraph suggestion API:
   - 新增 `ParagraphSuggestionRequest` 和 `ParagraphSuggestionResponse` schemas
   - 在 `structure.py` 添加 `/structure/paragraph-suggestion` 端点
   - 使用 LLM 为单个段落生成【问题诊断】【修改策略】【改写提示】格式的建议

3. **前端自动获取建议** / Frontend auto-fetch suggestions:
   - 添加 `fetchedSuggestions` 状态存储已获取的建议
   - 添加 `loadingParagraphs` 状态跟踪加载中的段落
   - 展开段落时自动调用API获取建议（如果尚未获取）
   - 显示加载动画和获取到的建议

### 修改内容 | Changes

| 文件 | 修改 |
|------|------|
| `frontend/src/components/editor/StructurePanel.tsx` | 过滤0词段落、添加自动获取建议逻辑、显示加载状态 |
| `frontend/src/services/api.ts` | 添加 `structureApi.getParagraphSuggestion()` 方法 |
| `src/api/schemas.py` | 添加 `ParagraphSuggestionRequest` 和 `ParagraphSuggestionResponse` |
| `src/api/routes/structure.py` | 添加 `/structure/paragraph-suggestion` 端点 |

### 结果 | Result

1. **0词段落不再显示** - 非内容元素（标题、表格、图片等）被正确过滤
2. **自动获取建议** - 用户点击展开中/高风险段落时，系统自动调用LLM生成修改建议
3. **加载状态显示** - 获取建议时显示 "正在分析段落并生成修改建议..." 动画
4. **手动重试选项** - 如果自动获取失败，提供 "点击获取修改建议" 按钮

Users now see only real paragraphs (no 0-word elements), and clicking to expand automatically fetches suggestions via LLM API.

---

## 2026-01-01: 添加趣味等待提示语库 | Add Fun Loading Messages Library

### 需求 | Requirements

用户希望在等待LLM返回时看到更有趣的提示语，而不是简单的"Loading..."或"加载中..."。
提示语应该随机显示，让用户在等待时保持愉悦。

Users want to see fun loading messages while waiting for LLM responses instead of boring "Loading..." text.
Messages should rotate randomly to keep users entertained while waiting.

### 方法 | Method

1. **创建趣味提示语库** / Create fun message library:
   - 创建 `frontend/src/utils/loadingMessages.ts`
   - 定义多个消息类别：general（通用）、analysis（分析）、structure（结构）、suggestion（建议）、transition（衔接）、upload（上传）、paragraph（段落）
   - 每个类别包含10+条中英双语趣味提示语
   - 提供 `useRotatingLoadingMessage` React hook 实现轮播效果

2. **创建可复用组件** / Create reusable component:
   - 创建 `frontend/src/components/common/LoadingMessage.tsx`
   - 提供多种变体：`LoadingMessage`（基础）、`FullPageLoading`（全页）、`InlineLoading`（内联）、`CardLoading`（卡片）
   - 支持 size、centered、showEnglish 等配置选项

3. **应用到各页面** / Apply to all pages:
   - ThreeLevelFlow.tsx（文档加载、结构分析、衔接分析）
   - StructurePanel.tsx（段落建议加载）
   - SuggestionPanel.tsx（句子分析、建议生成）
   - Intervention.tsx（会话加载）
   - Upload.tsx（上传处理）
   - Review.tsx（结果加载）
   - History.tsx（历史加载）

### 修改内容 | Changes

| 文件 | 修改 |
|------|------|
| `frontend/src/utils/loadingMessages.ts` | 新增：趣味提示语库和轮播hook |
| `frontend/src/components/common/LoadingMessage.tsx` | 新增：可复用加载消息组件 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 替换三处加载提示 |
| `frontend/src/components/editor/StructurePanel.tsx` | 替换段落建议加载提示 |
| `frontend/src/components/editor/SuggestionPanel.tsx` | 替换句子分析和建议加载提示 |
| `frontend/src/pages/Intervention.tsx` | 替换会话加载提示 |
| `frontend/src/pages/Upload.tsx` | 替换上传按钮加载提示 |
| `frontend/src/pages/Review.tsx` | 替换结果加载提示 |
| `frontend/src/pages/History.tsx` | 替换历史加载提示 |

### 提示语示例 | Message Examples

- 通用：泡壶茶，AI正在追逐灵感... / 咖啡还没凉，稍等片刻...
- 分析：AI侦探正在破译文本密码... / 显微镜下观察中，请勿打扰...
- 结构：正在绘制文章骨架图... / X光透视文章结构中...
- 建议：灵感小精灵正在头脑风暴... / 文字魔法师施法中...
- 上传：正在打包您的文字行李... / 文件传送门开启中...
- 段落：正在为这段文字把脉... / 语言美容师设计方案中...

### 结果 | Result

用户在等待AI处理时会看到随机轮播的趣味提示语，每3-3.5秒更换一条，提升等待体验。
所有提示语均为中英双语，可配置是否显示英文部分。

Users now see randomly rotating fun messages while waiting, refreshing every 3-3.5 seconds.
All messages are bilingual (Chinese + English), with option to show/hide English.


---

## 2026-01-03: 增强结构分析详细建议功能 | Enhanced Structure Analysis Detailed Suggestions

### 需求 | Requirements

用户反馈当前的"改进建议"太简陋，需要更具针对性的意见：
1. 摘要里面要提到某内容在某章节
2. 怎样改整体的逻辑顺序
3. 分章节给出具体意见（补充内容、拆分段落、合并章节等）
4. 在建议页面醒目位置提示：基于AI的DEAIGC分析，不保证逻辑和语义，请自行斟酌

Users want more specific improvement suggestions instead of generic advice.

### 方法 | Method

1. **添加详细建议数据模型** / Add detailed suggestion data models:
   - 新增 `SectionSuggestion` 模型：章节级别的详细建议
   - 新增 `DetailedImprovementSuggestions` 模型：包含摘要建议、逻辑建议、分章节建议
   - 在 `SmartStructureResponse` 中添加 `detailed_suggestions` 字段

2. **修改后端提示词** / Modify backend prompt:
   - 更新 `SMART_STRUCTURE_PROMPT` 在 `smart_structure.py`
   - 要求LLM生成详细的 `detailed_suggestions` JSON结构
   - 包含：abstract_suggestions, logic_suggestions, section_suggestions, priority_order, overall_assessment

3. **更新API响应** / Update API response:
   - 修改 `/structure/document` 端点解析和返回详细建议
   - 将LLM返回的详细建议转换为 `DetailedImprovementSuggestions` 对象

4. **更新前端组件** / Update frontend component:
   - 添加前端类型定义 `SectionSuggestion` 和 `DetailedImprovementSuggestions`
   - 修改 `StructurePanel.tsx` 显示详细建议
   - 添加免责声明横幅

### 修改内容 | Changes

| 文件 | 修改 |
|------|------|
| `src/api/schemas.py` | 添加 `SectionSuggestion` 和 `DetailedImprovementSuggestions` 模型 |
| `src/core/analyzer/smart_structure.py` | 更新 `SMART_STRUCTURE_PROMPT` 要求生成详细建议 |
| `src/api/routes/structure.py` | 解析和返回 `detailed_suggestions` |
| `frontend/src/types/index.ts` | 添加 `SectionSuggestion` 和 `DetailedImprovementSuggestions` 接口 |
| `frontend/src/components/editor/StructurePanel.tsx` | 添加详细建议展示组件和免责声明 |

### 新增建议类型 | New Suggestion Types

- `add_content`: 补充内容 - 增加文献引用、背景描述等
- `split`: 拆分 - 将过长章节拆分为多个小节
- `merge`: 合并 - 将相关章节合并整合
- `reorder`: 调整顺序 - 重新排列章节顺序
- `restructure`: 重组 - 重新组织段落结构
- `remove_connector`: 移除连接词 - 删除AI典型的显性连接词
- `add_citation`: 补充引用 - 增加文献引用

### 结果 | Result

1. **免责声明横幅** - 在建议区域顶部显示醒目的黄色横幅提示用户谨慎参考
2. **总体评估** - 显示文档整体的AI痕迹评估
3. **摘要改进** - 提供具体的摘要修改建议（如：应提到某章内容）
4. **结构调整** - 提供整体逻辑顺序的调整意见
5. **分章节建议** - 为每个章节提供具体的修改意见，包括：
   - 章节标识和标题
   - 建议类型标签（合并/拆分/补充内容等）
   - 优先级标签（高/中/低优先）
   - 具体修改建议文字
   - 详细操作步骤列表
   - 涉及的段落位置列表

The improvement suggestions panel now shows specific, actionable advice for each section with clear disclaimers about AI-based analysis.

---

## 2026-01-03: 添加生成提示词功能 | Add Prompt Generation Feature

### 需求 | Requirements

用户希望能够生成修改提示词，配合其他AI工具（如ChatGPT、Claude）来修改论文：
1. 在step1-1, step1-2, step2的建议下面提供"生成提示词"按钮
2. 生成的提示词包含分析结果和修改建议
3. 提示用户如何使用，特别是参考文献和实验数据的处理
4. 醒目提醒"基于AI的DEAIGC分析，不保证逻辑和语义，请自行斟酌"

### 方法 | Method

1. **添加提示词生成按钮**:
   - 在详细建议区域下方添加"AI辅助修改"卡片
   - 提供两个按钮：生成全文修改提示词、生成章节修改提示词

2. **创建提示词生成逻辑**:
   - `generatePrompt('full')`: 生成完整的全文修改提示词
   - `generatePrompt('section')`: 生成章节级修改提示词
   - 提示词包含：分析结果、检测问题、具体建议、修改原则

3. **添加弹窗组件**:
   - 显示生成的提示词
   - 包含免责声明横幅
   - 包含详细使用说明
   - 特别提醒参考文献和实验数据的重要性

4. **添加复制功能**:
   - 一键复制提示词到剪贴板
   - 复制成功后显示确认状态

### 修改内容 | Changes

| 文件 | 修改 |
|------|------|
| `frontend/src/components/editor/StructurePanel.tsx` | 添加提示词生成功能、弹窗组件、复制功能 |

### 新增功能特性 | New Features

1. **生成全文修改提示词**:
   - 包含整体评估（风险分数、段落数、章节数）
   - 包含检测到的问题（线性流程、重复模式、均匀长度等）
   - 包含需要移除的显性连接词列表
   - 包含详细的分章节修改建议
   - 包含修改原则和输出要求

2. **生成章节修改提示词**:
   - 针对单个章节的修改任务
   - 包含各章节的具体建议
   - 更简洁的提示词格式

3. **使用说明**:
   - 步骤化的使用指南
   - 重要提醒（参考文献、实验数据、专业术语、格式要求）

4. **免责声明**:
   - 弹窗顶部醒目的黄色横幅
   - 中英双语提示

### 结果 | Result

用户可以：
1. 点击"生成全文修改提示词"或"生成章节修改提示词"按钮
2. 在弹窗中查看生成的提示词
3. 阅读使用说明和重要提醒
4. 一键复制提示词
5. 将提示词粘贴到其他AI工具中使用

The prompt generation feature helps users leverage other AI tools for paper revision with structured guidance.

---

## 2026-01-03: Step1-1 �ĵ��޸Ĺ�����֤ | Step1-1 Document Modification Feature Verification

### �û����� | User Requirement

��֤ Step1-1 ҳ����ĵ��޸Ĺ����Ƿ�����������

### ��֤��� | Verification Result

������֤�ɹ� - Step1-1 ҳ�����й�������������

1. **�ṹ�������**:
   - ��ȷ��ʾ�½����Ͷ�����
   - ��ȷ��Ⲣ��ʾ�ṹ���⣨�����س̶ȱ�ǩ��
   - ��Ӣ˫������

2. **�Ľ�����**:
   - ��ɫ��Ƭ��ʾ����Ե��޸Ľ���

3. **�ĵ��޸�����** (��������):
   - �ϴ��ļ� / ճ���ı� ģʽ�л�
   - �ļ��Ϸ��ϴ�����֧�� TXT/DOCX ��ʽ
   - ������ʹ��ԭ�ĵ����� ��ť
   - ȷ���޸Ĳ����� ��ť

### �������� | Test Flow

1. �ϴ�ҳ����������ı�
2. ѡ���Ԥģʽ�������ʼ����
3. �Զ���ת�� Step1-1 ҳ��
4. ҳ����ȷ��ʾ����������ĵ��޸�����
5. UI ���ֺͽ������ܾ�����

Feature verification completed successfully.

---

## 2026-01-03: Step1-1 问题点击展开建议功能 | Step1-1 Issue Click-to-Expand Suggestion Feature

### 用户需求 | User Requirement

在 Step1-1 页面，点击结构问题应能获取：
1. 详细的问题诊断
2. 多种修改策略（带难度和效果评级）
3. 可复制到其他AI工具使用的完整提示词
4. 优先修改建议和注意事项

所有建议必须基于全面的 De-AIGC 知识库，同时确保修改后的文章仍符合学术规范。

### 方法 | Method

**1. 创建 De-AIGC 知识库** (`src/prompts/structure_deaigc.py`):
- `STRUCTURE_DEAIGC_KNOWLEDGE`: 结构层面 De-AIGC 方法大全
  - 宏观结构优化（打破线性叙事、章节功能重组、打破完美对称）
  - 段落层面优化（移除显性连接词、打破公式化模式、句子长度变化）
  - 衔接层面优化（隐性逻辑衔接、学术引用作为衔接）
  - 开头与结尾优化
  - 跨段落优化
- `ISSUE_SUGGESTION_PROMPT`: 详细建议提示词模板
- `QUICK_ISSUE_SUGGESTION_PROMPT`: 快速建议提示词模板
- `format_issue_prompt()`: 格式化提示词函数

**2. 添加后端 API** (`src/api/routes/structure.py`):
- 新增 `POST /api/v1/structure/issue-suggestion` 端点
- 接收问题类型、描述、严重程度和文档ID
- 调用 LLM（支持 Volcengine/DeepSeek/Gemini）
- 返回诊断、策略、提示词、建议和注意事项

**3. 添加前端 API 方法** (`frontend/src/services/api.ts`):
- `structureApi.getIssueSuggestion()`: 调用建议端点

**4. 修改 Step1_1 页面** (`frontend/src/pages/Step1_1.tsx`):
- 问题卡片可点击，点击后展开详细建议面板
- 加载状态显示
- 展开面板显示：
  - 问题诊断（详细分析）
  - 修改策略（3种，带难度/效果标签）
  - AI修改提示词（带一键复制按钮）
  - 优先修改建议
  - 注意事项

### 修改/新增的内容 | Changes

| 文件 | 类型 | 说明 |
|------|------|------|
| `src/prompts/structure_deaigc.py` | 新增 | De-AIGC 知识库和提示词模板 |
| `src/api/routes/structure.py` | 修改 | 添加 `/issue-suggestion` 端点 (line 1415) |
| `src/api/schemas.py` | 修改 | 添加 IssueSuggestionRequest/Response |
| `frontend/src/services/api.ts` | 修改 | 添加 getIssueSuggestion 方法 |
| `frontend/src/pages/Step1_1.tsx` | 修改 | 可点击问题卡片、展开建议面板 |

### 结果 | Result

用户可以：
1. 在 Step1-1 页面点击任意结构问题
2. 查看详细的问题诊断（问题本质+具体表现）
3. 查看多种修改策略，每种标明难度和效果
4. 一键复制完整的 AI 修改提示词到其他工具使用
5. 查看优先修改建议和注意事项

**测试验证**：
- 后端 API 正常返回（经 curl 测试）
- 前端点击展开功能正常
- LLM 成功生成高质量的中文建议
- 提示词复制功能可用

截图保存于: `.playwright-mcp/step1-1-issue-suggestion-success.png`

The issue click-to-expand suggestion feature is fully implemented and tested successfully.

### Bug修复 | Bug Fix

**问题**：修改策略面板只显示难度/效果标签，策略名称和描述为空

**原因**：前端 `transformKeys` 函数将后端返回的 `snake_case` 键转换为 `camelCase`，但前端渲染代码仍使用旧的键名：
- `strategy.name_zh` → 应为 `strategy.nameZh`
- `strategy.description_zh` → 应为 `strategy.descriptionZh`
- `strategy.example_before` → 应为 `strategy.exampleBefore`
- `strategy.example_after` → 应为 `strategy.exampleAfter`

**修复**：更新 `frontend/src/pages/Step1_1.tsx` 中的属性访问名称

---

## 2026-01-03 Bug修复 | Bug Fix

### 用户需求 | User Request
重启前后端服务器

### 问题 | Issue
启动 session 时出现 500 错误：`ImportError: cannot import name 'FingerprintWord' from 'src.api.schemas'`

### 原因 | Cause
`session.py` 中引用了 `FingerprintWord` 类（第 651 行），但该类未在 `schemas.py` 中定义。

### 修改内容 | Changes

| 文件 | 类型 | 说明 |
|------|------|------|
| `src/api/schemas.py` | 修改 | 添加 `FingerprintWord` Pydantic 模型（line 121-131） |

### 结果 | Result
- 后端服务器自动热重载成功
- `/api/v1/session/start` 端点正常工作
- 健康检查通过：`{"status":"healthy"}`

---

## 2026-01-03 - 口语化级别全流程集成 | Colloquialism Level Full Integration

### 用户需求 | User Requirements

用户反馈：选择了口语化程度1级（非常学术化），但系统给出的分析意见没有指出文章实际上是非常口语化的、主观的（像日记），与学术风格不符。口语化级别的选择应该在全部步骤中使用。

### 完成的功能 | Completed Features

| 优先级 | 功能 Feature | 文件 Files | 状态 Status |
|--------|--------------|-----------|-------------|
| P0 | Level 1 风格分析能力 | `src/core/analyzer/smart_structure.py` | ✅ 完成 |
| P0 | 风格分析 Prompt | `src/core/analyzer/smart_structure.py` | ✅ 完成 |
| P0 | 风格不匹配检测与警告 | `src/core/analyzer/smart_structure.py` | ✅ 完成 |
| P1 | 后端 API 传递 colloquialism_level | `src/api/routes/structure.py` | ✅ 完成 |
| P1 | 前端传递 sessionId | `frontend/src/services/api.ts`, `frontend/src/pages/Step1_1.tsx` | ✅ 完成 |
| P1 | 前端风格警告显示 | `frontend/src/pages/Step1_1.tsx` | ✅ 完成 |
| P2 | Level 3 评分使用用户 colloquialism_level | `src/api/routes/suggest.py` | ✅ 完成 |
| P3 | Level 2 衔接分析口语化 | 待定 | ⏳ 后续优化 |

### 新增/修改的文件 | New/Modified Files

**后端修改 Backend Changes:**

| 文件 File | 类型 Type | 说明 Description |
|-----------|----------|------------------|
| `src/core/analyzer/smart_structure.py` | 修改 | 添加 StyleAnalysis Pydantic模型、风格分析prompt、`_build_style_context()`、`_check_style_mismatch()` 方法 |
| `src/api/routes/structure.py` | 修改 | step1-1 端点接收 session_id，从 session 获取 colloquialism_level |
| `src/api/schemas.py` | 修改 | DocumentStructureRequest 添加 session_id 字段 |
| `src/api/routes/suggest.py` | 修改 | 修复硬编码 tone_level=4，使用 request.colloquialism_level |

**前端修改 Frontend Changes:**

| 文件 File | 类型 Type | 说明 Description |
|-----------|----------|------------------|
| `frontend/src/services/api.ts` | 修改 | analyzeStep1_1 接收 sessionId 参数，返回类型添加 styleAnalysis |
| `frontend/src/pages/Step1_1.tsx` | 修改 | 传递 sessionId，显示风格分析结果和不匹配警告 |

### 实现细节 | Implementation Details

**1. 风格分析能力 (smart_structure.py):**

- 新增 `StyleAnalysis` Pydantic模型，包含：
  - `detected_style`: 检测到的风格级别 (0-10)
  - `style_name`/`style_name_zh`: 风格名称
  - `style_indicators`/`style_indicators_zh`: 风格判断依据
  - `mismatch_warning`/`mismatch_warning_zh`: 不匹配警告

- 新增 `COLLOQUIALISM_LEVELS` 映射：
  ```python
  0: ("Most Academic", "最学术化")
  1: ("Very Academic", "非常学术")
  ...
  10: ("Most Casual", "最口语化")
  ```

- `_build_style_context()`: 根据用户目标级别构建 prompt 上下文
- `_check_style_mismatch()`: 检测风格不匹配（差异>=3级时触发警告）

**2. 风格分析 Prompt:**

LLM 被指示分析文档的实际风格，检查：
- 人称代词频率 (I/my/we vs. 非人称)
- 缩略语存在 (don't, can't, it's)
- 情感化/主观语言
- 引用/参考文献风格
- 句子复杂度和长度变化
- 使用模糊语言 vs. 绝对陈述
- 叙事 vs. 论证结构

**3. 风格不匹配警告逻辑:**

```python
if style_diff >= 3:
    # 生成警告
    if detected_style > target_colloquialism:
        # 文档比预期更口语化
        mismatch_warning = "⚠️ 风格不匹配警告..."
    else:
        # 文档比预期更正式
        mismatch_warning = "⚠️ 风格不匹配警告..."

    # 同时添加到 structure_issues 以提高可见性
    result["structure_issues"].insert(0, {
        "type": "style_mismatch",
        ...
    })
```

**4. Level 3 评分修复:**

```python
# 之前（硬编码）
tone_level = 4

# 现在（使用用户设置）
tone_level = request.colloquialism_level
```

### 前端显示 | Frontend Display

Step1_1 页面新增"文档风格分析"卡片：
- 显示检测到的风格级别和名称
- 显示风格判断依据列表
- 如有不匹配，显示醒目的黄色警告
- 如匹配良好，显示绿色确认

### 结果 | Result

用户现在可以：
1. 在上传时选择目标口语化级别 (0-10)
2. 在 Step1-1 看到文档实际风格分析
3. 如果文章风格与目标不匹配（如选1级学术但文章很口语化），系统会显示明确警告
4. Level 3 的评分和建议会根据用户选择的级别调整

**测试验证**：
- 后端服务器启动成功，健康检查通过
- 前端 HMR 更新成功
- 风格分析功能待实际文档测试


---

### 2026-01-04 - Step1-2 功能对齐 Step1-1 | Step1-2 Feature Alignment with Step1-1

#### 需求 | Requirements
Step1-2 页面需要与 Step1-1 功能对齐：
1. 问题可展开查看详细建议
2. 问题可勾选（复选框）
3. 合并生成提示词或AI直接修改
4. 上传新文件功能

Step1-2 page needs to align with Step1-1 features:
1. Expandable issue details with suggestions
2. Checkbox selection for issues
3. Merge modify (generate prompt or AI direct modify)
4. Upload new file functionality

#### 修改内容 | Changes

| 文件 File | 类型 Type | 说明 Description |
|-----------|----------|------------------|
| `frontend/src/pages/Step1_2.tsx` | 重写 Rewrite | 完整重构以添加所有 Step1-1 功能 |

#### 实现细节 | Implementation Details

**1. UnifiedIssue 接口：**

将四种不同类型的问题统一为单一接口：
- `connector`: 显性连接词问题
- `logic_break`: 逻辑断层问题
- `paragraph_risk`: 高风险段落
- `relationship`: 关系问题

```typescript
interface UnifiedIssue {
  id: string;
  type: string;
  description: string;
  descriptionZh: string;
  severity: string;
  affectedPositions: string[];
  category: 'connector' | 'logic_break' | 'paragraph_risk' | 'relationship';
  originalData: unknown;
}
```

**2. 问题展开功能：**

- `handleIssueClick()`: 点击问题时展开/收起详情
- 调用 `structureApi.getIssueSuggestion()` 获取 LLM 建议
- 显示诊断、修改策略、AI修改提示词、优先建议、注意事项

**3. 复选框选择功能：**

- `selectedIssueIndices`: Set<number> 管理选中状态
- `toggleIssueSelection()`: 切换单个问题选择
- `toggleSelectAll()`: 全选/取消全选
- 视觉反馈：选中时显示蓝色边框

**4. 合并修改功能：**

- `openMergeConfirm()`: 打开确认对话框，支持 'prompt' 或 'apply' 模式
- `executeMergeModify()`: 调用对应 API
  - prompt 模式: `structureApi.mergeModifyPrompt()`
  - apply 模式: `structureApi.mergeModifyApply()`
- `handleRegenerate()`: AI修改可重新生成（最多3次）
- `handleAcceptModification()`: 采纳AI修改，自动填入文本输入区

**5. 文档修改上传功能：**

- 两种模式：文件上传 / 文本粘贴
- 支持 TXT、DOCX 格式
- 验证文件类型和大小限制（10MB）
- 采纳AI修改后自动切换到文本模式

#### 新增状态管理 | New State Management

```typescript
// 问题展开
const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null);
const [issueSuggestion, setIssueSuggestion] = useState<...>(null);
const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);

// 合并修改
const [selectedIssueIndices, setSelectedIssueIndices] = useState<Set<number>>(new Set());
const [showMergeConfirm, setShowMergeConfirm] = useState(false);
const [mergeMode, setMergeMode] = useState<'prompt' | 'apply'>('prompt');
const [mergeResult, setMergeResult] = useState<...>(null);
const [regenerateCount, setRegenerateCount] = useState(0);

// 文档修改
const [modifyMode, setModifyMode] = useState<'file' | 'text'>('file');
const [newFile, setNewFile] = useState<File | null>(null);
const [newText, setNewText] = useState('');
```

#### 结果 | Result

Step1-2 现在拥有与 Step1-1 完全相同的功能：
- ✅ 检测到的问题可展开查看详细 LLM 建议
- ✅ 问题可通过复选框选择（支持全选）
- ✅ 选中问题后可生成合并提示词或AI直接修改
- ✅ AI修改结果可重新生成（最多3次）或采纳
- ✅ 支持上传修改后的文件或粘贴文本继续处理
- ✅ 完整的加载状态和错误处理

---

### 2026-01-04 - Step1-2 提示词添加 Step1-1 上下文约束 | Step1-2 Prompt Add Step1-1 Context

#### 问题 | Problem
Step1-2 的修改提示词没有包含 Step1-1 的分析结果，导致 LLM 可能会把之前的改进撤销，恢复到原文的风格。

Step1-2's modification prompts didn't include Step1-1 analysis results, causing LLM to potentially revert previous improvements back to original patterns.

#### 解决方案 | Solution
在合并修改的提示词中添加 Step1-1 的上下文约束，明确告诉 LLM 保持之前的改进。

Added Step1-1 context constraints to merge-modify prompts, explicitly instructing LLM to preserve previous improvements.

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|-----------|-------------------|
| `src/api/routes/structure.py` | 1. 修改 `MERGE_MODIFY_PROMPT_TEMPLATE` 添加 `{previous_improvements}` 占位符 |
| | 2. 修改 `MERGE_MODIFY_APPLY_TEMPLATE` 添加 `{previous_improvements}` 占位符 |
| | 3. 新增 `_build_previous_improvements_context()` 函数从缓存提取上下文 |
| | 4. 更新两个 API 端点调用该函数并传递参数 |

#### 实现细节 | Implementation Details

**新增辅助函数 `_build_previous_improvements_context()`:**

```python
def _build_previous_improvements_context(document) -> str:
    # 从 Step 1-1 缓存提取:
    # - structure_issues (结构问题)
    # - style_analysis (风格分析)
    # 从 Step 1-2 缓存提取:
    # - relationship_issues (关系问题)
    
    # 返回格式化的上下文块，包含:
    # - 已识别的问题列表
    # - 关键指令：保持改进，不要撤销
```

**提示词模板更新:**

```
## ⚠️ PREVIOUS ANALYSIS CONTEXT (MUST PRESERVE):
在之前的步骤中已对文档进行了分析，识别出以下问题/改进点：
- [Step 1-1 识别的问题列表]
- 文档原始风格: [风格名称]

**CRITICAL INSTRUCTION 关键指令:**
- 必须保留已根据这些问题所做的改进
- 不要将文档恢复到被标记为有问题的模式
- 仅对当前问题进行新的改进，同时保持之前的更改不变
```

#### 结果 | Result
现在 Step1-2 的合并修改功能会：
- ✅ 自动获取 Step1-1 的分析缓存
- ✅ 将之前识别的问题作为上下文传递给 LLM
- ✅ 明确指示 LLM 保持之前的改进
- ✅ 避免 LLM 把修改后的文档又改回原来的风格

---

### 2026-01-04 - 语义回声替换功能完整实现 | Semantic Echo Replacement Full Implementation

#### 需求 | Requirements
显性连接词转隐性连接功能需要：
1. 自动提取前一段的关键概念
2. 生成具体的语义回声替换示例
3. 在问题详情和合并修改中直接提供可用的替换文本

Explicit connector to implicit connection feature needs:
1. Auto-extract key concepts from previous paragraph
2. Generate concrete semantic echo replacement examples
3. Provide usable replacement text in issue details and merge modify

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|-----------|-------------------|
| `src/core/analyzer/smart_structure.py` | Step 1-2 prompt 添加语义回声替换生成指令 |
| `src/prompts/structure_deaigc.py` | Issue Suggestion prompt 添加 `semantic_echo_replacements` 输出 |
| `src/api/routes/structure.py` | 1. 更新合并修改模板添加 `{semantic_echo_context}` |
| | 2. 新增 `_build_semantic_echo_context()` 函数 |
| | 3. 两个合并修改 API 调用新函数 |

#### 实现细节 | Implementation Details

**1. Step 1-2 Prompt 更新 (`smart_structure.py`):**

每个检测到的显性连接词现在必须包含：
```json
{
  "word": "Furthermore",
  "position": "1(2)",
  "prev_paragraph_ending": "...the statistical significance reached p<0.05.",
  "prev_key_concepts": ["statistical significance", "p-value threshold"],
  "current_opening": "Furthermore, the results demonstrate...",
  "semantic_echo_replacement": "This pattern of statistical significance extends to...",
  "replacement_explanation_zh": "用前段关键概念'statistical significance'自然承接"
}
```

**2. Issue Suggestion Prompt 更新 (`structure_deaigc.py`):**

新增输出字段：
```json
{
  "semantic_echo_replacements": [
    {
      "original_text": "原始包含显性连接词的句子",
      "connector_word": "检测到的连接词",
      "prev_paragraph_concepts": ["关键概念1", "关键概念2"],
      "replacement_text": "使用语义回声重写后的句子",
      "explanation_zh": "解释为什么这个替换有效"
    }
  ]
}
```

**3. 新增 `_build_semantic_echo_context()` 函数:**

从 Step 1-2 缓存提取语义回声替换，格式化为：
```
## 🔄 SEMANTIC ECHO REPLACEMENTS (语义回声替换 - 必须使用):

### 位置 1(2): "Furthermore"
- **原文**: Furthermore, the results demonstrate...
- **前段关键概念**: statistical significance, p-value
- **语义回声替换**: This pattern of statistical significance extends to...
- **说明**: 用前段'statistical significance'概念自然承接
```

**4. 合并修改模板更新:**

- 添加 `{semantic_echo_context}` 占位符
- 强调 LLM 必须使用提供的替换文本
- 添加 CRITICAL 规则确保替换被执行

#### 流程 | Flow

```
Step 1-2 分析
    ↓
检测显性连接词 + 提取前段关键概念 + 生成语义回声替换
    ↓
保存到 step1_2_cache
    ↓
用户点击问题展开 → Issue Suggestion 生成详细替换建议
    ↓
用户选择合并修改 → _build_semantic_echo_context() 提取替换
    ↓
LLM 收到具体替换指令 → 直接使用替换文本
```

#### 结果 | Result

现在系统可以：
- ✅ 自动检测所有显性连接词
- ✅ 提取前一段的关键概念
- ✅ 生成可直接使用的语义回声替换文本
- ✅ 在问题详情中显示具体替换示例
- ✅ 在合并修改时强制使用这些替换
- ✅ 生成的替换保持学术风格和原文含义

---

### 2026-01-04 - Level2/Level3 改名为 Step2/Step3 | Rename Level2/Level3 to Step2/Step3

#### 需求 | Requirements
1. 将 Level2 改名为 Step2，Level3 改名为 Step3
2. Step2 需要与 Step1-2 相同的功能：多选问题、合并修改（提示词/直接修改）、上传新文件、确认/跳过
3. 合并修改时需注明前面改了什么，哪些可以动哪些不能动

1. Rename Level2 to Step2, Level3 to Step3
2. Step2 needs same features as Step1-2: multi-select issues, merge modify (prompt/apply), file upload, confirm/skip
3. Merge modify must note previous improvements and what can/cannot be changed

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `frontend/src/pages/Step2.tsx` | 新建文件，实现完整的 Step2 页面，包含多选问题、合并修改、文件上传等功能 |
| `frontend/src/pages/Level2.tsx` | 删除（已被 Step2.tsx 替代） |
| `frontend/src/App.tsx` | 路由从 `/flow/level2/` 改为 `/flow/step2/`，导入 Step2 组件 |
| `frontend/src/types/index.ts` | `SessionStep` 类型添加 `'step2' | 'step3'`（保持 level2/level3 向后兼容） |
| `frontend/src/pages/Step1_2.tsx` | 导航目标从 `/flow/level2/` 改为 `/flow/step2/`；进度指示器更新 |
| `frontend/src/pages/Step1_1.tsx` | 进度指示器从 "Level 2 → Level 3" 改为 "Step 2 → Step 3" |
| `frontend/src/pages/History.tsx` | 步骤路由和标签更新，添加 step2/step3 支持（保持 level2/level3 向后兼容） |
| `frontend/src/pages/Intervention.tsx` | `sessionApi.updateStep` 从 'level3' 改为 'step3' |
| `frontend/src/pages/Yolo.tsx` | `sessionApi.updateStep` 从 'level3' 改为 'step3' |
| `frontend/src/pages/ThreeLevelFlow.tsx` | UI 文本和注释从 Level 2/Level 3 改为 Step 2/Step 3 |

#### Step2.tsx 主要功能 | Step2.tsx Main Features

**多选功能:**
- 问题列表前加复选框
- 支持全选/取消全选
- 显示选中数量

**合并修改功能:**
- 生成提示词模式：调用 `structureApi.mergeModifyPrompt()`
- AI直接修改模式：调用 `structureApi.mergeModifyApply()`
- 结果显示支持复制和采纳
- 重新生成限制3次

**上下文保护:**
```typescript
const enhancedNotes = `${mergeUserNotes}

【重要】这是 Step 2（衔接分析）的修改。
Step 1-1 和 Step 1-2 中已经对文档结构和段落关系进行了分析和改进。
请务必保持这些改进，只针对当前选中的衔接问题进行修改。`;
```

**文件上传功能:**
- 支持上传 .txt/.md 文件
- 支持直接粘贴文本
- 验证后填入修改区域

#### 结果 | Result

- ✅ Level2/Level3 全面改名为 Step2/Step3
- ✅ Step2 具备与 Step1-2 相同的功能（多选、合并修改、上传）
- ✅ 路由和导航已更新
- ✅ 历史页面支持新旧步骤名称
- ✅ 合并修改时自动注入上下文保护说明
- ✅ ThreeLevelFlow 遗留组件也已更新

---

### 2026-01-04 - 修复 YOLO 模式完整 LLM 调用链路 | Fix YOLO Mode Complete LLM Call Chain

#### 问题分析 | Problem Analysis

YOLO 模式存在以下严重问题，导致其无法真正完成 De-AIGC 处理：

1. **Yolo.tsx 只是模拟处理**：只是轮询进度并显示随机生成的日志，没有调用真实的 LLM API
2. **ThreeLevelFlow YOLO 模式只分析不修改**：Step 1-1/1-2 和 Step 2 只调用分析 API，没有调用 `mergeModifyApply` 应用修改
3. **Step 3 后端缺失自动处理逻辑**：没有自动遍历句子并应用 LLM 建议的 API
4. **修改不累积**：每一步都是独立执行，后一步没有基于前一步的修改结果

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/api/routes/session.py` | 新增 `/session/{session_id}/yolo-process` API 端点，自动处理所有句子 |
| `frontend/src/services/api.ts` | 新增 `sessionApi.yoloProcess()` 方法，支持 10 分钟超时 |
| `frontend/src/pages/Yolo.tsx` | 完全重写，使用真实的 `yoloProcess` API 调用 |
| `frontend/src/pages/ThreeLevelFlow.tsx` | 修改 `startYoloProcessing()`，自动调用 `mergeModifyApply` 应用修改 |

#### 后端 yolo-process API | Backend yolo-process API

新增 `/session/{session_id}/yolo-process` 端点：
- 遍历所有句子
- 对每个句子调用 LLMTrack 和 RuleTrack 获取建议
- 选择风险降低最多的建议并自动应用
- 跳过低风险句子（分数 < 25）
- 返回完整的处理日志

#### 调用链路对比 | Call Chain Comparison

**修复前：**
```
Step 1-1: analyzeStep1_1 → 只记日志 → 没有修改
Step 1-2: analyzeStep1_2 → 只记日志 → 没有修改
Step 2:   analyzeDocument → 只记日志 → 没有修改
Step 3:   导航到 Yolo.tsx → 模拟日志 → 没有 LLM 调用
```

**修复后：**
```
Step 1-1: analyzeStep1_1 → mergeModifyApply → 记录日志 → 应用修改
Step 1-2: analyzeStep1_2 → mergeModifyApply → 记录日志 → 应用修改（保持 1-1 改进）
Step 2:   analyzeDocument → mergeModifyApply → 记录日志 → 应用修改（保持 1-1/1-2 改进）
Step 3:   导航到 Yolo.tsx → yoloProcess API → LLMTrack/RuleTrack → 逐句应用最佳建议
```

#### 结果 | Result

- ✅ YOLO 模式现在使用真实的 LLM 调用
- ✅ Step 1-1/1-2/2 自动应用修改（与干预模式相同的 API）
- ✅ Step 3 自动处理所有句子并选择最佳建议
- ✅ 每一步的修改都会注入上下文保护，保持前面步骤的改进
- ✅ 显示真实的处理日志和风险降低统计

---

### 2026-01-04: Citation格式保护强化 / Citation Format Protection Enhancement

#### 需求 | Requirement

用户要求：Citation的格式不要做任何改变。例如 `(Johnson et al., 2019)` 不能变成 `Johnson et al. (2019)`。

#### 问题分析 | Problem Analysis

之前的LLM prompt中有"CITATION ENTANGLEMENT"技巧，指示LLM将括号引用转换为叙述形式，这违反了用户"citation格式不变"的要求。

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/core/suggester/llm_track.py` | 将"CITATION ENTANGLEMENT"改为"CITATION PRESERVATION"，明确禁止修改citation格式 |
| `src/core/suggester/llm_track.py` | 强化PARAPHRASE PROTECTION，明确禁止改变citation格式 |
| `src/core/validator/quality_gate.py` | 新增 `_check_citation_format()` 方法，验证citation格式是否保持不变 |
| `src/core/validator/quality_gate.py` | 在validate中添加Layer 2.5: Citation format check |
| `src/core/validator/quality_gate.py` | 在_determine_action中添加citation_format失败返回"reject" |

#### Prompt修改 | Prompt Changes

**Before (CITATION ENTANGLEMENT):**
```
Transform parenthetical citations into narrative form to break AI pattern:
- "Smith (2023) observed this phenomenon..."
- "As Smith (2023) noted, this phenomenon..."
```

**After (CITATION PRESERVATION):**
```
Citations MUST remain in their EXACT original format. DO NOT modify:
- Parenthetical citations: "(Smith, 2023)" → KEEP AS-IS
- Numeric citations: "[1]", "[2,3]" → KEEP AS-IS
FORBIDDEN:
- Do NOT convert "(Smith, 2023)" to "Smith (2023)"
- Do NOT move citations to different positions
```

#### 验证层新增 | New Validation Layer

`_check_citation_format()`:
1. 使用正则表达式从原文提取所有citation
2. 检查每个citation是否以完全相同的格式存在于修改后的文本中
3. 如果有任何citation格式改变，检查失败

#### 结果 | Result

- ✅ Citation格式在LLM改写过程中保持不变
- ✅ 质量门控验证citation格式完整性
- ✅ 格式改变的建议会被拒绝

---

### 2026-01-04: 后端步骤名称统一 / Backend Step Name Unification

#### 需求 | Requirement

将后端 valid_steps 中的 `level2`, `level3` 改为 `step2`, `step3`，保持前后端步骤名称一致。

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `src/api/routes/session.py` | `valid_steps = ["step1-1", "step1-2", "level2", "level3", "review"]` → `["step1-1", "step1-2", "step2", "step3", "review"]` |
| `frontend/src/pages/Yolo.tsx` | `sessionApi.updateStep(sessionId, 'level3')` → `'step3'` |
| `src/db/models.py` | 注释更新 |
| `src/api/schemas.py` | 注释更新 |

#### YOLO 模式测试结果 | YOLO Mode Test Results

使用 `test_documents/test_high_risk.txt` 进行测试：

| 步骤 | 处理结果 |
|------|---------|
| Step 1-1 | 风险 70 (High)，识别 5 个章节 |
| Step 1-2 | 风险 70 (High)，9处连接词过度使用 |
| Step 2 | 5个过渡问题 |
| Step 3 | 9句 LLM 修改，14句跳过，用时 2.5 分钟 |

**改写示例：**
- "Furthermore, we explore the pivotal role..." → "The mitigation of climate change is examined here..."
- "The tapestry of environmental issues..." → "Contemporary environmental challenges are characterized by..."

**观察到被替换的高风险词：** Furthermore, pivotal, multifaceted, holistic, tapestry, nuanced, comprehensive, elucidate

#### 结果 | Result

- ✅ 后端步骤名称与前端统一（level2→step2, level3→step3）
- ✅ YOLO 模式完整调用链路正常工作
- ✅ 高风险句子成功改写，风险分数降低

---

### 2026-01-04: DEAI Engine 2.0 三层防御模型实现 | DEAI Engine 2.0 Three-Layer Defense Model Implementation

#### 需求 | Requirement

基于 `doc/223.md` 提案，实现 DEAI Engine 2.0 的三层防御模型增强功能：
- L1: 硬性词汇指纹（已有 LEVEL_1_FINGERPRINTS）
- L2: 句法空洞检测（新增）
- L3: 信息密度与学术锚点分析（新增）

以及配套的上下文免疫机制、生成后自检、动态提示词构建、Auto-fix模板库等功能。

#### 方法 | Method

分析 223.md 提案与现有系统的能力对比，识别需要新增的功能。经用户确认以下设计决策：
- spaCy 模型：`en_core_web_md`（40MB，平衡准确度与性能）
- 上下文免疫降权比例：50%（P0词周围有学术锚点时）
- P0词黑名单：LEVEL_1 全部 + 部分高风险 LEVEL_2 词
- Auto-fix 模式：展示预览，用户确认后应用

#### 修改内容 | Changes

| 文件 File | 修改 Modification |
|----------|-------------------|
| `data/fingerprints/safe_replacements.json` | **新建** - SafeReplacementDB，包含 P0 词安全替换映射、上下文提示、禁用词列表 |
| `src/core/analyzer/fingerprint.py` | **增强** - 添加上下文免疫机制，P0词周围有学术锚点时降权50% |
| `src/core/validator/quality_gate.py` | **增强** - 添加 `verify_suggestion()` 生成后自检，检测P0词和新引入指纹 |
| `src/core/analyzer/syntactic_void.py` | **新建** - 句法空洞检测器，使用spaCy依存句法树检测语义空洞模式 |
| `src/core/analyzer/anchor_density.py` | **新建** - 学术锚点密度分析器，检测幻觉风险（>50词段落，锚点密度<5%） |
| `src/core/suggester/prompt_builder.py` | **新建** - 动态诊疗提示词构建器，根据诊断结果组装针对性Prompt |
| `src/core/suggester/autofix_templates.py` | **新建** - Auto-fix句式模板库，40+规则的确定性替换模板 |

#### 新增功能详解 | New Features Details

**1. 上下文免疫机制 (Context Immunity)**

```python
# fingerprint.py - detect_with_context_immunity()
ACADEMIC_ANCHOR_PATTERNS = [
    r'\d+\.?\d*%',           # 百分比: 14.2%, 100%
    r'\d+(?:\.\d+)?\s*(?:kg|g|mg|μg|L|mL|μL|mol|M|mM|°C|K|Pa|Hz|kHz|MHz|nm|μm|mm|cm|m|km)',  # 带单位数字
    r'\([A-Z][a-zA-Z]+(?:\s+(?:et\s+)?al\.?)?,?\s*\d{4}[a-z]?\)',  # 括号引用
    r'\[[0-9,\s-]+\]',       # 数字引用 [1], [2,3]
    r'\b[A-Z]{2,}(?:-\d+)?\b',  # 缩写 ANOVA, COVID-19
    # ... 14种学术锚点模式
]

# 当周围5 token内有学术锚点时，权重降低50%
if has_anchor:
    match.risk_weight *= 0.5  # IMMUNITY_WEIGHT_FACTOR
    match.immunity_reason = f"academic_anchor_nearby:{anchor_type}"
```

**2. 生成后自检 (Post-Generation Validation)**

```python
# quality_gate.py - verify_suggestion()
def verify_suggestion(self, original: str, suggestion: str) -> SuggestionValidationResult:
    # 1. 检查P0词黑名单
    blocked_words = self._check_p0_words(suggestion)
    if blocked_words:
        return SuggestionValidationResult(passed=False, action="retry_without_p0")

    # 2. 检查是否引入新指纹
    introduced = self._get_introduced_fingerprints(original_fps, suggestion_fps)
    if introduced:
        return SuggestionValidationResult(passed=False, action="retry")

    return SuggestionValidationResult(passed=True, action="accept")
```

**3. 句法空洞检测器 (Syntactic Void Detector)**

检测语义空洞但语法正确的 AI 句式：
- "X plays a pivotal role in the comprehensive landscape of Y"
- "serves as a testament to the significance of"
- "It is important to note that..."

使用 spaCy 依存句法树分析抽象动词+抽象名词链条。

**4. 学术锚点密度分析器 (Anchor Density Analyzer)**

检测 14 种学术锚点类型（数字、百分比、引用、化学式、统计术语等），计算段落锚点密度：
- 阈值：>50词段落，锚点密度<5% → 标记幻觉风险

**5. 动态诊疗提示词构建器 (Dynamic Prompt Builder)**

根据诊断出的问题类型（P0指纹、句法空洞、线性逻辑、低锚点密度等）动态组装针对性 Prompt：

| 诊断问题 | Prompt策略 |
|---------|-----------|
| P0_FINGERPRINT | "Replace with a concrete action verb describing methodology" |
| SYNTACTIC_VOID | "Sentence is semantically empty. Rewrite to state specific findings" |
| LINEAR_LOGIC | "Reorganize using contrastive/causal structure" |
| LOW_ANCHOR_DENSITY | "Rewrite to include specific data or quantities" |

**6. Auto-fix 句式模板库**

40+ 确定性替换规则：

| AI句式 | Auto-fix操作 |
|--------|-------------|
| "It is important to note that X" | 删除开头 → "X" (首字母大写) |
| "X plays a crucial role in Y" | → "X affects Y" |
| "Due to the fact that X" | → "Because X" |
| "In the context of X" | → "For X" 或 "In X" |

#### SafeReplacementDB 结构 | SafeReplacementDB Structure

```json
{
  "_meta": {"version": "1.0.0", "description": "DEAI Engine 2.0 Safe Replacement Database"},
  "level_1_words": {
    "delve": {
      "safe_replacements": ["explore", "examine", "investigate", "study", "analyze"],
      "context_hints": {
        "methodology": ["investigate", "analyze"],
        "literature": ["examine", "explore"],
        "data": ["study", "analyze"]
      },
      "never_use": ["delve", "delves", "delving", "dive deep", "plunge into"],
      "risk_level": "level_1"
    }
    // ... 58个LEVEL_1词 + 20个高频LEVEL_2词
  },
  "p0_blocklist": ["delve", "delves", "delving", "tapestry", "tapestries", ...]
}
```

#### 架构同步 | Architecture Synchronization

实现了跨 Step1/2/3 的诊断结果流转：

```
Step1 (StructureAnalyzer)
    ↓ 输出：anchor_density, syntactic_void_score, structural_issues
Step2 (TransitionAnalyzer)
    ↓ 输入：Step1诊断结果
    ↓ 输出：transition_issues, autofix_suggestions
Step3 (LLMTrack/RuleTrack)
    ↓ 输入：Step1+Step2诊断结果
    ↓ 使用：PromptBuilder动态组装Prompt
    ↓ 验证：verify_suggestion()自检
```

#### 结果 | Result

- ✅ 上下文免疫机制 - P0词周围有学术锚点时降权50%，减少误报
- ✅ 生成后自检 - 检测P0词和新引入指纹，防止"越改越AI"
- ✅ SafeReplacementDB - 78个高风险词的安全替换映射
- ✅ 句法空洞检测器 - 使用spaCy检测10+种语义空洞模式
- ✅ 学术锚点密度分析 - 检测14种锚点类型，识别幻觉风险段落
- ✅ 动态诊疗提示词 - 9种问题类型的针对性Prompt策略
- ✅ Auto-fix模板库 - 40+规则的确定性替换，支持预览确认
