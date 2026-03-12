from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate

class CRUDTeam:
    async def get(self, db: AsyncSession, id: int) -> Optional[Team]:
        result = await db.execute(select(Team).where(Team.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, query: str = None) -> List[Team]:
        stmt = select(Team)
        if query:
            search = f"%{query}%"
            stmt = stmt.where(or_(Team.name.ilike(search), Team.description.ilike(search)))
        
        stmt = stmt.offset(skip).limit(limit).order_by(Team.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: TeamCreate) -> Team:
        db_obj = Team(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Team, obj_in: TeamUpdate) -> Team:
        if db_obj.is_readonly:
            # Although API should prevent this, we double check here or just allow updates if API handles it.
            # But let's just update the fields provided.
            pass
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> Optional[Team]:
        db_obj = await self.get(db, id)
        if db_obj:
            if db_obj.is_readonly:
                 raise ValueError("Cannot delete read-only team")
            await db.delete(db_obj)
            await db.commit()
        return db_obj

team = CRUDTeam()
