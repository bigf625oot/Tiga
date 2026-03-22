# Tiga

**Tiga**（Taichi Agent）是一个企业级 AI 智能体（Agent）管理与编排平台，帮助开发者和企业快速构建基于 LLM 的智能应用。后端采用 **Agno** 框架，集成 **LightRAG** 知识图谱检索、**Vanna** Text-to-SQL、**Pathway** 实时数据流处理以及 **OpenClaw** 分布式任务节点，全面支持 **MCP (Model Context Protocol)**。

前端采用 **Vue 3** + **Shadcn/UI** + **Element Plus** 的现代化架构，提供从非结构化文档问答、结构化数据分析到知识图谱修复的全栈能力。

***

## 项目结构

```
Tiga/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由 (Agent, Chat, RAG, MCP, OpenClaw 等)
│   │   ├── core/         # 核心配置与工具
│   │   ├── services/     # 业务逻辑服务
│   │   │   ├── agent/    # 智能体核心 (Planner, Skills, Tools)
│   │   │   ├── graph/    # 图谱关系修复与管理
│   │   │   ├── openclaw/ # 分布式任务节点与网关
│   │   │   ├── pathway/  # 实时数据流 ETL 引擎
│   │   │   ├── rag/      # RAG 引擎 (LightRAG, GraphitiRAG)
│   │   │   └── sandbox/  # 代码沙箱 (E2B, Codebox)
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/ui/ # Shadcn/UI 组件库
│   │   ├── features/      # 功能模块
│   │   │   ├── agent/     # 智能体管理
│   │   │   ├── analytics/ # 数据指标分析
│   │   │   ├── data_etl/  # ETL 数据流看板
│   │   │   ├── etl_editor/# 可视化 ETL 编排
│   │   │   ├── knowledge/ # 知识库管理
│   │   │   ├── qa/        # 智能问答
│   │   │   ├── relation_fix/ # 知识图谱关系修复
│   │   │   └── sandbox/   # 沙箱终端与结果查看
│   └── ...
└── ...
```

***

## 核心特性

| 模块         | 说明                                                                       |
| ---------- | ------------------------------------------------------------------------ |
| **智能体编排**  | 基于 Agno，支持 OpenAI、DeepSeek 等；可视化配置角色、系统提示词与工具；内置 Planner 与 Control Plane |
| **混合 RAG** | 集成 LightRAG、GraphitiRAG；支持 BM25 + 向量 + 图谱三路召回；知识图谱可视化与交互                 |
| **图谱治理**   | **Relation Fix**：可视化的知识图谱关系检测与修复工具，支持实体属性编辑、关系增删改、操作回滚                   |
| **数据智能**   | Vanna Text-to-SQL；Smart Data Query；自动图表生成与指标管理                           |
| **实时流处理**  | **Pathway** 引擎集成，支持实时数据连接、清洗、结构化与 AI 算子编排                                |
| **分布式执行**  | **OpenClaw**：分布式任务节点管理，支持负载均衡、心跳监测与任务分发                                  |
| **安全沙箱**   | 集成 E2B 与 Codebox，支持安全执行 Python/Node.js 代码与文件操作                           |
| **MCP 支持** | 全面支持 Model Context Protocol，可作为 MCP Client 连接多种 MCP Server               |
| **用户手册**   | 基于 **VitePress** 构建，遵循 **尼尔森十大交互原则**，采用 **Shadcn/UI** 标准，提供详尽的操作指南与组件参考  |

***

## 核心模块详解

### 1. 🤖 Agent 核心 (Agent Core)
基于前沿的 **Agno (原 Phidata)** 框架构建，支持单体智能体推理与多智能体（Multi-Agent）协同编排。
*   **优势**：
    *   **深度模型兼容**：无缝对接 OpenAI、DeepSeek 等支持 Reasoning（深度推理）能力的大模型。
    *   **多智能体协同**：内置 `TeamHandler`，支持 Leader 统筹、Coder 编写、Writer 总结的角色化协同机制。
    *   **工作流编排**：内置 Planner 组件，支持复杂任务的步骤拆解、状态可视化追踪（交互流与执行工作区双屏协同）。
*   **应用场景**：复杂业务流程自动化、代码生成与自修复、多步推理分析任务。

### 2. 🛠️ 工具系统 (Tool System & MCP)
构建了以 **MCP (Model Context Protocol)** 为核心的动态工具扩展生态。
*   **优势**：
    *   **边界无限扩展**：原生支持 MCP Client，可动态加载/卸载 MCP Servers（如数据库、文件系统、企业内部 API），实现工具的即插即用。
    *   **按需挂载**：支持基于 `MCPToolbox` 细粒度过滤和下发工具，确保大模型上下文不被无关工具污染。
    *   **Skills 体系**：支持预定义自定义技能（Skills Config）进行垂直场景的能力增强。
*   **应用场景**：连接企业私有数据库执行 SQL、跨系统调用第三方 SaaS 接口、自动化运维巡检。

### 3. 📦 安全沙箱运行 (Sandbox Execution)
深度集成 **E2B** 与 **Codebox** 云端代码执行沙箱。
*   **优势**：
    *   **安全隔离**：提供完全隔离的运行环境，支持自定义 CPU、内存、网络等资源限制，防止恶意代码越权。
    *   **多语言支持**：原生支持 Python、Node.js 动态代码片段执行及完整的文件系统读写。
    *   **状态保持**：沙箱实例具备生命周期管理，支持长时运行任务与上下文依赖安装。
*   **应用场景**：通过 Pandas/Numpy 进行结构化数据处理与可视化、自动化测试脚本执行、LLM 编写代码的即时运行验证与纠错。

### 4. 🧠 上下文与记忆 (Context & Memory)
通过 `ContextMemoryConfig` 实现智能体的长短期记忆与状态管理。
*   **优势**：
    *   **状态持久化**：结合 Redis 等存储后端，实现跨会话（Cross-Session）的记忆留存与上下文无缝恢复。
    *   **多维度记忆**：支持系统级全局上下文记忆与用户个性化偏好记忆分离。
    *   **动态管理**：有效管理上下文 Token 长度，支持冗长对话的滑动窗口截断与关键信息提取。
*   **应用场景**：长周期项目跟进助手、具有个性化人设的私人 AI 伴侣、复杂工单流转中的状态继承。

### 5. 📚 知识库 (Knowledge Base & RAG)
基于 **LightRAG** 与 **GraphitiRAG** 构建的企业级混合检索架构。
*   **优势**：
    *   **混合检索管线 (Hybrid RAG)**：融合 BM25（关键词） + Vector（语义向量） + Graph（知识图谱关系）三路召回，解决碎片化信息关联弱的痛点。
    *   **严格防幻觉机制**：注入强制性 Prompt 边界，生成带有 `[n]` 格式的参考来源索引，支持内容级别的精确溯源。
    *   **灵活的基础设施**：默认内置 LanceDB + NetworkX（开箱即用），支持无缝切换至生产级的 Qdrant/Milvus + Neo4j。
*   **应用场景**：超长财报/法务文档解析、复杂实体关系（如企业股权、人物图谱）推理问答、企业内部制度精准查询。

***

## 技术栈

| 层级       | 技术                                                                                              |
| -------- | ----------------------------------------------------------------------------------------------- |
| **后端**   | Python 3.12+、FastAPI、Agno、LightRAG、Vanna、Pathway、SQLAlchemy、Redis                               |
| **前端**   | Vue 3、Vite、**Shadcn/UI** (Radix Vue + TailwindCSS)、Element Plus、Vue Flow、ECharts、3d-force-graph |
| **向量/图** | LanceDB（默认）、Qdrant、Milvus；NetworkX、Neo4j                                                        |
| **存储**   | 本地 FS、AWS S3、阿里云 OSS                                                                            |
| **沙箱**   | E2B、Codebox                                                                                     |

***

## 快速开始

### 1. 基础设施（可选）

项目默认使用 SQLite + 本地存储；若需 Redis（任务队列、缓存等）、Neo4j 或 Qdrant：

```bash
docker-compose up -d
```

### 2. 后端

```bash
cd backend

# 虚拟环境 (Windows PowerShell)
python -m venv venv
.\venv\Scripts\activate

# 虚拟环境 (macOS/Linux)
source venv/bin/activate

# 验证 Python 版本 (需 >= 3.10)
python -V

# 安装依赖
pip install -r requirements.txt
# 或: make install

# 配置环境变量（复制并编辑 .env，填入 OPENAI_API_KEY 等）
# cp .env.example .env

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# 或: make run

# 安装Redis
docker run -d --name tiga-redis -p 6379:6379 redis:alpine
```

API 文档：`http://localhost:8000/docs`

### 3. 前端

```bash
cd frontend
npm install
npm run dev

# 启动用户操作手册（可选）
npm run docs:dev
# 访问：http://localhost:5173/docs/
```

访问应用：`http://localhost:5173`
访问手册：应用侧边栏底部入口或 `http://localhost:5173/docs/`

***

## 后端架构概要

- **API**（`app/api`）：路由与请求/响应，无业务与 DB 直接操作
- **Service**（`app/services`）：
  - **Agent**: 智能体核心逻辑
  - **OpenClaw**: 分布式节点通信与任务调度
  - **Pathway**: 数据流处理管道
  - **RAG**: 知识检索与图谱构建
  - **Sandbox**: 代码执行环境
- **Core**（`app/core`）：配置、日志、异常、安全、Redis 队列
- **CRUD**（`app/crud`）：数据库操作封装

主要 API 模块：`/agent`、`/chat`、`/knowledge`、`/rag`、`/workflows`、`/data-sources`、`/mcp`、`/openclaw`、`/pathway`、`/sandbox` 等。

***

## 开发命令（后端）

```bash
cd backend
make install   # 安装依赖
make run       # 启动开发服务器
make lint      # Ruff 检查
make format    # 格式化
make test      # 运行测试
make clean     # 清理缓存
```

***

## 环境与配置

- 后端配置见 `backend/app/core/config.py`，支持 `.env`（可放在项目根或 `backend/`）。
- 重要变量示例：`OPENAI_API_KEY`、`USE_SQLITE`、`REDIS_HOST`、`STORAGE_TYPE`、`OPENCLAW_*`、`DEEPSEEK_API_KEY` 等。

***

## 许可证

MIT License（见 [LICENSE](LICENSE)）。
