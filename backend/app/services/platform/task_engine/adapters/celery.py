import logging
from app.services.platform.task_engine.adapters.base import BaseTaskAdapter
from app.services.platform.task_engine.models import TaskRunContext, TaskEvent

try:
    from app.services.platform.task_engine.adapters.celery_worker import run_celery_task
    from app.core.celery_app import celery_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)

class CeleryAdapter(BaseTaskAdapter):
    """
    分布式调度任务适配器。
    将任务发送到 Celery 消息队列，由远程 Worker 异步执行。
    """
    
    async def start_task(self, context: TaskRunContext) -> bool:
        if not CELERY_AVAILABLE:
            logger.error("Celery is not available. Please install celery and configure Redis.")
            return False
            
        try:
            # 序列化 context
            context_dict = context.model_dump()
            
            # 发送任务到 Celery
            task = run_celery_task.apply_async(
                args=[context_dict],
                task_id=f"celery-{context.task_id}" # 关联 Celery Task ID 与 平台 Task ID
            )
            
            logger.info(f"Dispatched task {context.task_id} to Celery worker (Celery ID: {task.id})")
            
            # 发送初始事件
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="PENDING",
                progress=5,
                message="任务已进入分布式队列等待处理",
                step="queued"
            ))
            return True
            
        except Exception as e:
            logger.error(f"Failed to dispatch task to Celery: {e}", exc_info=True)
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="FAILED",
                progress=0,
                message=f"无法派发到分布式队列: {str(e)}",
                step="dispatch_error"
            ))
            return False

    async def stop_task(self, task_id: str) -> bool:
        if not CELERY_AVAILABLE:
            return False
        try:
            # 根据命名规则撤销任务
            celery_id = f"celery-{task_id}"
            celery_app.control.revoke(celery_id, terminate=True)
            logger.info(f"Revoked celery task {celery_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop celery task {task_id}: {e}")
            return False

    async def get_status(self, task_id: str) -> TaskEvent:
        if not CELERY_AVAILABLE:
            return TaskEvent(task_id=task_id, status="UNKNOWN")
            
        # 查询 Celery backend 里的状态
        celery_id = f"celery-{task_id}"
        res = celery_app.AsyncResult(celery_id)
        
        status_map = {
            "PENDING": "PENDING",
            "STARTED": "RUNNING",
            "RETRY": "RUNNING",
            "SUCCESS": "SUCCESS",
            "FAILURE": "FAILED",
            "REVOKED": "CANCELLED"
        }
        
        mapped_status = status_map.get(res.state, "UNKNOWN")
        
        return TaskEvent(
            task_id=task_id, 
            status=mapped_status,
            message=f"Celery state: {res.state}",
            step=res.state.lower()
        )