import logging
import asyncio
from app.services.platform.task_engine.adapters.base import BaseTaskAdapter
from app.services.platform.task_engine.models import TaskRunContext, TaskEvent
from app.core.worker_pool import task_pool

logger = logging.getLogger(__name__)

class AsyncTaskAdapter(BaseTaskAdapter):
    """
    通用异步任务适配器。
    这里封装了原先 task_runs.py 里直接提交给 worker_pool 的逻辑。
    """
    
    async def start_task(self, context: TaskRunContext) -> bool:
        # 直接把模拟的后台处理函数提交到线程池/协程池
        # 实际应用中可以根据 context.config 里的参数决定具体执行哪个业务函数
        await task_pool.submit_task(self._process_in_background, context)
        return True
        
    async def stop_task(self, task_id: str) -> bool:
        # 简单的 AsyncTask 可能不支持硬停止，这里仅标记或抛出异常
        logger.warning(f"AsyncTask {task_id} stop requested but not fully supported")
        return False
        
    async def get_status(self, task_id: str) -> TaskEvent:
        # AsyncTask 的状态都在 Redis 和 DB 里，无需额外查底层
        return TaskEvent(task_id=task_id, status="UNKNOWN")
        
    async def _process_in_background(self, context: TaskRunContext):
        """模拟一个处理流程，通过 emit_event 回传状态"""
        try:
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="RUNNING",
                progress=10,
                message="开始处理",
                step="initializing"
            ))
            
            # 模拟分步处理
            for i in range(20, 100, 20):
                await self.emit_event(TaskEvent(
                    task_id=context.task_id,
                    status="RUNNING",
                    progress=i,
                    message=f"处理中... {i}%",
                    step=f"step_{i}"
                ))
                await asyncio.sleep(0.5)
                
            # 完成
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="SUCCESS",
                progress=100,
                message="任务完成",
                step="completed",
                extend_data={"download_url": f"/uploads/{context.task_id}.zip"}
            ))
            
        except Exception as e:
            logger.error(f"AsyncTask failed: {e}", exc_info=True)
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="FAILED",
                progress=0,
                message=f"任务失败: {str(e)}",
                step="error"
            ))
