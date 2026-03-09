# Pathway ETL 开发计划 - 阶段 7 (图谱大盘数据查询与可视化增强)

## 1. 现状分析 (Gap Analysis)
*   **前端现状**: `DataDashboard.vue` 目前仅作为“监控大屏”，展示数据源的健康状态 (Health, Throughput) 和流水线日志。使用的是 Mock 数据 (`useDashboardMock.ts`)。**缺失**直接对数据源进行交互式查询、检索和即时分析的功能。
*   **后端现状**: 
    *   `data_source.py` 提供了 `GET /{id}/data` 接口，但仅支持简单的全量/分页拉取 (Dump)，不支持 SQL/Cypher 复杂查询。
    *   `kg_query/service.py` 实现了自然语言转图表 (NL2Chart)，但目前仅绑定 LightRAG/Mock，未与 `DataSource` 模块打通，也未暴露给仪表盘。

## 2. 核心目标 (Objectives)
在图谱大盘中增加“数据探索 (Data Explorer)”能力，使用户能够：
1.  **直接查询**: 对接入的 SQL/Graph 数据源执行 SQL 或 Cypher 查询。
2.  **智能问答**: 通过自然语言 (NL) 提问，自动生成统计图表 (基于 `KGQueryService`)。
3.  **实时预览**: 在大盘上即时查看查询结果（表格/图表）。

## 3. 后端开发任务 (Backend)

### 3.1 统一查询服务 (Unified Query Service)
*   [ ] **策略模式扩展**:
    *   在 `app/strategies/` 中为 Database (MySQL/PG) 和 Graph (Neo4j) 增加 `execute_query(query: str)` 方法。
    *   SQL 策略: 使用 `text()` 执行 SQL，返回字典列表。
    *   Graph 策略: 使用 Neo4j Driver 执行 Cypher。
*   [ ] **API 接口**:
    *   `POST /data-sources/{id}/query`: 
        *   Input: `{ query: "SELECT * FROM users LIMIT 10", type: "sql" }`
        *   Output: `{ columns: [...], rows: [...] }`

### 3.2 智能查询集成 (Smart Query Integration)
*   [ ] **改造 `KGQueryService`**:
    *   使其支持指定 `data_source_id`。
    *   当用户提问“查询最近订单”时，自动路由到对应的 SQL 数据源执行查询。
*   [ ] **图表配置生成**:
    *   复用 `_format_to_echarts` 逻辑，将查询结果转化为 ECharts 配置 (JSON)。

## 4. 前端开发任务 (Frontend)

### 4.1 数据探索面板 (Data Explorer)
*   [ ] **新增组件 `DataExplorer.vue`**:
    *   入口：在 `DataDashboard.vue` 增加“数据探索” Tab 或 侧边抽屉。
    *   功能：
        *   数据源选择器 (Dropdown)。
        *   查询编辑器 (Monaco Editor，支持 SQL/Cypher 高亮)。
        *   执行按钮 (Run)。
*   [ ] **结果展示**:
    *   **表格视图**: 使用 `shadcn-vue` DataTable 展示原始数据。
    *   **图表视图**: 集成 ECharts，渲染后端返回的 `chart_config`。

### 4.2 智能问答框 (AI Assistant)
*   [ ] **集成 `SmartDataQuery.vue`**:
    *   将现有的智能查询组件集成到 Dashboard 顶部。
    *   对接后端 `POST /kg/query` 接口。

## 5. 场景示例
1.  **运维排查**: 用户在 Dashboard 发现“SQL 数据库”吞吐量异常 -> 点击“探索” -> 输入 `SHOW PROCESSLIST` -> 发现死锁。
2.  **业务洞察**: 用户输入“展示过去 24 小时各分类的告警数量” -> 后端生成柱状图 -> Dashboard 渲染展示。
