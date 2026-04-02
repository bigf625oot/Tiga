from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from app.services.platform.task_engine.models import TaskRunContext, TaskEvent


class BaseTaskAdapter(ABC):
    """底层任务引擎的适配器基类"""
    
    def __init__(self):
        # 回调函数，用于将引擎内部的状态变更抛出给 TaskEngineService
        self._on_event_callback: Callable[[TaskEvent], Awaitable[None]] = None
        
    def set_event_callback(self, callback: Callable[[TaskEvent], Awaitable[None]]):
        """设置事件回调函数"""
        self._on_event_callback = callback
        
    async def emit_event(self, event: TaskEvent):
        """向中心调度器发射事件"""
        if self._on_event_callback:
            await self._on_event_callback(event)
            
    @abstractmethod
    async def start_task(self, context: TaskRunContext) -> bool:
        """
        启动任务
        :param context: 任务上下文
        :return: 是否启动成功
        """
        pass
        
    @abstractmethod
    async def stop_task(self, task_id: str) -> bool:
        """
        停止任务
        :param task_id: 统一的 TaskRun ID
        :return: 是否停止成功
        """
        pass
        
    @abstractmethod
    async def get_status(self, task_id: str) -> TaskEvent:
        """
        主动拉取任务当前状态（用于 reconcile 或重连）
        :param task_id: 统一的 TaskRun ID
        :return: 最新状态事件
        """
        pass
