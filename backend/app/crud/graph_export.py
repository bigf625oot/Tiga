from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph_export import GraphExportConfig
from app.schemas.graph_export import GraphExportConfigCreate, GraphExportConfigUpdate


class CRUDGraphExportConfig:
    async def get(self, db: AsyncSession, id: int) -> Optional[GraphExportConfig]:
        result = await db.execute(select(GraphExportConfig).filter(GraphExportConfig.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[GraphExportConfig]:
        result = await db.execute(select(GraphExportConfig).filter(GraphExportConfig.name == name))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[GraphExportConfig]:
        result = await db.execute(
            select(GraphExportConfig).offset(skip).limit(limit).order_by(GraphExportConfig.updated_at.desc())
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: GraphExportConfigCreate) -> GraphExportConfig:
        obj_data = obj_in.model_dump()
        db_obj = GraphExportConfig(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: GraphExportConfig, obj_in: GraphExportConfigUpdate
    ) -> GraphExportConfig:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> Optional[GraphExportConfig]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj


graph_export_config = CRUDGraphExportConfig()
