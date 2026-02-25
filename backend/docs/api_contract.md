# 接口契约规范 (Interface Contract Specifications)

## 版本控制
| 版本 | 日期 | 作者 | 描述 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-02-25 | Trae AI | 初始版本创建 |

## 1. 概述
本文档定义了智能体系统各核心组件之间的通信接口契约，遵循 RESTful 规范与 CloudEvents 协议。

## 2. 目标解析接口 (Goal Parsing)

### 2.1 提交复杂目标
- **URL**: `POST /api/v2/goals`
- **Description**: 提交一个高层业务目标，触发解析与拆分流程。
- **Request Body**:
```json
{
  "goal": "Analyze the competitor's Q3 financial report and summarize key risks.",
  "context": {
    "user_id": "u123",
    "priority": "high"
  },
  "constraints": {
    "max_cost": 5.0,
    "deadline": "2024-12-31T23:59:59Z"
  }
}
```
- **Response (202 Accepted)**:
```json
{
  "plan_id": "p-550e8400-e29b-41d4-a716-446655440000",
  "status": "parsing",
  "estimated_time": 15
}
```

## 3. 智能决策接口 (Decision Making)

### 3.1 获取最佳策略 (Internal)
- **URL**: `POST /internal/decision/policy`
- **Description**: 供 Planner 或 Agent 调用，获取当前状态下的最佳 Action。
- **Request Body**:
```json
{
  "state_vector": [0.1, 0.5, ...], 
  "available_tools": ["search_tool", "code_interpreter"],
  "history_summary": "Previous search failed..."
}
```
- **Response (200 OK)**:
```json
{
  "action": "use_tool",
  "tool_name": "code_interpreter",
  "parameters": {
    "script": "import pandas..."
  },
  "confidence": 0.92
}
```

## 4. 记忆系统接口 (Memory System)

### 4.1 检索长期记忆
- **URL**: `POST /internal/memory/retrieve`
- **Request Body**:
```json
{
  "query_text": "How to fix database connection timeout",
  "top_k": 3,
  "threshold": 0.75
}
```
- **Response (200 OK)**:
```json
{
  "results": [
    {
      "id": "exp-101",
      "content": "Increase pool_size in config...",
      "score": 0.88
    }
  ]
}
```

## 5. 异步事件协议 (CloudEvents)
系统内部组件通过消息队列通信，遵循 CloudEvents 1.0 规范。

### 5.1 任务完成事件
```json
{
  "specversion": "1.0",
  "type": "com.tiga.agent.task.completed",
  "source": "/agent/executor/node-1",
  "id": "evt-12345",
  "time": "2024-10-10T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "t-987",
    "plan_id": "p-550",
    "result": "Report generated successfully.",
    "metrics": {
      "duration_ms": 1200,
      "tokens": 450
    }
  }
}
```

## 6. 错误码规范

| 错误码 | 描述 | 处理建议 |
| :--- | :--- | :--- |
| `40001` | Goal Parse Failed | 检查输入是否模糊，重试。 |
| `50001` | Tool Execution Timeout | 增加超时阈值或切换工具。 |
| `50002` | Context Lock Conflict | 等待后重试 (Backoff)。 |
| `50003` | RL Model Inference Error | 降级为规则引擎决策。 |
