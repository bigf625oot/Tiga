# Tools RAG 与动态渐进式挂载架构规格说明书 (P10 Standard)

> **Document Context**
> 本文档定义 Tiga Agent 平台中工具链（Tools / MCP / Skills）的演进范式。
> 核心哲学：**工具即知识，按需注入，拒绝全量加载 (Tools as Knowledge, Just-in-Time Injection)**。
> 旨在彻底解决“工具集爆炸”导致的 Token 逃逸、TTFT 延迟飙升及大模型注意力稀释（幻觉）等致命架构问题。

## 1. 架构痛点洞察 (The Bottleneck)
当前的 `loader.py` 采用了最原始的**全量加载策略 (Eager Loading)**：
`tools = await registry.resolve_all_tools()`
这种做法在工具数量超过 10 个时，会暴露出极大的物理限制：
- **Token 击穿**：每个 Tool 的 JSON Schema（含 description, properties）平均占用 150-300 Tokens。50 个工具将耗费 15k Tokens 仅用于预置指令，造成严重的上下文污染。
- **降智效应 (Attention Dilution)**：提供无关工具会导致 LLM 在简单对话中产生“选择困难症”，触发无关的 Tool Call 甚至凭空捏造参数。
- **生态隔离**：无法支持海量的开放 MCP 插件市场，因为受限于窗口物理边界。

## 2. 第一性原理设计 (First Principles: Tools RAG)
将工具（Tools）降维等同于知识库中的文档（Documents）。我们不应在 Agent 初始化时“硬塞”工具，而是应该在 NLU 阶段，基于用户的意图和语境，进行 **Top-K 语义召回**。

### 2.1 架构核心：双路意图路由 (Dual-Track Routing)
在接收到用户请求时，`NluService` 必须执行并发的双路诊断：
- **宏观链路 (Macro Intent)**：判断执行范式（Chat, Task, Workflow）。
- **微观链路 (Micro Tools Retrieval)**：拿着 User Query，去 `Tools Index` 中检索匹配度最高的 K 个工具（Tools RAG）。

### 2.2 渐进式沙箱 (Progressive Sandbox)
- **Zero-Trust 启动**：Agent 实例创建时，`agent.tools` 默认为空或只保留最基础的 `search_available_tools`（元工具）。
- **JIT (Just-in-Time) 注入**：仅将 NLU 检索到的高度相关的工具（如 `yahoo_finance`）注入本次会话。
- **元认知自愈 (Meta-Cognition)**：如果 Agent 发现提供的工具不足以解决问题，它可以主动调用 `search_available_tools` 探查并请求挂载新工具。

## 3. 核心模块与改造协议 (Module Contracts)

### 3.1 ToolRetriever (工具检索器)
职责：维护全局可用工具的元数据索引，并提供高并发的语义召回能力。
- **预热机制**：系统启动时，遍历 `registry.py` 中所有的 Toolkit，提取 `__doc__` 和参数 Schema，构建倒排索引或轻量级内存向量树（如基于 TF-IDF / BM25 的快速启发式召回，以保证零延迟）。
- **查询接口**：`await tool_retriever.retrieve(query: str, top_k: int = 3) -> List[str]`。

### 3.2 NLU 升级契约
扩展 `IntentResult` 数据结构，加入 `suggested_tools` 字段。
```python
class IntentResult(BaseModel):
    intent: str
    paradigm: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    suggested_tools: List[str] = Field(default_factory=list)  # 新增：NLU 推荐装载的工具名单
```

### 3.3 Builder & Loader 剥离解耦
废弃 `resolve_all_tools()`，重写为 `resolve_tools_by_names(names: List[str])`。
在 `builder.py` 的装配阶段，仅装载 `IntentResult.suggested_tools` 中命中的工具实例。

## 4. 防御性降级策略 (Graceful Degradation)
- **冷启动回退**：如果 ToolRetriever 未命中任何高置信度工具，且用户意图为 `chat`，则严格保持零工具。
- **兜底工具池**：针对特定的范式（如 `agentic`），如果 NLU 识别失败，退退到一组极简的核心工具子集（如 `web_search` 和 `python_sandbox`），坚决拒绝全量兜底。