# Pathway ETL 开发计划 - 阶段 8 (系统设置与运维增强)

## 1. 现状分析 (Gap Analysis)
目前系统设置 (`SystemSettings.vue`) 及其子组件虽然提供了精美的 UI 界面，但缺乏真实的数据交互和持久化能力，处于“半成品”状态。

| 模块 | 前端组件 | 现状 | 缺失功能 |
| :--- | :--- | :--- | :--- |
| **模型配置** | `ModelConfig.vue` | **Mock 数据** | 无法获取真实模型列表，API Key 无法保存。 |
| **数据库连接** | `DatabaseConnectionConfig.vue` | **Mock 测试** | 连接测试仅为前端随机模拟，无保存接口。 |
| **告警规则** | `AlertRulesConfig.vue` | **本地状态** | 规则仅存储在浏览器内存，刷新即丢失。 |

## 2. 核心目标 (Objectives)
将系统设置模块从“静态展示”升级为“动态管理”，实现配置的**持久化存储**、**真实连接测试**和**告警监控闭环**。

## 3. 后端开发任务 (Backend)

### 3.1 告警规则管理 (Alert Rules CRUD)
*   [ ] **数据模型设计**:
    *   新增 `AlertRule` 模型 (`id`, `name`, `metric_type`, `threshold`, `severity`, `enabled`, `notification_channels`).
    *   `metric_type`: 支持 `pipeline_failure`, `api_latency`, `data_quality`.
*   [ ] **API 接口**:
    *   `GET /alerts/rules`: 获取规则列表。
    *   `POST /alerts/rules`: 创建规则。
    *   `PUT /alerts/rules/{id}`: 更新规则。
    *   `DELETE /alerts/rules/{id}`: 删除规则。

### 3.2 数据库连接配置 (DB Config)
*   [ ] **配置持久化**:
    *   在 `system_configs` 表中增加 `db_connection` 类型的记录，或扩展 `vanna_config.json` 的读写接口。
*   [ ] **真实测试接口**:
    *   `POST /system/db/test-connection`: 接收 `host`, `port`, `user`, `password`，尝试建立真实连接并返回结果。

### 3.3 模型配置对接
*   [ ] **复用接口**:
    *   确保 `/api/v1/models` 接口能够被 `SystemSettings` 调用，支持更新全局默认模型配置。

## 4. 前端开发任务 (Frontend)

### 4.1 告警规则对接
*   [ ] **API Client**:
    *   在 `api.ts` 中增加 `alertRuleApi` (list, create, update, delete)。
*   [ ] **组件改造**:
    *   修改 `AlertRulesConfig.vue`，移除 `ref` 本地数据，改用 `useQuery` 或 `onMounted` 加载后端数据。
    *   保存/删除操作调用真实 API。

### 4.2 数据库连接对接
*   [ ] **连接测试**:
    *   修改 `testConnection` 方法，调用后端 `/system/db/test-connection`。
*   [ ] **保存配置**:
    *   在界面增加“保存配置”按钮，调用保存接口。
    *   加载时回显后端存储的配置。

### 4.3 模型配置对接
*   [ ] **移除 Mock**:
    *   修改 `ModelConfig.vue`，动态加载后端返回的模型列表 (`gpt-4`, `claude-3` 等)。
    *   绑定真实的 API Key 输入框，支持脱敏显示与更新。

## 5. 监控告警闭环 (Ops Loop)
*   [ ] **监控守护进程 (Monitor Daemon)**:
    *   后端启动一个后台任务 (基于 APScheduler)。
    *   每分钟检查一次系统指标 (如 Redis 中的失败计数)。
    *   匹配 `AlertRule`，若超过阈值，则触发通知 (Log/Email)。
