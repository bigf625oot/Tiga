from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.user_script import UserScript
from app.schemas.agent import AgentCreate, AgentUpdate


class CRUDAgent:
    async def get(self, db: AsyncSession, id: str):
        result = await db.execute(select(Agent).filter(Agent.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, query: str = None, is_template: bool = None, is_active: bool = None):
        stmt = select(Agent)
        
        if is_template is not None:
            stmt = stmt.filter(Agent.is_template == is_template)
            
        if is_active is not None:
            stmt = stmt.filter(Agent.is_active == is_active)
            
        if query:
            search = f"%{query}%"
            stmt = stmt.filter(or_(Agent.name.ilike(search), Agent.description.ilike(search)))
            
        stmt = stmt.offset(skip).limit(limit).order_by(Agent.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: AgentCreate, commit: bool = True):
        obj_data = obj_in.model_dump()
        # Map Pydantic 'agent_model_config' back to DB 'model_config'
        if "agent_model_config" in obj_data:
            obj_data["model_config"] = obj_data.pop("agent_model_config")

        db_obj = Agent(**obj_data)
        db.add(db_obj)
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Agent, obj_in: AgentUpdate):
        update_data = obj_in.model_dump(exclude_unset=True)
        # Map Pydantic 'agent_model_config' back to DB 'model_config'
        if "agent_model_config" in update_data:
            update_data["model_config"] = update_data.pop("agent_model_config")

        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str):
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj


agent = CRUDAgent()
