# 研究发现 (Findings)

## 关于 ai-sdk/vue 与当前架构的适配调研
在推进 Phase 4 (深度整合 `ai-sdk/vue` 流式协议) 时，我对当前的流式处理 (`useChatSession.ts` 和 `eventDispatcher.ts`) 进行了深入分析。

### 1. 当前实现方式：自研的 Event Source (SSE) 解析
- `useChatSession.ts` 中的 `handleStreamResponse` 实现了手动的 `TextDecoder` 和 `reader.read()` 循环，按行解析 `event: xxx` 和 `data: xxx`。
- 然后它依赖 `createEventDispatcher` 将 `thought`, `text`, `tool_call`, `plan_created` 等事件手动追加到 `assistantMsg` 对象中 (`assistantMsg.content += ...`, `assistantMsg.reasoning += ...` 等)。

### 2. ai-sdk/vue 的工作方式
- `@ai-sdk/vue` 提供的 `useChat` 也是处理流式数据，但它有一套标准化的内部状态管理：
  - `messages`: 标准的 `{ role, content, toolInvocations, annotations }` 数组。
  - `append`, `reload`, `stop`: 标准的控制函数。
- 后端需要返回 Vercel AI SDK 兼容的数据流格式（如 `0:"text"`, `9:{"toolCallId":...}` 等），即 `StreamData` 协议。

### 3. 架构决策 (Trade-offs & P10 视野)
目前后端返回的是**自定义的 SSE 协议**（带有 `event: thought`, `event: plan_created` 等领域特定事件），而**不是 Vercel AI SDK 的标准流格式**。
如果强行在前端将自研 SSE 桥接到 `ai-sdk/vue` 的 `useChat`：
- **优点**：可以利用 `useChat` 提供的重试、状态管理等外围能力。
- **缺点**：我们需要写一个极其复杂的 adapter (DataStreamParser)，将自定义的 SSE `plan_created`, `task_start` 等映射到 `ai-sdk` 的 `annotations` 中。这反而增加了不必要的中间层。

**P10 级决断：保持核心流式引擎独立，但采用 Vercel AI SDK 的 UI 抽象思想。**
我们的 `MessageAdapter.ts` 已经完美承担了“将后端领域模型转化为 UI 渲染块 (Blocks)” 的职责。这其实就是 Vercel AI SDK 中处理 `annotations` 和 `toolInvocations` 的思想。我们无需强行引入 `@ai-sdk/vue` 的 fetch 逻辑，而是继续使用我们的 `useChatSession.ts` 获取数据，通过 `MessageAdapter.ts` 将响应式数据实时映射到刚刚建好的 `BlockRendererRegistry` 中。

### 4. 解决上下文隔离与 Provide/Inject
对于 `solo`, `team`, `workflow` 模式下卡片形态不同的问题。
我们可以通过在顶层容器 (`SmartQA.vue` / `ChatView.vue`) 中 Provide 一个 `chatContext` (包含 `modeId`, `agent` 等信息)，而在底层的 BlockRenderer 中 Inject 即可，避免层层透传 Props。