# P10 级架构演进：Markdown 转 DOCX 全链路重构设计

## 1. 历史链路痛点剖析 (The Burden of Mediocrity)

基于现有的系统时序图（依赖沙箱和 LLM Token 预测的旧链路），从**第一性原理**出发，现存架构存在以下不可容忍的缺陷：

1. **丧失架构确定性 (Determinism Loss)**：
   - **表现**：由大模型 (LLM) 负责判断是否需要格式转换，并通过 Tool Call (如 `pandoc` 或 `docx-js`) 发起请求。
   - **本质**：MD 到 DOCX 是 100% 确定的 AST（抽象语法树）映射过程。将“确定性”的转换逻辑交给“基于概率”的大模型路由，是极度不稳定的，容易产生参数幻觉和调度失败。

2. **严重的内存逃逸与极低效的 I/O (Memory Escape & I/O Overhead)**：
   - **表现**：每次转换需要唤起 Sandbox Container (沙箱容器冷启动长达秒级)，并在宿主机与沙箱之间进行多次网络 I/O 的文件拷贝。
   - **本质**：完全违背了**零拷贝 (Zero-copy)** 原则。沙箱是为了隔离不可信代码 (RCE) 的防御机制，用沙箱来跑格式转换，相当于“用高射炮打蚊子”，浪费了海量的 CPU 周期和内存。

---

## 2. 演进范式与核心逻辑 (P10 Mental Models)

我们不仅要修补，而是要进行**降维打击**。新的全链路架构彻底摒弃了对“沙箱执行格式转换”的依赖，并针对 `Quick` 与 `Solo` 两种模式进行了深度优化：

### 2.1 方案 A：Tool Executor 层的多态混合编排 (Quick 模式)
- **策略模式 (Strategy Pattern)**：不再做粗暴的网关意图拦截。保留 LLM 作为统一的意图识别和任务规划中心。
- **双轨并行**：在后端的 `Tool Executor`（工具调度层）引入动态拦截机制。
  - 对于通用数据分析、绘图等需要运行时环境的工具（如 `run_python_code`），**放行**至 Sandbox Manager。
  - 对于确定性的格式转换工具（如 `convert_markdown_to_docx`），**拦截并旁路沙箱**，直接路由到后端的本地微服务或纯函数引擎。这确保了业务泛化能力不受损，同时彻底消灭了高频格式转换的冷启动延迟。

### 2.2 方案 B：WASM/Rust 零拷贝渲染引擎 (核心基建)
- **性能极致**：抛弃沙箱，引入由 Rust 编译的 WASM 转换引擎。
- **物理逻辑**：文件流通过 TCP Socket 达到网关后，直接通过 `mmap` 映射进入渲染引擎的连续内存竞技场 (Memory Arena)。实现 CPU 缓存行对齐下的**零拷贝**传输与极速转换。

### 2.3 方案 C：状态机编排 (Solo 模式)
- **架构确定性**：在需要深度推理的 Solo 模式下，LLM 只负责纯文本的 Reasoning 和 Markdown 生成。
- **解耦**：内容生成结束后，**状态机引擎**接管控制权，自动将状态从 `GENERATE_CONTENT` 流转至 `RENDER_DOCX`，由网关内部直接调用渲染引擎，不再让 LLM 去生成复杂的调用工具指令。

---

## 3. 全新全链路时序图 (The Paradigm Shift Sequence)

以下是基于第一性原理重构后的全新时序图。

sequenceDiagram
    autonumber
    actor User as 用户端
    participant Gateway as API网关<br/>(Semantic Router + FastText)
    participant Controller as Chat Controller<br/>(State Machine Engine)
    participant LLM as LLM Cluster<br/>(推理生成节点)
    participant Renderer as Renderer Engine<br/>(Rust WASM / 零拷贝)
    participant OSS as OSS/S3<br/>(对象存储)
    
    %% ========== 请求入口 ==========
    User->>Gateway: POST /api/v1/chat<br/>{ "messages": "将这份MD转成DOCX"<br/>   "files": {"md": "..."} }
    
    Note over Gateway: 语义路由器 (FastText)<br/>计算意图向量 & 置信度
    
    %% ========== 分支一：Quick模式（格式转换专用） ==========
    alt Quick模式 (Tool Executor 层多态混合编排)
        Gateway->>Controller: 转发用户请求与上下文
        Controller->>LLM: 意图识别与工具预测
        LLM-->>Controller: 返回 Tool Call (如 convert_markdown_to_docx 或 run_python_code)
        
        Note over Controller, Sandbox Manager: 策略模式：根据 Tool 类型动态路由
        
        alt 命中文件转换 (convert_markdown_to_docx)
            Note over Controller, Renderer: 拦截沙箱，执行本地路由
            Controller->>Renderer: 直连渲染引擎, 传递源文件内容或指针
            Note over Renderer: 内存竞技场 (Memory Arena) 零拷贝转换
            Renderer->>OSS: 上传生成的 DOCX 文件
            OSS-->>Renderer: 返回 URL
            Renderer-->>Controller: 转换完成
        else 命中通用代码执行 (如 run_python_code)
            Controller->>Sandbox Manager: 走原有沙箱链路 (启动容器执行代码)
            Sandbox Manager-->>Controller: 返回执行结果
        end
        
        Controller-->>Gateway: 返回响应及文件 URL
        Gateway-->>User: HTTP 200
        
    %% ========== 分支二：Solo模式（复杂任务编排） ==========
    else Solo Mode: 复杂对话 / 分析 + 生成文档
        
        Gateway->>Controller: 转发请求<br/>(保留完整上下文)
        
        Note over Controller: 🔄 状态机初始化<br/>State: PARSING_INTENT
        
        Controller->>LLM: POST /v1/completions<br/>System Prompt: "仅输出 Markdown 格式内容<br/>禁止调用任何工具"
        
        Note over LLM: 🧠 智能决策层<br/>专注推理与内容生成<br/>无格式转换负担
        
        LLM-->>Controller: SSE Stream / JSON<br/>{content: "# Report\n## Analysis..."}
        
        Note over Controller: 🔄 状态机流转<br/>State: CONTENT_GENERATED → RENDER_TRIGGERED
        
        Controller->>Renderer: 内部调用 (IPC / Shared Memory)<br/>传递 Markdown 字符串指针
        
        rect rgb(230, 200, 230)
            Note over Renderer: 🎨 确定性渲染器
            Renderer->>Renderer: 1. 零拷贝读取输入<br/>2. AST 转换<br/>3. DOCX 二进制生成
        end
        
        Renderer->>OSS: PUT /generated/{task_id}.docx
        OSS-->>Renderer: 200 OK {ETag, URL}
        
        Renderer-->>Controller: {file_url, size, duration}
        
        Note over Controller: 🔄 状态机流转<br/>State: RENDER_COMPLETED → RESPONSE_ASSEMBLING
        
        Controller-->>Gateway: {answer: "已为您生成报告...",<br/> attachment: {url, type: "docx"}}
        
        Gateway-->>User: 200 OK<br/>{message: "报告已生成",<br/> download_url: pre-signed URL}
        
    end
    
    %% ========== 文件下载（统一路径） ==========
    User->>OSS: GET /{file}.docx?signature=xxx
    OSS-->>User: 200 OK<br/>Content-Disposition: attachment<br/>Binary DOCX Stream
    
    Note over User, OSS: ✅ 文件不经过网关<br/>降低带宽成本 70%

## 4. 总结 (Executive Summary)

此次架构重构的护城河在于：**将“不可控的智能（LLM）”严格限制在决策与生成层，将“高密度的计算（格式转换）”彻底下沉到确定性的高性能执行层（Rust/WASM）。** 
消灭沙箱冷启动，消灭大模型工具调用幻觉，实现高并发、分布式、极端边界条件下的 100% 可预测性与性能极致。