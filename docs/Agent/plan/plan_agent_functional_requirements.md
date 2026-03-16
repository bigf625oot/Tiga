# Plan Agent (Solo 模式) 功能需求说明书

## 1. 项目概述 (Project Overview)
本文档旨在定义 "Plan Agent" (Solo 模式) 的功能需求。该 Agent 旨在通过自动化的任务分解、推理链条展示、动态规划调整以及丰富的工具集成，为用户提供一个透明、可控且高效的智能任务执行环境。系统采用 "Chat + Workspace" 的左右分屏布局，强调执行过程的可视化与最终产物的即时预览。

## 2. 系统架构 (System Architecture)
系统主要由三层构成：
1.  **任务规划层 (Backend - Agno Logic)**: 负责任务的理解、分解、推理与动态调整。
2.  **工具执行层 (Tools Integration)**: 负责具体动作的执行（搜索、代码运行、RAG、MCP、Skills 等）并返回结构化数据。
3.  **前端展示层 (Frontend - UI/UX)**: 负责用户交互、状态展示及产物渲染，采用 Chat (左) + Workspace (右) 布局。

## 3. 详细功能需求 (Detailed Functional Requirements)

### 3.1 任务规划层 (Task Planning Layer)
基于 Agno 框架 (reasoning=True 模式) 实现核心逻辑。

*   **FR-01 任务分解 (Task Decomposition)**
    *   接收用户原始指令，自动生成包含多个步骤的执行计划 (List of Steps)。
    *   每个步骤需包含：标题 (title)、描述 (description)、状态 (status: pending/running/completed)。
*   **FR-02 推理链条 (Chain of Thought)**
    *   实时捕获并输出 LLM 的推理内容 (reasoning 字段)。
    *   在执行每个动作前，必须明确输出“为什么要这么做”的解释。
*   **FR-03 动态规划调整 (Dynamic Planning)**
    *   具备根据工具执行结果（如搜索失败、数据不足）实时修正剩余步骤的能力。
*   **FR-04 长时记忆与上下文 (Context & Memory)**
    *   Agent 必须能够访问和引用历史步骤的执行结果（例如：步骤 5 可以直接使用步骤 1 的搜索结果）。

### 3.2 工具执行层 (Tools Integration)
所有外部调用需转换为结构化数据流向前端。

*   **FR-05 联网搜索 (Web Search)**
    *   集成 DuckDuckGo 或 Tavily 等搜索引擎。
    *   返回数据需包含：搜索关键词、来源 URL 列表、网页摘要。
*   **FR-06 代码执行器 (Python REPL)**
    *   支持 Python/Node.js 代码即时运行。
    *   返回数据需包含：源代码、标准输出 (Stdout/Stderr)、生成的图表 (Matplotlib/Plotly)。
*   **FR-07 知识库检索 (RAG)**
    *   支持对本地或云端文档的检索。
    *   返回数据需包含：检索到的文档片段、置信度分数、来源文档名称。
*   **FR-08 文件生成与处理 (File Generation)**
    *   **扩展支持**：不仅支持文档 (Excel, PDF, CSV, Word)，还需支持 **代码文件** (Python, JS, etc.)、**图片** (PNG, SVG) 及 **视频** (MP4) 的生成。
    *   提供文件下载链接或在线预览接口。
*   **FR-09 模型上下文协议 (MCP Integration)**
    *   支持通过 MCP (Model Context Protocol) 协议连接外部工具和服务。
    *   允许动态加载和卸载 MCP 服务器，扩展 Agent 能力边界。
*   **FR-10 技能扩展 (Skills Integration)**
    *   支持加载自定义 Skills（预定义工具集合）。
    *   允许用户通过配置启用特定领域的 Skill（如数据分析、图像处理等）。

### 3.3 前端展示层 (Frontend Presentation Layer)
采用左右分屏布局，增强用户对执行过程的感知与控制。

#### 3.3.1 左侧：交互流 (Chat Panel)
*   **FR-11 流式对话**
    *   展示 Agent 最终汇总的自然语言回复。
*   **FR-12 状态气泡**
    *   在对话流中穿插简略的状态提示（如：“已完成搜索” -> “正在分析数据” -> “正在生成文件”）。

#### 3.3.2 右侧：工作区 (Execution Dashboard)
核心交互区域，需支持卡片式或时间轴布局。

*   **FR-13 [Tab 1] 任务看板 (Plan)**
    *   显示当前执行进度（例如：1/5 步）。
    *   状态可视化：已完成步骤打勾，进行中步骤高亮/旋转动画。
*   **FR-14 [Tab 2] 实时日志 (Internal Process)**
    *   **思考折叠区**: 显示 reasoning 推理内容（默认折叠或灰色倾斜字体）。
    *   **工具调用轨迹**:
        *   搜索卡片：点击可查看参考链接详情。
        *   知识库卡片：显示引用的具体文本片段。
        *   MCP/Skills 卡片：显示工具名称及执行结果摘要。
*   **FR-15 [Tab 3] 最终产物 (Artifacts)**
    *   **代码区**: 提供语法高亮的编辑器视图，支持用户修改代码并点击“重新运行”。
    *   **预览区**:
        *   Markdown/HTML: 直接渲染。
        *   表格 (CSV/Excel): 渲染为类 Excel 的表格视图。
        *   图表/图片: 实时展示 Matplotlib/Plotly 图片或生成的 PNG/SVG。
        *   视频: 提供视频播放器预览生成的内容。
        *   文件: 显示下载按钮 (Word/PDF/Code 等)。

### 3.4 沙箱环境 (Sandbox Environment)
构建一个有状态、受限的计算环境。

*   **FR-16 运行控制台 (Console)**
    *   类 VS Code 终端体验，实时流式输出代码运行的标准输出 (Stdout) 和错误 (Stderr)。
*   **FR-17 文件系统管理**
    *   提供 `/workspace` 目录，允许 Agent 读取上传文件及保存生成文件。
    *   **文件树视图**: 右侧展示当前任务产生的所有资产列表 (如 report.docx, data.csv, script.py, image.png)。
*   **FR-18 运行时监控**
    *   监控 CPU/内存占用。
    *   支持强制结束超时任务或死循环任务。
    *   状态指示器：显示“执行中”、“超时”、“内存溢出”等状态。
*   **FR-19 产物提取**
    *   自动识别沙箱内生成的新文件。
    *   将文件转换为 Base64 或生成临时 URL 推送至前端。

## 4. 用户故事 (User Story)

**场景**: 用户希望调研 2024 年低空经济政策并生成 Word 报告。

1.  **输入指令**:
    *   用户输入: “帮我调研 2024 年低空经济的政策并写一份 1000 字报告，存为 Word”。
2.  **规划阶段**:
    *   右侧面板立即弹出 "Task Plan"，显示步骤：
        1.  搜索最新政策
        2.  提取核心要点
        3.  撰写报告内容
        4.  转换 Word
3.  **执行阶段**:
    *   **左侧**: 显示“正在为您搜索相关政策...”。
    *   **右侧 (Live Feed)**: 实时跳出搜索到的 5 个政府官网链接。
    *   **右侧 (Thinking)**: 显示思考过程：“根据搜索到的政策，我发现主要集中在无人机领域，下一步我将重点分析准入标准。”
4.  **代码/文件阶段**:
    *   Agent 编写并执行 Python 脚本生成报告结构。
    *   右侧工作区切换到 "Artifacts" 视图，打字机式实时显示报告正文。
5.  **任务完成**:
    *   **左侧**: 回复“报告已生成”。
    *   **右侧**: 提供 generated_report.docx 的下载链接。
    *   用户可在右侧“代码工作区”修改生成脚本并点击“重新运行”以调整报告内容。

## 5. 技术规格与建议 (Technical Specifications)

### 5.1 协议标准化
定义一套严格的 JSON 流协议，确保前后端通信结构化。
*   每个 chunk 必须包含 `stream_type` 字段，枚举值包括：
    *   `thought`: 思考过程
    *   `tool`: 工具调用数据 (包含 MCP/Skills)
    *   `content`: 最终回复内容
    *   `plan`: 规划步骤更新
    *   `status_update`: 状态变更

### 5.2 并发处理
*   后端 Agent (Agno) 的工具调用可能并行发生。
*   前端右侧面板必须支持多任务卡片的同时展示与更新。

### 5.3 数据持久化
*   必须将 Agent 的推理过程、工具执行结果、生成的产物存入数据库。
*   确保用户刷新页面后，右侧工作区 (Workspace) 的历史记录完整保留，不丢失上下文。

### 5.4 关键技术指标
*   **文件 I/O**: 必须支持。
*   **网络请求**: 支持受限的外网访问（可选，视安全策略而定）。
*   **第三方库**: 支持预装或动态安装常用 Python 库 (pandas, numpy, matplotlib 等)。
*   **实时回传**: 执行结果需毫秒级回传前端。

## 6. 功能映射表 (Implementation Mapping)

| 功能模块 | Agno 参数/方法 | 前端消息类型 (type) | UI 表现形式 |
| :--- | :--- | :--- | :--- |
| **自规划** | `reasoning=True` | `plan_step` | 右侧 StepList 列表增加项 |
| **思考过程** | `chunk.reasoning` | `thought` | 灰色倾斜文字或折叠面板 |
| **网页搜索** | `DuckDuckGo() / Tavily()` | `web_search` | 搜索图标 + 蓝色链接列表 |
| **知识库** | `agent.knowledge` | `kb_retrieval` | 书本图标 + 文档片段 |
| **MCP 工具** | `MCP Tools` | `mcp_tool` | 插件图标 + 工具调用详情 |
| **Skills** | `Agent Skills` | `skill_exec` | 技能图标 + 执行结果 |
| **代码执行** | `PythonTools()` | `code_exec` | 黑色代码块 + 绿色运行结果 |
| **文件生成** | `agent.extra_data` | `file_output` | 文件下载/预览卡片 (支持代码/图/视频) |
| **进度更新** | 轮询 Agent 状态 | `status_update` | 进度条或步骤状态变更 |
