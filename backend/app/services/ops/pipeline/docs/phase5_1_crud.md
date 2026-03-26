# Pathway ETL 开发计划 - 阶段 5.1 (CRUD 功能补全)

## 1. 目标
完善流水线的基础管理功能，从简单的“能用”升级为“好用、安全”，满足企业级生产环境需求。

## 2. 后端开发任务 (Backend)

### 2.1 版本控制系统 (Versioning)
- [ ] **数据模型变更**:
    *   新增表 `pathway_pipeline_versions`:
        *   `id`: PK
        *   `pipeline_id`: FK -> `pathway_jobs.id`
        *   `version`: int (版本号, 1, 2, 3...)
        *   `dag_config`: JSON (该版本的配置快照)
        *   `description`: str (变更说明/Commit Message)
        *   `created_at`: datetime
- [ ] **API 扩展**:
    *   `POST /pipelines/{id}/versions`: 创建新版本（通常在保存时可选触发）。
    *   `GET /pipelines/{id}/versions`: 获取版本列表。
    *   `POST /pipelines/{id}/rollback/{version_id}`: 回滚到指定版本。

### 2.2 复制与导入导出
- [ ] **克隆接口**:
    *   `POST /pipelines/{id}/clone`: 复制目标流水线的配置，生成一个新的流水线（名称自动加 `_copy`）。
- [ ] **导入导出**:
    *   `GET /pipelines/{id}/export`: 返回包含完整配置的 JSON 文件下载。
    *   `POST /pipelines/import`: 接收 JSON 文件并创建新流水线。

### 2.3 数据安全
- [ ] **软删除机制**:
    *   修改 `PathwayJob` 模型，增加 `is_deleted` (bool) 和 `deleted_at` (datetime) 字段。
    *   改造 `delete_pipeline` 接口为软删除。
    *   新增 `GET /pipelines/trash` (回收站) 和 `POST /pipelines/{id}/restore` (还原)。

## 3. 前端开发任务 (Frontend)

### 3.1 前后端对接修复 (P0 - 紧急)
- [ ] **列表页真实对接**:
    *   修改 `EtlPipelineList.vue`，移除 `generatePipelines` Mock 逻辑。
    *   调用 `pipelineStore.fetchPipelines()` 获取真实数据。
    *   确保列表中的删除、状态切换操作调用 Store 中的真实 Action。
- [ ] **编辑器加载修复**:
    *   修改路由逻辑，确保从列表点击“编辑”时，URL 包含 ID (e.g., `/etl/edit/:id`)。
    *   编辑器挂载时调用 `store.loadPipeline(route.params.id)`。

### 3.2 版本历史面板对接
- [ ] **改造 `VersionHistory.vue`**:
    *   废弃基于 `Pinia` 的纯本地状态。
    *   对接后端版本 API，展示真实的历史记录列表。
    *   实现“对比”功能（Diff View，可选）。

### 3.3 列表页增强
- [ ] **操作列扩展**:
    *   增加“复制”、“导出”按钮。
- [ ] **回收站页面**:
    *   新增路由 `/data-etl/trash`，展示已删除流水线，支持还原。

### 3.4 导入功能
- [ ] **新建流水线模态框**:
    *   增加“从文件导入”选项，支持上传 JSON。

## 4. 优先级建议
1.  **P0**: **前后端对接修复** (列表页必须能看到真实数据)
2.  **P1**: 软删除 (防止数据丢失)
3.  **P2**: 版本控制 (支持回滚)
4.  **P3**: 复制/克隆 (提升效率)
5.  **P4**: 导入/导出 & 分组
