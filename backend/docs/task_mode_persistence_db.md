# 任务模式数据持久化：数据库设计

## 选型
- 默认：SQLite（开发/单机部署），与现有工程保持一致
- 可切换：PostgreSQL（高并发/生产建议），复用现有 `SQLAlchemy async` 连接方式
- ORM：SQLAlchemy 2.x async（与现有 `app/db/session.py` 统一）

## ER 图（逻辑）
```
users (id)
  ^                 ^                    ^
  | created_by      | assignee_id        | actor_id / user_id
  |                 |                    |
tasks (id) ----< task_versions (task_id, version)
  |
  +----< task_qas (task_id)
  |
  +----< task_logs (task_id)
```

## 表结构

### tasks（任务详情：当前态）
- id（PK，uuid）
- name（任务名称，可检索）
- description_enc（任务描述，加密存储）
- status（任务状态：open / in_progress / blocked / done / archived …）
- priority（优先级：1-5）
- assignee_id（负责人，FK users.id）
- created_by（创建人，FK users.id）
- current_version（当前版本号）
- created_at / updated_at

**核心索引**
- tasks(name)
- tasks(status)
- tasks(priority)
- tasks(assignee_id)
- tasks(created_by)
- tasks(created_at)
- tasks(updated_at)

### task_versions（任务详情：历史版本）
- id（PK，自增）
- task_id（FK tasks.id）
- version（版本号）
- name / description_enc / status / priority / assignee_id（该版本快照）
- changed_by（操作者，FK users.id）
- change_summary（变更摘要）
- created_at

**核心索引**
- UNIQUE(task_id, version)
- task_versions(task_id)
- task_versions(version)
- task_versions(created_at)
- task_versions(changed_by)
- task_versions(assignee_id)

### task_qas（问答记录）
- id（PK，自增）
- task_id（FK tasks.id）
- user_id（提问/记录人，FK users.id）
- question_enc / answer_enc（加密存储）
- created_at / updated_at

**核心索引**
- task_qas(task_id)
- task_qas(user_id)
- task_qas(created_at)
- task_qas(updated_at)

### task_logs（任务日志：操作审计）
- id（PK，自增）
- task_id（FK tasks.id）
- actor_id（操作者，FK users.id）
- action_type（操作类型：task.create / task.update / task.delete / qa.create …）
- importance（normal / important）
- content_enc（操作内容摘要，加密存储）
- before_state_enc / after_state_enc（变更前后状态，加密 JSON 存储）
- created_at
- expires_at（到期时间，用于分级保留/自动清理）

**核心索引**
- task_logs(task_id)
- task_logs(actor_id)
- task_logs(action_type)
- task_logs(importance)
- task_logs(created_at)
- task_logs(expires_at)

## 分级日志保留策略
- normal：默认保留 30 天（`TASK_MODE_LOG_RETENTION_NORMAL_DAYS`）
- important：默认保留 365 天（`TASK_MODE_LOG_RETENTION_IMPORTANT_DAYS`）
- 清理方式：
  - 启动时执行一次过期清理
  - 提供 API：`POST /api/v1/task-mode/logs/purge`

## 加密存储
- 字段级加密：使用 `SECRET_KEY` 派生 Fernet key，对以下字段加密：
  - tasks.description_enc
  - task_versions.description_enc
  - task_qas.question_enc / task_qas.answer_enc
  - task_logs.content_enc / before_state_enc / after_state_enc

## 迁移策略
- 生产建议：引入 Alembic 做标准化迁移
- 当前工程兼容：已扩展 `backend/migrate_db.py`，对 SQLite 安装场景可一键创建/补齐表与索引

