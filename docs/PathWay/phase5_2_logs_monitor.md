# Pathway ETL 开发计划 - 阶段 5.2 (日志与监控)

## 1. 现状概览 (Status Report)
*   **后端就绪**: API 路由 (`routes.py`) 已覆盖流水线增删改查与运行控制；`DAGParser` 已能解析节点关系。
*   **前端就绪**: 可视化编辑器 (`etl_editor`) 功能完整，支持组件拖拽、属性配置、代码生成（如文本清洗规则）。
*   **待解决**: 
    *   日志与监控目前为 Mock 数据 (前端 `pipeline.ts` 中 `logs` 方法返回静态数组)。
    *   数据源配置缺乏 Schema 自动提示。
    *   缺乏基于真实数据的中间步骤预览。

## 2. 核心任务列表 (Todo List)

### 2.1 后端开发 (Backend)

#### 数据源增强
- [ ] **实现 Schema 探测接口** (`POST /sources/discover`): 
    *   完善 `connectors/source.py`，支持连接数据库/文件并返回字段列表。
    *   目标：前端配置 Source 时可下拉选择 Table 和 Column。

#### 运行时反馈
- [ ] **实现数据采样预览** (`GET /pipelines/{id}/nodes/{nodeId}/preview`):
    *   在 `engine.py` 中增加调试模式或采样逻辑，允许获取 DAG 中任意节点的前 10 条数据。
    *   用于前端“数据预览”面板。
- [ ] **实现真实日志流**:
    *   改造 `engine.py` 的日志输出，将其推送到 Redis Stream 或内存队列。
    *   API 实现 `/pipelines/{id}/logs` (轮询) 或 `/ws/pipelines/{id}/logs` (WebSocket)。

#### 算子执行适配
- [ ] **统一清洗算子执行策略**:
    *   前端 `TextCleaningProperties` 生成了 Python 代码 (`code`) 和 规则配置 (`rules`)。
    *   后端 `operators/cleaning.py` 需要决定是直接执行代码（需沙箱环境，风险高）还是解析 `rules` JSON（更安全）。建议优先实现 `rules` 解析器。

### 2.2 前端开发 (Frontend)

#### 编辑器增强
- [ ] **对接 Schema Discovery**:
    *   在 `PropertyPanel.vue` 的 Source 配置区，当用户填好连接信息后，自动获取表结构供选择。
- [ ] **数据预览面板**:
    *   在底部面板 (`RunLogs.vue` 旁) 增加 "Data Preview" 标签。
    *   点击画布节点时，异步加载该节点的 Sample Data。
- [ ] **对接真实日志**:
    *   替换 `pipeline.ts` 中的 `logs` Mock 实现，接入后端 API。

#### 其他算子配置
- [ ] **完善 Filter/Aggregate 组件**:
    *   检查 `FilterBuilder.vue` 和 `AggregateProperties.vue`，确保其生成的配置结构与后端算子参数对齐。

### 2.3 集成测试 (Integration)
- [ ] **端到端冒烟测试**:
    *   场景：CSV 文件输入 -> 文本清洗 (Trim/Upper) -> 过滤 (Filter) -> Redis 输出。
    *   验证：流程运行成功，Redis 中有数据，前端能看到绿色状态和日志。

## 3. 详细文件变更计划

### 后端
*   `backend/app/services/pathway/api/routes.py`: 增加 preview 接口，完善 discover 接口。
*   `backend/app/services/pathway/core/engine.py`: 增加数据采样 hook。
*   `backend/app/services/pathway/operators/cleaning.py`: 增加 `apply_cleaning_rules` 函数。

### 前端
*   `frontend/src/features/etl_editor/api/pipeline.ts`: 移除 Mock，对接真实接口。
*   `frontend/src/features/etl_editor/components/PropertyPanel.vue`: 增加 Schema 加载逻辑。
*   `frontend/src/features/etl_editor/EditorLayout.vue`: 增加数据预览区域。

## 4. 里程碑
*   **M1**: 静态配置跑通（前后端参数对其）。
*   **M2**: 动态反馈跑通（能看到日志和数据）。
