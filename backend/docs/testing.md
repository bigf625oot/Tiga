# 测试文档 (Testing Strategy & Cases)

## 1. 单元测试 (Unit Testing)

目标：核心逻辑覆盖率 > 90%

### 1.1 任务解析模块 (Task Parser)
- **Case 1.1.1**: 输入简单的单一任务 Prompt，验证输出包含 1 个 SubTask。
- **Case 1.1.2**: 输入包含 "First... then..." 的复合 Prompt，验证输出包含依赖关系的 SubTasks。
- **Case 1.1.3**: 输入模糊或无法解析的 Prompt，验证抛出 `TaskParsingError` 或请求用户澄清。
- **Case 1.1.4**: 验证不同 LLM 模型 (GPT-4, Claude) 的响应解析兼容性。

### 1.2 任务拆分算法 (Splitter Algorithm)
- **Case 1.2.1**: 构建包含 3 层依赖的 DAG，验证拓扑排序正确性。
- **Case 1.2.2**: 验证循环依赖检测，输入 A->B->A 的依赖关系，预期抛出 `CyclicDependencyError`。
- **Case 1.2.3**: 验证孤立节点处理，确保无依赖任务也能被识别。

### 1.3 状态机转换 (State Machine)
- **Case 1.3.1**: PENDING -> SPLITTING -> READY -> QUEUED -> RUNNING -> COMPLETED (正常流程)。
- **Case 1.3.2**: RUNNING -> FAILED -> QUEUED (重试流程)。
- **Case 1.3.3**: RUNNING -> FAILED -> BLOCKED (重试耗尽)。
- **Case 1.3.4**: 验证非法状态转换（如 PENDING -> COMPLETED）抛出 `InvalidStateTransitionError`。

### 1.4 Token 计算准确性
- **Case 1.4.1**: 输入英文字符串，对比 `tiktoken` 标准输出。
- **Case 1.4.2**: 输入包含中文、Emoji 的字符串，验证计算误差在允许范围内。
- **Case 1.4.3**: 验证截断函数 `check_and_truncate` 是否正确保留首尾并在中间插入标记。

## 2. 集成测试 (Integration Testing)

### 2.1 端到端任务执行流程 (E2E)
- **Scenario**: 用户提交 "查询当前 BTC 价格并绘制趋势图"。
    - **Step 1**: API 接收请求，返回 `task_id`。
    - **Step 2**: Splitter 拆分为 "Search BTC Price" 和 "Plot Chart"。
    - **Step 3**: Scheduler 调度 "Search BTC Price" 执行。
    - **Step 4**: Worker 调用 MCP 工具获取数据。
    - **Step 5**: "Search BTC Price" 完成，触发 "Plot Chart" 入队。
    - **Step 6**: Sandbox 执行 Python 绘图代码。
    - **Step 7**: 最终状态 COMPLETED，结果包含图片 URL。

### 2.2 工具调用集成
- **Case 2.2.1**: 调用本地注册的 Python 函数 (Skill)，验证参数传递和返回值。
- **Case 2.2.2**: 调用外部 MCP 服务（如 Brave Search），验证网络通信和协议解析。
- **Case 2.2.3**: 模拟 MCP 服务超时，验证系统超时处理。

### 2.3 沙箱环境安全测试
- **Case 2.3.1**: 尝试执行 `os.system('rm -rf /')`，验证沙箱拦截或权限拒绝。
- **Case 2.3.2**: 尝试访问环境变量，验证敏感信息隔离。
- **Case 2.3.3**: 验证内存和 CPU 限制生效（如死循环代码被终止）。

### 2.4 异步任务调度
- **Case 2.4.1**: 并发提交 10 个任务，验证 Redis 队列长度变化。
- **Case 2.4.2**: 模拟 Worker 宕机重启，验证任务重新调度机制（ACK 机制）。

## 3. 性能测试 (Performance Testing)

### 3.1 高并发处理能力
- **Tool**: Locust / JMeter
- **Metrics**: TPS (Transactions Per Second), Latency (P95, P99).
- **Goal**: 100 任务/秒提交，P95 响应时间 < 200ms。

### 3.2 大数据量任务查询
- **Setup**: 数据库预置 100万条任务记录。
- **Test**: 根据 `status` 和 `created_at` 分页查询任务列表。
- **Goal**: 查询响应时间 < 500ms (验证索引有效性)。

### 3.3 Token 控制有效性
- **Test**: 提交生成超长文本的任务。
- **Goal**: 验证数据库中存储的日志已被截断，且内存占用未超标。

## 4. 测试环境配置

### 4.1 依赖服务
- **PostgreSQL**: 14.0 (Docker)
- **Redis**: 6.2 (Docker)
- **MCP Server**: Mock Server 用于测试
- **LLM API**: Mock / OpenAI Sandbox

### 4.2 测试数据准备
- 提供 `fixtures/tasks.json` 包含各种典型任务 Prompt。
- 提供 `fixtures/tools.json` 包含模拟工具定义。
