# 团队模式 (Team Mode) 架构差异分析与改造计划

## 1. 现状与需求差异分析

在审视当前代码（以 `TeamExecutor` 和 `AgentFactory` 为核心）与 `team.md` 描述的理想架构后，可以发现两者的实现细节差异巨大。当前代码仅仅是基于底层 LLM 框架（Agno）原生多智能体能力的一层薄封装，并未实现真正的分布式工程化团队协作。

### 具体差异对比

| 架构特性 | `team.md` 目标需求 | 当前代码库实现 (`TeamExecutor` 等) | 差异度 |
|---------|-------------------|-----------------------------------|--------|
| **核心架构** | 协调者-执行者 (Coordinator-Worker) 模式，独立的任务拆解和分发系统。 | 依赖 Agno 框架自带的 `Agent.team` 机制，TeamLeader 仅通过系统 Prompt 指导分发。 | 🔴 极高 |
| **通信机制** | 信箱系统 (Mailbox System)、异步消息总线。 | 无信箱机制。直接通过大模型底层 Tool Call (如 `transfer_task`) 进行阻塞式同步调用。 | 🔴 极高 |
| **任务认领** | 原子认领机制 (Atomic Claim)，防并发竞争。 | 缺失。无任务队列，无并发执行者抢占概念。 | 🔴 极高 |
| **安全与权限** | 权限信箱模式 (Permission Mailbox)，敏感操作（Bash等）拦截并需审批。 | 缺失。Developer 直接挂载 E2B 沙箱，无审批流和拦截机制。 | 🔴 极高 |
| **任务调度** | 基于 TaskQueue 的拓扑依赖解析 (Topological Dependency)，支持并发。 | 缺失。任务执行由 LLM 自行决定顺序（黑盒流转）。 | 🔴 极高 |
| **上下文管理** | 团队共享记忆、三层压缩架构 (MicroCompact, AutoCompact, FullCompact)。 | 仅有全局维度的 `ContextCompressor` (超过阈值统一压缩)，无细粒度的 Micro/Full 机制。 | 🟡 中高 |
| **隔离性** | 独立的 Git Worktrees，防止并发文件读写冲突。 | 缺失。仅为 Developer 提供统一的 E2B 容器，未在代码/工作区层面做多 Worker 隔离。 | 🔴 极高 |

---

## 2. 改造范围与受影响模块

要实现 `team.md` 中的设计，需要从**控制流、通信总线、执行沙箱、上下文管理**四个维度进行深度的重构，这几乎意味着要重写 `TeamExecutor` 并引入一套全新的调度引擎。

### 受影响的主要模块
1. **执行引擎层 (`app/services/agent/executors/team_executor.py`)**：
   - 需废弃现有的直接调用 `team_agent.arun()` 的方式。
   - 引入新的 `Coordinator` 引擎，专门负责大任务拆解和状态机维护。
2. **任务与调度层 (`app/core/queue.py`, 新增 `app/services/agent/orchestration/task_graph.py`)**：
   - 需要引入有向无环图（DAG）的任务解析器。
   - 需要实现支持拓扑排序的 `TaskQueue`。
3. **通信与总线层 (新增 `app/services/agent/communication/mailbox.py`)**：
   - 实现基于 Redis Pub/Sub 或 Stream 的 `Mailbox` 和 `Permission Mailbox`。
4. **上下文与记忆层 (`app/services/agent/components/memory_manager.py`)**：
   - 重构记忆压缩逻辑，引入 `MicroCompact`（针对冗余工具调用）和 `FullCompact`（灾难性长度恢复）。
5. **安全与沙箱层 (`app/services/platform/sandbox/e2b_sandbox.py` 或相关 Sandbox 模块)**：
   - 增加对多 Git Worktree 的支持，隔离多个并发 Worker 的代码工作区。

---

## 3. 详细改造计划 (Phased Implementation Plan)

改造将分为 4 个主要阶段进行，确保系统平滑过渡。

### 阶段一：通信总线与任务队列基础建设 (Foundation)
**目标**：建立 Agent 间解耦的通信基础和支持依赖关系的任务队列。
- [ ] **1.1 信箱系统实现**：在 `app/core/` 下引入基于 Redis 的异步 Mailbox 机制，每个 Agent 实例分配独立 `mailbox_id`。
- [ ] **1.2 拓扑任务队列**：实现 `TopologicalTaskQueue`，支持定义任务前置依赖（如 Task B 依赖 Task A），并支持原子认领（基于 Redis Lua 脚本或 Redlock）。
- [ ] **1.3 权限信箱模式**：实现 `PermissionMailbox`，将高危 Tool (如文件删除、命令执行) 的请求路由至此，等待前端用户的 WebSocket 确认回调。

### 阶段二：Coordinator-Worker 编排引擎 (Orchestration)
**目标**：重写 `TeamExecutor`，实现真正的“计划-拆解-分发-汇总”工作流。
- [ ] **2.1 Coordinator 智能体**：移除原本的 `TeamLeader`，重构为独立的 `Coordinator`。它的主要职责变为：接收 Goal -> 生成 JSON 格式的任务 DAG 图 -> 写入 `TopologicalTaskQueue`。
- [ ] **2.2 Worker 生命周期**：改造 `AgentFactory`，不再使用 `leader_agent.team = members`，而是启动多个独立的 Worker 协程，持续监听 `TopologicalTaskQueue` 和各自的 Mailbox。
- [ ] **2.3 状态机同步**：Worker 完成任务后，向 Coordinator 发送包含摘要和产出物的 `TaskCompleted` 消息，Coordinator 更新团队全局状态。

### 阶段三：沙箱隔离与安全性增强 (Isolation)
**目标**：防止多 Worker 协作时的资源竞争和代码冲突。
- [ ] **3.1 独立 Git Worktree 机制**：在沙箱管理模块中，当 Worker 认领任务时，自动为主仓库 `git worktree add` 一个临时目录，Worker 的所有读写工具均限定在此目录下。
- [ ] **3.2 合并机制**：Coordinator 在验证 Worker 任务通过后，负责合并 Worktree 变更到主分支。

### 阶段四：共享记忆与三层上下文压缩 (Context Management)
**目标**：解决长时间协作的 Token 爆炸问题。
- [ ] **4.1 MicroCompact (微压缩)**：在 `memory_manager.py` 中增加 Hook，在单步任务完成后，清洗掉中间失败的重试记录或过长的工具输出，只保留结果。
- [ ] **4.2 AutoCompact (自动压缩)**：完善现有的 `ContextCompressor`，将其从 Executor 剥离，作为独立后台任务，在 Token 到达 80% 时自动提取摘要。
- [ ] **4.3 FullCompact (极限压缩)**：当 Token 超过 95% 时触发，丢弃所有对话细节，仅保留核心规范 (`CLAUDE.md`) 和项目全局 State。

## 4. 结论建议
当前的 Team 模式属于**"LLM原生代理层面的软协作"**，而 `team.md` 描述的是**"系统工程层面的硬协作"**。
建议优先实施 **阶段一** 和 **阶段二**，这两步是实现并发和可靠任务拆解的核心。在重构期间，可以通过 `ab_variant` 或新开一个 `mode="team_v2"` 来灰度验证新架构，避免破坏现有的业务流。
