# 任务模式数据持久化：部署与运维

## 配置项
- `SECRET_KEY`：字段级加密密钥派生源（必须在生产环境替换）
- `USE_SQLITE` / `SQLALCHEMY_DATABASE_URI` / `POSTGRES_*`：数据库连接
- `REDIS_HOST` / `REDIS_PORT`：缓存（可选，未连通时自动降级到进程内 TTL 缓存）
- `TASK_MODE_CACHE_TTL_SECONDS`：缓存 TTL（默认 30 秒）
- `TASK_MODE_LOG_RETENTION_NORMAL_DAYS`：普通日志保留天数（默认 30）
- `TASK_MODE_LOG_RETENTION_IMPORTANT_DAYS`：重要日志保留天数（默认 365）

## 数据库迁移
- SQLite：
  - 新装：启动服务会自动建表（`Base.metadata.create_all`）
  - 老库：运行 `backend/migrate_db.py` 会补齐缺失表/索引
- PostgreSQL：
  - 新装：启动服务会自动建表
  - 生产建议：引入 Alembic 迁移流程（当前仓库已包含依赖）

## 备份与恢复
- 逻辑备份（推荐跨库/跨环境）：
  - 导出：`GET /api/v1/task-mode/backup/export`
  - 导入：`POST /api/v1/task-mode/backup/import`
- SQLite 物理备份（单机场景）：
  - 直接复制 `backend/recorder_v5.db` 文件

## 运维例行
- 日志过期清理：
  - 服务启动时会执行一次清理
  - 可周期触发：调用 `POST /api/v1/task-mode/logs/purge`
- 性能：
  - 建议在高并发场景启用 PostgreSQL + Redis
  - 生产环境建议关闭 SQLAlchemy `echo`

