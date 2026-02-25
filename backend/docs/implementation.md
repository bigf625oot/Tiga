# 实现方案文档 (Implementation Plan)

## 1. 核心类与方法设计

### 1.1 任务模型 (Domain Models)

```python
# app/models/task.py
from sqlalchemy import Column, String, JSON, Integer, ForeignKey, DateTime
from app.db.base import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    prompt = Column(String)
    status = Column(String, default="PENDING")  # PENDING, SPLITTING, READY, COMPLETED, FAILED
    priority = Column(Integer, default=1)
    
class SubTask(Base):
    __tablename__ = "sub_tasks"
    id = Column(String, primary_key=True)
    parent_id = Column(String, ForeignKey("tasks.id"))
    dependencies = Column(JSON)  # List of sub_task_ids
    status = Column(String, default="PENDING") # PENDING, QUEUED, RUNNING, COMPLETED, FAILED
    result = Column(JSON)
```

### 1.2 任务拆分器 (Smart Task Splitter)

利用 LLM 将自然语言需求拆解为结构化子任务。

```python
# app/services/task/splitter.py
class TaskSplitter:
    def __init__(self, llm_client):
        self.llm = llm_client

    async def split_task(self, task_prompt: str) -> List[SubTaskSchema]:
        system_prompt = """
        You are a Task Architect. Break down the user's request into atomic, executable steps.
        Return a JSON list of steps with dependencies.
        Example:
        [
            {"id": "step1", "type": "search", "desc": "Find info on X", "deps": []},
            {"id": "step2", "type": "code", "desc": "Process info", "deps": ["step1"]}
        ]
        """
        response = await self.llm.generate(system_prompt, task_prompt)
        return self.parse_response(response)
```

### 1.3 执行调度器 (Execution Scheduler)

调度器负责管理任务依赖，将就绪任务推入队列。

```python
# app/services/task/scheduler.py
class Scheduler:
    def __init__(self, db, queue):
        self.db = db
        self.queue = queue

    async def check_ready_tasks(self, parent_task_id: str):
        # 获取所有子任务
        sub_tasks = await self.db.get_sub_tasks(parent_task_id)
        completed_ids = {t.id for t in sub_tasks if t.status == 'COMPLETED'}
        
        for task in sub_tasks:
            if task.status == 'PENDING':
                # 检查依赖是否满足
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    await self.queue.push(task)
                    await self.db.update_status(task.id, 'QUEUED')
```

## 2. 任务执行沙箱环境 (Sandbox Environment)

集成 E2B Code Interpreter 确保安全性。

```python
# app/core/sandbox.py
from e2b_code_interpreter import Sandbox

class SafeExecutor:
    async def execute_code(self, code: str, env_vars: dict = None):
        async with Sandbox() as sandbox:
            if env_vars:
                await sandbox.process.start_and_wait(f"export {k}={v}" for k,v in env_vars.items())
            
            execution = await sandbox.run_code(code)
            return {
                "stdout": execution.logs.stdout,
                "stderr": execution.logs.stderr,
                "results": execution.results
            }
```

## 3. Token 输出控制策略

通过拦截器监控 Token 消耗，防止超额。

```python
# app/core/token_control.py
import tiktoken

class TokenMonitor:
    def __init__(self, model="gpt-4"):
        self.encoder = tiktoken.encoding_for_model(model)
        self.limit = 4096

    def check_and_truncate(self, text: str) -> str:
        tokens = self.encoder.encode(text)
        if len(tokens) > self.limit:
            # 保留首尾，中间截断
            keep = self.limit // 2
            return self.encoder.decode(tokens[:keep]) + "\n...[TRUNCATED]...\n" + self.encoder.decode(tokens[-keep:])
        return text
```

## 4. 工具注册与调用流程

支持动态加载 MCP 和 Python 函数。

```python
# app/services/tools/registry.py
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register_mcp(self, mcp_server_url: str):
        # Connect to MCP server and list tools
        tools = MCPClient(mcp_server_url).list_tools()
        for tool in tools:
            self.tools[tool.name] = tool

    async def execute_tool(self, name: str, args: dict):
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return await self.tools[name].run(**args)
```

## 5. 异步任务处理机制

使用 Redis 作为消息队列。

1.  **Producer**: `Scheduler` 发现依赖满足的任务，序列化后 `LPUSH` 到 Redis List `task_queue`.
2.  **Consumer**: 后台 Worker 进程循环 `BRPOP` 从 `task_queue` 获取任务。
3.  **Result Handling**: 执行完成后，Worker 更新 DB 状态，并发送 Pub/Sub 消息通知 Scheduler 检查后续依赖。

```python
# app/workers/task_worker.py
async def worker_loop():
    redis = await get_redis_connection()
    while True:
        _, task_json = await redis.brpop("task_queue")
        task = json.loads(task_json)
        
        try:
            result = await execute_task(task)
            await update_db_status(task['id'], 'COMPLETED', result)
            # 触发后续任务检查
            await scheduler.check_ready_tasks(task['parent_id'])
        except Exception as e:
            await update_db_status(task['id'], 'FAILED', str(e))
```
