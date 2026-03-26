from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate

class CRUDKnowledgeBase:
    async def get(self, db: AsyncSession, id: str) -> Optional[KnowledgeBase]:
        result = await db.execute(select(KnowledgeBase).filter(KnowledgeBase.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, query: str = None) -> List[KnowledgeBase]:
        stmt = select(KnowledgeBase)
        if query:
            stmt = stmt.filter(KnowledgeBase.name.ilike(f"%{query}%"))
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: KnowledgeBaseCreate) -> KnowledgeBase:
        db_obj = KnowledgeBase(
            name=obj_in.name,
            description=obj_in.description,
            status=obj_in.status
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: KnowledgeBase, obj_in: KnowledgeBaseUpdate) -> KnowledgeBase:
        update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: str) -> KnowledgeBase:
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

knowledge_base = CRUDKnowledgeBase()
