# Pathway ETL 生产化改造计划

## 目标
- 将当前 Pathway ETL 从“可跑的 Demo”升级为“可用于生产”的功能闭环：数据模型/迁移、CRUD、运行/停止/状态同步、任务中心适配、基础可观测性与错误处理。

## 范围与假设
- 以当前代码库的 FastAPI + SQLAlchemy + Alembic 为基线，不引入新的重量级基础设施（如 Celery）除非仓库已存在同类能力。
- 保持对开发模式（SQLite + create_all）的兼容，同时补齐 Alembic 迁移以支持生产。

## 阶段
### Phase 0：现状盘点（in_progress）
- 盘点现有 pipeline 引擎、CRUD、路由、任务中心适配器的真实能力与缺口
- 明确生产化最小闭环（MVP-Prod）

### Phase 1：数据模型与迁移（pending）
- PathwaySource / PathwayJob 模型完善：约束、索引、唯一性、可扩展字段（软删除/版本控制预留）
- Alembic 增量迁移：创建 pathway_sources、pathway_jobs（以及必要索引/约束）

### Phase 2：API 与业务逻辑闭环（pending）
- Sources：创建/列表/获取/更新/删除（含 secrets 加解密与字段校验）
- Pipelines：创建/列表/获取/更新/删除（软删除）、克隆、导入导出
- Run/Stop：与引擎交互、DB 状态与 pid 同步、失败错误落库

### Phase 3：任务中心适配器生产化（pending）
- PathwayAdapter：补齐 DAG 构建逻辑，避免空 nodes
- 监控与状态上报：RUNNING/STOPPED/FAILED 的稳定映射与降噪

### Phase 4：验证与回归（pending）
- 最小集成验证：启动、创建 source、创建 pipeline、run/stop、状态读取
- 必要单测/集成测试（按现有测试栈）

## 风险与对策
- 多 worker/多实例：内存中的进程表无法跨进程共享。对策：默认生产运行单 worker；中期改造为独立 worker 服务或基于现有任务系统的后台执行。
- pathway 依赖：引擎文件顶层依赖第三方包。对策：DB 模型与 CRUD 不依赖该包；运行时缺失时报出明确错误。

## 错误记录
| 时间 | 错误 | 组件 | 处理 |
|---|---|---|---|

