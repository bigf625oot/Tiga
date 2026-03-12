# 智能体中心与 Agno 服务功能现状与开发计划

本文档基于 `d:\Tiga\docs\Agent\task.md` 的需求，对当前系统（Tiga）的智能体中心及 Agno 服务集成情况进行了详细核查，并针对未完成的功能制定了后续开发与测试计划。

## 1. 现状分析 (Status Analysis)

经过对前后端代码库的深度扫描与分析，功能完成情况如下：

### ✅ 已完成功能 (Implemented)

1.  **智能体中心基础管理 (CRUD):**
    *   **后端:** `Agent` 模型的增删改查 API 已在 `app/api/endpoints/agents.py` 中完整实现。
    *   **前端:** `AgentManagement.vue` 实现了列表展示，`AgentEditorDrawer.vue` 实现了创建与编辑流程。

2.  **智能体配置:**
    *   **基本信息:** 名称、描述、头像等配置已打通。
    *   **系统提示词 (System Prompt):** 支持自定义角色设定。
    *   **用户脚本 (User Script):** 实现了 `UserScript` 模型与编辑器，支持动态加载脚本。
    *   **推理模式:** 支持 CoT (Chain of Thought) 开关及基座模型选择。

3.  **知识库集成 (Knowledge Base):**
    *   **后端:** 通过 LightRAG 与 MCP 协议 (`search_knowledge_base`, `query_knowledge_graph`) 实现了深度集成。
    *   **前端:** 支持在智能体配置中勾选关联知识库。

4.  **已集成的 Agno 工具:**
    *   **DuckDuckGo Search:** 支持联网搜索。
    *   **N8N Workflow:** 支持触发自动化工作流。
    *   **Sandbox (E2B):** 支持安全执行 Python 代码与 Shell 命令 (替代了部分 `ShellTools` 和 `PythonTools` 需求)。
    *   **OpenClaw:** 支持网页抓取与自动化任务。
    *   **MCP Tools:** 支持标准 MCP 协议工具的动态加载。

5.  **高级筛选与搜索 (Advanced Search & Filtering):**
    *   **后端:** `/api/v1/agents/` 接口已升级，支持 `q` (关键词模糊搜索) 和 `is_template` (模版/实例精确筛选) 参数。
    *   **前端:** 实现了基于服务端的实时搜索（防抖）与 Tab 切换过滤，有效应对大数据量场景。

### ❌ 未完成/待完善功能 (Pending)

1.  **Agno 工具箱扩展 (Tools Integration):**
    *   **金融类:** `YFinance`, `OpenBB`, `Financial Datasets` (代码中未发现实现及依赖)。
    *   **数据分析类:** `Pandas`, `DuckDB`, `SQL` (SQL 目前仅在 Vanna 服务中存在，未作为通用 Agent 工具暴露)。
    *   **开发运维类:** `GitHub`, `Docker` (未集成)。
    *   **多媒体类:** `DALL-E`, `Replicate`, `Fal.ai` (未集成)。
    *   **网页解析类:** `Firecrawl`, `BeautifulSoup` (虽有 OpenClaw，但作为独立工具未封装)。

---

## 2. 开发计划 (Development Plan)

### Phase 1: 核心功能增强 (搜索与筛选) - ✅ 已完成
**目标:** 提升智能体中心在大数据量下的可用性。

*   **Task 1.1:** 后端 `list_agents` API 升级 (✅ Done)
    *   **接口地址:** `GET /api/v1/agents/`
    *   **新增参数:**
        *   `q` (string, optional): 用于搜索 `name` 和 `description` 的关键词。
        *   `is_template` (boolean, optional): `true` 返回模版，`false` 返回实例，不传返回所有。
    *   **代码变更:** `app/crud/crud_agent.py`, `app/services/agent/service.py`, `app/api/endpoints/agents.py`
*   **Task 1.2:** 前端对接新 API (✅ Done)
    *   **功能:** 改造搜索框为服务端搜索模式（300ms Debounce），Tab 切换自动应用 `is_template` 过滤。
    *   **代码变更:** `frontend/src/features/agent/components/AgentManagement.vue`

### Phase 2: 金融工具集成 (Financial Tools)
**目标:** 赋予 Agent 金融数据分析能力。

*   **Task 2.1:** 依赖引入
    *   `pip install yfinance openbb financial-datasets`
*   **Task 2.2:** 工具封装 (`app/services/agent/tools/financial.py`)
    *   封装 `YFinanceTools` (股票价格、基本面数据)。
    *   封装 `OpenBBTools` (如果是开源版)。
*   **Task 2.3:** `AgentManager` 注册
    *   在 `create_agno_agent` 中添加对 `yfinance` 等配置项的解析与注入。

### Phase 3: 数据分析工具集成 (Data Analysis)
**目标:** 增强 Agent 的数据处理与查询能力。

*   **Task 3.1:** 依赖引入
    *   `pip install duckdb pandas` (Pandas 已存在)
*   **Task 3.2:** 工具封装 (`app/services/agent/tools/data.py`)
    *   封装 `PandasTools` (CSV/Excel 处理)。
    *   封装 `DuckDBTools` (本地高性能 SQL 查询)。
    *   通用 `SQLTools` (连接 Postgres/MySQL，需注意安全权限)。
*   **Task 3.3:** 前端配置支持
    *   允许用户上传 CSV/Excel 文件作为 Agent 的临时数据源。

### Phase 4: 开发与多媒体工具 (Dev & Media)
**目标:** 扩展 Agent 的编码协作与内容生成能力。

*   **Task 4.1:** 开发工具集成
    *   集成 `GitHubTools` (需处理 OAuth 或 PAT Token 配置)。
    *   集成 `DockerTools` (需宿主机 Docker Socket 权限控制，建议在 Sandbox 中运行)。
*   **Task 4.2:** 多媒体工具集成
    *   集成 `DALL-E` (OpenAI Image API)。
    *   集成 `Replicate` / `Fal.ai` (需 API Key 配置管理)。

---

## 3. 测试计划 (Test Plan)

### 3.1 单元测试 (Unit Testing)
*   **搜索功能:**
    *   测试 `crud.get_multi` 的过滤逻辑，确保关键词匹配准确，SQL 注入防御有效。
*   **工具封装:**
    *   对每个新封装的 Tool Class 编写 Mock 测试。
    *   例如：Mock `yfinance.Ticker`，验证 `YFinanceTools.get_stock_price` 能正确返回数据格式。

### 3.2 集成测试 (Integration Testing)
*   **Agent 流程测试:**
    *   创建一个配置了 `YFinance` 工具的 Agent。
    *   发送指令 "查询 Apple 今天的股价"。
    *   断言 Agent 成功调用了 `get_stock_price` 工具并返回了包含数字的自然语言回答。
*   **API 接口测试:**
    *   测试 `/agents/` 接口在不同参数组合下的响应时间和数据正确性。

### 3.3 安全测试 (Security Testing)
*   **SQL/Shell 工具:**
    *   重点测试权限隔离。验证 Agent 无法通过 `SQLTools` 访问系统敏感表 (如 `users`, `api_keys`)。
    *   验证 `Sandbox` 是否有效隔离了恶意代码执行。

### 3.4 用户验收测试 (UAT)
*   **前端交互:**
    *   在“智能体编辑”页面勾选新工具，保存后，在对话框中验证工具是否生效。
    *   测试搜索功能的响应速度和用户体验。
