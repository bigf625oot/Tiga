目录下各个 Vue 文件的深层架构和代码分析，该目录本质上是一个 处理大模型流式事件与异步 Agent 任务的可视化引擎 。它遵循了严格的组件分层和职责单一原则（第一性原理）。

以下是每个文件的核心职责与定位：

### 1. SmartQATaskPanel.vue（工作流容器适配器）
- 职责 ：它是整个侧边栏工作流（Task Panel）的顶层入口和调度中枢。
- 机制 ：通过判断当前 Agent 的工作模式（例如是否为 Auto Task 模式），决定是渲染传统的问答流，还是挂载底层的多标签页工作区（ WorkspaceTabs ）。它起到了 防腐层 的作用，将 SmartQA 的业务逻辑与底层的通用工作流组件隔离开来。
### 2. SoloTaskCard.vue（单任务状态机卡片）
- 职责 ：这是该目录下 复杂度最高 的核心业务组件，负责渲染 Agent 在执行单一复杂任务时的完整生命周期。
- 机制 ：
  - 全链路聚合 ：它内部消化了规划步骤（Plan Steps）、思维链（ThinkingBlock）、工具调用日志（Tool Calls）、最终交付物（Artifacts）以及图表渲染（ChartFrame）。
  - 状态驱动 ：内部维护了一个复杂的 computeExecution 状态机，能够将非结构化的 SSE 流式事件（Stream Events）实时解析并映射为进度条和节点状态（Pending -> Running -> Done / Error），实现了 100% 的渲染确定性。
### 3. StreamSteps.vue（流式事件观测器）
- 职责 ：专注于将 Agent 执行过程中的原始底层事件（如 thought , tool_call , status ）以时间线（Timeline）的模式展示出来。
- 机制 ：它是一个 纯展示组件 。设计亮点在于交互的自动化：它会监听流的结束状态，并在任务完成 1.5 秒后自动收起详情，以降低用户的视觉认知负载。
### 4. ToolCallPanel.vue（工具调用详情抽象）
- 职责 ：专门用于渲染某一次具体工具（Tool/Function）的调用细节。
- 机制 ：它充当了系统协议与用户之间的“翻译官”。负责将大模型发出的 args （入参）和执行返回的 result （出参）进行 JSON 格式化与高亮展示。同时，根据工具的状态（成功或失败），自适应切换边框颜色和图标。
### 5. ToolStatus.vue（轻量级工具监控器）
- 职责 ：提供一个紧凑型的工具执行状态摘要（例如： 正在使用搜索工具... 或 已完成 3 个工具调用 ）。
- 机制 ：它是 ToolCallPanel 的宏观摘要版。其设计精髓在于 错误阻断逻辑 ——当任何一个工具调用失败时，组件会强制保持展开状态，确保异常能够第一优先级暴露给用户，拒绝被折叠隐藏。
### 架构洞察 (P10 Insights)
该目录的组件拓扑构成了一个典型的 复合组件模式（Compound Components） ：

- 调度层 ： SmartQATaskPanel 负责路由。
- 聚合层 ： SoloTaskCard 负责编排业务。
- 原子层 ： StreamSteps 、 ToolCallPanel 、 ToolStatus 负责底层状态的微观展示。
这种设计的护城河在于 ：当未来系统从单体 Agent（Solo）演进为多 Agent 协作（Multi-Agent）时，底层的原子展示组件和状态解析器可以零修改复用，只需在顶层更换新的编排卡片即可。