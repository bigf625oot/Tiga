智能体系统全链路优化方案 (Optimization Blueprint)
1. 方案概述
解决现有系统在高并发下的稳定性、长对话的响应延迟、复杂任务的调度可靠性以及全链路监控缺失四大核心问题。通过引入分布式消息队列、状态机乐观锁、Agent 缓存池及结构化追踪，构建一个工业级的 AI 智能体平台。
2. 基础设施层重构 (Infrastructure)
2.1 分布式任务队列 (Redis Streams)
目标：取代 asyncio.Queue，实现任务持久化与多实例 Worker 负载均衡。
技术选型：Redis Streams (使用 redis-py)。
关键逻辑：
API 层作为 Producer，将任务 ID 和元数据推入 task_stream。
后台 Worker 进程作为 Consumer Group，确保每个任务至少被处理一次（ACK 机制）。
2.2 状态机与并发控制
目标：防止任务状态逆转，确保状态变更的原子性。
实施方案：
乐观锁：在 OpenClawTask 和 SubTask 表中增加 version 字段。使用 SQLAlchemy 的 version_id_col 特性。
状态机校验：定义严格的状态转换映射（例如：禁止直接从 PENDING 跳到 COMPLETED）。
2.3 统一 AgentExecutor 代理层
目标：屏蔽底层不同 Agent 框架（Agno, OpenClaw, TaskSplitter）的调用差异。
架构设计：
定义 BaseAgentExecutor 抽象基类。
实现 ChatAgentExecutor、WorkflowAgentExecutor 和 AutoTaskAgentExecutor。
统一输入输出协议，支持流式 (Stream) 和阻塞 (Sync) 两种执行模式。
3. 业务模式专项优化 (Mode Optimizations)
3.1 对话模式 (Chat Mode)：性能与交互
Agent 实例池 (LRU Cache)：使用 cachetools 实现内存缓存，缓存已初始化的 Agent 对象，减少 300ms+ 的启动开销。
上下文滑动窗口：实现 get_optimized_context 算法，动态计算 Token 长度，仅保留最近 N 条关键消息，并在窗口头部保留 System Prompt。
思维链支持：针对 DeepSeek 等模型，在后端流式解析 <think> 标签，将“思考过程”与“正式回复”通过不同的前端事件分发。
3.2 智能规划模式 (Workflow Mode)：复杂调度
DAG 依赖管理：子任务表增加 dependencies 字段（JSON 数组）。
调度引擎升级：
子任务完成时，触发 check_ready_tasks 逻辑。
只有依赖项全部处于 COMPLETED 状态的任务才会被推入 Redis Stream。
数据流转：实现 Output-to-Input 映射器，允许下游任务引用上游任务的执行结果（如 {{task_1.output}}）。
3.3 自动任务模式 (Auto Task Mode)：可靠执行
意图识别增强：在 LLM Parser 中引入 Few-shot Prompting，通过 5-10 个标准 Action 示例降低意图误判率。
指数退避重试：集成 tenacity 库，对网络超时、浏览器崩溃等非逻辑错误进行自动重试（2s, 4s, 8s）。
资源限流 (Semaphore)：利用 Redis 分布式锁/信号量，限制单个用户并发运行的浏览器实例数，保护节点资源。
4. 全链路可观测性 (Observability)
4.1 追踪与日志 (Trace ID)
Trace 穿透：通过 FastAPI 中间件生成 request_id，利用 contextvars 将其传递至异步任务处理函数及远程 Node 节点。
结构化日志：引入 structlog，所有日志以 JSON 格式输出，包含 task_id、duration、token_usage 等关键字段。
4.2 核心指标埋点
性能指标：P95 首字响应延迟 (TTFT)、任务排队时长。
成功率指标：子任务成功率、意图解析准确率、重试触发频率。