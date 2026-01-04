# AcademicGuard

**英文论文 AIGC 检测与人源化协作引擎**
**Academic Paper AIGC Detection & Human-AI Collaborative Humanization Engine**

> 🚀 **最新更新 (2026-01-04)**: 全新的三阶分析流程 (Three-Level Flow)、风格检测 (Style Analysis)、批量 AI 修改 (Merge Modify) 与语义回声 (Semantic Echo) 功能已上线！

---

## 📖 项目简介 | Introduction

AcademicGuard 是一套集"多维检测"与"人机协作改写"于一体的深度 De-AIGC 工具。不同于简单的同义词替换，我们采用**三阶分析架构 (Three-Level Analysis)**，从全文章节结构、段落逻辑关系到句子指纹特征，全方位降低被 Turnitin、GPTZero 等检测器误判的风险，同时显著提升文章的学术性与可读性。

**核心理念：AI 教你改，而非 AI 替你改**
**Core Philosophy: AI guides you to revise, not revise for you**

---

## 🌟 核心特性 | Key Features

### 🔄 全新三阶分析流程 (Three-Level Flow)

我们采用由宏观到微观的渐进式优化流程：

#### **Step 1-1: 结构分析 (Structure Analysis)**
- **全篇扫描**: 检测线性流程、重复模式、均句长度等 AI 典型特征。
- **风格检测**: 自动识别文章口语化等级 (0-10)，并与目标风格（如期刊论文级）对比，发出不匹配警告。
- **详细建议**: 提供分章节的具体修改建议（拆分、合并、补充内容等）。
- **批量修改**: 支持勾选多个问题，生成 AI 提示词或直接进行 AI 修改。

#### **Step 1-2: 关系分析 (Relationship Analysis)**
- **逻辑断层检测**: 识别段落间缺乏语义连接的断点。
- **显性连接词识别**: 捕捉 "Furthermore", "Moreover", "In conclusion" 等 AI 高频使用的连接词。
- **语义回声 (Semantic Echo)**: 自动提取上一段的核心概念，生成自然的承接句替代显性连接词。

#### **Step 2: 衔接优化 (Transition Optimization)**
- **深度衔接修复**: 专注于段落间的流畅过渡。
- **批量处理**: 整合 Step 1-2 的发现，支持批量生成优化的过渡句。
- **上下文保护**: 修改时自动保护前序步骤的优化成果。

#### **Step 3: 句子精修 (Sentence Polishing)**
- **指纹消除**: 识别并替换 40+ 高频 AI 指纹词和短语。
- **句式重组**: 打破公式化句型，增加句式多样性。
- **双轨建议**: 提供 LLM (智能改写) 和 Rule (规则替换) 两种建议。
- **干预/YOLO 模式**: 支持逐句精修（干预模式）或全自动处理（YOLO 模式）。

### 🛡️ 硬核 De-AIGC 技术

- **CAASS v2.0 评分系统**: 基于上下文感知的动态风险评分，结合 ONNX PPL (困惑度) 模型。
- **PPL 可视化**: 实时显示句子的困惑度，通过 Emoji (🤯/⚠️/🤖) 直观展示 AI 特征风险。
- **突发性 (Burstiness) 分析**: 检测句子长度和结构的单一性。
- **智能保护**: 自动锁定学术术语、统计数据 (p < 0.05) 和引用格式，防止被错误修改。

### 💡 智能协作功能

- **Merge Modify (合并修改)**: 在 Step 1 & 2 中，支持多选问题，一键生成针对性的 AI 修改提示词 (Prompt) 或直接应用修改。
- **Unified Task List (统一任务列表)**: 全新的历史记录页面，统一管理所有文档和会话，实时查看各阶段进度。
- **口语化程度控制**: 0-10 级可调，从"极度学术"到"日常口语"，全程贯穿分析与修改建议。

---

## 🛠️ 技术栈 | Tech Stack

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI (Python 3.8+), SQLAlchemy (Async), SQLite |
| **前端** | React 18, TypeScript, Vite, Zustand, TailwindCSS |
| **AI/NLP** | ONNX (PPL Model), spaCy, Transformers |
| **LLM 集成** | Claude, OpenAI, Volcengine (豆包), DeepSeek, Gemini |
| **工具** | Git, PowerShell |

---

## 🚀 快速开始 | Quick Start

### 环境要求 | Requirements

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 安装 | Installation

```bash
# 1. 克隆项目
git clone <repository-url>
cd DEAI

# 2. 创建虚拟环境并安装后端依赖
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install
cd ..
```

### 配置 | Configuration

1. 复制环境配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入至少一个 LLM 的 API Key：
   ```env
   # 推荐使用 Volcengine 或 DeepSeek 以获得高性价比
   VOLCENGINE_API_KEY=your_key
   VOLCENGINE_ENDPOINT_ID=your_endpoint_id
   
   # 或者
   OPENAI_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   GEMINI_API_KEY=your_key
   ```

### 运行 | Run

**方式一：使用启动脚本（推荐）**

```bash
# Windows
scripts\dev.bat

# Linux/Mac
chmod +x scripts/dev.sh
./scripts/dev.sh
```

**方式二：手动启动**

```bash
# 终端 1 - 启动后端
venv\Scripts\activate  # Windows
uvicorn src.main:app --reload --port 8000

# 终端 2 - 启动前端
cd frontend
npm run dev
```

**访问地址：**
- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

---

## 📂 项目结构 | Project Structure

```
DEAI/
├── src/                    # FastAPI 后端源码
│   ├── api/                # API 路由与数据模型
│   │   ├── routes/         # 核心路由 (structure, suggest, session...)
│   │   └── schemas.py      # Pydantic 模型
│   ├── core/               # 核心业务逻辑
│   │   ├── analyzer/       # 分析器 (Structure, PPL, Fingerprint)
│   │   ├── suggester/      # 改写建议引擎
│   │   └── preprocessor/   # 预处理 (分句, 白名单)
│   ├── db/                 # 数据库模型 (SQLite)
│   └── prompts/            # LLM 提示词模板 (De-AIGC 核心知识库)
├── frontend/               # React 前端源码
│   ├── src/
│   │   ├── components/     # UI 组件 (RiskCard, StructurePanel...)
│   │   ├── pages/          # 页面 (Step1_1, Step1_2, Step2, Step3...)
│   │   ├── services/       # API 客户端
│   │   └── stores/         # Zustand 状态管理
│   └── ...
├── data/                   # 数据资源
│   ├── fingerprints/       # AI 指纹词库
│   └── terms/              # 术语白名单
└── doc/                    # 开发文档
```

---

## 📝 许可证 | License

MIT License

---

## 🔧 双模式系统 | Dual-Mode System

AcademicGuard 支持两种运行模式，通过环境变量 `SYSTEM_MODE` 切换：

| 模式 Mode | 登录 Login | 支付 Payment | 用途 Purpose |
|-----------|-----------|--------------|--------------|
| `debug` (默认) | 不需要 | 免费 | 开发测试 |
| `operational` | 需要 | 按字数收费 | 正式运营 |

### 环境变量配置 | Environment Configuration

```env
# 系统模式 | System Mode
SYSTEM_MODE=debug  # 可选: debug | operational

# 中央平台配置 (运营模式需要) | Central Platform (for operational mode)
PLATFORM_BASE_URL=https://api.yourplatform.com
PLATFORM_API_KEY=your_api_key
PLATFORM_APP_ID=academicguard

# 定价配置 | Pricing
PRICE_PER_100_WORDS=2.0
MINIMUM_CHARGE=50.0

# 安全配置 | Security
JWT_SECRET_KEY=your-super-secret-key
JWT_EXPIRE_MINUTES=1440

# 任务配置 | Task
TASK_EXPIRY_HOURS=24
```

### 计费规则 | Billing Rules

- **计费单位**: 100词/单元，向上取整
- **定价**: ¥2.0 / 100词
- **最低消费**: ¥50.0
- **字数统计**: 自动排除参考文献部分

---

## 📡 中央平台预留接口 | Central Platform Reserved Interfaces

本节详细描述了 AcademicGuard 与中央平台对接所需的全部接口规范。运营模式下，系统会调用这些接口进行用户认证和支付处理。

### 认证接口 | Authentication Interfaces

#### 1. 发送短信验证码 | Send SMS Code

**功能描述 | Description:**
向用户手机发送短信验证码，用于登录验证。

**请求 | Request:**
```http
POST {PLATFORM_BASE_URL}/api/v1/auth/send-sms
Content-Type: application/json
```

**请求体 | Request Body:**
```json
{
    "phone": "13800138000",
    "app_id": "academicguard"
}
```

**响应 | Response:**
```json
{
    "success": true,
    "message": "sent",
    "expires_in": 300
}
```

**字段说明 | Field Description:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 11位手机号码 |
| app_id | string | 是 | 应用ID，固定为 "academicguard" |
| success | boolean | - | 是否发送成功 |
| expires_in | integer | - | 验证码有效期（秒） |

---

#### 2. 验证码登录 | Verify SMS Code & Login

**功能描述 | Description:**
验证短信验证码，返回用户信息和访问令牌。

**请求 | Request:**
```http
POST {PLATFORM_BASE_URL}/api/v1/auth/verify-sms
Content-Type: application/json
```

**请求体 | Request Body:**
```json
{
    "phone": "13800138000",
    "code": "123456",
    "app_id": "academicguard"
}
```

**响应 | Response:**
```json
{
    "success": true,
    "user_id": "platform_uid_xxx",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "refresh_token_xxx",
    "expires_in": 86400,
    "user_info": {
        "phone": "138****8000",
        "nickname": "用户昵称"
    }
}
```

**字段说明 | Field Description:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 11位手机号码 |
| code | string | 是 | 4-6位短信验证码 |
| user_id | string | - | 平台用户唯一ID |
| access_token | string | - | JWT访问令牌 |
| refresh_token | string | - | 刷新令牌 |
| expires_in | integer | - | 令牌有效期（秒） |

---

#### 3. 获取用户信息 | Get User Info

**功能描述 | Description:**
根据用户ID获取用户基本信息。

**请求 | Request:**
```http
GET {PLATFORM_BASE_URL}/api/v1/users/{user_id}
Authorization: Bearer {PLATFORM_API_KEY}
```

**响应 | Response:**
```json
{
    "user_id": "platform_uid_xxx",
    "phone": "138****8000",
    "nickname": "用户昵称",
    "created_at": "2024-01-01T10:00:00Z"
}
```

---

#### 4. 刷新令牌 | Refresh Token

**功能描述 | Description:**
使用刷新令牌获取新的访问令牌。

**请求 | Request:**
```http
POST {PLATFORM_BASE_URL}/api/v1/auth/refresh
Content-Type: application/json
```

**请求体 | Request Body:**
```json
{
    "refresh_token": "refresh_token_xxx"
}
```

**响应 | Response:**
```json
{
    "success": true,
    "access_token": "new_jwt_token",
    "expires_in": 86400
}
```

---

### 支付接口 | Payment Interfaces

#### 1. 创建支付订单 | Create Payment Order

**功能描述 | Description:**
为文档处理任务创建支付订单，返回支付链接或二维码。

**请求 | Request:**
```http
POST {PLATFORM_BASE_URL}/api/v1/payments/create
Authorization: Bearer {PLATFORM_API_KEY}
Content-Type: application/json
```

**请求体 | Request Body:**
```json
{
    "app_id": "academicguard",
    "external_order_id": "task_uuid_xxx",
    "user_id": "platform_uid_xxx",
    "amount": 50.00,
    "currency": "CNY",
    "description": "AcademicGuard - 3200词文档处理",
    "notify_url": "https://yoursite.com/api/v1/payment/callback",
    "return_url": "https://yoursite.com/payment/success",
    "metadata": {
        "document_id": "doc_xxx",
        "word_count": 3200
    }
}
```

**响应 | Response:**
```json
{
    "success": true,
    "order_id": "platform_order_xxx",
    "payment_url": "https://pay.platform.com/checkout/xxx",
    "qr_code_url": "https://pay.platform.com/qr/xxx.png",
    "expires_at": "2024-01-01T12:00:00Z",
    "amount": 50.00,
    "currency": "CNY"
}
```

**字段说明 | Field Description:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| external_order_id | string | 是 | 本地任务ID，用于关联 |
| user_id | string | 是 | 平台用户ID |
| amount | float | 是 | 支付金额（人民币） |
| notify_url | string | 是 | 支付成功回调地址 |
| return_url | string | 否 | 支付成功后跳转地址 |
| order_id | string | - | 平台订单ID |
| payment_url | string | - | 支付页面链接 |
| qr_code_url | string | - | 扫码支付二维码图片URL |

---

#### 2. 查询订单状态 | Check Order Status

**功能描述 | Description:**
查询支付订单的当前状态。

**请求 | Request:**
```http
GET {PLATFORM_BASE_URL}/api/v1/payments/{order_id}/status
Authorization: Bearer {PLATFORM_API_KEY}
```

**响应 | Response:**
```json
{
    "order_id": "platform_order_xxx",
    "external_order_id": "task_uuid_xxx",
    "status": "paid",
    "amount": 50.00,
    "paid_at": "2024-01-01T10:30:00Z",
    "payment_method": "wechat"
}
```

**状态值说明 | Status Values:**
| 状态 | 说明 |
|------|------|
| `created` | 订单已创建，待支付 |
| `pending` | 支付处理中 |
| `paid` | 支付成功 |
| `failed` | 支付失败 |
| `cancelled` | 订单已取消 |
| `refunded` | 已退款 |

---

#### 3. 申请退款 | Request Refund

**功能描述 | Description:**
对已支付订单申请退款。

**请求 | Request:**
```http
POST {PLATFORM_BASE_URL}/api/v1/payments/{order_id}/refund
Authorization: Bearer {PLATFORM_API_KEY}
Content-Type: application/json
```

**请求体 | Request Body:**
```json
{
    "amount": 50.00,
    "reason": "User requested cancellation before processing"
}
```

**响应 | Response:**
```json
{
    "success": true,
    "refund_id": "refund_xxx",
    "refund_amount": 50.00,
    "refund_status": "processing"
}
```

---

#### 4. 支付回调 | Payment Callback (Webhook)

**功能描述 | Description:**
平台在支付状态变更时，向本系统发送回调通知。

**请求 | Request (由平台发送):**
```http
POST https://yoursite.com/api/v1/payment/callback
Content-Type: application/json
X-Signature: hmac_sha256_signature
```

**请求体 | Request Body:**
```json
{
    "order_id": "platform_order_xxx",
    "external_order_id": "task_uuid_xxx",
    "status": "paid",
    "amount": 50.00,
    "paid_at": "2024-01-01T10:30:00Z",
    "payment_method": "wechat",
    "timestamp": 1704096600,
    "signature": "hmac_sha256_signature_string"
}
```

**签名验证 | Signature Verification:**
```python
import hmac
import hashlib

def verify_signature(payload: dict, signature: str, api_key: str) -> bool:
    # Remove signature from payload for verification
    data = {k: v for k, v in payload.items() if k != 'signature'}
    # Sort and concatenate
    sorted_data = '&'.join(f'{k}={v}' for k, v in sorted(data.items()))
    # Calculate HMAC-SHA256
    expected = hmac.new(
        api_key.encode(),
        sorted_data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**本系统响应 | Our Response:**
```json
{
    "status": "processed",
    "message": "Payment callback processed successfully"
}
```

---

### 接口错误码 | Error Codes

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求体格式 |
| 401 | 认证失败 | 检查API Key或Token |
| 403 | 权限不足 | 检查用户权限 |
| 404 | 资源不存在 | 检查ID是否正确 |
| 429 | 请求频率过高 | 降低请求频率 |
| 500 | 服务器内部错误 | 联系平台技术支持 |

**错误响应格式 | Error Response Format:**
```json
{
    "success": false,
    "error": {
        "code": "INVALID_PHONE",
        "message": "Invalid phone number format",
        "message_zh": "手机号格式不正确"
    }
}
```

---

### 安全说明 | Security Notes

1. **API Key 保护**: `PLATFORM_API_KEY` 仅用于服务端调用，禁止暴露给前端。
2. **签名验证**: 所有支付回调必须验证 HMAC-SHA256 签名。
3. **HTTPS**: 所有接口调用必须使用 HTTPS。
4. **Token 存储**: 用户访问令牌存储在前端 localStorage，过期自动刷新。
5. **幂等性**: 支付回调接口需保证幂等性，防止重复处理。

---

## 🤝 贡献 | Contributing

欢迎提交 Issue 和 Pull Request。本项目致力于帮助学术写作者提升写作水平，请遵守学术诚信规范。

> **免责声明**: 本工具仅辅助优化文章语言风格，不保证能 100% 通过所有 AIGC 检测器。最终内容的学术严谨性由作者本人负责。