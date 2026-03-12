# Tiga

**Tiga**（Taichi Agent）是一个企业级 AI 智能体（Agent）管理与编排平台，帮助开发者和企业快速构建基于 LLM 的智能应用。后端采用 **Agno** 框架，集成 **LightRAG** 知识图谱检索、**Vanna** Text-to-SQL、**Pathway** 实时数据流处理以及 **OpenClaw** 分布式任务节点，全面支持 **MCP (Model Context Protocol)**。

前端采用 **Vue 3** + **Shadcn/UI** + **Element Plus** 的现代化架构，提供从非结构化文档问答、结构化数据分析到知识图谱修复的全栈能力。

---

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

---

## 核心特性

| 模块 | 说明 |
|------|------|
| **智能体编排** | 基于 Agno，支持 OpenAI、DeepSeek 等；可视化配置角色、系统提示词与工具；内置 Planner 与 Control Plane |
| **混合 RAG** | 集成 LightRAG、GraphitiRAG；支持 BM25 + 向量 + 图谱三路召回；知识图谱可视化与交互 |
| **图谱治理** | **Relation Fix**：可视化的知识图谱关系检测与修复工具，支持实体属性编辑、关系增删改、操作回滚 |
| **数据智能** | Vanna Text-to-SQL；Smart Data Query；自动图表生成与指标管理 |
| **实时流处理** | **Pathway** 引擎集成，支持实时数据连接、清洗、结构化与 AI 算子编排 |
| **分布式执行** | **OpenClaw**：分布式任务节点管理，支持负载均衡、心跳监测与任务分发 |
| **安全沙箱** | 集成 E2B 与 Codebox，支持安全执行 Python/Node.js 代码与文件操作 |
| **MCP 支持** | 全面支持 Model Context Protocol，可作为 MCP Client 连接多种 MCP Server |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12+、FastAPI、Agno、LightRAG、Vanna、Pathway、SQLAlchemy、Redis |
| **前端** | Vue 3、Vite、**Shadcn/UI** (Radix Vue + TailwindCSS)、Element Plus、Vue Flow、ECharts、3d-force-graph |
| **向量/图** | LanceDB（默认）、Qdrant、Milvus；NetworkX、Neo4j |
| **存储** | 本地 FS、AWS S3、阿里云 OSS |
| **沙箱** | E2B、Codebox |

---

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

---

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

---

## 许可证

MIT License（见 [LICENSE](LICENSE)）。
