# Pathway ETL 流水线开发计划 - 阶段 4 & 5 (前端全栈开发)

## 1. 概览
本阶段将基于已完成的后端 DAG API，构建基于 Vue Flow 和 shadcn-vue 的可视化 ETL 编排界面。目标是实现所见即所得的流水线设计、配置与运行监控。

## 2. 后端就绪情况 (已完成)
*   **API 接口 (已对接)**:
    *   [x] `GET /pathway/pipelines`: 获取流水线列表。
    *   [x] `GET /pathway/pipelines/{id}`: 获取指定流水线详情。
    *   [x] `POST /pathway/pipelines`: 创建 Pipeline。
    *   [x] `PUT /pathway/pipelines/{id}`: 更新 DAG 配置。
    *   [x] `DELETE /pathway/pipelines/{id}`: 删除流水线。
    *   [x] `POST /pathway/pipelines/{id}/run`: 触发运行。
    *   [x] `POST /pathway/pipelines/{id}/stop`: 停止运行。
    *   [x] `GET /pathway/pipelines/{id}/logs`: 获取运行日志 (支持 Mock 降级)。
*   **数据模型**: [x] `PathwayJob` 表已扩展 `dag_config` 字段存储前端图数据。

## 3. 前端执行计划 (Vue)

### 3.1 技术栈与设计规范
*   **核心库**: `vue-flow` (画布), `shadcn-vue` (组件), `pinia` (状态管理), `vee-validate` (表单)。
*   **交互原则 (尼尔森)**:
    *   **状态可见性**: 节点右上角实时显示运行状态 (Loading/Success/Error)。
    *   **系统与现实匹配**: 使用标准的数据库、文件图标。
    *   **用户控制**: 支持撤销/重做 (Undo/Redo)，支持手动停止/启动。
    *   **防错**: 连线时校验 Handle 类型（如：Source 节点不可作为 Target）。

### 3.2 页面结构规划
建议在 `frontend/src/features/etl_editor` 下构建以下结构：

1.  **流水线列表页 (`PipelineList.vue`)**
    *   [x] 使用 `shadcn-vue` 的 `DataTable` 组件。
    *   [x] 列：名称、状态 (Badge)、最近运行时间、操作 (编辑/运行/删除)。
    *   [x] 功能：搜索过滤、新建流水线模态框。
    *   [x] 对接 `pipelineStore.fetchPipelines()` 获取真实数据。
    *   [x] 实现 `deletePipeline` 并同步后端删除。
    *   [x] 运行/停止按钮对接 Store 的 `runPipeline`/`stopPipeline`。

2.  **画布编辑器页 (`EditorLayout.vue`)**
    *   [x] **布局**: `ResizablePanel` (左侧组件库 | 中间画布 | 右侧属性面板)。
    *   [x] **左侧组件库 (`Sidebar.vue`)**:
        *   [x] 分组展示：`Sources` (Kafka, S3, API...), `Transforms` (Clean, Filter...), `Sinks` (Redis, DB...)。
        *   [x] 支持拖拽 (Draggable) 到画布。
    *   [x] **中间画布 (`PipelineCanvas.vue`)**:
        *   [x] 集成 `Vue Flow`。
        *   [x] 自定义节点 (`CustomNode.vue`): 包含图标、标题、状态指示器、Handles。
        *   [x] 控制栏 (`Controls`): 缩放、对齐、保存按钮、运行按钮。
    *   [x] **右侧属性面板 (`PropertyPanel.vue`)**:
        *   [x] 点击节点时触发。
        *   [x] 根据 `node.data.type` 动态渲染表单 (Schema Form)。
        *   [x] 例如 Source 节点显示 Host/Port 输入框，Transform 节点显示 SQL/Python 代码框。

### 3.3 关键逻辑实现 Todo

- [x] **API Client 集成**: 生成/编写 `src/features/etl_editor/api/pipeline.ts` 调用后端 `/pipelines` 接口。
- [x] **自定义节点开发**:
    *   `BaseNode.vue`: 通用外壳，处理选中样式、Handles。
    *   `SourceNode/TransformNode/SinkNode`: 不同配色与图标。
- [x] **拖拽逻辑**:
    *   `onDragStart`: 传递组件类型数据。
    *   `onDrop`: 计算画布坐标，创建新节点。
- [x] **连线校验**:
    *   `isValidConnection`: 禁止自环，禁止 Sink->Source，禁止类型不兼容（可选）。
- [x] **运行与监控**:
    *   点击“运行”调用 `/pipelines/{id}/run`。
    *   轮询 `/pipelines/{id}` 或使用 WebSocket 获取状态，更新节点样式。
- [x] **集成修复 (列表页)**:
    *   `usePipelineStore.ts`: 添加 `deletePipeline` action。
    *   `EtlPipelineList.vue`: 移除 Mock 数据生成逻辑，`onMounted` 调用 `store.fetchPipelines()`。
    *   `EtlPipelineList.vue`: 对接 `store.deletePipeline(id)` 实现真实删除。
    *   `EtlPipelineList.vue`: 对接 `store.runPipeline`/`stopPipeline` 实现真实控制。
- [x] **集成修复 (编辑器)**:
    *   修复 `App.vue` 路由参数传递，确保编辑器能加载指定 ID 的流水线。

## 4. 测试计划 (前端)
*   **单元测试 (已完成)**:
    *   [x] `usePipelineStore.spec.ts`: 验证 Store 的 CRUD 和运行控制逻辑。
*   **集成测试 (已完成)**:
    *   [x] `EtlPipelineList.integration.spec.ts`: 验证列表页加载真实数据的全链路流程。
*   **UI 测试**: 验证拖拽添加节点是否流畅，连线是否准确。
*   **集成测试**:
    *   创建 Pipeline -> 拖拽 Kafka Source + Log Sink -> 连线 -> 保存。
    *   刷新页面，验证画布还原是否正确 (JSON 反序列化)。
    *   点击运行，验证后端返回 200，且状态变为 Running。

----------------------------------------------
