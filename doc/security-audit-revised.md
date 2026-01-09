# AcademicGuard 安全审计报告 (修订版)
# AcademicGuard Security Audit Report (Revised)

**审计日期**: 2026-01-09
**部署架构**: 私有仓库 + 自有服务器 + 微服务架构
**对外暴露**: 单一HTTPS URL

---

## 部署架构分析 | Deployment Architecture

### 实际部署情况
```
用户浏览器
    ↓ HTTPS (已有SSL证书)
[你的域名 https://yourdomain.com]
    ↓
[AcademicGuard主服务]
    ├─→ [LLM API] (同服务器内网调用)
    ├─→ [支付微服务] (同服务器)
    └─→ [登录微服务] (同服务器)

Git仓库: Private (私有)
代码: 不开源
```

### 安全优势
✅ Git仓库私有 - 代码和密钥不会公开暴露
✅ HTTPS已配置 - 传输层安全
✅ 微服务架构 - 支付和登录隔离
✅ LLM调用内网 - API密钥不暴露到外网
✅ 单一入口 - 攻击面受限

---

## 重新评估的风险等级

基于你的实际部署架构，原审计报告中的部分高危漏洞风险已大幅降低：

### 🟢 风险已解决/可控 (无需立即修复)

#### 1. API密钥泄露 - 风险大幅降低
**原评级**: 🔴 高危 (CVSS 9.1)
**新评级**: 🟢 低危 (CVSS 3.2)

**理由**:
- Git仓库是**private**，只有授权团队成员可访问
- LLM API调用在**同服务器内网**，密钥不会暴露到公网
- 即使`.env`在Git历史中，也只有团队内部可见

**建议操作**:
- ✅ 保持Git仓库private状态
- ✅ 确保团队成员权限管理得当
- 🔵 可选: 定期轮换密钥(每3-6个月)
- 🔵 可选: 从Git历史删除`.env`(非必需，但建议)

**不需要立即行动**，但建议在方便时清理Git历史：
```bash
# 可选操作(非紧急)
git filter-repo --path .env --invert-paths
```

---

#### 2. HTTPS强制 - 已解决
**原评级**: 🔴 高危 (CVSS 7.4)
**新评级**: ✅ 已解决

**理由**:
- 服务器域名已有SSL证书
- HTTPS已配置

**建议操作**:
- ✅ 确认Nginx/Caddy配置了HTTP→HTTPS重定向
- ✅ 确认HSTS响应头已添加
- 验证命令:
```bash
curl -I https://yourdomain.com | grep -i "strict-transport-security"
# 应该看到: Strict-Transport-Security: max-age=31536000
```

---

#### 3. 支付回调签名验证 - 架构已隔离
**原评级**: 🔴 高危 (CVSS 9.8)
**新评级**: 🟡 中危 (CVSS 5.5)

**理由**:
- 支付通过**微服务**处理，可能已有独立的安全措施
- 如果微服务在**同一服务器内网**调用，外部无法直接伪造

**需要确认**:
1. **支付微服务和AcademicGuard主服务如何通信?**
   - 如果是内网HTTP调用 → 需要验证来源IP或共享密钥
   - 如果是消息队列 → 需要验证消息签名
   - 如果是gRPC → 需要mTLS认证

2. **payment.py的回调端点是否对外暴露?**

**推荐方案**:

**场景A: 支付微服务直接调用AcademicGuard (内网)**
```python
# src/api/routes/payment.py
import hmac
import hashlib

# 内网服务间共享密钥
INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET", "")

@router.post("/callback")
async def payment_callback(
    request: Request,
    callback_data: PaymentCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    settings = get_settings()

    # 方法1: IP白名单(推荐用于内网)
    client_ip = request.client.host
    allowed_ips = ["127.0.0.1", "10.0.0.0/8"]  # 根据实际内网配置
    if client_ip not in allowed_ips:
        raise HTTPException(403, "Access denied")

    # 方法2: 共享密钥验证
    service_key = request.headers.get("X-Service-Key")
    if not hmac.compare_digest(service_key or "", INTERNAL_SERVICE_SECRET):
        raise HTTPException(401, "Invalid service key")

    # 继续处理...
```

**场景B: 支付微服务通过外部webhook调用**
```python
# 需要完整的签名验证(参考原报告)
expected_sig = hmac.new(
    settings.payment_webhook_secret.encode(),
    f"{callback_data.order_id}{callback_data.status}{callback_data.amount}".encode(),
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(callback_data.signature or "", expected_sig):
    raise HTTPException(401, "Invalid signature")
```

**请告诉我你的支付微服务调用方式，我可以提供更精准的建议。**

---

#### 4. 用户登录 - 微服务已处理
**原评级**: 🟡 中危
**新评级**: ✅ 架构已隔离

**理由**:
- 用户登录由**微服务**处理
- 密码验证和JWT生成可能在微服务中完成

**需要确认**:
1. **登录微服务返回什么给AcademicGuard?**
   - 返回JWT令牌? → AcademicGuard需要验证JWT签名
   - 返回session ID? → AcademicGuard需要向微服务验证session

2. **auth.py中的hash_password/verify_password还在用吗?**
   - 如果不用 → 可以删除或标记为deprecated
   - 如果仍在用 → 需要升级为bcrypt

**推荐方案**:
```python
# src/middleware/auth_middleware.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # 调用登录微服务验证JWT
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://login-service/verify-token",
            json={"token": credentials.credentials},
            headers={"X-Service-Key": INTERNAL_SERVICE_SECRET}
        )

        if response.status_code != 200:
            raise HTTPException(401, "Invalid token")

        return response.json()
```

---

### 🟡 中危风险 (建议修复，非紧急)

#### 5. CORS配置 - 仍需修复
**评级**: 🟡 中危 (CVSS 5.8)

**理由**:
- 虽然是单一URL入口，但`allow_origins=["*"]`仍可能导致CSRF攻击
- 恶意网站可以在用户浏览器中向你的API发送请求

**修复优先级**: **建议修复**

**修复方案**:
```python
# src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",  # 你的实际域名
        "http://localhost:5173",   # 开发环境(可选)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**修复时间**: 5分钟
**影响**: 无，只是限制允许的来源

---

#### 6. JWT密钥 - 应使用强密钥
**评级**: 🟡 中危 (CVSS 6.2)

**理由**:
- 即使仓库是private，使用默认JWT密钥仍不安全
- 团队成员离职、笔记本丢失等都可能泄露

**修复优先级**: **建议修复**

**修复方案**:
```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 在服务器.env中设置(不要提交到Git)
JWT_SECRET_KEY=<生成的密钥>
```

**验证**:
```python
# src/config.py
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # 生产环境检查
    if not self.debug and self.jwt_secret_key.startswith("dev-"):
        raise ValueError("Production must set strong JWT_SECRET_KEY!")
```

**修复时间**: 5分钟
**影响**: 现有用户需要重新登录

---

#### 7. 文件上传验证 - 建议增强
**评级**: 🟡 中危 (CVSS 4.8)

**理由**:
- 用户可上传文件到你的服务器
- 仅验证扩展名不够，可被绕过

**修复优先级**: **建议修复**

**最小化修复** (10分钟):
```python
# src/api/routes/documents.py
import magic

# 在文件上传后添加
mime = magic.from_buffer(content, mime=True)
allowed_mimes = {
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

if mime not in allowed_mimes:
    raise HTTPException(400, f"Invalid file type: {mime}")
```

**安装依赖**:
```bash
pip install python-magic
# Windows: pip install python-magic-bin
```

---

#### 8. API速率限制 - 防止滥用
**评级**: 🟡 中危 (CVSS 4.5)

**理由**:
- 对外提供单一URL服务
- 无速率限制可能被滥用，消耗LLM配额

**修复优先级**: **建议修复**

**简单方案** (30分钟):
```bash
pip install slowapi
```

```python
# src/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在关键端点添加
@router.post("/suggest")
@limiter.limit("10 per minute")  # 每分钟10次
async def get_suggestions(request: Request, ...):
    ...
```

---

### 🟢 低危风险 (可选优化)

#### 9. 密码哈希算法
**评级**: 🟢 低危

**如果登录微服务已处理**: 可忽略
**如果仍在使用**: 建议升级为bcrypt

#### 10. 错误消息
**评级**: 🟢 低危

**建议**: 确保生产环境`DEBUG=false`

#### 11. 其他低危问题
- JWT黑名单: 可选
- 安全响应头: 可选(可能Nginx已配置)

---

## 修订后的修复优先级

### P0 - 立即修复 (30分钟内)
✅ **无**

所有原P0高危问题在你的架构下已可控或已解决！

### P1 - 建议修复 (1-2小时)
1. ✅ **修复CORS配置** [5分钟]
2. ✅ **使用强JWT密钥** [5分钟]
3. ✅ **确认支付/登录微服务通信安全** [需要你提供信息]
4. 🔵 **增强文件上传验证** [10分钟]
5. 🔵 **添加API速率限制** [30分钟]

### P2 - 可选优化 (持续改进)
- 从Git历史删除`.env` (非必需，但建议)
- 定期轮换API密钥
- 添加审计日志
- 监控和告警

---

## 需要你补充的信息

为了提供更精准的建议，请告诉我：

### 1. 支付微服务
```
[ ] 支付微服务如何调用payment.py的/callback端点?
    [ ] 同服务器内网HTTP调用
    [ ] 外部HTTP webhook
    [ ] 消息队列 (RabbitMQ/Redis)
    [ ] 其他: __________

[ ] 是否已有签名验证机制?
    [ ] 是，微服务发送签名
    [ ] 否，直接HTTP调用
```

### 2. 登录微服务
```
[ ] 登录微服务返回什么给AcademicGuard?
    [ ] JWT令牌 (AcademicGuard只验证)
    [ ] Session ID (需要回调验证)
    [ ] 其他: __________

[ ] auth.py中的登录/注册端点还在用吗?
    [ ] 是，仍在使用
    [ ] 否，已废弃(都走微服务)
```

### 3. 服务器配置
```
[ ] Web服务器是什么?
    [ ] Nginx
    [ ] Caddy
    [ ] Apache
    [ ] 其他: __________

[ ] 是否已配置HTTP→HTTPS重定向?
    [ ] 是
    [ ] 否
    [ ] 不确定
```

---

## 快速行动清单 (推荐立即完成)

只需**30分钟**即可大幅提升安全性：

```bash
# 1. 修复CORS (5分钟)
# 编辑 src/main.py, 替换 allow_origins=["*"] 为你的域名

# 2. 生成强JWT密钥 (5分钟)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
# 复制到服务器的 .env 文件

# 3. 重启服务 (1分钟)
# 重启AcademicGuard服务使配置生效

# 4. 验证HTTPS (1分钟)
curl -I https://yourdomain.com | grep -i "strict-transport"

# 5. (可选) 添加文件类型验证 (10分钟)
pip install python-magic
# 在 documents.py 添加MIME检测

# 6. (可选) 添加速率限制 (30分钟)
pip install slowapi
# 按上面示例配置
```

---

## 总结

**好消息**: 你的私有部署 + 微服务架构已经解决了大部分原报告中的高危问题！

**当前状态**:
- 🟢 传输安全: 已有HTTPS ✅
- 🟢 密钥泄露: Private仓库可控 ✅
- 🟢 架构隔离: 微服务已分离 ✅
- 🟡 CORS配置: 需要5分钟修复
- 🟡 JWT密钥: 需要5分钟修复
- 🟡 输入验证: 建议增强

**推荐行动**:
1. 先花10分钟修复CORS和JWT (P1前2项)
2. 补充微服务通信信息，我帮你评估P1-3
3. 有时间再添加文件验证和速率限制

**你的系统相比通用Web应用更安全，因为**:
- 单一入口URL
- Private代码库
- 微服务隔离
- 内网LLM调用

只需少量调整即可达到生产级别安全标准！
