1. 核心架构模式：协调者-执行者 (Coordinator-Worker)
Claude Code 的团队模式并非简单的并行运行，而是一个典型的三层编排体系：[2]
协调者 (Coordinator)： 顶层逻辑。负责接收用户的宏观目标（Goal），将其拆解为细粒度的任务（Tasks），并进行动态调度。[3]
执行者 (Workers/Sub-Agents)： 底层逻辑。多个独立的 Claude 实例作为工人，每个工人通常拥有受限的工具集（Restricted Toolset），在隔离的环境（如独立的 Git 工作树）中执行具体任务。
团队管理层 (Teams)： 负责维护整个作业流的状态、权限分配和结果汇总。
1. 通信与协作机制
为了让多个 Agent 像团队一样工作，架构中设计了精密的中间件：
信箱系统 (Mailbox System)： 采用异步消息总线（Message Bus）机制。每个 Agent 都有自己的信箱，通过发送消息来请求协作或传递执行结果。
原子认领机制 (Atomic Claim Mechanism)： 在处理任务队列时，使用原子操作确保同一个任务不会被多个 Agent 同时抢占，避免资源竞争。
权限信箱模式 (Permission Mailbox Pattern)： 这是一个安全设计。当 Worker 需要执行高危操作（如删除文件或执行 Bash 脚本）时，请求会发送到权限信箱，由 Coordinator 或人类用户审批。
1. 任务调度与依赖处理[3][4][5]
拓扑依赖解析 (Topological Dependency Resolution)： 任务不是乱序执行的。架构中包含一个 TaskQueue，能够识别任务间的依赖关系（例如：必须先写好接口定义，才能写实现类），并按拓扑顺序调度。
并发控制： 代码显示其支持根据机器性能和 Token 预算动态调整并行 Worker 的数量。
1. 共享记忆系统 (Shared Team Memory)
为了解决长对话下的上下文爆炸问题，团队模式采用了三层压缩架构：
团队级共享内存： 记录项目的全局状态、已完成的任务摘要和发现的约束条件（如 CLAUDE.md 中的规范）。
上下文压缩 (Context Compaction)：
MicroCompact： 局部清理，删除冗余的工具调用记录。
AutoCompact： 自动摘要，当上下文接近极限时进行总结。[1][6]
Full Compact： 紧急压缩，仅保留最核心的任务状态和代码片段。
1. 隔离与安全性
独立工作树 (Isolated Git Worktrees)： 泄露的代码显示，为了防止多个 Agent 同时修改同一份文件导致冲突，系统会为每个 Worker 创建临时的 Git worktree。
沙箱机制： 工具执行（尤其是 BashTool）运行在受限的进程中，且所有写操作都有多层审批流拦截。