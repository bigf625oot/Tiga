# Tiga Backend Documentation

> **Project**: Tiga
> **Version**: 1.0.0
> **Last Updated**: 2026-02-24

欢迎查阅 Tiga 后端文档库。本文档库旨在为开发者、运维人员和集成方提供全面、结构化的技术指引。

## 📚 文档目录 (Table of Contents)

### 1. 架构设计 (Architecture)

*   [工作流架构 (Workflow)](modules/workflow/architecture.md): 详解基于 Agno 的 Agent 工作流机制。
*   [重构提案 (Refactoring Proposal)](architecture/refactoring_proposal.md): 关于系统重构的设想与规划。

### 2. 核心模块 (Modules)

#### 2.1 任务模式 (Task Mode)
*   [API 参考文档](modules/task_mode/api_reference.md): 任务管理、QA、日志、备份等接口说明。
*   [运维指南](modules/task_mode/ops_guide.md): 日常运维操作手册。
*   [性能报告](modules/task_mode/perf_report.md): 性能基准测试结果。
*   [数据库设计](modules/task_mode/db_schema.md): 数据持久化方案。

#### 2.2 沙箱环境 (Sandbox)
*   [测试方案](modules/sandbox/test_scheme.md): 沙箱安全与功能测试计划。

#### 2.3 Agent 系统
*   [自检方案](modules/agent/self_check.md): Agent 健康检查与自愈机制。

### 3. 第三方集成 (Integration)

#### 3.1 MinerU (文档解析)
*   [集成方案](integration/mineru/integration_plan.md): MinerU PDF 解析引擎集成技术方案。
*   [实施待办](integration/mineru/todo_list.md): 集成实施 Checklist。

#### 3.2 E2B (云沙箱)
*   [集成报告](integration/e2b/integration_report.md): E2B 沙箱集成验证报告。

#### 3.3 Agno (Agent 框架)
*   [集成检查单](integration/agno/checklist.md): Agno 框架集成关键点检查。

### 4. 资源与模板 (Resources)

*   [文档模板](templates/DOC_TEMPLATE.md): 编写新文档的标准模板。

## 🛠️ 贡献指南 (Contribution)

1.  **新增文档**: 请复制 `templates/DOC_TEMPLATE.md` 并按需修改。
2.  **命名规范**: 使用 `模块名/功能_版本.md` 或 `模块名/功能.md` 的格式。
3.  **格式要求**: 统一使用 Markdown，代码块需指定语言。
4.  **更新索引**: 新增文档后，请同步更新本 `README.md`。

## 📅 更新日志 (Global Changelog)

| 日期 | 变更内容 | 维护人 |
| :--- | :--- | :--- |
| 2026-02-24 | 文档库重构，建立模块化目录结构 | Tiga Agent |
