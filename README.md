# Tiga

**Tiga**（Taichi Agent）是一个企业级 AI 智能体（Agent）管理与编排平台，帮助开发者和企业快速构建基于 LLM 的智能应用。后端采用 **Agno** 框架，集成 **LightRAG** 知识图谱检索、**Vanna** Text-to-SQL 以及 **MCP (Model Context Protocol)**，提供从非结构化文档问答到结构化数据分析的全栈能力。

---

## 项目结构

```
Tiga/
├── backend/          # 后端服务 (FastAPI + Agno)
├── frontend/         # 前端应用 (Vue 3 + Vite + Element Plus)
├── docker-compose.yml # Redis 等基础设施
├── LICENSE
└── README.md
```

---

## 核心特性

| 模块 | 说明 |
|------|------|
| **智能体编排** | 基于 Agno，支持 OpenAI、DeepSeek 等；可视化配置角色、系统提示词与工具；MCP 协议支持 |
| **混合 RAG** | LightRAG 图谱检索；BM25 + 向量 + 图谱三路召回；LanceDB/Qdrant/Milvus、NetworkX/Neo4j |
| **数据智能** | Vanna Text-to-SQL；数据源与指标管理；自动图表生成 |
| **自动化扩展** | N8N 工作流、用户脚本、Agno Workflow 任务编排；S3/OSS 存储 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12+、FastAPI、Agno、LightRAG、Vanna、SQLAlchemy、Redis |
| **前端** | Vue 3、Vite、Element Plus、TailwindCSS、Pinia、ECharts、Vue Flow |
| **向量/图** | LanceDB（默认）、Qdrant、Milvus；NetworkX、Neo4j |
| **存储** | 本地 FS、AWS S3、阿里云 OSS |

---

## 快速开始

### 1. 基础设施（可选）

项目默认使用 SQLite + 本地存储；若需 Redis（任务队列、缓存等）：

```bash
docker-compose up -d
# Redis: localhost:6379
```

### 2. 后端

```bash
cd backend

# 虚拟环境 (Windows PowerShell)
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
# 或: make install

# 配置环境变量（复制并编辑 .env，填入 OPENAI_API_KEY 等）
# cp .env.example .env

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# 或: make run
```

API 文档：`http://localhost:8000/docs`

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

### 4. 可选 Docker 服务

```bash
# Neo4j（图数据库）
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5

# Qdrant（向量库）
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

---

## 后端架构概要

- **API**（`app/api`）：路由与请求/响应，无业务与 DB 直接操作  
- **Service**（`app/services`）：Agent、RAG、存储、LLM、数据、媒体、OpenClaw 等业务逻辑  
- **CRUD**（`app/crud`）：数据库 CRUD 封装  
- **Core**（`app/core`）：配置、日志、异常、安全  

主要 API 模块：`/agent`、`/chat`、`/knowledge`、`/rag`、`/workflows`、`/data-sources`、`/mcp`、`/openclaw`、`/health` 等。

---

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

---

## 环境与配置

- 后端配置见 `backend/app/core/config.py`，支持 `.env`（可放在项目根或 `backend/`）。
- 重要变量示例：`OPENAI_API_KEY`、`USE_SQLITE`、`REDIS_HOST`、`STORAGE_TYPE`、`OPENCLAW_*`、`DEEPSEEK_API_KEY` 等。
- Windows 上安装 `lancedb`、`numpy` 等可能需要 **Visual C++ Build Tools**。

---

## 许可证

MIT License（见 [LICENSE](LICENSE)）。

---

## 更多说明

- 后端详细说明、RAG/存储/OpenClaw 等见 [backend/README.md](backend/README.md)。
