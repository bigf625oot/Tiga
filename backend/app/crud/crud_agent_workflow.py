from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_workflow import AgentWorkflow
from app.schemas.agent_workflow import AgentWorkflowCreate, AgentWorkflowUpdate

class CRUDAgentWorkflow:
    async def get(self, db: AsyncSession, id: str) -> Optional[AgentWorkflow]:
        result = await db.execute(select(AgentWorkflow).filter(AgentWorkflow.id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        query: Optional[str] = None
    ) -> List[AgentWorkflow]:
        stmt = select(AgentWorkflow)
        
        if query:
            search = f"%{query}%"
            stmt = stmt.filter(
                or_(
                    AgentWorkflow.name.ilike(search),
                    AgentWorkflow.description.ilike(search)
                )
            )
            
        stmt = stmt.offset(skip).limit(limit).order_by(AgentWorkflow.updated_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: AgentWorkflowCreate) -> AgentWorkflow:
        db_obj = AgentWorkflow(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: AgentWorkflow,
        obj_in: AgentWorkflowUpdate
    ) -> AgentWorkflow:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str) -> Optional[AgentWorkflow]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

agent_workflow = CRUDAgentWorkflow()
