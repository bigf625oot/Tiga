# Pathway ETL 生产化改造方案

## 1. 当前痛点分析
目前 Pathway 的引擎实现是强依赖内存的 `engine.active_jobs` 字典。这意味着：
- 如果启动了多个 API Worker（比如 gunicorn 起 4 个 worker），在 Worker A 启动的作业，Worker B 通过 `/status` 接口查不到，会错误地返回 stopped。
- 服务重启后，即使后台的 Python 子进程还在跑，内存里的 `active_jobs` 也会丢失，导致失去对作业的控制权（成为孤儿进程）。
- 无法实现跨节点的负载均衡，所有请求都会在当前 API 节点直接 fork 子进程。

## 2. 目标架构
要实现生产级别的可靠性，必须将**调度下发**、**状态维护**和**实际执行**解耦，并接入系统已有的异步任务体系。

### 2.1 状态持久化为王
- 废弃 `PathwayEngine` 中使用 `self.active_jobs` 维护状态的做法。
- 所有状态判断必须基于数据库（`PathwayJob.status`）+ OS 级别探活（`kill -0 pid` 或 `psutil`，辅以 hostname/worker_id 校验）。
- 只有这样，API 节点才可以无状态扩展。

### 2.2 借助 TaskStream / Celery 下发
- 用户在 API 调用 `/pipelines/{id}/run` 时，**不再直接 `engine.start_job()`**。
- 而是组装一个 Task（类型如 `pathway_etl_run`），写入 Redis Stream (`task_stream`) 或 `celery`。
- API 立即返回 200/Accepted，并告知任务已进入队列。

### 2.3 专职 Worker 消费与执行
- `AsyncTaskWorkerPool` 或专用的 ETL Worker 从 Stream 中消费任务。
- Worker 拿到任务后，在自己所在的节点执行 `multiprocessing.Process`（也就是目前的 `_run_dag`）。
- **关键**：Worker 在启动子进程后，必须将 `pid` 和自己所在机器的标识（如 `hostname` 或 `worker_id`）更新到数据库的 `pathway_jobs` 表中。

### 2.4 状态同步与上报 (TaskEvent)
- **定期心跳**：Worker 需要起一个协程，定期（如每 5 秒）使用 `psutil` 检查自己拉起的 Pathway 子进程是否还活着，并收集指标（如 CPU、内存、Pathway 的 `/metrics`）。
- **统一上报**：通过现有的 `TaskProgress` 机制（`TaskEvent`）向中心汇报状态。前端可以通过 WebSocket 实时收到这些事件。
- **异常捕获**：如果子进程退出，Worker 负责获取 exitcode，将最终状态写回 DB，并 ack 这条任务。

### 2.5 孤儿进程与故障恢复 (Failover)
- 场景：Worker A 拉起了进程 P1，然后 Worker A 所在机器断电宕机。
- 此时数据库里记录该作业还在 RUNNING，由 Worker A 负责。
- **机制**：需要一个全局的 Scheduler（可以复用已有的 `app.services.ops.task.scheduler`），定期扫描数据库中长期未更新心跳的 RUNNING 作业。
- 发现后，将其状态重置为 FAILED（或重新派发）。

## 3. 实施步骤拆解

### 步骤 1: 改造 PathwayEngine (去内存化)
1. 修改 `app/services/ops/pipeline/core/engine.py`。
2. 移除 `self.active_jobs`。
3. `start_job` 只负责 `multiprocessing.Process(...).start()`，并返回 `pid`，不维护生命周期。
4. `stop_job` 改为接收 `pid`（如果支持跨节点，可能需要 RPC，但目前假设先做单机/同节点）。

### 步骤 2: 接入 TaskEngine / TaskStream
1. 在 `app/services/platform/task_engine/adapters/pathway.py` 中，完善 `PathwayAdapter`。
2. 确保它可以像普通任务一样，被放入执行队列。

### 步骤 3: 重构 API 层
1. `routes.py` 中的 `run_pipeline` 接口，改为调用任务下发逻辑，而不是直接 `engine.start_job`。
2. 接口响应体调整为包含 `task_id`。

### 步骤 4: Worker 侧执行与监控循环
1. 编写专门的 Worker 消费逻辑（或者在现有的 AsyncTaskWorkerPool 中注册 handler）。
2. Worker 收到任务 -> 查 DB 获取配置 -> 构建 DAG -> `engine.start_job` 拿到 PID -> 写 DB。
3. Worker 进入 `while True` 循环，监控 PID 状态 -> 调用 `emit_event` 更新进度 -> 直到进程结束。

### 步骤 5: 故障清理任务
1. 在系统启动时或定时任务中，清理属于本节点（基于 hostname）但实际不存在的 PID 对应的 DB 记录。
