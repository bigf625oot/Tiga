# EAH Agent 架构重构计划 (4阶段)

## 目标
将 `eah_agent` 系统从基于 Handler 的脚本式架构升级为模块化、组件化的 Executor-Engine 架构，同时保留轻量级的 `FastExecutor` 以保障低延迟场景的性能。

## Phase 1: 基础设施与核心抽象建设 (基建期) - [x] Completed
- [x] 1.1 创建目录结构：在 `eah_agent/core/` 下新建 `executors/` 和 `components/`。
- [x] 1.2 定义核心组件接口：在 `components/` 中定义 `StateManager`, `MemoryManager`, `PlanValidator`, `ExperienceStore`, `ToolRegistry` 的接口及基础实现。
- [x] 1.3 编写基础执行器：在 `executors/` 中实现 `BaseExecutor` (重度闭环基类) 和 `LightBaseExecutor` (轻量级基类，去除复杂反思和规划)。
- [x] 1.4 重构路由层：将 `agent_control_plane.py` 的核心逻辑提取并重构为 `ModeRouter`，支持“快慢思考”的动态路由（保留对旧版 Handler 的兼容）。

## Phase 2: 共享引擎层开发 (核心逻辑剥离) - [x] Completed
- [x] 2.1 规划引擎 (PlanningEngine)：重构 `agent_planner.py` 逻辑。
- [x] 2.2 执行引擎 (ExecutionEngine)：统一工具调用执行逻辑。
- [x] 2.3 评估引擎 (EvaluationEngine)：引入 LLM 结果打分/规则校验。
- [x] 2.4 反思引擎 (ReflectionEngine)：错误日志捕获，经验提取并写入 `ExperienceStore`。

## Phase 3: 执行器实现与业务迁移 (业务迁移期) - [x] Completed
- [x] 3.1 迁移 Quick 模式：将 `quick_handler.py` 升级为 `FastExecutor` (继承 `LightBaseExecutor`)。
- [x] 3.2 迁移 Plan 模式：将 `plan_handler.py` 升级为 `SingleExecutor` (接入四大引擎)。
- [x] 3.3 迁移 Team 模式：升级 `team_handler.py` 为 `TeamExecutor`。
- [x] 3.4 迁移 Workflow 模式：升级 `flow_handler.py` 为 `WorkflowExecutor`。
- [x] 3.5 标记废弃：将原 `handlers/` 目录下的代码标记为 `@deprecated`。

## Phase 4: 全链路联调与切量验证 (灰度发布期) - [x] Completed
- [x] 4.1 自动化测试回归：运行 `秒懂-全链路测试套件.json`。
- [x] 4.2 灰度发布：在 `ModeRouter` 增加灰度开关。
- [x] 4.3 性能基准测试：重点验证 `FastExecutor` 的 TTFT (首字延迟) 不高于旧版。
- [x] 4.4 全量切换与清理：下线旧路由，删除旧 Handler。

## Phase 5: 组件实现与代码清理 (全量整理期) - [x] Completed
- [x] 5.1 实现缺失的核心组件：补充 `StateManager`, `PlanValidator`, `ExperienceStore`, `ToolRegistry` 的默认实现类。
- [x] 5.2 将组件依赖注入各个 Executor (`SingleExecutor`, `TeamExecutor` 等) 中。
- [x] 5.3 梳理 `eah_agent` 目录：删除不再使用的遗留文件 (如旧的 orchestrator、旧的 workflows 等，视依赖分析而定)。
- [x] 5.4 修复全链路测试套件：确保在完全切换为新架构并移除旧文件后，测试依然能跑通。

## Phase 6: 全局深层目录代码审查与清理 (全局体检期) - [x] Completed
- [x] 6.1 审查 `team/` 目录：排查是否残留与旧 `TeamHandler` 绑定的冗余配置。
- [x] 6.2 审查 `workflows/` 目录：排查旧版 DAG 引擎的冗余代码（之前清理了 dynamic，需检查 base 和 helper）。
- [x] 6.3 审查 `handlers/` 目录残余：确保之前的删除操作没有漏网之鱼。
- [x] 6.4 审查全局引用：使用 `grep` 排查是否还有代码在尝试 import 已经删除的文件（如 `quick_handler`, `plan_handler`, `nexus_executor` 等）。

| 阶段 | 遇到的问题 | 解决方案 |
|---|---|---|
| | | |
