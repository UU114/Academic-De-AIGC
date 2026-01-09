# AcademicGuard Production Deployment Notes
# AcademicGuard 生产环境部署注意事项

> **CRITICAL**: This document contains security-sensitive configuration requirements.
> **关键**: 本文档包含安全敏感的配置要求。

---

## Table of Contents | 目录

1. [Security Keys Generation | 安全密钥生成](#1-security-keys-generation--安全密钥生成)
2. [Environment Variables | 环境变量配置](#2-environment-variables--环境变量配置)
3. [Microservice Integration | 微服务集成](#3-microservice-integration--微服务集成)
4. [LLM API Configuration | LLM API配置](#4-llm-api-configuration--llm-api配置)
5. [Nginx Configuration | Nginx配置](#5-nginx-configuration--nginx配置)
6. [Startup Checklist | 启动检查清单](#6-startup-checklist--启动检查清单)

---

## 1. Security Keys Generation | 安全密钥生成

### Generate All Required Keys | 生成所有必需的密钥

```bash
# Generate JWT secret (REQUIRED)
# 生成JWT密钥（必需）
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate internal service secret (REQUIRED for operational mode)
# 生成内部服务密钥（运营模式必需）
python -c "import secrets; print('INTERNAL_SERVICE_SECRET=' + secrets.token_urlsafe(32))"

# Generate payment webhook secret (REQUIRED for payment callbacks)
# 生成支付回调密钥（支付回调必需）
python -c "import secrets; print('PAYMENT_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"

# Generate admin secret (optional, for admin dashboard)
# 生成管理员密钥（可选，用于管理仪表板）
python -c "import secrets; print('ADMIN_SECRET_KEY=' + secrets.token_urlsafe(16))"
```

### Key Requirements | 密钥要求

| Key | Minimum Length | Required Mode |
|-----|----------------|---------------|
| `JWT_SECRET_KEY` | 32 characters | Operational |
| `INTERNAL_SERVICE_SECRET` | 32 characters | Operational |
| `PAYMENT_WEBHOOK_SECRET` | 32 characters | Operational (for payments) |
| `ADMIN_SECRET_KEY` | 16 characters | Optional |

---

## 2. Environment Variables | 环境变量配置

### Production .env Template | 生产环境 .env 模板

```bash
# ==========================================
# System Mode (CRITICAL!)
# 系统模式（关键！）
# ==========================================
SYSTEM_MODE=operational  # DO NOT use "debug" in production!

# ==========================================
# Security Keys (REQUIRED!)
# 安全密钥（必需！）
# ==========================================
JWT_SECRET_KEY=<your-generated-32-char-key>
INTERNAL_SERVICE_SECRET=<your-generated-32-char-key>
PAYMENT_WEBHOOK_SECRET=<your-generated-32-char-key>
ADMIN_SECRET_KEY=<your-generated-16-char-key>

# ==========================================
# CORS Configuration
# 跨域配置
# ==========================================
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# ==========================================
# Internal Service IP Whitelist (Optional)
# 内网服务IP白名单（可选）
# ==========================================
# Default: 127.0.0.1, ::1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
INTERNAL_ALLOWED_IPS=127.0.0.1,10.0.0.0/8,192.168.1.0/24

# ==========================================
# Database
# 数据库
# ==========================================
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/academicguard

# ==========================================
# LLM Configuration (see section 4)
# LLM配置（见第4节）
# ==========================================
LLM_PROVIDER=volcengine
VOLCENGINE_API_KEY=<your-volcengine-api-key>
```

---

## 3. Microservice Integration | 微服务集成

### 3.1 Payment Service Integration | 支付服务集成

#### Callback Signature Verification | 回调签名验证

Your payment microservice **MUST** sign all callbacks using HMAC-SHA256:

您的支付微服务**必须**使用 HMAC-SHA256 签名所有回调：

```python
import hmac
import hashlib
import time
import secrets

def generate_payment_callback(order_id: str, status: str, amount: float, secret: str) -> dict:
    """
    Generate signed payment callback request
    生成签名的支付回调请求
    """
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)

    # Build signature string
    # 构建签名字符串
    sign_string = f"{order_id}|{status}|{amount}|{timestamp}|{nonce}"

    # Calculate HMAC-SHA256 signature
    # 计算 HMAC-SHA256 签名
    signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return {
        "order_id": order_id,
        "status": status,  # "paid", "failed", "refunded"
        "amount": amount,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature
    }

# Example usage:
# 使用示例：
callback_data = generate_payment_callback(
    order_id="order_123456",
    status="paid",
    amount=50.00,
    secret="your-PAYMENT_WEBHOOK_SECRET-here"
)
```

#### Calling the Callback Endpoint | 调用回调端点

```bash
# The payment service must include X-Service-Key header
# 支付服务必须包含 X-Service-Key 头

curl -X POST http://localhost:8000/api/v1/payment/callback \
  -H "Content-Type: application/json" \
  -H "X-Service-Key: your-INTERNAL_SERVICE_SECRET-here" \
  -d '{
    "order_id": "order_123456",
    "status": "paid",
    "amount": 50.00,
    "timestamp": 1704067800,
    "nonce": "abc123def456",
    "signature": "computed-hmac-sha256-signature"
  }'
```

### 3.2 Authentication Service Integration | 认证服务集成

If using external authentication service:

如果使用外部认证服务：

```python
# Internal service calls must include X-Service-Key header
# 内部服务调用必须包含 X-Service-Key 头

import httpx

async def call_internal_api(endpoint: str, data: dict, internal_secret: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000{endpoint}",
            json=data,
            headers={
                "X-Service-Key": internal_secret,
                "Content-Type": "application/json"
            }
        )
        return response.json()
```

### 3.3 Internal Endpoint Protection | 内部端点保护

Protected endpoints (require IP whitelist + X-Service-Key):

受保护的端点（需要IP白名单 + X-Service-Key）：

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/payment/callback` | Payment status updates |
| `/api/v1/internal/*` | Internal service APIs |

---

## 4. LLM API Configuration | LLM API配置

### 4.1 Supported Providers | 支持的提供商

| Provider | Environment Variable | Base URL |
|----------|---------------------|----------|
| Volcengine (火山引擎) | `VOLCENGINE_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3` |
| DashScope (阿里云灵积) | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| DeepSeek (官方) | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` |
| Google Gemini | `GEMINI_API_KEY` | Google API |
| OpenAI | `OPENAI_API_KEY` | OpenAI API |
| Anthropic | `ANTHROPIC_API_KEY` | Anthropic API |

### 4.2 Recommended Configuration (Volcengine) | 推荐配置（火山引擎）

```bash
# Volcengine DeepSeek - Faster than official DeepSeek API
# 火山引擎 DeepSeek - 比官方API更快

LLM_PROVIDER=volcengine
VOLCENGINE_API_KEY=your-volcengine-api-key
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=deepseek-v3-2-251201

# LLM Parameters
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
```

### 4.3 Internal LLM Proxy Setup | 内部LLM代理设置

If routing LLM calls through internal proxy:

如果通过内部代理路由LLM调用：

```bash
# Option 1: Use custom base URL
# 选项1：使用自定义基础URL
VOLCENGINE_BASE_URL=http://internal-llm-proxy:8080/v1

# Option 2: Use environment proxy
# 选项2：使用环境代理
HTTP_PROXY=http://internal-proxy:8080
HTTPS_PROXY=http://internal-proxy:8080
```

### 4.4 LLM Rate Limiting | LLM速率限制

Built-in rate limits (configurable in `rate_limiter.py`):

内置速率限制（可在 `rate_limiter.py` 中配置）：

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/suggest` | 20 requests | 60 seconds |
| `/api/v1/structure` | 10 requests | 60 seconds |
| `/api/v1/transition` | 10 requests | 60 seconds |
| `/api/v1/analysis` | 30 requests | 60 seconds |

---

## 5. Nginx Configuration | Nginx配置

### 5.1 Recommended Nginx Config | 推荐Nginx配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security Headers (additional layer)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # CRITICAL: File upload size limit (defense in depth)
    # 关键：文件上传大小限制（纵深防御）
    client_max_body_size 10M;

    # Rate limiting (defense in depth)
    # 速率限制（纵深防御）
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Block internal endpoints from external access
    # 阻止外部访问内部端点
    location /api/v1/internal/ {
        deny all;
        return 403;
    }

    # Payment callback - only from internal IPs
    # 支付回调 - 仅限内部IP
    location /api/v1/payment/callback {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Main API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 6. Startup Checklist | 启动检查清单

### Before Starting in Operational Mode | 运营模式启动前检查

- [ ] `SYSTEM_MODE=operational` is set
- [ ] `JWT_SECRET_KEY` is generated and configured (32+ chars)
- [ ] `INTERNAL_SERVICE_SECRET` is generated and configured
- [ ] `PAYMENT_WEBHOOK_SECRET` is generated and shared with payment service
- [ ] `ALLOWED_ORIGINS` contains your production domain
- [ ] Database is configured and accessible
- [ ] LLM API key is configured and valid
- [ ] Nginx is configured with `client_max_body_size`
- [ ] SSL certificate is valid and configured
- [ ] Payment service is configured to sign callbacks correctly

### Expected Startup Log (Operational Mode) | 预期启动日志（运营模式）

```
INFO:src.main:============================================================
INFO:src.main:  OPERATIONAL MODE - Production Security Enabled
INFO:src.main:============================================================
INFO:src.main:Starting AcademicGuard v1.0.0...
INFO:src.main:System Mode: OPERATIONAL
INFO:src.main:Database initialized
```

### If You See This, DO NOT DEPLOY | 如果看到以下内容，请勿部署

```
CRITICAL:src.main:============================================================
CRITICAL:src.main:  FATAL: INSECURE JWT_SECRET_KEY DETECTED!
CRITICAL:src.main:============================================================
```

The application will **refuse to start** with insecure configuration.

应用将**拒绝启动**如果配置不安全。

---

## Quick Reference | 快速参考

### Generate All Keys at Once | 一次生成所有密钥

```bash
echo "# Security Keys for AcademicGuard"
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "INTERNAL_SERVICE_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "PAYMENT_WEBHOOK_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "ADMIN_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(16))')"
```

### Test Payment Callback Signature | 测试支付回调签名

```python
# Test script to verify your payment service generates correct signatures
# 测试脚本验证您的支付服务生成正确的签名

import hmac
import hashlib

def test_signature():
    secret = "your-PAYMENT_WEBHOOK_SECRET"
    order_id = "test_order_001"
    status = "paid"
    amount = "50.0"
    timestamp = "1704067800"
    nonce = "test_nonce_123"

    sign_string = f"{order_id}|{status}|{amount}|{timestamp}|{nonce}"
    signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    print(f"Sign string: {sign_string}")
    print(f"Signature: {signature}")

test_signature()
```

---

## Support | 技术支持

For security issues, please contact the development team immediately.

如有安全问题，请立即联系开发团队。
