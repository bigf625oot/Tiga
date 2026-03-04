# Taichi Agent - 智能体编排与数据智能平台

Taichi Agent (内部代号: Tiga) 是一个集成了智能体编排、多模态知识库（RAG）、数据智能分析、自动化工作流与全网搜索的现代化全栈平台。本项目采用前后端分离架构，旨在为开发者提供开箱即用的企业级 AI 应用开发框架，支持从简单的对话机器人到复杂的自主智能体任务执行。

---

## 📚 目录

- [🎨 前端工程 (Frontend)](#-前端工程-frontend)
  - [项目简介](#项目简介)
  - [技术栈](#技术栈)
  - [目录结构](#目录结构)
  - [核心功能模块](#核心功能模块)
  - [环境准备与启动](#环境准备与启动)
- [⚙️ 后端服务 (Backend)](#%EF%B8%8F-后端服务-backend)
  - [技术架构](#技术架构)
  - [核心服务](#核心服务)
  - [OpenClaw 集成](#openclaw-集成)
  - [数据库与存储](#数据库与存储)
  - [环境配置与启动](#环境配置与启动)
  - [Task Mode (任务模式)](#task-mode-任务模式)
  - [API 接口](#api-接口)

---

## 🎨 前端工程 (Frontend)

### 项目简介
前端采用 **Vue 3 + Vite + TypeScript** 现代化技术栈构建，集成了 **Element Plus** 和 **Ant Design Vue** 双组件库，提供流畅的交互体验和强大的数据可视化能力（基于 **V-Network-Graph** 和 **3D-Force-Graph**）。

### 技术栈
| 类别 | 技术/库 | 说明 |
| :--- | :--- | :--- |
| **框架** | Vue 3.3+ | 核心 UI 框架 |
| **构建工具** | Vite 4.4+ | 极速开发与构建工具 |
| **语言** | TypeScript 5.x | 静态类型检查 |
| **UI 组件库** | Element Plus / Ant Design Vue | 双 UI 库支持，适配不同业务场景 |
| **样式** | Tailwind CSS 3.3 | 原子化 CSS 框架 |
| **状态管理** | Pinia 2.1 | 响应式状态管理 |
| **可视化** | V-Network-Graph / 3D-Force-Graph | 知识图谱与网络关系可视化 |
| **图表** | Chart.js / Vue-Chartjs | 数据报表与指标展示 |
| **录音** | Recorder-Lib | 浏览器端音频录制与处理 |
| **沙箱** | XTerm.js | Web 终端模拟器 |

### 目录结构
```bash
frontend/
├── public/              # 静态资源 (图标, 录音库等)
├── src/
│   ├── core/            # 核心层 (API 客户端, 全局配置)
│   ├── features/        # 业务功能模块 (按领域划分)
│   │   ├── agent/       # 智能体管理 (服务市场, 技能, 脚本)
│   │   ├── analytics/   # 数据分析 (指标, SQL 查询)
│   │   ├── knowledge/   # 知识库与图谱 (Graph Export)
│   │   ├── qa/          # 智能问答 (Chat)
│   │   ├── recording/   # 录音与多媒体 (ASR)
│   │   ├── relation_fix/# 知识图谱关系修复
│   │   ├── sandbox/     # 代码沙箱与终端管理
│   │   ├── search/      # 全网搜索智能体 (News, Web)
│   │   ├── system/      # 系统设置 (DB, Model)
│   │   └── workflow/    # 工作流编排 (Task Panel, Artifacts)
│   ├── shared/          # 共享资源
│   │   ├── components/  # 通用组件
│   │   └── hooks/       # 组合式函数
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
└── vite.config.js       # Vite 配置
```

### 核心功能模块
- **Search Agent**: 集成 DuckDuckGo 的全网搜索与新闻聚合，支持实时信息检索。
- **Agent Management**: 智能体创建、技能配置 (Skills)、用户脚本 (User Scripts) 与服务市场。
- **Knowledge Base**: 基于 LightRAG 的知识库管理，支持 2D/3D 图谱导出与可视化。
- **Analytics**: 基于 Vanna 的 Text-to-SQL 数据查询与关键指标 (Indicators) 监控。
- **Smart QA**: 基于 RAG 的智能问答系统，支持多模态交互。
- **Workflow**: 可视化工作流编排，支持任务面板、日志审计与产物编辑。
- **Media & ASR**: 浏览器端录音与自动语音转文字功能。
- **Sandbox**: 基于 E2B 的代码执行沙箱，支持 Python/Shell 交互。
- **OpenClaw Dashboard**: 集成 OpenClaw 网关状态监控、任务管理与节点管理面板。

### 环境准备与启动
1.  **安装依赖**:
    ```bash
    cd frontend
    pnpm install  # 或 npm install
    ```
2.  **启动开发服务**:
    ```bash
    npm run dev
    ```
    服务默认运行在 `http://localhost:5173`。

---

## ⚙️ 后端服务 (Backend)

### 技术架构
后端基于 **Python 3.10+** 和 **FastAPI** 框架构建，遵循 RESTful 规范。采用了 **Agno** 作为智能体核心框架，集成 **LightRAG** 进行知识检索，并支持 **MCP (Model Context Protocol)** 扩展工具能力。

### 技术栈与框架版本
- **Web 框架**: FastAPI (>=0.111.0)
- **智能体框架**: Agno (Phidata fork/successor)
- **数据库 ORM**: SQLAlchemy (2.0+) + Alembic
- **AI/LLM**: OpenAI SDK, Vanna (Text-to-SQL)
- **RAG 引擎**: LightRAG, LanceDB (向量库), Neo4j (图数据库支持)
- **工具协议**: MCP (Model Context Protocol)
- **搜索服务**: DuckDuckGo Search (ddgs)
- **沙箱运行时**: E2B (Firecracker VM)
- **分布式监控**: OpenClaw Gateway Integration
- **存储**: Local, AWS S3, Aliyun OSS
- **工具库**: Pandas, NumPy, Pydantic, NetworkX

### 核心服务 (`app/services`)
- **Agent Service**: 智能体管理与执行，支持 Search Agent 和自定义 Tools。
- **MCP Client**: 模型上下文协议客户端，用于连接外部工具与服务。
- **Task Mode**: 复杂的任务执行引擎，支持任务持久化、版本控制与状态流转。
- **RAG Service**: 基于 LightRAG 的知识库构建与检索，支持图谱生成。
- **Media Service**: 音频处理与 ASR 服务。
- **Analytics (Vanna)**: 自然语言转 SQL 与数据分析可视化。
- **Sandbox Service**: 集成 E2B 的安全代码执行环境。
- **OpenClaw Service**: 提供节点监控、定时任务调度与远程网关交互能力。

### OpenClaw 集成
Taichi Agent 深度集成了 OpenClaw 分布式监控与任务调度系统，采用双通道通信架构：
1.  **Control Plane (HTTP)**: 基于 `OpenClawHttpClient`，负责配置管理、任务增删改查、节点列表拉取与健康检查。支持静默失败处理，确保核心服务稳定性。
2.  **Data Plane (WebSocket)**: 基于 `OpenClawWsClient` (Node Monitor)，负责与 Gateway 建立长连接，实现节点心跳维持、实时指令接收与身份认证 (Ed25519 签名)。

### 数据库与存储
后端默认使用 SQLite (`recorder_v5.db`)，支持平滑切换至 PostgreSQL 或 MySQL。
- **主要实体**: Agent, Chat, Workflow, Knowledge, Task (Task Mode), Indicator, UserScript, Skill, Node (OpenClaw).
- **Task Mode 持久化**: 专门的任务表结构，记录任务版本、QA 历史与审计日志。

### 环境配置与启动

1.  **环境配置**:
    在 `backend/` 目录下创建 `.env` 文件：
    ```ini
    PROJECT_NAME="Taichi Agent"
    
    # Database
    USE_SQLITE=True
    # POSTGRES_SERVER=localhost
    
    # LLM API Keys
    OPENAI_API_KEY=sk-xxxx
    DEEPSEEK_API_KEY=sk-xxxx
    E2B_API_KEY=e2b_xxxx  # 用于沙箱环境
    
    # OpenClaw Integration
    OPENCLAW_BASE_URL=wss://gateway.example.com
    OPENCLAW_GATEWAY_TOKEN=xxxx
    OPENCLAW_DEVICE_ID=xxxx
    OPENCLAW_DEVICE_PRIVATE_KEY=xxxx # Base64 encoded Ed25519 key
    
    # Storage
    STORAGE_TYPE=local
    ```

2.  **安装依赖**:
    ```bash
    cd backend
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # Linux/Mac: source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **启动服务**:
    ```bash
    # 自动初始化数据库并启动
    python -m app.main
    # 或
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

### Task Mode (任务模式)
Task Mode 是本项目的一个重要特性，专为长流程、复杂任务设计。
- **API 文档**: `backend/docs/task_mode_api.md`
- **功能**:
  - **任务全生命周期管理**: 创建、分配、更新、完成。
  - **版本控制**: 每次更新自动生成新版本，支持回溯。
  - **审计日志**: 记录所有操作流水。
  - **QA 记录**: 任务执行过程中的问答对持久化。
  - **备份与恢复**: 支持任务数据的导出与导入。

### 部署 (Deployment)
项目包含 K8s 部署脚本 (`deploy/`)，支持蓝绿部署与回滚。
- **K8s**: 使用 Helm Chart 进行管理。
- **Scripts**: `deploy.sh` (部署), `rollback.sh` (回滚)。

### API 接口
- **Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `/api/v1/openapi.json`
- **主要模块**:
  - `/api/v1/agent`: 智能体与工具
  - `/api/v1/search`: 搜索服务
  - `/api/v1/task-mode`: 任务模式管理
  - `/api/v1/knowledge`: 知识库与 RAG
  - `/api/v1/mcp`: MCP 工具集成
  - `/api/v1/sandbox`: 沙箱环境管理
  - `/api/v1/openclaw`: OpenClaw 网关代理接口
  - `/api/v1/nodes`: 本地节点管理接口

---

*Taichi Agent Team &copy; 2026*
