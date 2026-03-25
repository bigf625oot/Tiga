# EAH Agent 架构重构 - 核心发现与记录

## 核心设计原则
1. **保留 Quick Agent 的轻量级特性 (Fast Track)**
   - 痛点：完整的 "规划-执行-评估-反思" 闭环会引入显著的延迟 (TTFT)。
   - 方案：引入 `LightBaseExecutor` 和 `FastExecutor`，旁路掉规划和反思组件，仅保留基础的上下文组装和模型调用（支持 Function Calling）。
   
2. **状态与记忆解耦**
   - 痛点：当前 `agent_base_handler.py` 和 `agent_control_plane.py` 内部硬编码了历史记录的获取与压缩。
   - 方案：使用 `MemoryManager` 统一管理历史和图谱记忆；使用 `StateManager` 追踪任务的多步执行状态。

3. **引擎共享 (Engines)**
   - 痛点：目前 `plan_handler` 和 `team_handler` 等各自维护了部分相似的执行逻辑。
   - 方案：将具体的业务动作抽离为 `PlanningEngine`, `ExecutionEngine`, `EvaluationEngine`, `ReflectionEngine`。所有 Heavy Executor 均依赖这些底层引擎。

## 现有代码映射
- 入口层：`agent_control_plane.py` -> 需演进为 `ModeRouter`。
- 基类层：`agent_base_handler.py` -> 需演进为 `BaseExecutor` / `LightBaseExecutor` 配合五大 Components。
- 业务层：`handlers/quick_handler.py` -> `FastExecutor`。
- 业务层：`handlers/plan_handler.py` -> `SingleExecutor`。
