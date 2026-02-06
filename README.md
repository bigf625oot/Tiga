# Taichi Agent - 智能体编排与数据智能平台

Taichi Agent 是一个集成了智能体编排、多模态知识库（RAG）、数据智能分析与自动化工作流的现代化全栈平台。本项目采用前后端分离架构，旨在为开发者提供开箱即用的企业级 AI 应用开发框架。

---

## 📚 目录

- [🎨 前端工程 (Frontend)](#-前端工程-frontend)
  - [项目简介](#项目简介)
  - [技术栈](#技术栈)
  - [目录结构](#目录结构)
  - [环境准备](#环境准备)
  - [快速开始](#快速开始)
  - [构建与部署](#构建与部署)
  - [核心功能模块](#核心功能模块)
  - [常见问题与解决方案](#常见问题与解决方案)
- [⚙️ 后端服务 (Backend)](#%EF%B8%8F-后端服务-backend)
  - [技术架构](#技术架构)
  - [数据库设计](#数据库设计)
  - [环境配置](#环境配置)
  - [服务启动](#服务启动)
  - [API 接口规范](#api-接口规范)
  - [安全与认证](#安全与认证)
  - [测试与质量保证](#测试与质量保证)
  - [容器化与 CI/CD](#容器化与-cicd)
  - [故障排查手册](#故障排查手册)

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
| **路由** | Vue Router 4.x | 页面路由管理 |
| **状态管理** | Pinia 2.1 | 响应式状态管理 |
| **可视化** | V-Network-Graph / 3D-Force-Graph | 知识图谱与网络关系可视化 |
| **HTTP 客户端** | Axios 1.6+ | 接口请求处理 |

### 目录结构
```bash
frontend/
├── public/              # 静态资源 (图标, 录音库等)
├── src/
│   ├── core/            # 核心层 (API 客户端, 全局配置)
│   ├── features/        # 业务功能模块 (按领域划分)
│   │   ├── agent/       # 智能体管理
│   │   ├── analytics/   # 数据分析
│   │   ├── knowledge/   # 知识库与图谱
│   │   ├── qa/          # 智能问答
│   │   ├── recording/   # 录音与多媒体
│   │   ├── search/      # 搜索智能体
│   │   ├── system/      # 系统设置
│   │   └── workflow/    # 工作流编排
│   ├── shared/          # 共享资源
│   │   ├── components/  # 通用组件 (原子/分子/有机体设计)
│   │   ├── hooks/       # 组合式函数
│   │   └── types/       # 全局类型定义
│   ├── App.vue          # 根组件
│   ├── main.js          # 入口文件
│   └── style.css        # 全局样式
├── index.html           # HTML 模板
├── vite.config.js       # Vite 配置
└── package.json         # 依赖配置
```

### 环境准备
- **Node.js**: >= 18.0.0
- **pnpm** (推荐) 或 **npm** / **yarn**

### 快速开始

1.  **进入前端目录**
    ```bash
    cd frontend
    ```

2.  **安装依赖**
    ```bash
    npm install
    # 或
    pnpm install
    ```

3.  **启动开发服务器**
    ```bash
    npm run dev
    ```
    服务默认运行在 `http://localhost:5173`。

### 构建与部署

1.  **生产环境打包**
    ```bash
    npm run build
    ```
    构建产物将输出至 `dist/` 目录。

2.  **本地预览打包结果**
    ```bash
    npm run preview
    ```

3.  **部署说明**
    - 将 `dist/` 目录下的所有文件上传至 Nginx、Apache 或 CDN。
    - **Nginx 配置示例**（解决 History 模式路由刷新 404 问题）：
      ```nginx
      location / {
          try_files $uri $uri/ /index.html;
      }
      ```

### 核心功能模块
- **Agent Management**: 智能体创建、技能配置与脚本编辑。
- **Knowledge Base**: 知识库管理，支持图谱导出与可视化 (2D/3D)。
- **Analytics**: 基于 Vanna 的 Text-to-SQL 数据查询与指标监控。
- **Smart QA**: 基于 RAG 的智能问答系统。
- **Workflow**: 类似 n8n 的可视化工作流编排。

### 常见问题与解决方案
1.  **依赖安装失败**
    - **现象**: `npm install` 报错。
    - **解决**: 尝试删除 `node_modules` 和 `package-lock.json` 后重试，或检查 Node 版本是否符合要求。建议使用淘宝镜像或科学上网。
2.  **组件样式冲突**
    - **现象**: Element Plus 与 Ant Design Vue 样式相互覆盖。
    - **解决**: 本项目使用了 Tailwind CSS，尽量使用 Utility Class 覆盖默认样式。如遇严重冲突，需在 `vite.config.js` 中配置按需加载或调整 CSS 引入顺序。
3.  **API 跨域问题**
    - **现象**: 接口请求 403 或 CORS 错误。
    - **解决**: 确保后端 `CORSMiddleware` 配置正确（开发环境通常允许 `*`）。前端 `vite.config.js` 中可配置 `server.proxy` 进行转发。

---

## ⚙️ 后端服务 (Backend)

### 技术架构
后端基于 **Python 3.10+** 和 **FastAPI** 框架构建，遵循 RESTful 规范，集成了 SQLAlchemy ORM、Celery (可选) 和多种 AI 引擎接口。

### 技术栈与框架版本
- **Web 框架**: FastAPI (>=0.111.0)
- **服务器**: Uvicorn
- **数据库 ORM**: SQLAlchemy (2.0+) + Alembic
- **数据库支持**: SQLite (默认), PostgreSQL, MySQL
- **AI/LLM**: Agno, OpenAI SDK, Vanna (Text-to-SQL)
- **RAG 引擎**: LightRAG, LanceDB (向量库)
- **对象存储**: Local, AWS S3, Aliyun OSS
- **工具库**: Pandas, NumPy, Pydantic, Requests

### 数据库设计
后端默认使用 SQLite (`recorder_v5.db`)，支持平滑切换至 PostgreSQL。

**主要实体表结构 (Models):**
- **Agent**: 智能体定义 (名称, 模型, 配置)。
- **Chat**: 聊天会话记录。
- **Workflow**: 工作流定义与执行状态。
- **Knowledge**: 知识库元数据与分块索引。
- **DataSource**: 外部数据源连接配置。

### 环境配置

1.  **配置文件**
    在 `backend/` 目录下创建 `.env` 文件（参考 `app/core/config.py`）：
    ```ini
    PROJECT_NAME="Taichi Agent"
    LOG_LEVEL=INFO
    
    # Database (默认 SQLite, 可选 Postgres)
    USE_SQLITE=True
    # POSTGRES_SERVER=localhost
    # POSTGRES_USER=postgres
    # POSTGRES_PASSWORD=password
    # POSTGRES_DB=tiga_db

    # LLM API Keys
    OPENAI_API_KEY=sk-xxxx
    DEEPSEEK_API_KEY=sk-xxxx

    # Storage
    STORAGE_TYPE=local # local, s3, aliyun_oss
    ```

### 依赖管理与安装

1.  **进入后端目录**
    ```bash
    cd backend
    ```

2.  **创建虚拟环境 (推荐)**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

### 服务启动

1.  **数据库初始化**
    服务启动时会自动检测并创建表结构。如需手动迁移：
    ```bash
    # (如果配置了 alembic)
    alembic upgrade head
    ```

2.  **启动开发服务**
    ```bash
    # 在 backend 目录下
    python -m app.main
    # 或者直接使用 uvicorn
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    API 文档地址: `http://localhost:8000/docs`

### API 接口规范
- 所有接口位于 `/api/v1` 前缀下。
- 请求与响应均使用 JSON 格式。
- 标准响应结构：
  ```json
  {
    "data": { ... },
    "message": "Success",
    "code": 200
  }
  ```
- 详细接口定义请参考 Swagger UI (`/docs`)。

### 安全与认证
- **API 安全**: 目前主要面向内部/单用户使用，API 默认开放。
- **敏感数据**: API Key 等敏感信息在数据库中存储时使用 `Fernet` 对称加密（Key 由 `SECRET_KEY` 派生）。
- **建议**: 生产环境部署建议在 Nginx 层增加 Basic Auth 或集成 OAuth2 中间件。

### 日志与监控
- **日志**: 使用 Python 标准 `logging` 模块，配置在 `app/core/logger.py`。默认输出到控制台，支持文件滚动。
- **监控**: 系统包含基本的性能指标监控（在 `app/services/metrics` 中）。

### 单元测试与集成测试
使用 `pytest` 进行测试。

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_crud_chat.py
```

### 故障排查手册

**错误码参考**
- `422 Validation Error`: 请求参数格式错误，请检查 JSON Body 字段类型。
- `500 Internal Server Error`: 服务器内部错误，请查看控制台/日志文件获取堆栈信息。

**常见问题**
1.  **数据库锁定 (Database is locked)**
    - **场景**: 使用 SQLite 且高并发写入时。
    - **解决**: SQLite 对并发写入支持有限。建议开发环境容忍，生产环境切换至 PostgreSQL。
2.  **缺少 API Key**
    - **现象**: 调用 AI 功能时报错 `401` 或 `Provider not authorized`。
    - **解决**: 检查 `.env` 文件中是否配置了 `OPENAI_API_KEY` 或其他对应厂商的 Key。
3.  **模块未找到 (ModuleNotFoundError)**
    - **现象**: `ModuleNotFoundError: No module named 'app'`.
    - **解决**: 确保在 `backend` 根目录下运行命令，并且已激活虚拟环境。如果在 IDE 中运行，确保将 `backend` 目录标记为 Sources Root。

---

*Taichi Agent Team &copy; 2026*
