# Pathway ETL 开发计划 - 阶段 6 (外部集成与服务化)

## 1. 概览 (Overview)
在完成基础的 ETL 能力 (Phase 1-3) 和 可视化编辑器 (Phase 4-5) 后，本阶段旨在打破数据孤岛，将 ETL 流水线从封闭的“处理工具”转变为开放的“数据服务”。
本阶段将重点实现：数据即服务 (DaaS)、自动化触发器 (Webhook) 和 智能调度集成。

## 2. 核心功能 (Core Features)

### 2.1 API 生成器 (Data as a Service)
将 Pipeline 的输出结果自动封装为标准 RESTful API，供外部系统消费。
- [ ] **API 配置节点**:
    *   新增 Sink 类型 `API Endpoint`。
    *   配置项：Endpoint Path (如 `/api/v1/data/sales`), Auth Method (API Key/JWT), Rate Limit。
- [ ] **动态路由注册**:
    *   后端根据 Pipeline 配置，动态注册 FastAPI 路由。
    *   实现通用的查询接口 (Filter, Pagination)。
- [ ] **API 网关集成 (可选)**:
    *   如果系统复杂，考虑集成 Kong 或 Nginx 转发。

### 2.2 Webhook 触发器 (Event-Driven)
允许外部系统通过 HTTP 请求触发流水线运行，实现事件驱动的 ETL。
- [ ] **Webhook Source**:
    *   新增 Source 类型 `Webhook`。
    *   功能：接收 POST 请求 Payload 作为初始流数据。
- [ ] **签名验证**:
    *   支持 HMAC SHA256 签名验证，确保请求来源安全。

### 2.3 调度系统集成 (Scheduler)
集成专业任务调度器，支持复杂的定时任务。
- [ ] **Cron 调度**:
    *   在 Pipeline 属性中增加 `Schedule` 配置 (如 `0 0 * * *`)。
    *   集成 `APScheduler` 或 `Celery Beat`。
- [ ] **依赖调度**:
    *   支持 Pipeline 之间的依赖 (Pipeline B 在 Pipeline A 成功后运行)。

### 2.4 通知与告警 (Notifications)
- [ ] **通知通道**:
    *   集成 Email (SMTP), Slack (Webhook), 钉钉/飞书 (Webhook)。
- [ ] **告警规则**:
    *   配置规则：运行失败、处理延迟 > 10s、数据量 < 预期。

## 3. 执行计划 (Execution Plan)

### 3.1 后端开发
- [ ] **Webhook Listener**: 实现 `POST /hooks/{pipeline_id}` 接收外部数据。
- [ ] **API Generator**: 实现动态路由挂载逻辑 (`app.include_router` 动态调用或基于 DB 的路由分发)。
- [ ] **Scheduler Service**: 启动独立的调度进程。

### 3.2 前端开发
- [ ] **调度配置面板**: 在编辑器右侧属性栏增加“调度设置” Tab。
- [ ] **API 管理页面**: 展示已发布的 API 列表、调用次数、文档 (Swagger)。
- [ ] **告警配置**: 在“系统设置”中配置通知渠道。

## 4. 场景示例
*   **场景 A (API 服务)**: 清洗每日销售数据 -> 存入 Redis -> 自动生成 `GET /api/sales/daily` 供报表系统调用。
*   **场景 B (Webhook)**: GitHub Webhook (Push Event) -> 触发代码分析流水线 -> 结果存入图数据库。
*   **场景 C (定时任务)**: 每晚 2 点从 FTP 拉取 CSV -> 增量更新到数据仓库。
