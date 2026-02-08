# 任务模式数据持久化：API 文档与示例

## OpenAPI
- OpenAPI JSON：`/api/v1/openapi.json`
- Swagger UI：启动服务后访问 `http://localhost:8000/docs`

## 任务详情（Task）

### 创建任务
- `POST /api/v1/task-mode/tasks`

请求示例：
```json
{
  "name": "修复导出报表超时",
  "description": "用户反馈导出接口 504",
  "status": "open",
  "priority": 2,
  "assignee_id": "user-123",
  "created_by": "user-123"
}
```

### 查询任务
- `GET /api/v1/task-mode/tasks/{task_id}`

### 列表查询（支持多条件）
- `GET /api/v1/task-mode/tasks`
- Query 参数：
  - `assignee_id` / `created_by`
  - `status` / `priority`
  - `created_from` / `created_to`（ISO8601）
  - `updated_from` / `updated_to`（ISO8601）
  - `skip` / `limit`

### 更新任务（自动版本递增 + 写审计日志）
- `PUT /api/v1/task-mode/tasks/{task_id}`

请求示例：
```json
{
  "status": "in_progress",
  "priority": 1,
  "change_summary": "开始排查，先降级导出并添加索引",
  "actor_id": "user-123"
}
```

### 变更状态（语义化入口）
- `POST /api/v1/task-mode/tasks/{task_id}/status`

请求示例：
```json
{
  "status": "done",
  "note": "已修复并回归通过",
  "actor_id": "user-123"
}
```

### 删除任务（级联删除版本/问答/日志）
- `DELETE /api/v1/task-mode/tasks/{task_id}?actor_id=user-123`

## 任务版本（Versioning）

### 版本列表
- `GET /api/v1/task-mode/tasks/{task_id}/versions`

### 查询指定版本
- `GET /api/v1/task-mode/tasks/{task_id}/versions/{version}`

## 问答记录（QA）

### 新增问答
- `POST /api/v1/task-mode/tasks/{task_id}/qas`

请求示例：
```json
{
  "question": "导出接口慢的根因是什么？",
  "answer": "慢查询：缺少 where 条件字段索引，导致全表扫描",
  "user_id": "user-123"
}
```

### 查询问答（按任务 / 用户 / 时间范围）
- `GET /api/v1/task-mode/tasks/{task_id}/qas?user_id=user-123&created_from=2026-01-01T00:00:00Z`

### 更新/删除问答
- `PUT /api/v1/task-mode/qas/{qa_id}`
- `DELETE /api/v1/task-mode/qas/{qa_id}?actor_id=user-123`

## 任务日志（Audit Logs）

### 查询任务日志（多维度过滤）
- `GET /api/v1/task-mode/tasks/{task_id}/logs`
- 过滤参数：`actor_id / action_type / importance / created_from / created_to / skip / limit`

### 全局日志查询
- `GET /api/v1/task-mode/logs`

### 过期日志清理
- `POST /api/v1/task-mode/logs/purge`

## 备份与恢复（逻辑备份）

### 导出
- `GET /api/v1/task-mode/backup/export?task_id=...&include_logs=true`

### 导入
- `POST /api/v1/task-mode/backup/import?overwrite=false`
- Body：导出内容原样 JSON

