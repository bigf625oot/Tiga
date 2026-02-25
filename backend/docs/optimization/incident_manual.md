# 故障应急手册 (Fault Emergency Manual)

## 1. 概述
本手册旨在提供针对 Tiga 系统常见故障的快速诊断与恢复流程，确保 RTO (Recovery Time Objective) < 5 分钟。

## 2. 故障等级定义

| 等级 | 描述 | 响应时间 | 通知对象 |
| :--- | :--- | :--- | :--- |
| **P0** | 系统完全不可用，核心业务中断 | < 5分钟 | CTO, 运维负责人, 全员 |
| **P1** | 核心功能受损 (如: 智能体响应极慢) | < 15分钟 | 技术总监, 对应开发组 |
| **P2** | 非核心功能异常 (如: 报表导出失败) | < 1小时 | 对应开发组 |
| **P3** | 轻微 Bug (如: UI 样式问题) | < 24小时 | 客服, 测试 |

## 3. 常见故障诊断流程

### 3.1 智能体无响应 (Agent Timeout)
**现象**: API 返回 504 Gateway Timeout，或前端一直在 Loading。

**诊断步骤**:
1.  **检查 Pod 状态**:
    ```bash
    kubectl get pods -n tiga-system -l app=tiga-agent
    ```
    - 若状态为 `CrashLoopBackOff` -> 查看日志 `kubectl logs <pod_name>`。
    - 若状态为 `Running` 但无响应 -> 进入 Pod `curl localhost:8000/health`。

2.  **检查资源使用率**:
    - 查看 Grafana 面板，确认 CPU/Memory 是否飙升。
    - 若 OOM Killed -> 临时扩容 (HPA) 或增加 Request/Limit。

3.  **检查依赖服务**:
    - Redis 是否连接正常？
    - Vector DB 是否响应？
    - LLM Provider (OpenAI/DeepSeek) 是否有 Outage？

**恢复措施**:
- **重启服务**: `kubectl rollout restart deployment tiga-agent -n tiga-system`
- **降级**: 切换到备用 LLM 模型。

### 3.2 任务队列积压 (Queue Backlog)
**现象**: 用户提交任务后长时间处于 `PENDING` 状态。

**诊断步骤**:
1.  **查看 Redis 队列长度**:
    ```bash
    redis-cli LLEN task_queue
    ```
2.  **检查 Worker 状态**:
    - Worker 是否存活？
    - Worker 日志是否有大量报错？

**恢复措施**:
- **水平扩容**: 增加 Worker 副本数。
  ```bash
  kubectl scale deployment tiga-worker --replicas=10 -n tiga-system
  ```
- **清空死信队列**: 若因特定毒丸任务导致阻塞，手动清理。

### 3.3 数据库连接耗尽 (DB Connection Pool Exhausted)
**现象**: API 报错 `FATAL: remaining connection slots are reserved for non-replication superuser roles`.

**诊断步骤**:
1.  **查看当前连接数**:
    ```sql
    SELECT count(*) FROM pg_stat_activity;
    ```
2.  **检查慢查询**:
    - 查看 `pg_stat_statements`。

**恢复措施**:
- **Kill 空闲连接**:
  ```sql
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';
  ```
- **重启应用**: 释放连接池。
- **启用 PgBouncer**: 增加连接池中间件。

## 4. 应急联系人
- **运维值班**: ops@tiga.ai (Phone: +86-138-xxxx-xxxx)
- **后端负责人**: backend@tiga.ai
- **DBA**: dba@tiga.ai
