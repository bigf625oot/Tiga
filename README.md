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
*   **多存储支持**: 兼容 AWS S3 及 Aliyun OSS 对象存储。

---

## 🛠️ 技术栈 (Tech Stack)

| 模块 | 技术组件 |
| :--- | :--- |
| **Backend** | **FastAPI**, **Agno**, **LightRAG**, **Vanna**, SQLAlchemy, Celery/APScheduler |
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
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key 和数据库配置

# 4. 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## 🔍 系统自检 (Health Checks)

系统启动时会自动执行 **混合检查 (Mixed Check)**，确保 RAG 组件正常：

1.  **Vector Check**: 验证 LanceDB/Qdrant 读写权限及集合状态。
2.  **Graph Check**: 验证 LightRAG 本地索引或 Neo4j 连通性。
3.  **Model Check**: 发送 Probe Token 验证 LLM/Embedding API Key 有效性。

---
全流程服务的日志增强，涵盖了 文档解析、分块处理、图谱生成、异步任务 以及 OSS 服务 。

主要修改如下：

1. 文档解析服务 ( backend/app/services/document_parser.py )
   
   - 将所有的 print 语句替换为规范的 logger 调用。
   - 增加了详细的解析日志，包括使用的解析器（PyMuPDF/pdfplumber/OCR等）、解析页数/段落数、以及具体的失败原因。
2. LightRAG 服务 ( backend/app/services/lightrag_service.py )
   
   - 分块 (Chunking) : 在 insert_text 和 insert_text_async 中增加了基于字符数的 分块数量估算日志 ( Estimated chunks: ~N )，让您能直观看到文本被切分的大致规模。
   - 图谱 (Graph) : 在 get_graph_data 中增加了 图谱节点和边数量 的统计日志 ( Graph loaded. Nodes: X, Edges: Y )。
   - 异步插入 : 完善了异步插入流程的日志，清晰记录开始、重试和完成状态。
3. 知识库服务 ( backend/app/services/knowledge_base.py )
   
   - Fallback 图谱提取 : 在 _extract_subgraph 中增加了 LLM 提取图谱的详细日志，包括提取到的 节点和边数量 。
4. 知识库 API ( backend/app/api/endpoints/knowledge.py )
   
   - 异步分块处理 : 在 background_upload_and_index 中增加了大文件分块的汇总日志 ( Chunking result: N parts )。
   - 增量索引 : 在 background_incremental_index 循环中增加了 每一块 (Chunk) 处理进度的详细日志 ( [Async Incremental] Processing chunk i/N ... )。
5. OSS 服务 ( backend/app/services/oss_service.py )
   
   - 增加了文件 上传、下载、删除成功 的 Info 级别日志（此前只有错误日志），确保文件流转全链路可追踪。
## 🤝 贡献
欢迎提交 PR 或 Issue！

## 📄 许可证
MIT License
