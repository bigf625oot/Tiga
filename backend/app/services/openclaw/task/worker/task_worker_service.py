"""
应用场景：
    OpenClaw 任务工作器服务。
    负责异步处理任务状态更新和网关调用。

核心功能：
    - 异步任务队列管理
    - 任务分发与执行
    - 状态更新（乐观锁）
    - 错误处理与日志记录

__author__ = "xucao"
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.openclaw_task import OpenClawTask
from app.crud.crud_openclaw_task import OpenClawTaskCRUD
from app.core.logger import logger

logger = logging.getLogger(__name__)

class OpenClawTaskWorker:
    """OpenClaw 任务工作器 - 负责异步处理任务状态更新"""
    
    def __init__(self):
        self._running = False
        self._task_queue = asyncio.Queue()
        self._worker_task = None
    
    async def start(self):
        """启动工作器"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("OpenClaw Task Worker started")
    
    async def stop(self):
        """停止工作器"""
        if not self._running:
            return
        
        self._running = False
        await self._task_queue.put(None)  # 发送停止信号
        
        if self._worker_task:
            await self._worker_task
        
        logger.info("OpenClaw Task Worker stopped")
    
    async def dispatch_task(
        self,
        task_id: str,
        gateway_call_func,
        db_session_factory
    ):
        """分发任务到工作队列"""
        await self._task_queue.put({
            "task_id": task_id,
            "gateway_call_func": gateway_call_func,
            "db_session_factory": db_session_factory,
            "created_at": datetime.utcnow()
        })
        logger.debug(f"Task {task_id} dispatched to worker queue")
    
    async def _worker_loop(self):
        """工作器主循环"""
        while self._running:
            try:
                task_data = await self._task_queue.get()
                if task_data is None:  # 停止信号
                    break
                
                await self._process_task(task_data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1)  # 避免快速重试
    
    async def _process_task(self, task_data: Dict[str, Any]):
        """处理单个任务"""
        task_id = task_data["task_id"]
        gateway_call_func = task_data["gateway_call_func"]
        db_session_factory = task_data["db_session_factory"]
        
        logger.info(f"Worker: 开始处理任务 task_id={task_id}")
        
        try:
            # 调用 Gateway
            logger.info(f"Worker: 正在执行 gateway_call (DispatchService)... task_id={task_id}")
            result = await gateway_call_func()
            logger.info(f"Worker: gateway_call 执行成功: task_id={task_id}, result={result}")
            
            # Check result for errors
            if isinstance(result, dict) and "error" in result:
                raise Exception(f"Gateway returned error: {result['error']}")

            # 更新任务状态为 DISPATCHED
            async with db_session_factory() as db:
                success = await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
                    db,
                    task_id,
                    "PENDING",
                    "DISPATCHED"
                )
                
                if not success:
                    logger.warning(f"Task {task_id} status update failed - likely already processed")
                else:
                    logger.info(f"Task {task_id} 状态更新为 DISPATCHED 成功")
            
        except Exception as e:
            # 处理失败情况
            error_msg = f"Worker处理任务失败: {str(e)}"
            error_details = traceback.format_exc()
            logger.error(f"{error_msg}\n堆栈追踪:\n{error_details}")
            
            error_log = json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_details,
                "task_id": task_id
            })
            
            try:
                async with db_session_factory() as db:
                    # Retry logic: If PENDING -> FAILED, but if already DISPATCHED (e.g. gateway success but DB fail?), 
                    # we should probably not overwrite unless we are sure.
                    # But here we are in the catch block of the whole process.
                    # If gateway call failed, status is still PENDING.
                    success = await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
                        db,
                        task_id,
                        "PENDING",
                        "FAILED",
                        error_log
                    )
                    
                    if success:
                        logger.error(f"Task {task_id} 已标记为 FAILED")
                    else:
                        # Could be already processed or concurrency issue
                        logger.error(f"Task {task_id} 标记 FAILED 失败 (并发冲突或状态已变更)")
            except Exception as db_e:
                logger.error(f"Worker更新失败状态时发生数据库错误: {db_e}", exc_info=True)
    
    @property
    def is_running(self) -> bool:
        """检查工作器是否运行中"""
        return self._running

# 全局工作器实例
task_worker = OpenClawTaskWorker()