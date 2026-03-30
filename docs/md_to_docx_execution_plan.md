# P10 级架构演进：Markdown 转 DOCX 实施方案与详细计划

基于我们之前确定的“抛弃沙箱，引入零拷贝 Rust/WASM 引擎”的架构演进范式，考虑到系统的复杂性和对现有生产环境的稳定性要求，我们不能一蹴而就。必须遵循**渐进式演进、平滑灰度、第一性原理**的原则。

本实施方案将庞大的架构重构拆解为可验证、可回滚的 4 个 Phase（阶段）。

---

## 总体演进策略 (Evolution Strategy)

1. **解耦优先**：先剥离 LLM 对工具的直接依赖，引入状态机概念。
2. **双写与灰度 (Shadow Traffic)**：新旧渲染引擎并行运行一段时间，只校验结果，不阻断主链路。
3. **基础设施下沉**：逐步将计算密集型任务从 Python/Node.js 沙箱下沉到 Rust/WASM 扩展中。

---

## 阶段一：大模型意图保留与 Tool Call 混合编排优化 (Phase 1: Hybrid Tool Execution)

**目标**：保留大模型作为统一的意图识别与推理入口。在工具执行层引入**策略模式 (Strategy Pattern)**，实现“文件转换本地化”与“普通代码沙箱化”的双轨并行。坚决避免一刀切，确保其他需要沙箱的场景（如数据分析、代码运行）不受影响。

*   **Step 1.1: 重构 LLM Tool Schema (多态工具定义)**
    *   **动作**：为大模型注册两种不同性质的工具：
        1.  `convert_markdown_to_docx`: 明确声明这是一个**纯数据转换工具**，大模型只需传入源文件参数（或 Markdown 内容）。
        2.  `run_python_code`: 保持原样，用于需要真实执行计算和分析的通用沙箱任务。
*   **Step 1.2: Tool Executor 层的动态路由拦截 (Dynamic Interception)**
    *   **动作**：在后端的 `Tool Executor` (工具调度层) 引入策略工厂。
    *   **替换逻辑**：
        *   当拦截到 `convert_markdown_to_docx` 时，**阻断沙箱链路**，路由至本地纯函数微服务（临时使用本地 pandoc 或 docx-js）进行零冷启动的格式转换。
        *   当拦截到 `run_python_code` (或其它沙箱工具) 时，**放行**，继续沿用现有的 Sandbox Manager 链路分配容器执行。
*   **验证标准**：Quick 模式下，文档转换请求不再唤起沙箱；而数据分析或绘图请求依然能够正常通过沙箱执行代码。

## 阶段二：Solo 模式状态机深度解耦 (Phase 2: State Machine Decoupling)

**目标**：在 Solo 模式下，剥离大模型生成“执行沙箱脚本”的逻辑，改为只输出纯文本。

*   **Step 2.1: 调整 LLM Prompt 与工具清单**
    *   **动作**：移除传给 LLM 的 `docx-js` 或 `pandoc` 工具声明。
    *   **系统指令约束**：强制 LLM 仅输出标准 Markdown 格式的最终答案，不允许生成任何代码来执行转换。
*   **Step 2.2: 引入状态机编排引擎 (Chat Controller 改造)**
    *   **动作**：在 `Chat Controller` 中引入状态机（如 `Transitions` 库或简单的状态枚举）。
    *   **状态定义**：`REASONING` -> `GENERATE_CONTENT` -> `RENDER_DOCX` -> `RESPONSE_ASSEMBLING`。
    *   **流转逻辑**：当流转到 `RENDER_DOCX` 时，后端代码显式捕获 Markdown 字符串。
*   **验证标准**：Solo 模式的执行计划中不再出现代码执行节点，而是纯逻辑推导后直接跟一个后处理步骤。

## 阶段三：渲染引擎过渡与新基建 (Phase 3: Renderer Engine Transition)

**目标**：平滑替换沙箱，先用本地纯函数代替沙箱，再引入高性能 Rust 引擎。

*   **Step 3.1: 剥离沙箱冷启动 (Local Python/Node Engine)**
    *   **动作**：作为中间态，在 Backend 服务器本地直接运行一个无沙箱的纯函数转换服务（如本地直接调 `pandoc` 或一个内部微服务）。这消除了沙箱的冷启动和网络 I/O 损耗。
*   **Step 3.2: 研发 Rust/WASM 零拷贝引擎 (核心护城河)**
    *   **动作**：新建一个独立的工程模块，使用 Rust 编写 `markdown-to-docx` 转换器。
    *   **技术栈**：使用 `pulldown-cmark` 解析 AST，使用 `docx-rs` 生成 DOCX 结构。暴露 C API 或 WASM 接口给 Python/Node 后端。
    *   **内存优化**：确保传入的字节流直接在内存竞技场中被解析，不发生多余的字符串拷贝。
*   **Step 3.3: 影子测试 (Shadow Testing)**
    *   **动作**：在生产环境，同时调用本地引擎和新的 Rust 引擎，只返回本地引擎的结果，但在后台比对 Rust 引擎生成的 DOCX 的哈希值和性能指标。
*   **验证标准**：Rust 引擎在影子测试中表现出 100% 的准确率，且转换延迟降低至毫秒级（< 50ms）。

## 阶段四：全量切流与架构固化 (Phase 4: Full Cutover)

**目标**：彻底下线旧版基于沙箱的格式转换链路。

*   **Step 4.1: 网关直连渲染引擎 (Zero-Copy I/O)**
    *   **动作**：在 Quick 模式命中后，API 网关直接将请求的 Body Stream 传递给 Rust 引擎的内存指针。
*   **Step 4.2: 清理技术债 (Technical Debt Cleanup)**
    *   **动作**：删除原有的沙箱上传/下载逻辑、删除旧版的 LLM 工具定义。
*   **Step 4.3: 性能基准测试定档 (Benchmarking)**
    *   **动作**：压测新架构在极端高并发下的表现，验证 CPU 缓存行对齐和零拷贝带来的吞吐量提升。

---

## 执行计划时间表建议

| 阶段 | 核心任务 | 预期收益 | 风险点 |
| :--- | :--- | :--- | :--- |
| **Phase 1** | 优化 Tool Schema 与本地拦截 | 沙箱冷启动次数降为 0 | LLM 依然有幻觉生成脚本的可能 |
| **Phase 2** | Solo 模式状态机 | 消除工具调用幻觉，提升稳定性 | 破坏现有复杂 Task 的上下文连贯性 |
| **Phase 3** | Rust 引擎研发与双写 | 为零拷贝基建打基础 | Rust 与 Python/Node 的 FFI 内存泄漏 |
| **Phase 4** | 全量切流与清理 | 彻底消灭沙箱 I/O，延迟降至毫秒 | 极端并发下的底层 Panic |

**下一步行动建议：**
既然我们决定保留大模型的意图识别，我建议我们**首先执行 Phase 1 (Step 1.1 和 1.2)**。
这不需要改动网关，只需要我们：
1. 更新注册给大模型的 `docx` 技能的 Prompt / Schema。
2. 在 `Chat Controller` (或对应的工具分发层) 拦截这个特定的 Tool Call，将其重定向到本地的转换函数，而不是发给沙箱。