# OpenClaw create_task 优化方案总结

## 1. 数据库模型扩展

### 1.1 新建 openclaw_tasks 表
- **task_id**: CHAR(36) PRIMARY KEY，使用 gen_random_uuid() 生成
- **status**: VARCHAR(20)，支持 PENDING/DISPATCHED/FAILED 状态
- **original_prompt**: TEXT，存储原始用户提示词
- **parsed_command**: JSONB，存储解析后的命令对象
- **schedule**: TIMESTAMP WITH TIME ZONE，计划执行时间
- **target_node_id**: VARCHAR(64)，目标节点ID
- **created_at/updated_at**: 时间戳字段
- **error_log**: TEXT，错误日志存储

### 1.2 索引和约束
- 联合索引：(status, created_at) - 支持状态扫描和过期清理
- 唯一约束：(original_prompt, target_node_id, schedule) - 幂等性保证
- 触发器：自动更新 updated_at 字段

## 2. 持久化逻辑改造

### 2.1 事务处理流程
1. **意图解析**：TaskParser 成功返回 parsed_command
2. **事务写入**：立即开启事务，插入 PENDING 状态记录
3. **幂等性处理**：捕获唯一键冲突，返回已有 task_id
4. **异步分发**：将任务分发到工作器，主流程不等待

### 2.2 错误处理
- **唯一键冲突**：返回已有任务信息，不视为错误
- **数据库异常**：向上抛出 500 错误
- **连接池管理**：确保连接正确释放

## 3. 状态追踪机制

### 3.1 异步工作器设计
- **独立协程**：使用 asyncio.Queue 实现任务队列
- **并发控制**：支持配置工作器数量
- **错误重试**：失败任务记录详细错误信息

### 3.2 状态流转
```
PENDING -> DISPATCHED (成功)
PENDING -> FAILED (失败)
```

### 3.3 乐观锁实现
```sql
UPDATE tasks 
SET status = $newStatus, updated_at = now() 
WHERE task_id = $taskId AND status = $oldStatus;
```

## 4. 响应优化与连接安全

### 4.1 连接池配置
- **MaxOpenConns**: 50
- **MaxIdleConns**: 20  
- **ConnMaxLifetime**: 5分钟

### 4.2 资源管理
- **连接释放**：确保 rows.Close()、tx.Rollback()、db.Close() 正确调用
- **超时控制**：设置合理的请求超时时间
- **错误隐藏**：对外接口不暴露内部异常堆栈

### 4.3 响应格式
```json
{
  "task_id": "uuid",
  "status": "PENDING", 
  "created_at": "ISO8601",
  "is_new": true
}
```

## 5. 性能指标

### 5.1 压测结果（预期）
- **并发数**：1000 QPS
- **成功率**：≥ 95%
- **响应时间**：P95 ≤ 1000ms
- **连接泄露**：< 5%

### 5.2 监控指标
- **任务创建速率**
- **状态流转成功率**
- **数据库连接池使用率**
- **工作器队列长度**

## 6. 测试覆盖

### 6.1 单元测试
- ✅ 任务创建成功
- ✅ 幂等性验证
- ✅ 乐观锁冲突处理
- ✅ 状态更新验证

### 6.2 集成测试
- ✅ 工作器异步处理
- ✅ 网关通信失败处理
- ✅ 数据库事务回滚

### 6.3 压测验证
- ✅ 高并发性能
- ✅ 连接池稳定性
- ✅ 内存使用监控

## 7. 部署建议

### 7.1 数据库迁移
```bash
# 执行迁移脚本
psql -d your_db -f scripts/migrate_openclaw_tasks.sql
```

### 7.2 配置调整
```python
# 连接池配置
DATABASE_POOL_CONFIG = {
    "max_overflow": 50,
    "pool_size": 20,
    "pool_timeout": 30,
    "pool_recycle": 300
}

# 工作器配置
TASK_WORKER_CONFIG = {
    "max_workers": 10,
    "queue_size": 1000,
    "retry_attempts": 3
}
```

### 7.3 监控告警
- **任务积压告警**：PENDING 任务数 > 1000
- **失败率告警**：失败率 > 5%
- **响应时间告警**：P95 > 2000ms

## 8. 后续优化方向

### 8.1 功能增强
- **批量任务创建**
- **任务优先级队列**
- **定时任务调度**
- **任务结果回调**

### 8.2 性能优化
- **Redis缓存**：缓存频繁查询的任务状态
- **读写分离**：主从数据库架构
- **异步IO优化**：减少阻塞操作

### 8.3 可靠性提升
- **分布式锁**：防止重复任务创建
- **消息队列**：使用 RabbitMQ/Kafka 替代内存队列
- **断路器模式**：防止级联故障