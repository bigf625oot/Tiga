# Pathway ETL & Data Platform 完整开发计划

基于项目现有进度，本计划将任务划分为四个核心模块：**数据大屏 (Dashboard)**、**数据源管理 (Data Sources)**、**ETL 流水线 (ETL Pipeline)** 和 **系统设置 (System Settings)**。

---

## 1. 数据大屏 (Dashboard)

**目标**: 将当前仅用于监控的大屏升级为集成了**实时监控**、**数据探索**和**智能问答**的综合指挥中心。

### 1.1 现状与缺口
*   **现状**: 前端 `DataDashboard.vue` 使用 Mock 数据展示健康度与日志。
*   **缺口**: 缺乏真实数据查询能力；智能问答组件未集成；数据源状态未实时联动。

### 1.2 开发任务 (Todo List)
- [ ] **统一查询服务 (Unified Query Service)**
    - [ ] 后端策略扩展: 为 `Database` 和 `Graph` 策略增加 `execute_query(query)` 方法。
    - [ ] API 开发: `POST /data-sources/{id}/query` (支持 SQL/Cypher)。
- [ ] **数据探索器 (Data Explorer)**
    - [ ] 前端组件: 开发 `DataExplorer.vue`，集成 Monaco Editor (SQL高亮) 和 ECharts (结果可视化)。
    - [ ] 交互实现: 下拉选择数据源 -> 输入查询 -> 展示表格/图表结果。
- [ ] **智能问答集成 (AI Assistant)**
    - [ ] 后端改造: `KGQueryService` 支持路由到指定数据源执行查询。
    - [ ] 前端集成: 将 `SmartDataQuery.vue` 嵌入 Dashboard 顶部，对接 `/kg/query`。
- [ ] **实时指标对接**
    - [ ] 替换 Mock: 将 `Health` 和 `Throughput` 指标对接后端 WebSocket/SSE 数据流。

### 1.3 测试用例
| ID | 用例名称 | 操作步骤 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC-DASH-01 | SQL 查询执行 | 在探索器选择 MySQL 数据源，输入 `SELECT * FROM users LIMIT 5` 并运行 | 下方表格显示 5 条用户数据 |
| TC-DASH-02 | 智能问答绘图 | 输入“统计过去 7 天的订单趋势” | 自动生成折线图并渲染在 Dashboard 上 |
| TC-DASH-03 | 实时吞吐量 | 启动一个高频写入的流水线 | Dashboard 上的吞吐量曲线实时上升 |

---

## 2. 数据源管理 (Data Sources)

**目标**: 确保所有类型数据源（DB, API, File, Crawler）的 CRUD 功能稳定，并增强**Schema 探测**能力以支持 ETL 配置。

### 2.1 现状与缺口
*   **现状**: 前端 CRUD 已完整实现；后端支持基础连接。
*   **缺口**: 缺乏获取表结构 (Schema Discovery) 的接口，导致 ETL 配置时无法下拉选择字段。

### 2.2 开发任务 (Todo List)
- [ ] **Schema 探测能力**
    - [ ] 后端扩展: 在 `connectors/source.py` 中增加 `get_schema()` 方法。
    - [ ] API 开发: `POST /data-sources/{id}/discover`，返回表名、字段名及类型。
- [ ] **高级配置增强**
    - [ ] 完善 API 数据源的分页策略配置 (Cursor/Offset) 测试。
    - [ ] 验证 SSH 隧道连接数据库的稳定性。

### 2.3 测试用例
| ID | 用例名称 | 操作步骤 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC-DS-01 | 数据库 Schema 获取 | 选择已连接的 PostgreSQL，点击“获取结构” | 返回所有 Table 名称及 Column 列表 |
| TC-DS-02 | API 分页抓取 | 配置 API 数据源，设置 PageSize=10，运行测试 | 成功抓取多页数据并合并 |

---

## 3. ETL 流水线 (ETL Pipeline)

**目标**: 实现全功能的**可视化编排**、**版本控制**、**实时调试**及**自动化调度**。

### 3.1 现状与缺口
*   **现状**: DAG 解析与运行核心已就绪；前端编辑器可用。
*   **缺口**: 列表页未对接真实数据；缺乏版本控制；日志与中间数据预览缺失；调度功能未集成。

### 3.2 开发任务 (Todo List)
- [ ] **前后端集成 (P0)**
    - [ ] 列表页对接: `EtlPipelineList.vue` 移除 Mock，调用 `pipelineStore.fetchPipelines()`。
    - [ ] 编辑器加载: 修复路由参数传递，确保 `EditorLayout` 能加载指定 ID 的流水线。
- [ ] **CRUD 增强 (P1)**
    - [ ] 版本控制: 后端新增 `pipeline_versions` 表；前端对接 `VersionHistory` 面板。
    - [ ] 软删除: 实现 `is_deleted` 逻辑及回收站功能。
    - [ ] 复制/克隆: 实现 `POST /pipelines/{id}/clone`。
- [ ] **运行反馈 (P2)**
    - [ ] 数据预览: 后端实现节点采样 Hook；前端在属性面板增加“Preview”标签。
    - [ ] 真实日志: 对接 Redis Stream 日志流，前端实时展示运行 Log。
- [ ] **外部集成 (P3)**
    - [ ] Webhook 触发: 实现 `POST /hooks/{pipeline_id}`。
    - [ ] 调度配置: 集成 APScheduler，支持 Cron 表达式配置。

### 3.3 测试用例
| ID | 用例名称 | 操作步骤 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC-ETL-01 | 端到端运行 | 创建 CSV->Clean->Redis 流水线并运行 | 运行状态变更为 Success，Redis 中查到清洗后的数据 |
| TC-ETL-02 | 版本回滚 | 修改配置保存为 V2，然后在历史面板点击“回滚 V1” | 配置恢复为 V1 内容，V2 记录保留 |
| TC-ETL-03 | 数据预览 | 在 Transform 节点上点击“预览” | 弹出窗口显示该节点处理后的前 10 条 JSON 数据 |

---

## 4. 系统设置 (System Settings)

**目标**: 将静态的配置界面升级为具备**持久化存储**和**真实交互**的运维管理中心。

### 4.1 现状与缺口
*   **现状**: `ModelConfig`, `DBConfig`, `AlertRules` 均为前端 Mock 或本地状态。
*   **缺口**: 无法保存配置；无法真实测试连接；告警规则未生效。

### 4.2 开发任务 (Todo List)
- [ ] **告警规则闭环**
    - [ ] 后端开发: 新增 `AlertRule` 模型及 CRUD 接口。
    - [ ] 监控守护进程: 启动后台任务，定期检查指标并触发告警。
    - [ ] 前端对接: `AlertRulesConfig.vue` 对接真实 API。
- [ ] **基础设施配置**
    - [ ] 数据库连接: 实现 `/system/db/test-connection` 及配置持久化。
    - [ ] 模型配置: `ModelConfig.vue` 对接 `/api/v1/models`，支持 API Key 更新。

### 4.3 测试用例
| ID | 用例名称 | 操作步骤 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC-SYS-01 | 告警触发 | 创建“流水线失败 > 0”的告警规则，手动触发一次失败 | 系统发送通知（日志或邮件），前端显示告警状态 |
| TC-SYS-02 | 向量库连接测试 | 输入错误的 Milvus 端口并点击测试 | 提示“连接失败”及具体错误信息 |
| TC-SYS-03 | 模型切换 | 在设置中将默认 LLM 切换为 Claude-3 | 智能问答模块随后开始使用 Claude-3 回答 |
