# 后端架构重构方案 (Backend Refactoring Proposal)

## 1. 现状分析 (Current State Analysis)

### 1.1 架构分层
项目采用了 `API` -> `Service` -> `CRUD` -> `Model` 的分层架构，但存在严重的层级穿透和职责不清问题。
*   **Fat API**: `app/api/endpoints/chat.py` 承担了核心业务逻辑，包括模型选择、DeepSeek 特殊处理、工具组装等。
*   **Impure CRUD**: `app/crud/crud_agent.py` 包含业务副作用（创建 Agent 时自动创建剧本），违反单一职责原则。
*   **Cross-Layer Calls**: API 层经常跳过 Service 层直接调用 CRUD，导致业务逻辑分散且难以复用。

### 1.2 性能瓶颈
*   **同步阻塞**: `app/services/tools/` 目录下的工具大量使用同步的 `requests` 库和 `time.sleep`，阻塞了主线程的 asyncio 事件循环。
*   **缓存碎片化**: 缺乏统一的缓存层抽象，混合使用了 Redis 和本地文件缓存，且部分高频调用（如工具执行结果）未充分利用缓存。

### 1.3 依赖管理
*   项目依赖清晰，使用了 `requirements.txt` 进行管理。
*   存在潜在的模块间耦合风险，特别是 `Agent` 与 `RAG` 模块之间。

---

## 2. 重构目标 (Objectives)

1.  **分层净化**: 严格遵循分层架构，API 层仅负责路由和参数解析，业务逻辑下沉至 Service 层，CRUD 层仅负责数据存取。
2.  **异步改造**: 将所有外部 I/O 操作（HTTP 请求、数据库查询）改造为异步非阻塞模式，提升并发吞吐量。
3.  **模块解耦**: 明确 `Chat`、`Agent`、`RAG`、`Tools` 等核心模块的边界，通过 Service 接口进行交互。
4.  **可测试性**: 提升单元测试覆盖率，确保核心业务逻辑可独立测试。

---

## 3. 详细重构计划 (Detailed Plan)

### Phase 1: 核心业务逻辑抽离 (Chat Refactoring)
**目标**: 解决 `chat.py` 过于臃肿的问题，建立标准的 Service 调用模式。

*   **Task 1.1**: 创建 `app/services/chat/service.py`，定义 `ChatService` 类。
*   **Task 1.2**: 将 `chat_session` 中的以下逻辑迁移至 `ChatService`:
    *   历史记录加载 (`crud_chat.get_history`)
    *   模型参数组装
    *   DeepSeek 推理模式处理
    *   Agent/Workflow 执行器调用
    *   流式响应生成
*   **Task 1.3**: 重构 `app/api/endpoints/chat.py`，使其仅作为 Controller 调用 `ChatService`。
*   **Task 1.4**: 编写 `tests/services/test_chat_service.py` 进行验证。

### Phase 2: 数据层净化 (CRUD Purification)
**目标**: 移除 CRUD 层中的业务副作用。

*   **Task 2.1**: 将 `app/crud/crud_agent.py` 中的 `create_with_user_script` 逻辑拆分。
*   **Task 2.2**: 在 `app/services/agent/service.py` 中实现 `create_agent` 方法，协调 `Agent` 和 `UserScript` 的创建。
*   **Task 2.3**: 更新 `app/api/endpoints/agents.py` 调用新的 Service 方法。

### Phase 3: 工具层异步化 (Async Tools)
**目标**: 消除主线程阻塞，提升系统并发能力。

*   **Task 3.1**: 识别 `app/services/tools/` 中使用 `requests` 的工具（如 `zoom.py`, `linear.py`）。
*   **Task 3.2**: 引入 `httpx` (Async Client) 替换 `requests`，或使用 `starlette.concurrency.run_in_threadpool` 包装同步调用。
*   **Task 3.3**: 统一工具层的错误处理机制，抛出标准异常而非返回错误 JSON 字符串。

### Phase 4: 全链路测试 (Integration Testing)
**目标**: 确保重构不破坏现有功能。

*   **Task 4.1**: 完善 `tests/api/endpoints/test_chat.py`，覆盖新的 Service 调用链路。
*   **Task 4.2**: 执行 `pytest` 全量回归测试。

---

## 4. 架构规范 (Architectural Guidelines)

*   **API Layer**: 仅包含 `router`, `schema` 验证, `dependency` 注入。禁止包含 `if/else` 业务分支。
*   **Service Layer**: 包含所有业务逻辑、事务控制、第三方服务调用。
*   **CRUD Layer**: 仅包含 `SQLAlchemy` 查询语句。禁止包含业务逻辑或副作用。
*   **Model Layer**: 仅包含数据库表定义。

## 5. 交付物 (Deliverables)

1.  重构后的代码库
2.  更新的 API 文档 (Swagger/OpenAPI)
3.  单元测试报告 (Coverage Report)
4.  重构总结报告
