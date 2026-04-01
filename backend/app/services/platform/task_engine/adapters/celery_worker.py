from app.core.celery_app import celery_app
from app.services.platform.task_engine.models import TaskRunContext, TaskEvent
from app.db.session import AsyncSessionLocal
from app.crud.async_task import async_task, async_task_log
from app.core.task_progress import task_progress

import asyncio
import logging

logger = logging.getLogger(__name__)

# This runs in a separate process!
@celery_app.task(bind=True, name="run_celery_task")
def run_celery_task(self, context_dict: dict):
    """
    Celery worker 端执行函数。
    由于运行在不同进程中，需要自己处理 DB 连接和 Redis 事件发射。
    """
    import asyncio
    
    # 恢复 context 模型
    context = TaskRunContext(**context_dict)
    task_id = context.task_id
    user_id = context.user_id or "anonymous"
    
    logger.info(f"Celery worker received task: {task_id}")
    
    # 创建一个新事件循环，执行真正的异步业务逻辑
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_async_execute_and_report(task_id, user_id, context))
    return {"task_id": task_id, "status": "completed_by_celery"}

async def _emit_celery_event(event: TaskEvent, user_id: str):
    """Worker 端复用服务端的进度写库逻辑（直接写 DB 和 Redis）"""
    try:
        async with AsyncSessionLocal() as db:
            if event.status in ["SUCCESS", "FAILED", "CANCELLED"]:
                await async_task.update_status(
                    db, 
                    event.task_id, 
                    event.status, 
                    progress=event.progress, 
                    msg=event.message,
                    result=event.extend_data
                )
            else:
                await async_task.update_progress(
                    db, 
                    event.task_id, 
                    event.progress, 
                    event.status, 
                    event.message, 
                    event.step, 
                    event.extend_data
                )
                
            await async_task_log.create(
                db,
                event.task_id,
                event.progress,
                event.status,
                event.message,
                event.step,
                event.extend_data
            )

        # 更新 Redis 并通过 WS 广播
        await task_progress.set_progress(
            event.task_id, 
            event.progress, 
            event.status, 
            event.message, 
            event.step, 
            event.extend_data
        )
        await task_progress.publish_update(event.task_id, user_id)
    except Exception as e:
        logger.error(f"Failed to write progress to DB/Redis in celery worker: {e}", exc_info=True)


async def _async_execute_and_report(task_id: str, user_id: str, context: TaskRunContext):
    """
    Celery Worker 中的具体业务模拟
    """
    try:
        await _emit_celery_event(TaskEvent(
            task_id=task_id,
            status="RUNNING",
            progress=10,
            message="Celery Worker 已接单并开始处理",
            step="celery_initializing"
        ), user_id)
        
        # 模拟分布式耗时任务
        for i in range(20, 100, 20):
            await _emit_celery_event(TaskEvent(
                task_id=task_id,
                status="RUNNING",
                progress=i,
                message=f"分布式处理中... {i}%",
                step=f"celery_step_{i}"
            ), user_id)
            await asyncio.sleep(1)
            
        await _emit_celery_event(TaskEvent(
            task_id=task_id,
            status="SUCCESS",
            progress=100,
            message="Celery Worker 处理完成",
            step="completed",
            extend_data={"executor": "celery"}
        ), user_id)
        
    except Exception as e:
        logger.error(f"Celery task failed: {e}", exc_info=True)
        await _emit_celery_event(TaskEvent(
            task_id=task_id,
            status="FAILED",
            progress=0,
            message=f"分布式处理失败: {str(e)}",
            step="error"
        ), user_id)