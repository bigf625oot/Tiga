from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.task import ExecutionTask, SubTask
from app.schemas.task import TaskCreate, TaskUpdate, SubTaskCreate, SubTaskUpdate

class CRUDTask:
    async def get(self, db: AsyncSession, id: str) -> Optional[ExecutionTask]:
        result = await db.execute(select(ExecutionTask).filter(ExecutionTask.id == id))
        return result.scalars().first()

    async def create(self, db: AsyncSession, obj_in: TaskCreate) -> ExecutionTask:
        db_obj = ExecutionTask(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: ExecutionTask, obj_in: TaskUpdate) -> ExecutionTask:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDSubTask:
    async def get(self, db: AsyncSession, id: str) -> Optional[SubTask]:
        result = await db.execute(select(SubTask).filter(SubTask.id == id))
        return result.scalars().first()

    async def get_by_parent(self, db: AsyncSession, parent_id: str) -> List[SubTask]:
        result = await db.execute(select(SubTask).filter(SubTask.parent_id == parent_id).order_by(SubTask.execution_order))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: SubTaskCreate, parent_id: str) -> SubTask:
        obj_data = obj_in.model_dump()
        obj_data["parent_id"] = parent_id
        db_obj = SubTask(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: SubTask, obj_in: SubTaskUpdate) -> SubTask:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

task = CRUDTask()
sub_task = CRUDSubTask()
