# 任务模式数据持久化：性能测试报告

## 测试目标
- 高并发读写：读写混合压测
- 响应时间：目标 p95 < 200ms（在合理部署条件下）

## 测试方法
- 工具：`backend/scripts/benchmark_task_mode.py`
- 请求组合（循环）：
  - 读取任务详情：`GET /task-mode/tasks/{id}`
  - 读取版本列表：`GET /task-mode/tasks/{id}/versions`
  - 写入问答：`POST /task-mode/tasks/{id}/qas`
  - 读取问答列表：`GET /task-mode/tasks/{id}/qas`

## 运行方式
1. 启动后端服务（建议生产配置近似：PostgreSQL + Redis）
2. 执行脚本：
   - `python backend/scripts/benchmark_task_mode.py`

## 指标输出
脚本输出样例：
```
count=800 p50_ms=12.34 p95_ms=45.67 p99_ms=80.12
```

## 优化点说明
- 索引：覆盖 `task_id / user_id / created_at / expires_at` 等高频过滤字段
- 缓存：任务详情、列表查询、版本/问答/日志列表加入 TTL 缓存（Redis 可选，自动降级）
- 写放大控制：任务更新单事务写入 `tasks + task_versions + task_logs`，减少跨请求不一致

## 结论与建议
- SQLite：适合单机/轻量并发；高并发写入会受锁限制
- PostgreSQL：建议用于生产与高并发场景
- Redis：建议启用以提升热点任务的读取性能

