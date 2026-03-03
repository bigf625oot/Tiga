# 系统改造任务清单

本文档基于 `improvement_task_list.md` 生成，详细列出了系统全链路优化的具体执行任务。

## 1. 基础设施层重构 (Infrastructure)

### 1.1 分布式任务队列 (Redis Streams)
- [ ] **引入 Redis Streams 依赖**
  - [ ] 在 `backend/requirements.txt` 中确认或添加 `redis-py` 依赖。
  - [ ] 配置 Redis 连接池参数（`backend/app/core/redis.py`）。
- [ ] **实现 Producer 逻辑 (API 层)**
  - [ ] 修改任务提交接口，不再使用 `asyncio.Queue`。
  - [ ] 实现 `enqueue_task` 函数，将任务 ID 和元数据写入 Redis Stream (`task_stream`)。
- [ ] **实现 Consumer Group 逻辑 (Worker 层)**
  - [ ] 创建后台 Worker 进程/服务。
  - [ ] 实现 Consumer Group 初始化（如果不存在则创建）。
  - [ ] 实现任务拉取循环 (`xreadgroup`)。
  - [ ] 实现任务处理后的 ACK 机制 (`xack`)。
  - [ ] 实现故障恢复机制（处理 Pending List 中的滞留任务）。

### 1.2 状态机与并发控制
- [ ] **数据库模型变更**
  - [ ] 修改 `OpenClawTask` 模型，添加 `version` 字段 (SQLAlchemy `version_id_col`)。
  - [ ] 修改 `SubTask` 模型，添加 `version` 字段。
  - [ ] 生成并执行数据库迁移脚本 (`alembic` 或 `scripts/migrate_db.py`)。
- [ ] **状态机逻辑实现**
  - [ ] 定义状态枚举 `TaskStatus` (PENDING, RUNNING, COMPLETED, FAILED, etc.)。
  - [ ] 实现状态转换校验函数 `validate_state_transition(current, new)`。
  - [ ] 在状态更新服务中集成乐观锁异常处理 (`StaleDataError`)。

### 1.3 统一 AgentExecutor 代理层
- [ ] **定义抽象基类**
  - [ ] 创建 `backend/app/services/agent/executor.py`。
  - [ ] 定义 `BaseAgentExecutor` 类，包含 `execute` (sync) 和 `stream` (async) 抽象方法。
- [ ] **实现具体 Executor**
  - [ ] 实现 `ChatAgentExecutor` (适配 Agno/现有 Chat 逻辑)。
  - [ ] 实现 `WorkflowAgentExecutor` (适配 TaskSplitter/OpenClaw)。
  - [ ] 实现 `AutoTaskAgentExecutor` (适配自动任务逻辑)。
- [ ] **重构调用方**
  - [ ] 修改 `backend/app/api/endpoints/agent_workflow.py` 使用新的 Executor 接口。

## 2. 业务模式专项优化 (Mode Optimizations)

### 2.1 对话模式 (Chat Mode)
- [ ] **Agent 实例缓存**
  - [ ] 引入 `cachetools` 库。
  - [ ] 实现 `AgentPool` 类，使用 LRU 策略缓存 Agent 实例。
  - [ ] 在 `ChatAgentExecutor` 中集成 `AgentPool`。
- [ ] **上下文滑动窗口优化**
  - [ ] 实现 `get_optimized_context(history, max_tokens)` 算法。
  - [ ] 确保 System Prompt 始终保留。
  - [ ] 集成 Token 计算工具（如 `tiktoken`）。
- [ ] **思维链 (Chain of Thought) 支持**
  - [ ] 更新流式响应解析逻辑，识别 `<think>` 标签。
  - [ ] 定义新的 SSE 事件类型（如 `thought_start`, `thought_chunk`, `thought_end`）。
  - [ ] 前端适配：在 `frontend/src/features/qa/components/MessageItem.vue` 中展示思考过程。

### 2.2 智能规划模式 (Workflow Mode)
- [ ] **DAG 依赖管理**
  - [ ] 修改 `SubTask` 模型，添加 `dependencies` JSON 字段。
  - [ ] 更新任务创建逻辑，解析并存储依赖关系。
- [ ] **调度引擎升级**
  - [ ] 实现 `check_ready_tasks(task_id)` 函数。
  - [ ] 在子任务完成的 Hook 中触发依赖检查。
  - [ ] 仅当所有依赖任务为 COMPLETED 时，将后续任务推入 Redis Stream。
- [ ] **数据流转映射**
  - [ ] 实现模板变量解析器，支持 `{{task_id.output}}` 语法。
  - [ ] 在任务执行前，解析输入参数中的变量引用并替换为实际值。

### 2.3 自动任务模式 (Auto Task Mode)
- [ ] **意图识别增强**
  - [ ] 优化 `LLM Parser` 的 Prompt。
  - [ ] 添加 5-10 个 Few-shot 示例（标准 Action 格式）。
- [ ] **重试机制**
  - [ ] 引入 `tenacity` 库。
  - [ ] 为关键执行函数添加 `@retry` 装饰器。
  - [ ] 配置指数退避策略 (2s, 4s, 8s) 和重试条件（网络错误、超时）。
- [ ] **资源限流**
  - [ ] 引入 Redis 分布式锁/信号量。
  - [ ] 实现 `BrowserSemaphore` 上下文管理器，限制并发浏览器实例数。

## 3. 全链路可观测性 (Observability)

### 3.1 追踪与日志
- [ ] **Trace ID 穿透**
  - [ ] 创建 FastAPI 中间件，生成或提取 `X-Request-ID`。
  - [ ] 使用 `contextvars` 存储当前 `trace_id`。
  - [ ] 确保异步任务和后台 Worker 能获取并传递 `trace_id`。
- [ ] **结构化日志**
  - [ ] 引入并配置 `structlog`。
  - [ ] 替换现有的 `logger` 配置，确保输出 JSON 格式。
  - [ ] 统一日志字段：`task_id`, `trace_id`, `event`, `duration`, `token_usage`。

### 3.2 核心指标埋点
- [ ] **指标收集**
  - [ ] 定义 Prometheus 指标或日志埋点。
  - [ ] 记录 TTFT (Time To First Token)。
  - [ ] 记录任务在 Redis Stream 中的排队时长。
  - [ ] 记录子任务成功/失败计数。
  - [ ] 记录意图解析准确率（需定义校验逻辑）。
