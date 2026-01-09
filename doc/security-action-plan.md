# 安全漏洞修复行动计划
# Security Vulnerability Fix Action Plan

**优先级**: P0 = 立即 | P1 = 1周内 | P2 = 1个月内

---

## P0 - 立即修复 (上线前必须完成)

### 1. 轮换所有已泄露的API密钥 [30分钟]

**问题**: `.env`文件包含明文密钥已提交到Git

**操作步骤**:

```bash
# 1. 登录阿里云DashScope控制台
https://dashscope.console.aliyun.com/apiKey
# 删除旧密钥: sk-e7d2081841744801aafb1fc0ee7253bd
# 创建新密钥并记录

# 2. 登录火山引擎控制台
https://console.volcengine.com/ark
# 删除旧密钥: 3a958a8d-bcc2-4578-a391-dd0df7c20b79
# 创建新密钥并记录

# 3. 生成新的JWT和Admin密钥
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 4. 更新生产环境的.env文件(不要提交到Git!)
# 示例密钥(仅供格式参考):
# JWT_SECRET_KEY=ReAfqN9Ffqwme5-5H507wVlilNyepvIFc137LWPg0Nw
# ADMIN_SECRET_KEY=gzBJA_7MichdNUUabCeUjBlduysTb1s-aMVMS2O_b-Q
```

---

### 2. 从Git历史中删除.env文件 [15分钟]

**问题**: 密钥已被提交到Git历史记录

**操作步骤**:

```bash
# 方法1: 使用git filter-repo (推荐)
pip install git-filter-repo
git filter-repo --path .env --invert-paths

# 方法2: 使用BFG Repo-Cleaner
# 下载: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送到远程(警告:会改写历史)
git push origin --force --all

# 通知团队成员重新clone仓库
```

**验证**:
```bash
# 确认.env不在Git中
git ls-files | grep .env
# 应该没有输出

# 确认.gitignore包含.env
grep ".env" .gitignore
# 应该显示: .env
```

---

### 3. 修复CORS配置 [10分钟]

**问题**: 允许任意来源访问API

**修改文件**: `src/main.py`

**当前代码** (第50-56行):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ 不安全!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**修复后**:
```python
from src.config import get_settings
import os

settings = get_settings()

# 从环境变量读取允许的来源
allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # ✅ 明确指定
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**在.env中添加**:
```bash
# 开发环境
ALLOWED_ORIGINS=http://localhost:5173

# 生产环境
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

### 4. 实现支付回调签名验证 [30分钟]

**问题**: 支付回调可被伪造

**修改文件**: `src/api/routes/payment.py`

**当前代码** (第345-348行):
```python
# TODO: Verify signature
# TODO: 验证签名
```

**修复后**:
```python
import hmac
import hashlib

@router.post("/callback")
async def payment_callback(
    request: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    settings = get_settings()

    # 跳过调试模式
    if settings.is_debug_mode():
        return {"status": "skipped", "reason": "debug_mode"}

    # ===== 1. 验证签名 =====
    if not request.signature:
        raise HTTPException(
            status_code=401,
            detail={"error": "missing_signature", "message": "Signature required"}
        )

    # 构建签名字符串(顺序和平台约定必须一致!)
    sign_string = f"{request.order_id}{request.status}{request.amount or 0}"

    # 计算预期签名
    expected_sig = hmac.new(
        settings.payment_webhook_secret.encode(),  # 需要在config中添加
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # 常量时间比较防止时序攻击
    if not hmac.compare_digest(request.signature, expected_sig):
        # 记录可疑请求
        logger.warning(
            f"Invalid payment signature from {request.remote_addr}. "
            f"Order: {request.order_id}"
        )
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_signature", "message": "Invalid signature"}
        )

    # ===== 2. 查找订单 =====
    result = await db.execute(
        select(Task).where(Task.platform_order_id == request.order_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ===== 3. 验证幂等性(防止重复处理) =====
    if task.payment_status == PaymentStatus.PAID.value:
        logger.info(f"Order {request.order_id} already processed")
        return {"status": "already_processed", "task_id": task.task_id}

    # ===== 4. 验证金额匹配 =====
    if request.amount and abs(float(request.amount) - task.price_final) > 0.01:
        logger.error(
            f"Amount mismatch for order {request.order_id}. "
            f"Expected: {task.price_final}, Got: {request.amount}"
        )
        raise HTTPException(
            status_code=400,
            detail={"error": "amount_mismatch", "message": "Payment amount mismatch"}
        )

    # ===== 5. 更新状态 =====
    if request.status == "paid":
        task.status = TaskStatus.PAID.value
        task.payment_status = PaymentStatus.PAID.value
        task.paid_at = datetime.utcnow()
        logger.info(f"Order {request.order_id} marked as paid")
    elif request.status == "failed":
        task.payment_status = PaymentStatus.FAILED.value
        logger.info(f"Order {request.order_id} marked as failed")
    elif request.status == "refunded":
        task.payment_status = PaymentStatus.REFUNDED.value
        logger.info(f"Order {request.order_id} marked as refunded")

    await db.commit()

    return {"status": "processed", "task_id": task.task_id}
```

**在config.py中添加**:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    payment_webhook_secret: str = Field(
        default="",
        description="Secret key for payment webhook signature verification"
    )
```

**在.env中添加**:
```bash
# 从支付平台获取
PAYMENT_WEBHOOK_SECRET=your_payment_webhook_secret_here
```

---

### 5. 强制生产环境HTTPS [20分钟]

**问题**: 未强制使用HTTPS

#### 5.1 创建中间件

**创建文件**: `src/middleware/security_middleware.py`

```python
"""
Security Middleware
安全中间件
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import get_settings


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Force HTTPS in production"""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # 生产环境强制HTTPS
        if not settings.debug:
            # 检查X-Forwarded-Proto头(Nginx设置)
            proto = request.headers.get("x-forwarded-proto", "http")
            if proto != "https":
                raise HTTPException(
                    status_code=403,
                    detail="HTTPS required in production environment"
                )

        response = await call_next(request)

        # 添加安全响应头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        if not settings.debug:
            # HSTS: 强制浏览器使用HTTPS (1年)
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
```

#### 5.2 在main.py中启用

```python
# src/main.py
from src.middleware.security_middleware import HTTPSRedirectMiddleware

# 添加到其他中间件之后
app.add_middleware(HTTPSRedirectMiddleware)
```

#### 5.3 配置Nginx (生产环境)

**创建文件**: `deploy/nginx.conf`

```nginx
# HTTP -> HTTPS重定向
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 强制重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书(Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # 安全响应头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API反向代理
    location /api/v1/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # 重要!FastAPI需要此头
    }

    # 前端静态文件
    location / {
        root /var/www/academicguard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

#### 5.4 获取免费SSL证书

```bash
# 安装Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 获取证书(自动配置Nginx)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
sudo certbot renew --dry-run
```

---

## P1 - 高优先级 (上线后1周内)

### 6. 升级密码哈希算法 [45分钟]

**安装依赖**:
```bash
pip install bcrypt
```

**修改文件**: `src/api/routes/auth.py`

**替换hash_password和verify_password函数**:
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False
```

**数据迁移**: 现有用户需要在下次登录时重新设置密码

---

### 7. 增强文件上传验证 [30分钟]

**安装依赖**:
```bash
pip install python-magic python-docx
# Linux需要: sudo apt-get install libmagic1
# macOS需要: brew install libmagic
```

**修改文件**: `src/api/routes/documents.py`

在`upload_document`函数中添加:
```python
import magic
from docx import Document
import io

# ... 读取文件内容后 ...

# 1. MIME类型验证
mime = magic.from_buffer(content, mime=True)
allowed_mimes = {
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

if mime not in allowed_mimes:
    raise HTTPException(
        status_code=400,
        detail=f"Invalid file type. Detected: {mime}"
    )

# 2. 对.docx文件额外验证
if file_ext == '.docx':
    try:
        doc = Document(io.BytesIO(content))
        # 检查宏(可选,根据需求)
        # if hasattr(doc, 'part') and doc.part.vba_project:
        #     raise HTTPException(400, "Macros not allowed")
    except Exception as e:
        raise HTTPException(400, f"Invalid DOCX: {str(e)}")
```

---

### 8. 添加API速率限制 [1小时]

**安装依赖**:
```bash
pip install slowapi redis
```

**创建文件**: `src/middleware/rate_limiter.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

**在main.py中启用**:
```python
from src.middleware.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**在关键端点添加限制**:
```python
from src.middleware.rate_limiter import limiter

# 登录端点 - 严格限制
@router.post("/login")
@limiter.limit("5 per minute")
async def login(request: Request, ...):
    ...

# 注册端点
@router.post("/register")
@limiter.limit("3 per hour")
async def register(request: Request, ...):
    ...

# LLM调用端点
@router.post("/suggest")
@limiter.limit("10 per minute")
async def get_suggestions(request: Request, ...):
    ...
```

---

## P2 - 中优先级 (1个月内)

### 9. 为管理员添加MFA

需要研究和实现TOTP双因素认证

### 10. 规范错误消息处理

创建统一的错误处理器,避免泄露内部信息

### 11. 实现JWT黑名单

使用Redis存储已撤销的令牌

---

## 验证清单

完成修复后,运行以下检查:

```bash
# 1. 检查.env不在Git中
git ls-files | grep .env
# 应该没有输出

# 2. 检查API密钥已轮换
grep -E "DASHSCOPE_API_KEY|VOLCENGINE_API_KEY" .env
# 应该显示新密钥

# 3. 运行安全扫描
pip install bandit
bandit -r src/

# 4. 检查依赖包漏洞
pip install pip-audit
pip-audit

# 5. 测试CORS配置
curl -H "Origin: https://evil.com" http://localhost:8000/api/v1/documents/
# 应该被拒绝

# 6. 测试速率限制
for i in {1..10}; do curl http://localhost:8000/api/v1/auth/login; done
# 应该在第6次被限制
```

---

## 完成后

更新`doc/process.md`记录修复进度:

```markdown
## 安全漏洞修复 (2026-01-09)

- [x] P0-1: 轮换所有API密钥
- [x] P0-2: 从Git删除.env历史
- [x] P0-3: 修复CORS配置
- [x] P0-4: 实现支付签名验证
- [x] P0-5: 强制HTTPS
- [ ] P1-6: 升级密码哈希
- [ ] P1-7: 增强文件上传验证
- [ ] P1-8: 添加速率限制
```

---

**问题?** 参考完整的安全审计报告: `doc/security-audit-report.md`
