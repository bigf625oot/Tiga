# 智能体执行器拓扑架构 (Agent Executors Topology)

基于双系统理论与微服务架构的执行器矩阵设计：

1. **FastExecutor (System 1 - Intuition)**: 
   - **定位**: O(1) 复杂度的旁路执行引擎。
   - **Trade-offs**: 牺牲重型规划与状态流转，换取极低延迟与零状态副作用。适用于确定性高频 QA。
2. **SingleExecutor (System 2 - Reasoning)**: 
   - **定位**: 基于有限状态机(FSM)的全生命周期(Plan-Execute-Evaluate-Reflect)执行引擎。
   - **Trade-offs**: 引入时间开销与重试成本，换取单体任务的高容错与闭环交付能力。
3. **TeamExecutor (Microservices Collaboration)**: 
   - **定位**: 基于 Actor 模型的动态拓扑协作网络。
   - **Trade-offs**: 引入节点间通信开销与不可预测性，通过降维打击解决跨域复杂问题。
4. **WorkflowExecutor (Deterministic DAG)**: 
   - **定位**: 基于 Kahn 拓扑排序的静态有向无环图(DAG)调度器。
   - **Trade-offs**: 彻底剥离 LLM 运行时规划的不确定性，实现 100% 流程可预测性，但丧失运行时自适应能力。