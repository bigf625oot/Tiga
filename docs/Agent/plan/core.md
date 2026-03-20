企业级 Agent 异步编排与工作流引擎技术方案
1. 概述 (Executive Summary)
本方案设计了一套高度可观测、可持久化的 Agent 编排系统。区别于传统的单轮对话或黑盒 ReAct 循环，本方案采用 Planner-Executor（规划-执行） 架构，将复杂的用户目标拆解为可管理的任务序列，并通过标准化的事件流（Standardized Event Stream）实现类似 Claude Code 的极致前端交互体验。
2. 系统架构 (System Architecture)
系统分为四层结构：
交互层 (Interaction Layer)：负责事件流的标准化处理，识别并分离思维链、工具调用与正文。
编排层 (Orchestration Layer)：AgentWorkflowEngine 负责任务的生命周期管理（Pending -> Running -> Completed）。
执行层 (Execution Layer)：具体的 Agent（如 Planner, Executor）利用 ReAct 模式完成具体任务。
持久层 (Persistence Layer)：基于 SQLAlchemy 的任务状态存储，支持断点续传。
3. 核心组件设计
3.1 编排引擎：Planner-Executor 模式
Planner (规划者)：接收 user_goal，调用 LLM 生成 AgentPlan 及一系列 AgentTask。
Executor (执行者)：
内部逻辑：采用 ReAct (Reasoning and Acting) 模式。
任务原子性：每个任务是一个独立的 ReAct 循环，确保逻辑闭环。
上下文传递：自动将上一个任务的 result 注入到下一个任务的 context 中。
3.2 事件流标准化器 (Event Normalizer)
功能：对所有 Agent 输出进行实时过滤。
Claude Style 适配：
thought：独立输出思维过程（支持 <think> 标签跨包解析）。
call / result：结构化工具调用。
text：纯净的正文输出。
意义：解耦后端逻辑与前端渲染，前端无需复杂的正则匹配即可实现专业 UI。
3.3 辅助服务：智能标题生成 (Title Generator)
策略：异步后台任务。
触发：在第一轮对话完成后，利用 Fast LLM 提取摘要。
4. 业务流程 (Workflow Sequence)
初始化：用户输入指令，AgentWorkflowEngine.start_workflow 被激活。
任务规划 (Planning Phase)：
Planner Agent 分析指令。
数据库生成 AgentPlan (Status: PENDING)。
写入 AgentTask 列表。
循环执行 (Execution Phase)：
引擎按 sequence 锁死当前任务。
Executor 启动，通过 ReAct 模式调取外部工具。
实时反馈：Executor 的每一次 Thought 和 Tool Call 通过 normalize_event_stream 即时推送到前端。
上下文流转：任务 
完成后，结果写入数据库 plan.context，作为任务 的背景输入。
归档：所有任务完成，更新计划状态，同时触发 TitleGenerator 更新侧边栏名称。
5. 与 Agno (ReAct/CoT) 的对比与结合
特性	本方案 (Planner-Executor)	纯 ReAct / CoT
可预测性	高。用户可预见总步骤和当前进度。	低。LLM 随时可能进入死循环。
持久性	强。服务器宕机后可从最后一个任务恢复。	弱。状态丢失，必须从头开始。
人工介入	支持。可在任务间设置“审批点”。	难。逻辑在 LLM 内部黑盒运行。
适用场景	复杂办公自动化、长周期调研、多步报表生成。	简单问答、即时工具调用。
结合点：
本方案将 ReAct 降级为任务执行的工具。即：外层是确定的任务流（Workflow），内层是灵活的推理引擎（ReAct）。
