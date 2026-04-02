import logging
from typing import Dict, Type

from app.db.session import AsyncSessionLocal
from app.crud.async_task import async_task, async_task_log
from app.core.task_progress import task_progress

from app.services.platform.task_engine.models import TaskEngineType, TaskRunContext, TaskEvent
from app.services.platform.task_engine.adapters.base import BaseTaskAdapter

logger = logging.getLogger(__name__)


class TaskEngineService:
    """任务引擎分发器（Dispatcher）"""
    
    def __init__(self):
        self._adapters: Dict[TaskEngineType, BaseTaskAdapter] = {}
        
    def register_adapter(self, engine_type: TaskEngineType, adapter: BaseTaskAdapter):
        """注册底层引擎适配器"""
        adapter.set_event_callback(self.handle_task_event)
        self._adapters[engine_type] = adapter
        logger.info(f"Registered Task Adapter for: {engine_type.value}")
        
    def get_adapter(self, engine_type: TaskEngineType) -> BaseTaskAdapter:
        if engine_type not in self._adapters:
            raise ValueError(f"No adapter registered for engine type: {engine_type}")
        return self._adapters[engine_type]

    async def start_task(self, context: TaskRunContext) -> bool:
        """统一启动入口，分发到对应适配器"""
        adapter = self.get_adapter(context.engine_type)
        logger.info(f"Dispatching task {context.task_id} to {context.engine_type.value} adapter")
        return await adapter.start_task(context)
        
    async def stop_task(self, task_id: str, engine_type: TaskEngineType) -> bool:
        """统一停止入口"""
        adapter = self.get_adapter(engine_type)
        return await adapter.stop_task(task_id)

    async def handle_task_event(self, event: TaskEvent):
        """
        统一事件处理器
        所有 Adapter 产生状态变更时都会调用此方法，统一回写 DB(AsyncTask表) 和 Redis(WebSocket)
        """
        try:
            # 1. 查出现有任务获取 user_id (用于 ws 推送)
            user_id = "anonymous"
            async with AsyncSessionLocal() as db:
                task = await async_task.get(db, event.task_id)
                if task and task.user_id:
                    user_id = task.user_id
                    
                # 2. 更新 DB 进度与状态
                if event.status in ["SUCCESS", "FAILED"]:
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
                    
                # 3. 记录日志
                await async_task_log.create(
                    db,
                    event.task_id,
                    event.progress,
                    event.status,
                    event.message,
                    event.step,
                    event.extend_data
                )

            # 4. 更新 Redis 并通过 WS 广播
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
            logger.error(f"Failed to handle task event for {event.task_id}: {e}", exc_info=True)


# 全局单例
task_engine_service = TaskEngineService()
