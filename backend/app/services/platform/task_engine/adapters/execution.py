import logging
from app.services.platform.task_engine.adapters.base import BaseTaskAdapter
from app.services.platform.task_engine.models import TaskRunContext, TaskEvent
from app.core.worker_pool import task_pool
from app.db.session import AsyncSessionLocal
from app.services.ops.task.service import task_service

logger = logging.getLogger(__name__)

class ExecutionTaskAdapter(BaseTaskAdapter):
    """
    复杂执行编排任务适配器。
    对接原有的 execution_tasks 体系（带子任务拆分与调度）。
    """
    
    async def start_task(self, context: TaskRunContext) -> bool:
        prompt = context.config.get("prompt", "")
        execution_task_id = context.config.get("execution_task_id")
        
        if not execution_task_id:
            logger.error("ExecutionTaskAdapter requires execution_task_id in config")
            return False
            
        # 抛出一个开始事件
        await self.emit_event(TaskEvent(
            task_id=context.task_id,
            status="RUNNING",
            progress=5,
            message="提交到执行引擎...",
            step="dispatching"
        ))
        
        # 将原 tasks.py 的 run_in_background 移到这里
        await task_pool.submit_task(self._run_execution_task, context, execution_task_id, prompt)
        return True
        
    async def stop_task(self, task_id: str) -> bool:
        # TODO: 原 Execution 体系目前尚未实现硬停止，预留接口
        return False
        
    async def get_status(self, task_id: str) -> TaskEvent:
        # TODO: 从 DB 的 execution_tasks 表反向查询汇总状态
        return TaskEvent(task_id=task_id, status="UNKNOWN")
        
    async def _run_execution_task(self, context: TaskRunContext, execution_task_id: str, prompt: str):
        """包装原有执行引擎，并监听/抛出进度（简化版，后续可在 task_service 内部更细粒度地回调）"""
        try:
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="RUNNING",
                progress=10,
                message="开始拆分执行子任务",
                step="splitting"
            ))
            
            async with AsyncSessionLocal() as db:
                await task_service.process_task_creation(execution_task_id, prompt, db)
                
            # 假设到这里是完成的（实际 process_task_creation 可能是纯异步拆分，后续调度在别处）
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="SUCCESS",
                progress=100,
                message="执行编排已处理",
                step="completed"
            ))
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="FAILED",
                progress=0,
                message=f"执行失败: {str(e)}",
                step="error"
            ))
