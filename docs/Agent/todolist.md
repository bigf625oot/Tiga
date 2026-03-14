# Agent 架构升级与待办事项

## ✅ 已完成升级 (Refactoring Completed)

### 1. 核心架构重构 (Core Architecture)
- **目录结构调整**: 将 `engines/` 重命名为 `handlers/`，明确职责。
- **统一接口定义**: 创建 `BaseHandler` 基类，规范所有 Agent 模式（Quick, Plan, Team, Flow）的统一接口。
- **控制平面升级**: 重构 `AgnoControlPlane`，引入 `process_stream` 支持流式输出，并根据 NLU 意图分发请求到对应的 Handler。

### 2. 处理器实现 (Handlers Implementation)
- **QuickHandler**: 实现快问快答模式，支持基础对话。
- **PlanHandler**: 实现自规划模式框架（ReAct），集成 Agno Agent。
    - **流式增强**: 实现 `agent.run(stream=True)` 对接，支持思维链（CoT）内容的实时透传。
    - **动态初始化**: 采用懒加载模式异步初始化 Agent。
- **TeamHandler**: 建立多 Agent 协作模式框架。
    - **团队构建**: 实现基于 `create_team` 的团队实例化逻辑。
    - **流式协作**: 支持团队内部消息交互的流式反馈。
- **FlowHandler**: 建立工作流模式框架。
    - **引擎集成**: 对接 `AgentWorkflowEngine`，实现工作流启动与执行。
    - **事件反馈**: 支持 Status, Task Start/Complete, Error 等细粒度事件的流式输出。

### 3. 配置与工厂模式 (Configuration & Factory)
- **配置模型**: 定义 `domain/config.py` (Pydantic)，标准化 `AgentConfig` 和 `ToolConfig`。
- **Agent 工厂**: 创建 `core/agent_factory.py`，实现基于配置动态创建 Agent 实例。
    - **Team 支持**: 实现 `create_team` 方法，支持递归创建成员 Agent 和 Leader Agent。
    - **Skill 集成**: 实现从本地 `skills/` 目录自动加载 Skill 并注入 Agent。
    - **模型参数**: 支持 `temperature`, `max_tokens` 等模型参数的透传配置。
- **工具工厂**: 创建 `tools/tool_factory.py`，实现工具的自动发现与动态实例化。

### 4. 流式处理增强 (Stream Processing)
- **智能解析**: 升级 `core/stream_processor.py`，支持 `<think>` 标签解析，兼容混合内容类型（Content/Status/Error）。

### 5. NLU 与持久化 (NLU & Persistence)
- **意图识别**: 升级 `NluService`，支持 `Team` (团队协作) 和 `Workflow` (工作流) 意图识别。
- **参数提取**: 增强参数提取能力，支持解析团队角色、工作流步骤等复杂参数。
- **会话记忆**: 实现 `storage/session_history.py`，支持基于 DB 的会话历史存储（User & Assistant 消息）。
- **状态管理**: `AgnoControlPlane` 集成会话持久化，自动保存交互历史。

### 6. 测试体系 (Testing)
- **单元测试**: 建立 `tests/` 目录，覆盖 `NluService`, `PlanHandler`, `TeamHandler`, `FlowHandler`, `SessionHistory`。
- **测试运行器**: 提供 `run_tests.py` 脚本，实现一键回归测试。

---

## 📝 待补充完善功能 (Backend To-Do List)

### 1. 处理器逻辑深化 (Deepen Handler Logic)
- [x] **PlanHandler**:
    - [x] 完善与 Agno Agent 的流式对接，确保 `reasoning` 内容能实时透传。
    - [x] 支持动态加载工具配置。
- [ ] **TeamHandler**:
    - [x] 实现真正的团队初始化逻辑（对接 `ResearchTeam` 等）。
    - [x] 实现多 Agent 间的消息路由与状态共享。
    - [ ] **动态化增强**: 基于 NLU 提取的参数动态生成 `TeamConfig`，而非仅使用默认模板。
- [ ] **FlowHandler**:
    - [x] 对接 `WorkflowEngine`，实现基于 DAG 的步骤执行。
    - [x] 实现工作流状态的持久化与恢复。
    - [ ] **执行器实现**: 完善 `ExecutorAgent`，实现真实的工具调用和任务执行逻辑（目前为模拟）。

### 2. 工厂与配置增强 (Factory & Config Enhancements)
- [x] **AgentFactory**:
    - [x] 实现 `create_team` 方法，支持通过配置创建 Team。
    - [x] 完善 LLM 模型解析逻辑，支持更多模型参数配置。
- [x] **Skill 集成**:
    - [x] 在 `AgentFactory` 中集成 `Skills` 加载逻辑，使 Agent 能同时使用 Tools 和 Skills。

### 3. NLU 服务升级 (NLU Service Upgrade)
- [x] **意图识别**:
    - [x] 升级 `NluService`，接入真实模型或更复杂的 Router。
    - [x] 优化对 `Team` 和 `Workflow` 意图的分类准确率。
- [x] **参数提取**:
    - [x] 增强从自然语言中提取任务参数（如目标 URL、时间范围）的能力。

### 4. 数据持久化 (Persistence)
- [ ] **配置存储**:
    - [ ] 实现将 `AgentConfig` 和 `ToolConfig` 保存到数据库。
    - [ ] `AgentManager` 支持从数据库加载配置。
- [x] **会话记忆**:
    - [x] 完善 Redis/DB 的会话存储，支持跨 Handler 的上下文共享。

### 5. 工具库完善 (Tools Expansion)
- [ ] **工具适配**:
    - [ ] 检查并修复所有自动发现的工具，确保其依赖和配置正确。
    - [ ] 为核心工具添加详细的单元测试。
- [ ] **高级错误恢复**:
    - [ ] 实现 LLM/工具调用失败后的自动重试与降级策略。
