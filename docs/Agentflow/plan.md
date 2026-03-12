# Agentflow 实施计划

## 1. 阶段一：基础架构搭建

### 1.1 数据模型定义 (Database Schema)
- [ ] 创建 `WorkflowDefinition` 表：存储工作流的 JSON 定义。
- [ ] 创建 `WorkflowSession` 表：存储会话状态、当前步骤、变量。
- [ ] 创建 `StepExecutionRecord` 表：存储每一步的执行日志。

### 1.2 核心执行引擎 (Core Engine)
- [ ] 实现 `WorkflowEngine` 类：负责加载定义、初始化 Session。
- [ ] 实现 `StepExecutor` 抽象基类。
- [ ] 实现 `AgentExecutor`：集成现有的 `AgnoAgent`。
- [ ] 实现 `FunctionExecutor`：集成基础工具函数。

### 1.3 基础流程控制
- [ ] 实现简单的线性流程执行。
- [ ] 实现步骤间的参数传递 (Input Mapping)。
- [ ] 实现基本的错误捕获 (Try/Catch)。

## 2. 阶段二：高级功能扩展

### 2.1 人机交互 (HITL)
- [ ] 扩展 `StepDefinition` 支持 `hitl_config`。
- [ ] 修改 `WorkflowEngine` 支持暂停 (`pause`) 和恢复 (`resume`)。
- [ ] 实现 `POST /resume` 接口。

### 2.2 复杂流程控制
- [ ] 实现条件分支 (`ConditionNode`)。
- [ ] 实现并行执行 (`ParallelNode` - 可选)。
- [ ] 实现循环控制 (`LoopNode` - 可选)。

### 2.3 重试机制与健壮性
- [ ] 集成 `tenacity` 库实现重试策略。
- [ ] 完善错误处理策略 (`stop`, `skip`, `retry`)。

## 3. 阶段三：集成与优化

### 3.1 前端集成
- [ ] 更新 `AgentFlowEditor` 以支持配置 HITL 和高级属性。
- [ ] 更新执行状态展示组件，实时显示步骤进度。

### 3.2 性能优化
- [ ] 引入 Redis 缓存 Session 状态。
- [ ] 优化大文件/Artifacts 的处理。

### 3.3 测试与验证
- [ ] 编写单元测试覆盖核心引擎逻辑。
- [ ] 编写集成测试验证完整流程。
- [ ] 进行压力测试。

## 4. 详细任务清单 (To-Do List)

### Backend
- [ ] Define SQLAlchemy models for Workflow & Session.
- [ ] Implement `WorkflowService` for CRUD operations.
- [ ] Implement `WorkflowEngine.run()` method.
- [ ] Implement `WorkflowEngine.resume()` method.
- [ ] Create API endpoints in `backend/app/api/endpoints/workflows.py`.

### Frontend
- [ ] Add "Wait for Input" node type in Editor.
- [ ] Add Execution Log viewer.
- [ ] Add Resume button in UI.
