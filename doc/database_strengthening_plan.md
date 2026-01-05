# 后端数据库补强方案 (Backend Database Strengthening Plan)

## 1. 核心目标
将当前的 MVP 级数据存储方案（SQLite）升级为生产级、高并发、可扩展的架构。重点解决并发写入限制、复杂查询性能以及长耗时任务的处理。

## 2. 架构演进建议

### 2.1 数据库迁移：SQLite -> PostgreSQL
**建议：** 强烈推荐直接迁移到 PostgreSQL。

**理由：**
*   **并发处理：** SQLite 是文件级锁，高并发下（多用户同时分析文档）会出现 `database is locked` 错误。PostgreSQL 支持行级锁和 MVCC，完美支持高并发。
*   **JSONB 支持：** 项目中大量使用 JSON 字段存储分析结果（`structure_analysis_cache`, `analysis_json` 等）。PostgreSQL 的 `JSONB` 类型支持高效的索引和查询，允许未来针对分析结果进行深度搜索（例如：“查找所有风险等级为 High 的段落”）。
*   **生态与扩展：** 它是生产环境的标准选择，支持未来可能需要的向量搜索（pgvector，用于语义检索）。

### 2.2 引入 Redis：缓存与消息队列
**建议：** 必须引入 Redis。

**理由（回答您的疑问）：**
1.  **任务队列 (Task Queue)：** 您的应用涉及 LLM 分析（Claude/GPT），这通常是**长耗时操作**（几秒到几分钟）。
    *   *现状：* 如果直接在 HTTP 请求中 `await`，会阻塞服务器线程，导致前端超时或服务器无响应。
    *   *改进：* 使用 Redis 作为消息代理（Broker），配合 Celery 或 ARQ（异步任务队列），将分析任务放入后台执行。前端通过轮询或 WebSocket 获取进度。
2.  **API 缓存与限流：**
    *   对于重复的查询或需要快速响应的配置数据（如 Whitelist, RiskWeights），Redis 内存读取比 DB 快得多。
    *   防止恶意或意外的高频 API 调用（Rate Limiting）。
3.  **Session 存储：** 虽然目前 Session 在 DB 中，但高频更新的 Session 状态（如当前阅读进度、临时编辑状态）适合放在 Redis 中，减少对主库的写压力。

## 3. 详细实施方案

### 3.1 技术栈更新
*   **Database:** PostgreSQL 15+
*   **Driver:** `asyncpg` (高性能异步驱动，替换 `aiosqlite`)
*   **Migration:** Alembic (数据库版本管理工具)
*   **Cache/Queue:** Redis 7+
*   **Task Queue Lib:** `arq` (轻量级异步队列，适合 FastAPI) 或 `Celery`

### 3.2 基础设施 (Docker Compose)
在项目根目录创建 `docker-compose.yml`，一键启动开发环境依赖。

```yaml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: academicguard
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 3.3 数据库迁移管理 (Alembic)
不再依赖 `Base.metadata.create_all`，改用 Alembic 管理 schema 变更。

1.  初始化：`alembic init alembic`
2.  配置 `alembic.ini` 和 `env.py` 连接到 PostgreSQL。
3.  生成迁移脚本：`alembic revision --autogenerate -m "Initial tables"`
4.  应用迁移：`alembic upgrade head`

### 3.4 代码改造点

1.  **`src/config.py`**:
    *   更新 `database_url` 默认值为 PostgreSQL 格式：`postgresql+asyncpg://user:password@localhost/academicguard`。
    *   添加 Redis 配置。

2.  **`src/db/database.py`**:
    *   调整 `create_async_engine` 参数（Postgres 需要连接池配置，如 `pool_size`, `max_overflow`）。

3.  **长任务异步化 (新增模块)**:
    *   创建 `src/worker.py` 处理后台任务。
    *   修改 `analyze.py` 路由，不再同步等待结果，而是提交任务 ID，由前端轮询状态。

## 4. 迁移步骤

1.  **准备环境：** 安装 Docker Desktop，添加 `docker-compose.yml`。
2.  **安装依赖：** `pip install asyncpg alembic redis arq`。
3.  **配置 Alembic：** 设置迁移环境。
4.  **数据迁移（可选）：** 如果有重要的 SQLite 数据，编写脚本将其导出并导入 Postgres（MVP阶段建议直接在新库重建）。
5.  **切换配置：** 修改 `.env` 指向本地 Postgres。
6.  **验证：** 运行现有测试用例，确保 ORM 层无缝切换。

## 5. 总结
直接上 **PostgreSQL + Redis** 是最稳妥的方案。PostgreSQL 解决数据存储的可靠性和查询能力，Redis 解决 LLM 长任务带来的系统阻塞问题。两者结合能支撑从 MVP 到正式产品的平滑过渡。
