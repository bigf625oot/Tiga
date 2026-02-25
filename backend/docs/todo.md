# 开发 Todo List (Development Roadmap)

## Phase 1: 基础设施搭建 (Infrastructure)
- [ ] **数据库初始化**
    - [ ] 设计 `tasks`, `sub_tasks`, `execution_logs`, `tools` 表结构的 Alembic 迁移脚本
    - [ ] 配置 PostgreSQL 连接池与异步 Session
- [ ] **消息队列配置**
    - [ ] 搭建 Redis 服务（Docker）
    - [ ] 实现 Redis 连接池工具类 `app/core/redis.py`
    - [ ] 封装 Queue Producer/Consumer 基础类

## Phase 2: 核心模块开发 (Core Modules)
- [ ] **任务模型与CRUD**
    - [ ] 实现 `Task` 和 `SubTask` 的 SQLAlchemy 模型
    - [ ] 实现 Pydantic Schema (`TaskCreate`, `TaskResponse`)
    - [ ] 编写 CRUD Service (`create_task`, `get_task_status`)
- [ ] **任务解析引擎 (Parser & Splitter)**
    - [ ] 集成 LLM 客户端 (OpenAI/Anthropic)
    - [ ] 编写 System Prompt 用于任务拆分
    - [ ] 实现 `TaskSplitter` 类，解析 JSON 输出并构建 DAG
    - [ ] 单元测试：验证不同类型 Prompt 的拆分效果

## Phase 3: 执行引擎实现 (Execution Engine)
- [ ] **调度器 (Scheduler)**
    - [ ] 实现 `check_ready_tasks` 逻辑，处理依赖关系
    - [ ] 实现任务入队逻辑 (`LPUSH`)
- [ ] **Worker 服务**
    - [ ] 实现后台 Worker 进程入口
    - [ ] 实现 `worker_loop` (`BRPOP`)
    - [ ] 实现任务状态更新与结果回写
    - [ ] 实现 Pub/Sub 机制通知调度器

## Phase 4: 工具与环境集成 (Tools & Environment)
- [ ] **沙箱环境 (Sandbox)**
    - [ ] 集成 `e2b-code-interpreter` SDK
    - [ ] 封装 `SafeExecutor` 类，支持 Python 代码执行
    - [ ] 实现环境变量注入与文件上传/下载
- [ ] **工具注册中心 (Tool Registry)**
    - [ ] 设计工具注册 API
    - [ ] 实现 MCP Client 集成，支持加载外部 MCP 服务
    - [ ] 实现本地 Python 函数（Skills）的装饰器注册机制

## Phase 5: 控制与优化 (Control & Optimization)
- [ ] **Token 控制**
    - [ ] 集成 `tiktoken`
    - [ ] 实现 Output Interceptor，自动截断过长输出
    - [ ] 记录每个子任务的 Token 消耗
- [ ] **错误处理**
    - [ ] 实现指数退避重试机制
    - [ ] 实现死信队列处理逻辑
- [ ] **API 接口开发**
    - [ ] 开发任务提交、查询、取消接口
    - [ ] 开发日志查询接口

## Phase 6: 测试与部署 (Testing & Deployment)
- [ ] **测试**
    - [ ] 编写 Core 模块单元测试 (>90% 覆盖率)
    - [ ] 编写端到端集成测试 (提交任务 -> 拆分 -> 执行 -> 结果)
    - [ ] 进行高并发压力测试
- [ ] **文档与审查**
    - [ ] 完善 API 文档 (OpenAPI/Swagger)
    - [ ] 代码审查 (Code Review)
    - [ ] 编写部署脚本 (Dockerfile, docker-compose.yml)
