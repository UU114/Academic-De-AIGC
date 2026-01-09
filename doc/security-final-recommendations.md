# AcademicGuard 最终安全建议
# AcademicGuard Final Security Recommendations

**部署架构**: 私有仓库 + 自有服务器 + 内网微服务
**通信方式**: 内网HTTP端口调用
**日期**: 2026-01-09

---

## 部署架构确认

```
互联网用户
    ↓ HTTPS (SSL已配置)
[Nginx/前端入口 - :443]
    ↓
[AcademicGuard主服务 - :8000]
    ├─→ [LLM API服务] (内网HTTP)
    ├─→ [支付微服务 - :8001] (内网HTTP)
    └─→ [登录微服务 - :8002] (内网HTTP)

通信: localhost/127.0.0.1 或 内网IP (10.x.x.x/172.x.x.x/192.168.x.x)
```

---

## 🎯 核心结论

**你的架构已经很安全！** 内网HTTP调用消除了大部分外部攻击面。

### 已解决的安全问题 ✅

1. **API密钥泄露**: Private仓库 + 内网调用 = 不会暴露到外网 ✅
2. **HTTPS传输**: 已有SSL证书 ✅
3. **微服务隔离**: 支付/登录独立，降低风险 ✅
4. **支付回调**: 内网调用，外部无法伪造 ✅

### 需要10分钟修复的问题 🔧

1. **CORS配置**: 限制允许的来源
2. **JWT密钥**: 使用强随机密钥

### 建议增强的问题 💡

3. **内网服务认证**: 添加IP白名单或共享密钥
4. **文件上传验证**: MIME类型检测
5. **API速率限制**: 防止滥用

---

## 立即修复清单 (10分钟)

### 1. 修复CORS配置 [3分钟]

**文件**: `src/main.py`

**当前代码** (第50-56行):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**修复后**:
```python
import os

# 从环境变量读取允许的域名
allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'https://yourdomain.com')
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # ✅ 只允许你的域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**在服务器.env中添加**:
```bash
# 生产环境
ALLOWED_ORIGINS=https://yourdomain.com

# 如果有多个域名(CDN等)
ALLOWED_ORIGINS=https://yourdomain.com,https://cdn.yourdomain.com
```

**验证**:
```bash
# 测试其他域名被拒绝
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://yourdomain.com/api/v1/documents/

# 应该返回 CORS error 或 不包含 Access-Control-Allow-Origin
```

---

### 2. 使用强JWT密钥 [2分钟]

**生成新密钥**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 输出示例: ReAfqN9Ffqwme5-5H507wVlilNyepvIFc137LWPg0Nw
```

**在服务器.env中设置** (不要提交到Git!):
```bash
JWT_SECRET_KEY=<上面生成的密钥>
```

**添加生产环境检查** (可选，防止忘记设置):

**文件**: `src/config.py`

在`Settings`类的`__init__`方法中添加:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 生产环境强制检查
        if not self.debug:
            if self.jwt_secret_key == "dev-secret-key-change-in-production":
                raise ValueError(
                    "Production environment MUST set JWT_SECRET_KEY! "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
```

**影响**: 现有已登录用户需要重新登录（JWT签名已变）

---

### 3. 重启服务 [5分钟]

```bash
# 如果使用systemd
sudo systemctl restart academicguard

# 或使用supervisord
sudo supervisorctl restart academicguard

# 或直接kill进程重启
pkill -f "uvicorn src.main:app"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 验证服务正常
curl https://yourdomain.com/api/v1/health
```

---

## 内网服务安全加固 (可选，30分钟)

虽然内网调用已经相对安全，但建议添加额外保护：

### 方案A: IP白名单验证 (推荐，简单)

适用于所有内网HTTP调用的端点。

**创建中间件**: `src/middleware/internal_service_middleware.py`

```python
"""
Internal Service Security Middleware
内网服务安全中间件
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List
import ipaddress


class InternalServiceMiddleware(BaseHTTPMiddleware):
    """
    Verify that requests come from allowed internal IPs
    验证请求来自允许的内网IP
    """

    def __init__(self, app, allowed_ips: List[str] = None):
        super().__init__(app)
        self.allowed_ips = allowed_ips or [
            "127.0.0.1",
            "::1",  # IPv6 localhost
        ]
        # 支持CIDR格式
        self.allowed_networks = [
            ipaddress.ip_network(ip, strict=False) for ip in self.allowed_ips
        ]

    async def dispatch(self, request: Request, call_next):
        # 只检查特定路径（内网服务端点）
        internal_paths = [
            "/api/v1/payment/callback",  # 支付回调
            "/api/v1/internal/",  # 所有内部端点
        ]

        # 检查是否是内网端点
        is_internal_endpoint = any(
            request.url.path.startswith(path) for path in internal_paths
        )

        if is_internal_endpoint:
            # 获取客户端IP
            client_ip = request.client.host

            # 检查X-Forwarded-For (如果有Nginx代理)
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()

            # 验证IP
            client_addr = ipaddress.ip_address(client_ip)
            is_allowed = any(
                client_addr in network for network in self.allowed_networks
            )

            if not is_allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. IP {client_ip} not in whitelist."
                )

        response = await call_next(request)
        return response
```

**在main.py中启用**:

```python
# src/main.py
from src.middleware.internal_service_middleware import InternalServiceMiddleware

# 添加内网服务中间件
app.add_middleware(
    InternalServiceMiddleware,
    allowed_ips=[
        "127.0.0.1",
        "::1",
        "10.0.0.0/8",      # 如果微服务在10.x.x.x网段
        "172.16.0.0/12",   # 如果微服务在172.x.x.x网段
        "192.168.0.0/16",  # 如果微服务在192.168.x.x网段
    ]
)
```

---

### 方案B: 共享密钥验证 (更安全，稍复杂)

适用于需要更高安全性的场景。

**在.env中添加**:
```bash
# 内网服务间共享密钥
INTERNAL_SERVICE_SECRET=<生成一个随机密钥>
```

**生成密钥**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**修改支付回调端点**: `src/api/routes/payment.py`

```python
import hmac
import os

INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")

@router.post("/callback")
async def payment_callback(
    request: Request,
    callback_data: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    settings = get_settings()

    # 验证内网服务密钥（从请求头获取）
    service_key = request.headers.get("X-Service-Key", "")

    if not hmac.compare_digest(service_key, INTERNAL_SERVICE_SECRET):
        raise HTTPException(
            status_code=401,
            detail="Invalid service key"
        )

    # 继续处理回调
    if settings.is_debug_mode():
        return {"status": "skipped", "reason": "debug_mode"}

    order_id = callback_data.order_id

    # 查找订单
    result = await db.execute(
        select(Task).where(Task.platform_order_id == order_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 防止重复处理
    if task.payment_status == PaymentStatus.PAID.value:
        return {"status": "already_processed", "task_id": task.task_id}

    # 更新状态
    if callback_data.status == "paid":
        task.status = TaskStatus.PAID.value
        task.payment_status = PaymentStatus.PAID.value
        task.paid_at = datetime.utcnow()
    elif callback_data.status == "failed":
        task.payment_status = PaymentStatus.FAILED.value
    elif callback_data.status == "refunded":
        task.payment_status = PaymentStatus.REFUNDED.value

    await db.commit()

    return {"status": "processed", "task_id": task.task_id}
```

**支付微服务调用时需要添加密钥**:
```python
# 在你的支付微服务中
import httpx

async def notify_payment_success(order_id: str, amount: float):
    headers = {
        "X-Service-Key": os.getenv("INTERNAL_SERVICE_SECRET"),
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/payment/callback",
            json={
                "order_id": order_id,
                "status": "paid",
                "amount": amount
            },
            headers=headers
        )
        return response.json()
```

---

## 建议增强 (非紧急，1-2小时)

### 4. 文件上传MIME验证 [15分钟]

防止用户上传伪造扩展名的恶意文件。

**安装依赖**:
```bash
pip install python-magic

# Windows额外需要
pip install python-magic-bin
```

**修改**: `src/api/routes/documents.py`

在`upload_document`函数中，读取文件内容后添加:

```python
import magic

@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # ... existing code to read file ...

    content = await file.read()

    # 验证文件大小
    max_size = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large")

    # ===== 新增: MIME类型验证 =====
    mime = magic.from_buffer(content, mime=True)

    allowed_mimes = {
        'text/plain',  # .txt
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'  # .docx
    }

    if mime not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_type",
                "message": f"Invalid file type. Detected: {mime}",
                "message_zh": f"文件类型无效。检测到: {mime}",
                "allowed": "Only .txt and .docx files are allowed",
                "allowed_zh": "仅允许 .txt 和 .docx 文件"
            }
        )

    # 继续原有逻辑...
    if file_ext == '.txt':
        text = content.decode('utf-8', errors='ignore')
    elif file_ext == '.docx':
        # ... docx processing ...
```

**测试**:
```bash
# 测试伪造文件会被拒绝
cp malware.exe test.txt
curl -F "file=@test.txt" https://yourdomain.com/api/v1/documents/upload
# 应该返回: Invalid file type. Detected: application/x-executable
```

---

### 5. API速率限制 [30分钟]

防止单个用户滥用API，消耗LLM配额。

**安装依赖**:
```bash
pip install slowapi redis
```

**创建限流器**: `src/middleware/rate_limiter.py`

```python
"""
API Rate Limiter
API速率限制
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# 使用内存存储(简单场景)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# 如果有Redis(推荐)
# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"],
#     storage_uri="redis://localhost:6379"
# )
```

**在main.py中启用**:

```python
# src/main.py
from src.middleware.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**在关键端点添加限制**:

```python
# src/api/routes/suggest.py
from fastapi import Request
from src.middleware.rate_limiter import limiter

@router.post("/", response_model=SuggestResponse)
@limiter.limit("10 per minute")  # 每分钟10次LLM调用
async def get_suggestions(
    request: Request,  # 必须添加此参数
    sentence: str = Body(...),
    ...
):
    # ... existing code ...
```

```python
# src/api/routes/documents.py
@router.post("/upload", response_model=DocumentInfo)
@limiter.limit("20 per hour")  # 每小时20次上传
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    ...
):
    # ... existing code ...
```

```python
# src/api/routes/auth.py (如果还在用)
@router.post("/login")
@limiter.limit("5 per minute")  # 防止暴力破解
async def login(
    request: Request,
    login_request: LoginRequest,
    ...
):
    # ... existing code ...
```

**自定义限流键** (可选，按用户ID限流):

```python
from slowapi import Limiter

def get_user_id_or_ip(request: Request) -> str:
    """优先使用用户ID，否则用IP"""
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.get('user_id')}"
    return f"ip:{request.client.host}"

limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["200 per day"]
)
```

---

## 其他可选优化

### 6. 添加审计日志 (可选)

记录关键操作，便于追溯。

```python
# src/utils/audit_logger.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

async def log_audit(
    action: str,
    user_id: str = None,
    details: dict = None,
    ip_address: str = None
):
    """记录审计日志"""
    audit_logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "user_id": user_id,
        "details": details,
        "ip": ip_address
    })

# 使用示例
await log_audit(
    action="payment_success",
    user_id=user["user_id"],
    details={"order_id": order_id, "amount": amount},
    ip_address=request.client.host
)
```

---

### 7. 监控和告警 (可选)

使用Prometheus + Grafana或简单的邮件告警。

```python
# 示例: 支付失败告警
if payment_failed_count > 10:
    send_email_alert(
        subject="支付失败异常",
        body=f"最近1小时内有{payment_failed_count}次支付失败"
    )
```

---

## 最终检查清单

完成修复后，运行以下验证:

```bash
# 1. CORS配置
curl -H "Origin: https://evil.com" \
     -X OPTIONS https://yourdomain.com/api/v1/documents/
# 应该被拒绝

# 2. HTTPS重定向
curl -I http://yourdomain.com
# 应该返回 301 重定向到 https://

# 3. 安全响应头
curl -I https://yourdomain.com | grep -i "strict-transport"
# 应该看到 HSTS 头

# 4. 服务健康检查
curl https://yourdomain.com/api/v1/health
# 应该返回 200

# 5. JWT验证
curl https://yourdomain.com/api/v1/documents/ \
     -H "Authorization: Bearer invalid_token"
# 应该返回 401 Unauthorized

# 6. 速率限制(如果已添加)
for i in {1..20}; do
    curl https://yourdomain.com/api/v1/suggest
done
# 应该在第11次被限制
```

---

## 总结

### 立即完成 (10分钟)
- ✅ 修复CORS配置
- ✅ 设置强JWT密钥
- ✅ 重启服务

### 建议完成 (1-2小时)
- 🔵 添加内网服务IP白名单
- 🔵 文件上传MIME验证
- 🔵 API速率限制

### 可选优化 (持续改进)
- 📝 审计日志
- 📊 监控告警
- 🔄 定期密钥轮换

---

## 修复后的安全状态

**传输安全**: ✅ HTTPS已配置
**身份认证**: ✅ JWT + 微服务
**访问控制**: ✅ CORS限制 + 内网隔离
**输入验证**: ✅ 文件类型检测(修复后)
**速率限制**: ✅ API限流(添加后)
**数据安全**: ✅ 密钥管理 + Private仓库
**架构隔离**: ✅ 微服务分离

**你的系统安全级别: 🟢 生产就绪**

只需完成前面10分钟的立即修复，就可以安全上线了！
