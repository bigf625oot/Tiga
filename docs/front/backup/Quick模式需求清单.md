# Lite (Quick) 模式产品架构与规格规范 (P10 Standard)

> **Document Context**
> 本文档定义 Tiga 平台 Lite (Quick) 模式的全链路架构标准与功能规范。
> 核心哲学：**极简交互，降维执行 (Less is More, Execution is All)**。
> 摒弃重度 Agentic 规划循环，聚焦 O(1) 的单次调度闭环，同时保留全量工具链与外挂知识能力。

## 1. 架构第一性原理 (First Principles)
Lite (Quick) 模式的本质不是“阉割功能”，而是“确定性调度”。
- **去反思化 (No Reflection)**：砍掉执行器内部的多轮自我修正循环（Self-Refine/Plan-and-Solve），一切意图在 NLU 阶段决断，执行流 100% 可预测。
- **并发组装 (Concurrent Assembly)**：上下文、历史记忆、工具链必须以并发态 (asyncio.gather) 注入，极致压缩 TTFT (Time To First Token)。
- **动态降级 (Graceful Degradation)**：当遇到 Token 超限或外部工具超时，系统通过状态机实现无缝降级，而非崩溃。

## 2. 交互入口与预处理 (Input & Preprocessing)

### 2.1 全模态输入流
- **无界文本缓冲**：输入框采用虚拟滚动+自适应高度（最高 40% vh），底层维护内存映射，防止 DOM 节点过多导致浏览器卡顿。
- **零拷贝附件池**：支持拖拽与点击上传（PDF, Docx, TXT, MD, PNG, JPG）。前端生成文件 Hash，实现秒传与缓存命中。

### 2.2 并发预处理引擎 (Pipeline)
- **文档解析 (FileContext)**：非结构化文本采用流式解析。
- **边缘视觉 (Edge OCR)**：对于图片，挂载轻量级视觉模型/专用 OCR 提取文本特征。
- **元数据抽提**：并发抽取文件 Meta（大小、类型、页数），为后续大模型的 `Citation`（引用）机制提供物理坐标。

## 3. 上下文与内存拓扑 (Memory Topology)

### 3.1 确定性记忆管理 (Determinism Memory)
- **滑动窗口与衰减 (Sliding Window)**：严格限制携带最近 N 轮上下文。
- **自适应 Token 压缩**：当上下文触及水位线（如 80% Token Limit），触发异步后台摘要机制（Summary Compression），防止主线程阻塞。
- **图谱长记忆 (Graph Memory)**：历史关键实体沉淀至 Graph DB，实现跨会话的记忆穿透。

### 3.2 动态向量挂载 (Ephemeral RAG)
- **拒绝硬拼图**：严禁将大文件文本直接 `append` 到 Prompt（导致 OOM 与注意力稀释）。
- **临时空间映射**：将会话附件实时向量化，挂载为内存态向量库 (In-Memory Vector Store)。模型通过 `Knowledge Base Query` 召回，确保回答的信噪比。

## 4. 调度与工具沙箱 (Execution & Toolchain)

### 4.1 思维链显式化 (Transparent CoT)
- **推流分离**：后端流式引擎严格区分 `<thought>` 与 `<content>` 块。
- **前端折叠**：默认收起推理过程（"正在思考..."），释放认知负担，保留技术溯源能力。

### 4.2 意图驱动工具池 (Intent-Driven Tools)
废弃“一刀切”的工具卸载，采用**策略模式 (Strategy Pattern)** 按需装载：
- **网络嗅探 (Web Search)**：DuckDuckGo/Google 搜索。
- **沙箱计算 (Sandbox)**：Python Interpreter 进行数据处理与计算。
- **知识/图谱混合检索 (Hybrid RAG)**：向量与图谱的双路召回。
- **技能与 MCP (Skills & MCP)**：接入企业级外部 API。

## 5. 渲染与展现范式 (Render Paradigm)

### 5.1 响应式流管道 (Reactive SSE)
采用 Server-Sent Events (SSE) 推送标准化的 Event Schema，确保前端渲染的 60fps 丝滑度。

### 5.2 结构化组件库 (Componentized Markdown)
基于 AST 抽象语法树拦截 Markdown 渲染，实现卡片化降维：
- **精准引用 (Citations)**：文内 `[1]` 必须关联具体的文件块物理坐标。
- **富媒体沙箱**：LaTeX 公式解析、Mermaid.js 图表实时重绘、代码高亮+一键复制。
- **实体卡片化**：将冰冷的 URL、文件链接、知识库索引转换为高信息密度的交互式卡片（Link Cards, File Cards）。

## 6. 交互 UI 规范 (UI/UX Moat)

**视觉减法，信息提纯**
- **顶部链路**：可折叠的 `Thought process` 状态机。
- **腰部徽章**：`Used tool` 胶囊（仅展示核心网络/绘图工具的微缩状态）。
- **核心视界**：沉浸式的富文本排版流（无 Diff 视觉噪音）。
- **底盘支撑**：References 参考文献网格及快捷操作（复制、重试）。