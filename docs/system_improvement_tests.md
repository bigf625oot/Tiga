# 系统改造测试文档

本文档定义了基于 `improvement_task_list.md` 的系统改造验证方案，涵盖单元测试、集成测试及性能指标验证。

## 1. 测试范围与策略 (Scope & Strategy)

- **目标**：验证基础设施重构后的稳定性、业务模式优化的功能性以及可观测性方案的有效性。
- **环境**：
  - **Unit Test**: 使用 Pytest + Mock (redis, db)
  - **Integration Test**: 使用 Testcontainers (Redis, Postgres) + FastAPI TestClient
  - **Performance Test**: 使用 Locust 或 k6

## 2. 基础设施层测试 (Infrastructure Tests)

### 2.1 分布式任务队列 (Redis Streams)
- [ ] **Test Case: 任务入队与出队 (Enqueue/Dequeue)**
  - **Input**: 模拟 API 请求提交一个新任务。
  - **Check**:
    - Redis Stream (`task_stream`) 中存在对应 Entry。
    - Worker 能够从 Consumer Group 读取到该消息。
    - 任务 ID 和元数据完整无误。
- [ ] **Test Case: 消息确认 (ACK)**
  - **Input**: Worker 处理完任务后调用 `xack`。
  - **Check**: 再次读取 PEL (Pending Entries List)，该消息应被移除或标记为已处理。
- [ ] **Test Case: 故障恢复 (Consumer Failover)**
  - **Input**: 模拟 Worker 崩溃（不发送 ACK）。
  - **Check**: 重启 Worker 后，能够重新获取未 ACK 的消息并继续处理。

### 2.2 状态机与并发控制
- [ ] **Test Case: 乐观锁并发冲突**
  - **Input**: 两个并发请求尝试修改同一个 `OpenClawTask` 实例。
  - **Check**:
    - 一个请求成功，版本号 +1。
    - 另一个请求抛出 `StaleDataError` 或类似异常，并触发重试/报错。
- [ ] **Test Case: 状态流转校验**
  - **Input**: 尝试将任务状态从 `PENDING` 直接修改为 `COMPLETED`（假设定义中禁止）。
  - **Check**: 抛出 `StateTransitionError`，状态未变更。

### 2.3 统一 AgentExecutor
- [ ] **Test Case: 接口一致性**
  - **Input**: 分别调用 `ChatAgentExecutor`, `WorkflowAgentExecutor`, `AutoTaskAgentExecutor` 的 `execute` 方法。
  - **Check**: 返回值结构统一（包含 `result`, `status`, `usage` 等字段）。

## 3. 业务模式测试 (Mode Tests)

### 3.1 对话模式 (Chat Mode)
- [ ] **Test Case: Agent 实例复用**
  - **Input**: 连续两次请求同一个 Session ID。
  - **Check**: 第二次请求响应时间显著低于第一次（< 300ms 差异），且 `AgentPool` 命中率增加。
- [ ] **Test Case: 上下文窗口截断**
  - **Input**: 构造超过 Token 限制的历史消息列表。
  - **Check**: `get_optimized_context` 返回的消息列表 Token 总数在限制范围内，且 System Prompt 依然存在。
- [ ] **Test Case: 思维链流式输出**
  - **Input**: 模拟 LLM 返回带有 `<think>...</think>` 的流。
  - **Check**: 前端收到的 SSE 事件序列中，包含独立的 `thought` 事件，且最终回复不包含 `<think>` 标签内容。

### 3.2 智能规划模式 (Workflow Mode)
- [ ] **Test Case: 依赖任务阻塞**
  - **Input**: 创建任务 B 依赖任务 A。任务 A 处于 RUNNING 状态。
  - **Check**: 任务 B 保持 PENDING，未进入 Redis Stream。
- [ ] **Test Case: 依赖满足触发**
  - **Input**: 将任务 A 更新为 COMPLETED。
  - **Check**: 任务 B 自动进入 Redis Stream，状态变更为 QUEUED/RUNNING。
- [ ] **Test Case: 变量替换**
  - **Input**: 任务 B 输入参数为 `{{task_A.output}}`，任务 A 输出 `{"result": 42}`。
  - **Check**: 任务 B 执行时，实际输入参数被替换为 `42`。

### 3.3 自动任务模式 (Auto Task Mode)
- [ ] **Test Case: 意图识别准确率**
  - **Input**: 使用测试集（包含 50+ 条典型指令）。
  - **Check**: 解析出的 Action 类型和参数与预期一致率 > 90%。
- [ ] **Test Case: 自动重试机制**
  - **Input**: 模拟网络超时异常 (`NetworkError`)。
  - **Check**: 函数自动重试 3 次（时间间隔符合指数退避），最终失败或成功。
- [ ] **Test Case: 浏览器并发限制**
  - **Input**: 瞬间发起 N+1 个浏览器任务（N=限制数）。
  - **Check**: 第 N+1 个任务处于等待状态，直到有资源释放。

## 4. 可观测性验证 (Observability Tests)

### 4.1 追踪与日志
- [ ] **Test Case: Trace ID 连通性**
  - **Input**: 发起 HTTP 请求。
  - **Check**:
    - API 响应 Header 包含 `X-Request-ID`。
    - 应用日志中包含该 ID。
    - 关联的后台 Worker 日志中也包含相同的 ID。
- [ ] **Test Case: 结构化日志格式**
  - **Input**: 触发一条日志记录。
  - **Check**: 日志输出为合法的 JSON 字符串，且包含 `level`, `timestamp`, `message`, `trace_id` 等字段。

### 4.2 性能指标
- [ ] **Test Case: TTFT 监控**
  - **Input**: 执行流式对话任务。
  - **Check**: 监控系统（或日志）记录了从收到请求到生成第一个 Token 的时间差。
