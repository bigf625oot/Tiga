# Taichi Agent - 智能体编排与数据智能平台

Taichi Agent 是一个企业级 AI 智能体（Agent）管理与编排平台，旨在帮助开发者和企业快速构建基于 LLM 的智能应用。

本项目采用前沿的 **Agno (原 Phidata)** 框架，融合了 **LightRAG** 知识图谱检索、**Vanna** Text-to-SQL 数据分析以及 **MCP (Model Context Protocol)** 协议，提供从非结构化文档问答到结构化数据分析的全栈解决方案。

---

## ✨ 核心特性 (Core Features)

### 1. 🤖 强大的智能体编排
*   **多模态 Agent**: 基于 **Agno** 框架，支持 OpenAI、DeepSeek 等主流模型。
*   **角色与工具**: 可视化配置 Agent 角色 (Persona)、系统提示词 (System Prompt) 及工具 (Tools)。
*   **MCP 协议支持**: 率先支持 **Model Context Protocol (MCP)**，实现跨应用上下文与工具共享。

### 2. 🧠 增强型混合检索 (Hybrid RAG)
*   **LightRAG 集成**: 内置 **LightRAG (HKU)**，实现基于图谱的高精度检索，有效解决复杂实体关系问答。
*   **混合检索管线**: 结合 **BM25 关键词** + **向量语义** + **知识图谱** 三路召回，并通过 CrossEncoder 重排。
*   **灵活后端**:
    *   **向量库**: 默认 LanceDB (嵌入式)，支持 Qdrant, Milvus (生产环境)。
    *   **图数据库**: 默认 NetworkX (本地)，支持 Neo4j (企业级)。

### 3. 📊 数据智能与 BI (Data Intelligence)
*   **Text-to-SQL**: 集成 **Vanna.ai**，支持自然语言查询 SQL 数据库 (MySQL, PG, SQLite)。
*   **数据源管理**: 统一管理数据库连接、API 数据源。
*   **指标与看板**: 自定义业务指标 (Indicators)，支持自动生成可视化图表。

### 4. 🔄 自动化与扩展
*   **N8N 工作流**: 无缝集成 N8N，支持 Agent 触发复杂业务流程 (Webhook)。
*   **用户脚本 (User Scripts)**: 支持挂载自定义 Python 脚本，灵活扩展 Agent 能力。
*   **Workflow System**: 基于 Agno.Workflow 的原子化任务编排系统，支持静态 DAG 与动态规划模式。
*   **多存储支持**: 兼容 AWS S3 及 Aliyun OSS 对象存储。

---

## 🛠️ 技术栈 (Tech Stack)

### 技术架构
后端基于 **Python 3.12+** 和 **FastAPI** 框架构建，遵循 RESTful 规范。采用了 **Agno** 作为智能体核心框架，集成 **LightRAG** 进行知识检索，并支持 **MCP (Model Context Protocol)** 扩展工具能力。

| 模块 | 技术组件 |
| :--- | :--- |
| **Backend** | **FastAPI**, **Agno Workflow**, **LightRAG**, **Vanna**, SQLAlchemy, Celery/APScheduler |
| **Frontend** | **Vue 3**, **Vite**, **Element Plus**, TailwindCSS, Pinia |
| **Vector DB** | LanceDB (Default), Qdrant, Milvus |
| **Graph DB** | NetworkX (Local), Neo4j |
| **Storage** | Local FS, S3, Aliyun OSS |

---

## 💻 环境配置与启动

为了确保在不同操作系统上顺利运行，请仔细阅读以下环境配置差异：

### 1. Python 虚拟环境

*   **macOS / Linux**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **Windows (PowerShell)**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
    > **注意**: 如遇权限错误，请执行 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`。

### 2. 依赖安装注意事项

*   **Windows 用户**:
    *   安装 `lancedb`, `numpy` 等库通常需要 **Microsoft Visual C++ 14.0+ Build Tools**。
    *   请确保安装了 "Desktop development with C++" 工作负载。
*   **macOS 用户**:
    *   建议安装 `xcode-select --install`。

---

## 🚀 快速开始 (Quick Start)

### 1. 启动后端 (Backend)

```bash
cd backend

# 1. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate # Windows

# 2. 安装依赖
make install  # 或者 pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key 和数据库配置

# 4. 启动服务
make run      # 或者 python -m uvicorn app.main:app --reload
```

### 2. 启动前端 (Frontend)

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```
访问: `http://localhost:5173`

### 3. (可选) Docker 服务依赖
如果使用高级组件 (Qdrant, Neo4j)，请使用 Docker 启动：

```bash
# Neo4j (Graph DB)
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5

# Qdrant (Vector DB)
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

---

## 🏗️ 架构重构 (Refactoring)

项目已进行全面的架构重构，遵循 **Controller-Service-DAO** 分层原则：

*   **API Layer (`app/api`)**: 仅负责路由分发和请求响应，不包含业务逻辑和数据库操作。
*   **Service Layer (`app/services`)**: 封装核心业务逻辑（如 Agent 编排、RAG 检索）。
*   **DAO Layer (`app/crud`)**: 统一封装数据库 CRUD 操作，隔离底层 SQL 细节。
*   **Core Layer (`app/core`)**: 统一的日志 (`logger`)、异常处理 (`exceptions`) 和配置管理。

### 开发命令 (Development)

本项目提供 `Makefile` 简化常用开发任务：

```bash
make install   # 安装依赖
make run       # 启动开发服务器
make lint      # 代码风格检查 (Ruff)
make format    # 代码自动格式化
make test      # 运行单元测试
make clean     # 清理缓存文件
```

---

## 🤝 贡献
欢迎提交 PR 或 Issue！

## 📄 许可证
MIT License


现在的 app/services/ 结构清晰，按业务领域划分：

- agent/ : 智能体相关服务
  - manager.py : 统一的 AgentManager 。
  - qa.py : 问答智能体服务 ( QAAgentService )。
  - search/ : 搜索与新闻服务 ( NewsQueryExecutor )。
  - tools/ : 工具运行器 ( run_reasoning_tool_loop ) 和具体工具 ( duckduckgo )。
- rag/ : RAG（检索增强生成）核心模块
  - engines/lightrag.py : 封装 LightRAG 引擎 ( LightRAGEngine )，处理底层向量/图谱操作。
  - knowledge_base.py : 知识库管理服务 ( KnowledgeBaseService )。
  - qa.py : RAG 问答服务 ( QAService )。
  - service.py : 对外统一 RAG API 服务 ( RagService )。
  - providers.py , models.py , parser.py , graph.py , context.py : 辅助组件。
- storage/ : 统一存储层
  - 策略模式 : 定义了 StorageProvider 抽象基类。
  - 实现 : LocalProvider , AliyunOSSProvider , S3Provider 。
  - Facade : StorageService ( service.py ) 统一对外提供接口，自动根据配置切换实现。
- llm/ : 模型工厂
  - factory.py : ModelFactory 统一管理 LLM 和 Embedding 模型的创建与配置。
- data/ : 数据处理与分析
  - extraction.py : 数据提取服务（原 metrics_tool ），包含 Prompt 生成与 LLM 提取逻辑。
  - vanna/ : SQL 生成与数据查询服务（原 vanna 模块）。
- media/ : 多媒体服务
  - asr.py : 语音转文字服务（原 aliyun_asr_service ）。
  - `TaskParsingError` 异常处理：
    OpenClaw 的任务解析模块现在更加严格。如果遇到 `TaskParsingError`，调用方可以检查 `retry_count` 和 `validation_error` 来决定是提示用户修改输入还是降级处理（例如使用默认参数）。
    ```python
    try:
        task_data = await parse_task_intent(prompt, db)
    except TaskParsingError as e:
        logger.error(f"Failed to parse task: {e.validation_error}")
        # 降级策略或返回用户友好错误
    ```

- metrics/ : 系统监控
  - service.py : 系统指标记录服务。
- utils/ : 通用工具
  - markdown.py : Markdown 处理工具。