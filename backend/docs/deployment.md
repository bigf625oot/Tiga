# 部署文档 (Deployment Guide)

## 1. 环境要求 (Prerequisites)

*   **OS**: Linux (Ubuntu 20.04+ Recommended) / Windows (WSL2) / macOS
*   **Runtime**: Python 3.10+
*   **Container**: Docker & Docker Compose
*   **Database**: PostgreSQL 14+
*   **Cache/Queue**: Redis 6+

## 2. 容器化部署方案 (Docker Compose)

我们使用 Docker Compose 编排所有服务。

### 2.1 `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: python -m app.workers.task_worker
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
      - E2B_API_KEY=${E2B_API_KEY}
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### 2.2 配置文件模板 (`.env.example`)

```ini
# Database
DB_USER=postgres
DB_PASSWORD=secret
DB_NAME=agent_tasks

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM Provider
OPENAI_API_KEY=sk-...

# Sandbox
E2B_API_KEY=e2b_...

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## 3. 数据库初始化

首次部署需运行 Alembic 迁移脚本创建表结构。

```bash
# 进入 API 容器
docker-compose exec api bash

# 运行迁移
alembic upgrade head

# (可选) 导入初始数据
python scripts/init_db.py
```

## 4. 监控与告警配置

建议使用 Prometheus + Grafana 监控任务执行指标。

### 4.1 Prometheus 配置 (`prometheus.yml`)

```yaml
scrape_configs:
  - job_name: 'agent_api'
    static_configs:
      - targets: ['api:8000']
  - job_name: 'agent_worker'
    static_configs:
      - targets: ['worker:8000']
```

### 4.2 关键监控指标
*   `task_queue_length`: Redis 队列堆积数量 (Gauge)
*   `task_execution_duration_seconds`: 任务执行耗时 (Histogram)
*   `task_failure_total`: 任务失败总数 (Counter)
*   `token_usage_total`: Token 消耗总量 (Counter)

## 5. 灰度发布策略 (Canary Release)

1.  **部署新版本 Worker**: 启动少量新版本 Worker 容器，打上 `v2` 标签。
2.  **流量切分**: 在 Scheduler 中配置 10% 的任务路由到 `v2` 队列。
3.  **观察**: 监控 `v2` Worker 的错误率和性能指标。
4.  **全量发布**: 确认无误后，替换所有旧版本 Worker。

## 6. 回滚方案 (Rollback)

如果新版本出现严重 Bug：

1.  **停止新版本容器**: `docker-compose stop worker-v2`
2.  **回滚数据库 (如果需要)**: `alembic downgrade -1`
3.  **恢复旧版本**: `docker-compose up -d --build` (使用旧代码分支)
