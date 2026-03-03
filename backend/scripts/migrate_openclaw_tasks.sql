-- 增量 SQL 脚本：创建 openclaw_tasks 表
-- 用于存储 OpenClaw 创建的任务，支持状态追踪和幂等性

-- 创建扩展（如果尚未安装）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建任务表
CREATE TABLE IF NOT EXISTS openclaw_tasks (
    task_id CHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING','DISPATCHED','FAILED')),
    original_prompt TEXT NOT NULL,
    parsed_command JSONB NOT NULL,
    schedule TIMESTAMP WITH TIME ZONE,
    target_node_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    error_log TEXT,
    
    -- 幂等性唯一键
    CONSTRAINT uq_openclaw_task UNIQUE (original_prompt, target_node_id, schedule)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_openclaw_tasks_status_created 
    ON openclaw_tasks(status, created_at);

CREATE INDEX IF NOT EXISTS idx_openclaw_tasks_created_at 
    ON openclaw_tasks(created_at);

-- 创建更新触发器
CREATE OR REPLACE FUNCTION update_openclaw_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_openclaw_tasks_updated_at
    BEFORE UPDATE ON openclaw_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_openclaw_tasks_updated_at();

-- 回滚脚本（如果需要撤销）
-- DROP TRIGGER IF EXISTS trg_update_openclaw_tasks_updated_at ON openclaw_tasks;
-- DROP FUNCTION IF EXISTS update_openclaw_tasks_updated_at();
-- DROP INDEX IF EXISTS idx_openclaw_tasks_status_created;
-- DROP INDEX IF EXISTS idx_openclaw_tasks_created_at;
-- DROP TABLE IF EXISTS openclaw_tasks;