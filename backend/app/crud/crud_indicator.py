from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indicator import Indicator
from app.schemas.indicator import IndicatorCreate, IndicatorUpdate


class CRUDIndicator:
    async def get(self, db: AsyncSession, id: int) -> Optional[Indicator]:
        result = await db.execute(select(Indicator).filter(Indicator.id == id, Indicator.is_deleted == False))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 20, search: Optional[str] = None
    ) -> List[Indicator]:
        query = select(Indicator).filter(Indicator.is_deleted == False)
        if search:
            query = query.filter(Indicator.name.ilike(f"%{search}%"))
        query = query.order_by(Indicator.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: IndicatorCreate) -> Indicator:
        db_obj = Indicator(
            group=obj_in.group,
            name=obj_in.name,
            alias=obj_in.alias,
            description=obj_in.description,
            advanced_options=obj_in.advanced_options,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Indicator, obj_in: IndicatorUpdate) -> Indicator:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> Optional[Indicator]:
        # Logical delete
        db_obj = await self.get(db, id)
        if db_obj:
            db_obj.is_deleted = True
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def get_by_group_and_name(self, db: AsyncSession, group: str, name: str) -> Optional[Indicator]:
        result = await db.execute(
            select(Indicator).filter(Indicator.group == group, Indicator.name == name, Indicator.is_deleted == False)
        )
        return result.scalars().first()


crud_indicator = CRUDIndicator()
