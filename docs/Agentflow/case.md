1.完整的流程流转机制
用户请求
    ↓
Workflow.run(input="...")
    ↓
[初始化]
- 创建 session_id
- 加载/创建 WorkflowSession
- 准备 RunContext
    ↓
[步骤准备]
- 遍历 steps 列表
- 为每个 step 创建 StepInput
- StepInput 包含：
  - input: 原始输入
  - previous_step_content: 上一步输出
  - previous_step_outputs: 所有之前步骤输出
  - images/videos/audio/files: 媒体资源
    ↓
[步骤执行]
for step in steps:
    - 检查 HITL（确认/输入）
    - 如果需要确认 → 暂停 → return
    - 否则继续执行
    ↓
    执行 step.execute()
    - 根据 executor 类型调用：
      * Agent → agent.run()
      * Team → team.run()
      * Function → function()
    - 应用 max_retries 重试逻辑
    - 处理异常（on_error 决策）
    ↓
[结果收集]
- 收集 step_output
- 更新 previous_step_outputs
- 累积 images/videos/audio/files
- 检查 step.stop 标志
- 如果 stop=True → 终止后续步骤
    ↓
[完成]
- 返回 WorkflowRunOutput
- 包含 content, metrics, step_results
- 保存到 WorkflowSession
