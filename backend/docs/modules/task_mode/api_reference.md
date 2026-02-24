# 任务模式 (Task Mode) - API 参考文档

> **版本**: 1.0.0
> **最后更新**: 2026-02-24
> **状态**: 已发布

## 1. 简介 (Introduction)
任务模式（Task Mode）API 提供了对任务全生命周期的管理能力，包括任务创建、状态流转、版本控制、问答记录（QA）以及审计日志。支持逻辑备份与恢复功能。

## 2. 核心概念 (Core Concepts)

*   **Task (任务)**: 工作的基本单元，具有状态、优先级和指派人。
*   **Version (版本)**: 任务每次更新都会生成一个快照版本，用于追溯变更历史。
*   **QA (问答)**: 关联到任务的知识沉淀，记录问题与解答。
*   **Audit Log (审计日志)**: 记录所有对任务的操作记录，用于审计和回溯。

## 3. API 列表

### 3.1 任务管理 (Tasks)

#### 3.1.1 创建任务

*   **URL**: `/api/v1/task-mode/tasks`
*   **Method**: `POST`
*   **Summary**: 创建一个新的任务。

**请求参数 (Body)**

| 参数名 | 类型 | 必选 | 说明 | 限制 |
| :--- | :--- | :--- | :--- | :--- |
| `name` | string | 是 | 任务名称 | 1-200 字符 |
| `description` | string | 否 | 任务描述 | |
| `status` | string | 否 | 初始状态 | 默认为 "open" |
| `priority` | int | 否 | 优先级 | 1-5, 默认为 3 |
| `assignee_id` | string | 否 | 指派给的用户ID | |
| `created_by` | string | 否 | 创建者ID | |

**请求示例**

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

**响应示例**

```json
{
  "name": "修复导出报表超时",
  "description": "用户反馈导出接口 504",
  "status": "open",
  "priority": 2,
  "assignee_id": "user-123",
  "id": "task-abc-123",
  "created_by": "user-123",
  "current_version": 1,
  "created_at": "2026-02-24T10:00:00Z",
  "updated_at": null
}
```

#### 3.1.2 查询任务详情

*   **URL**: `/api/v1/task-mode/tasks/{task_id}`
*   **Method**: `GET`
*   **Summary**: 获取指定任务的详细信息。

#### 3.1.3 更新任务

*   **URL**: `/api/v1/task-mode/tasks/{task_id}`
*   **Method**: `PUT`
*   **Summary**: 更新任务信息，会自动增加版本号。

**请求参数 (Body)**

| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `status` | string | 新状态 |
| `priority` | int | 新优先级 |
| `change_summary` | string | 变更摘要（用于审计） |
| `actor_id` | string | 操作人ID |

**请求示例**

```json
{
  "status": "in_progress",
  "priority": 1,
  "change_summary": "开始排查，先降级导出并添加索引",
  "actor_id": "user-123"
}
```

### 3.2 问答记录 (QA)

#### 3.2.1 新增问答

*   **URL**: `/api/v1/task-mode/tasks/{task_id}/qas`
*   **Method**: `POST`
*   **Summary**: 为任务添加一条问答记录。

**请求示例**

```json
{
  "question": "导出接口慢的根因是什么？",
  "answer": "慢查询：缺少 where 条件字段索引，导致全表扫描",
  "user_id": "user-123"
}
```

### 3.3 审计与日志 (Audit Logs)

#### 3.3.1 查询任务日志

*   **URL**: `/api/v1/task-mode/tasks/{task_id}/logs`
*   **Method**: `GET`
*   **Summary**: 查询特定任务的操作日志。

**Query 参数**

| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `actor_id` | string | 操作人ID |
| `action_type` | string | 操作类型 |
| `skip` | int | 分页偏移 |
| `limit` | int | 分页大小 |

### 3.4 备份与恢复 (Backup)

*   **导出**: `GET /api/v1/task-mode/backup/export`
*   **导入**: `POST /api/v1/task-mode/backup/import`

## 4. 错误码 (Error Codes)

| HTTP 状态码 | 说明 |
| :--- | :--- |
| `404` | Task not found / QA not found |
| `422` | Validation Error (参数校验失败) |
| `500` | Internal Server Error |
