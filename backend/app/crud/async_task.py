from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple

from app.models.async_task import AsyncTask, AsyncTaskLog
from app.schemas.async_task import AsyncTaskCreate


class CRUDAsyncTask:
    async def create(self, db: AsyncSession, obj_in: AsyncTaskCreate, user_id: Optional[str] = None) -> AsyncTask:
        db_obj = AsyncTask(
            name=obj_in.name,
            task_type=obj_in.task_type,
            priority=obj_in.priority,
            user_id=user_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: str) -> Optional[AsyncTask]:
        result = await db.execute(
            select(AsyncTask).filter(AsyncTask.id == id, AsyncTask.deleted == False)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AsyncTask], int]:
        query = select(AsyncTask).filter(AsyncTask.deleted == False)

        if user_id:
            query = query.filter(AsyncTask.user_id == user_id)
        if status:
            query = query.filter(AsyncTask.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AsyncTask.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()
        return items, total

    async def update_progress(
        self,
        db: AsyncSession,
        id: str,
        percent: int,
        status: str,
        msg: str = "",
        step: str = "",
        extend: Optional[dict] = None
    ) -> Optional[AsyncTask]:
        task = await self.get(db, id)
        if not task:
            return None

        task.progress = percent
        task.status = status
        task.msg = msg
        task.step = step

        await db.commit()
        await db.refresh(task)
        return task

    async def update_status(self, db: AsyncSession, id: str, status: str, **kwargs) -> Optional[AsyncTask]:
        task = await self.get(db, id)
        if not task:
            return None

        task.status = status
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        await db.commit()
        await db.refresh(task)
        return task

    async def soft_delete(self, db: AsyncSession, id: str) -> bool:
        task = await self.get(db, id)
        if not task:
            return False
        task.deleted = True
        await db.commit()
        return True

    async def soft_delete_by_status(self, db: AsyncSession, user_id: Optional[str], statuses: List[str]) -> int:
        query = update(AsyncTask).where(
            AsyncTask.deleted == False,
            AsyncTask.status.in_(statuses)
        )
        if user_id:
            query = query.where(AsyncTask.user_id == user_id)

        query = query.values(deleted=True)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount


class CRUDAsyncTaskLog:
    async def create(
        self,
        db: AsyncSession,
        task_id: str,
        percent: int,
        status: str,
        msg: str = "",
        step: str = "",
        extend: Optional[dict] = None
    ) -> AsyncTaskLog:
        db_obj = AsyncTaskLog(
            task_id=task_id,
            percent=percent,
            status=status,
            msg=msg,
            step=step,
            extend=extend
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_task(
        self,
        db: AsyncSession,
        task_id: str,
        limit: int = 50
    ) -> List[AsyncTaskLog]:
        result = await db.execute(
            select(AsyncTaskLog)
            .filter(AsyncTaskLog.task_id == task_id)
            .order_by(AsyncTaskLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async_task = CRUDAsyncTask()
async_task_log = CRUDAsyncTaskLog()