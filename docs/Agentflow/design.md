# Agentflow 核心设计文档

## 1. 概述
本文档旨在设计 `Agentflow` 的核心执行引擎，以支持 `case.md` 中描述的完整流程流转机制。该引擎将支持灵活的工作流定义、步骤执行、人机交互（HITL）、重试机制及错误处理。

## 2. 核心概念与数据结构

### 2.1 WorkflowDefinition (工作流定义)
描述工作流的静态结构。
```python
class WorkflowDefinition(BaseModel):
    id: str
    name: str
    steps: List[StepDefinition]
    connections: List[ConnectionDefinition] # 定义步骤间的流转关系
    input_schema: Dict[str, Any] # 输入参数定义
    output_schema: Dict[str, Any] # 输出结果定义
```

### 2.2 StepDefinition (步骤定义)
描述单个步骤的配置。
```python
class StepDefinition(BaseModel):
    id: str
    type: str # "agent", "team", "function", "start", "end", "condition"
    name: str
    config: Dict[str, Any] # 步骤特定配置 (例如 agent_id, prompt_template)
    input_mapping: Dict[str, str] # 输入参数映射 (例如 {"query": "{{previous_step.output}}"})
    retry_policy: Optional[RetryPolicy]
    on_error: str = "stop" # "stop", "skip", "retry"
    hitl_config: Optional[HITLConfig] # 人机交互配置
```

### 2.3 WorkflowSession (会话状态)
持久化存储工作流的执行状态。
```python
class WorkflowSession(BaseModel):
    session_id: str
    workflow_id: str
    status: str # "running", "paused", "completed", "failed"
    current_step_id: Optional[str]
    variables: Dict[str, Any] # 全局变量
    history: List[StepExecutionRecord] # 执行历史
    created_at: datetime
    updated_at: datetime
```

### 2.4 RunContext (运行上下文)
单次运行时的内存上下文，包含临时数据。
```python
class RunContext(BaseModel):
    session_id: str
    step_inputs: Dict[str, StepInput]
    step_outputs: Dict[str, Any]
    artifacts: List[Artifact] # 图片/视频/文件
    stop_flag: bool = False
```

### 2.5 StepInput (步骤输入)
标准化每个步骤的输入。
```python
class StepInput(BaseModel):
    input_data: Any # 原始输入或映射后的数据
    previous_step_output: Any # 上一步的输出
    context_variables: Dict[str, Any] # 全局上下文变量
    media_resources: List[MediaResource] # 媒体资源
```

## 3. 执行引擎架构

### 3.1 WorkflowEngine
负责调度和执行工作流。

```python
class WorkflowEngine:
    def __init__(self, session_store, executor_factory):
        self.session_store = session_store
        self.executor_factory = executor_factory

    async def run(self, session_id: str, input_data: Any = None) -> WorkflowRunOutput:
        # 1. 加载/初始化 Session
        session = await self.session_store.get(session_id)
        context = self._initialize_context(session, input_data)

        # 2. 步骤遍历与执行
        while not context.stop_flag and session.current_step_id:
            step_def = self._get_step_def(session.workflow_id, session.current_step_id)
            
            # 3. 准备 StepInput
            step_input = self._prepare_step_input(step_def, context)
            
            # 4. 检查 HITL
            if self._check_hitl(step_def, session):
                session.status = "paused"
                await self.session_store.save(session)
                return WorkflowRunOutput(status="paused", message="Waiting for user input")

            # 5. 执行步骤
            try:
                executor = self.executor_factory.get_executor(step_def.type)
                result = await self._execute_with_retry(executor, step_def, step_input)
                
                # 6. 结果收集与状态更新
                context.step_outputs[step_def.id] = result
                session.history.append(StepExecutionRecord(step_id=step_def.id, output=result))
                
                # 7. 决定下一步
                session.current_step_id = self._determine_next_step(step_def, result)
                
            except Exception as e:
                if step_def.on_error == "stop":
                    session.status = "failed"
                    raise e
                # 处理其他错误策略...

        # 8. 完成
        session.status = "completed"
        await self.session_store.save(session)
        return WorkflowRunOutput(status="completed", outputs=context.step_outputs)
```

### 3.2 Executor 体系
支持多态执行器。

- **AgentExecutor**: 调用单个 Agent (如 `AgnoAgent`)。
- **TeamExecutor**: 协调多个 Agent 协作。
- **FunctionExecutor**: 执行本地 Python 函数或工具。

## 4. 关键功能详细设计

### 4.1 步骤输入映射 (Input Mapping)
支持使用模板语法 (如 Jinja2 或简单的 `{{variable}}`) 从 `context.step_outputs` 或 `session.variables` 中提取数据作为当前步骤的输入。

### 4.2 人机交互 (HITL)
- **配置**: 在 `StepDefinition` 中标记 `requires_confirmation` 或 `input_schema`。
- **暂停**: 引擎遇到 HITL 标记时，将 Session 状态置为 `paused` 并返回。
- **恢复**: 用户调用 `resume_workflow(session_id, input_data)`，引擎更新当前步骤输入并继续执行。

### 4.3 重试机制
- **策略**: 固定间隔、指数退避。
- **实现**: 在 `_execute_with_retry` 方法中封装 `tenacity` 或自定义循环逻辑。

### 4.4 结果收集
- 所有步骤的输出默认存储在 `context.step_outputs` 字典中，键为 `step_id`。
- 最终输出可由 `End` 节点配置模板来聚合生成。

## 5. 接口设计

### 5.1 启动工作流
`POST /api/v1/workflows/{workflow_id}/run`
```json
{
  "input": { ... }
}
```

### 5.2 恢复工作流
`POST /api/v1/workflows/{workflow_id}/sessions/{session_id}/resume`
```json
{
  "step_id": "step_123",
  "input": { "approval": true, "feedback": "..." }
}
```

### 5.3 获取执行状态
`GET /api/v1/workflows/sessions/{session_id}`

## 6. 数据存储方案
- **Database**: PostgreSQL (存储定义、Session 元数据、历史记录)。
- **Object Storage**: S3/MinIO (存储大文件、Artifacts)。
- **Cache**: Redis (可选，用于高频状态访问)。
