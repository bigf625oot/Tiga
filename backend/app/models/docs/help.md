# Tiga 系统数据建模说明文档

本文档基于 `backend/app/models/` 目录下的 SQLAlchemy 模型代码生成，详细描述了系统的核心业务对象、字段设计、以及它们之间的关联关系。系统整体架构基于 **多智能体协同** 和 **工作流编排**，并深度集成了大语言模型 (LLM) 的能力。

---

## 1. 智能体建模 (Agent)
**文件**: `agent.py`

智能体是系统的核心执行单元，不仅封装了 LLM，还集成了工具、技能、记忆和知识库。

### 核心字段设计
*   **身份标识**: 
    *   `id` (UUID): 唯一主键。
    *   `name` / `role` / `category`: 智能体的名称、角色（如前端开发、数据分析师）和业务分类。
    *   `version`: 支持多版本控制。
    *   `is_template`: 是否作为模板供其他用户克隆。
*   **LLM 配置**:
    *   `provider`: 大模型提供商（如 OpenAI, Anthropic）。
    *   `model_id`: 具体的模型版本（如 gpt-4o）。
    *   `model_config` (JSON): 模型生成参数（如 temperature, top_p）。
*   **提示词工程**:
    *   `system_prompt` (Text): 全局系统提示词。
    *   `instructions` (JSON): 结构化的指令集。
*   **能力与外挂 (JSON 配置)**:
    *   `tools_config` / `mcp_config` / `skills_config` / `knowledge_config`: 以外挂形式挂载工具、MCP 服务器、自定义技能和知识库。
*   **框架特性开关**:
    *   `enable_react`, `enable_cot`, `show_tool_calls`: 控制智能体的推理模式和执行过程透明度。

---

## 2. 团队协作建模 (Team)
**文件**: `team.py`

定义多智能体如何协同工作，支持复杂的任务分发与结果聚合。

### 核心字段设计
*   **协作模式 (`mode`)**: 采用枚举 `TeamMode` 强约束。
    *   `COORDINATE`: Leader 协调模式。
    *   `ROUTE`: 路由模式，分发给特定专家。
    *   `BROADCAST`: 广播模式，全员并行处理。
    *   `TASKS`: 任务模式，生成清单按序执行。
*   **成员结构**:
    *   `leader_id`: 指定团队的 Leader 智能体。
    *   `members` (JSON): 存储团队中所有成员智能体的 ID 列表。
*   **运行时配置**:
    *   `team_config` (JSON): 团队级的运行参数（如 `max_loops`）。

---

## 3. 工作流建模 (Workflow)
**文件**: `workflow.py`, `agent_workflow.py`

基于图结构的任务编排系统，支持版本管理和可视化定义。

### 核心字段设计
*   **版本控制体系**:
    *   `id` (UUID): 每次修改发布都会生成新 ID。
    *   `original_id`: 溯源 ID，将同一工作流的不同版本串联起来。
    *   `version` (Integer): 递增版本号。
    *   `is_latest` / `is_draft`: 状态标识位，方便快速查询最新发布版或草稿。
*   **图结构定义**:
    *   `definition` (JSON): 核心字段，存储前端可视化编辑器生成的节点 (Nodes) 和连线 (Edges) 的拓扑结构。
    *   `webhook_url` (可选): 支持将工作流注册为外部系统（如 N8N）的触发器。
*   **运行参数**:
    *   `input_variables` / `runtime_config`: 定义工作流启动时需要的参数格式和环境配置。

---

## 4. 技能与工具扩展建模 (Skill & MCP)
**文件**: `skill.py`, `mcp.py`, `tool.py`

定义了智能体与外部世界交互的边界和动作。

### Skill (高级业务技能)
*   `slug`: 唯一 URL 标识符。
*   `content`: 存储 Prompt 模板或执行逻辑。
*   `input_schema` / `output_schema` (JSONB): 严格定义输入输出的 JSON Schema。
*   `tools_config`: 绑定底层的基础工具函数。

### MCP (Model Context Protocol 服务器)
*   `transport_type`: `stdio` (本地进程) 或 `sse` (远程流式)。
*   `config`: 连接配置（如启动命令、URL）。
*   `env_vars`: 敏感环境变量（建议业务层加密）。
*   `capabilities_cache` (JSONB): 核心优化设计，预先缓存服务器提供的 Tools、Resources 和 Prompts，避免每次决策前建立真实连接。

---

## 5. 任务执行与状态机建模 (Task)
**文件**: `task.py`

将复杂的业务请求拆解为可追踪的执行单元。

### ExecutionTask (主任务)
*   存储原始请求 (`original_prompt`) 和全局生命周期状态 (`status`)。

### SubTask (子任务)
*   `task_type`: 标识任务类型（代码生成、数据检索等）。
*   `dependencies` (JSON): 存储前置任务 ID，实现 DAG（有向无环图）执行顺序。
*   **状态机控制**: 内部包含 `validate_transition` 逻辑，严格控制 `PENDING` -> `RUNNING` -> `COMPLETED`/`FAILED` 的状态流转。

### ExecutionLog (执行日志)
*   记录 `stdout`, `stderr`, 详细的耗时以及 `tokens_used`。

---

## 6. 知识库建模 (Knowledge)
**文件**: `knowledge.py`

为智能体提供 RAG (检索增强生成) 的数据基础。

### KnowledgeDocument (文档与目录)
*   `parent_id` / `is_folder`: 支持树状目录结构。
*   `oss_key` / `oss_url`: 物理文件存储映射。
*   `status`: 跟踪文件解析生命周期 (`UPLOADING` -> `INDEXING` -> `INDEXED` -> `FAILED`)。

### KnowledgeChat (知识问答)
*   记录基于知识库的问答历史。
*   `sources` (JSON): 记录回答引用的文档片段，提供可解释性。

---

## 7. 基础设施建模 (LLM, Node)
**文件**: `llm_model.py`, `node.py`

*   **LLMModel**: 集中管理各大模型提供商的 API Keys、端点、成本 (`input_token_price`) 以及能力约束 (`supports_vision`, `supports_tools`)。
*   **Node**: 监控分布式执行节点的状态，包含 `status` (ONLINE/OFFLINE)、`metrics` (CPU/内存 JSON) 以及 `alerts`。

---

## 核心关联关系总结
1.  **Agent (智能体)** 是系统的中心枢纽。它向上被 **Team (团队)** 组合或被 **Workflow (工作流)** 编排；向下挂载 **LLMModel (大模型)** 提供智力，挂载 **Skill/MCP (技能/工具)** 提供行动力，挂载 **Knowledge (知识库)** 提供业务上下文。
2.  **Workflow (工作流)** 的 `definition` 决定了 **Agent** 或 **Tool** 的执行顺序。
3.  **Agent/Workflow** 的一次运行会实例化为一个 **ExecutionTask (主任务)**。
4.  主任务被拆解为多个 **SubTask (子任务)**，依据 `dependencies` 构成 DAG 图，最终在 **Node (计算节点)** 上执行并产生 **ExecutionLog (执行日志)**。