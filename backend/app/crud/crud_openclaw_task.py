from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.openclaw_task import OpenClawTask
from app.core.logger import logger

class OpenClawTaskCRUD:
    """OpenClaw 任务 CRUD 操作"""

    @staticmethod
    async def create_task(
        db: AsyncSession,
        original_prompt: str,
        parsed_command: Dict[str, Any],
        schedule: Optional[datetime] = None,
        target_node_id: Optional[str] = None
    ) -> tuple[OpenClawTask, bool]:
        """
        创建任务（支持幂等性）
        
        Returns:
            (task, created): 任务对象和是否为新创建的标志
        """
        try:
            # 尝试创建新任务
            task = OpenClawTask(
                original_prompt=original_prompt,
                parsed_command=parsed_command,
                schedule=schedule,
                target_node_id=target_node_id,
                status="PENDING"
            )
            db.add(task)
            await db.flush()  # 获取生成的 ID
            await db.commit()
            logger.info(f"Created new openclaw task: {task.task_id}")
            return task, True
            
        except IntegrityError as e:
            # 唯一键冲突，查询已存在的任务
            await db.rollback()
            
            stmt = select(OpenClawTask).where(
                and_(
                    OpenClawTask.original_prompt == original_prompt,
                    OpenClawTask.target_node_id == target_node_id,
                    OpenClawTask.schedule == schedule
                )
            )
            result = await db.execute(stmt)
            existing_task = result.scalar_one_or_none()
            
            if existing_task:
                logger.info(f"Found existing openclaw task: {existing_task.task_id}")
                return existing_task, False
            else:
                # 其他完整性错误
                raise e

    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: str) -> Optional[OpenClawTask]:
        """根据 ID 获取任务"""
        stmt = select(OpenClawTask).where(OpenClawTask.task_id == task_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_task_status_with_optimistic_lock(
        db: AsyncSession,
        task_id: str,
        old_status: str,
        new_status: str,
        error_log: Optional[str] = None
    ) -> bool:
        """
        使用乐观锁更新任务状态
        
        Returns:
            True: 更新成功
            False: 并发冲突（状态已变更）
        """
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        if error_log is not None:
            update_data["error_log"] = error_log

        stmt = (
            update(OpenClawTask)
            .where(
                and_(
                    OpenClawTask.task_id == task_id,
                    OpenClawTask.status == old_status
                )
            )
            .values(**update_data)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        affected_rows = result.rowcount
        if affected_rows == 0:
            logger.warning(f"Optimistic lock conflict for task {task_id}: expected status {old_status}")
            return False
        
        logger.info(f"Updated task {task_id} status from {old_status} to {new_status}")
        return True

    @staticmethod
    async def get_tasks_by_status(
        db: AsyncSession,
        status: str,
        limit: Optional[int] = None
    ) -> List[OpenClawTask]:
        """根据状态获取任务列表"""
        stmt = select(OpenClawTask).where(OpenClawTask.status == status)
        
        if limit:
            stmt = stmt.limit(limit)
        
        stmt = stmt.order_by(OpenClawTask.created_at.asc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def cleanup_expired_tasks(
        db: AsyncSession,
        days: int = 7,
        batch_size: int = 100
    ) -> int:
        """清理过期的失败任务"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(OpenClawTask)
            .where(
                and_(
                    OpenClawTask.status == "FAILED",
                    OpenClawTask.created_at < cutoff_date
                )
            )
            .limit(batch_size)
        )
        
        result = await db.execute(stmt)
        tasks_to_delete = result.scalars().all()
        
        deleted_count = 0
        for task in tasks_to_delete:
            await db.delete(task)
            deleted_count += 1
        
        await db.commit()
        logger.info(f"Cleaned up {deleted_count} expired failed tasks")
        return deleted_count