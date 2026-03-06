from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.crud_agent import agent as crud_agent
from app.models.user_script import UserScript
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.models.agent import Agent

class AgentService:
    async def create_agent(self, db: AsyncSession, obj_in: AgentCreate) -> Agent:
        """
        Create a new agent and its default UserScript.
        """
        # 1. Create Agent via CRUD (Pure data operation)
        # Do NOT commit yet, wait for UserScript
        db_obj = await crud_agent.create(db, obj_in, commit=False)
        
        # 2. Create Default UserScript (Business Logic)
        default_script = UserScript(
            agent_id=db_obj.id,
            title="默认剧本",
            content="# 默认剧本\n\n这是一个自动生成的剧本模板。",
            sort_order=0
        )
        db.add(default_script)
        
        # 3. Commit everything
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_agent(self, db: AsyncSession, agent_id: str) -> Agent:
        return await crud_agent.get(db, agent_id)

    async def get_agents(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        return await crud_agent.get_multi(db, skip=skip, limit=limit)

    async def update_agent(self, db: AsyncSession, agent_id: str, obj_in: AgentUpdate) -> Agent:
        db_obj = await crud_agent.get(db, agent_id)
        if not db_obj:
            return None
        return await crud_agent.update(db, db_obj, obj_in)

    async def delete_agent(self, db: AsyncSession, agent_id: str) -> Agent:
        return await crud_agent.delete(db, agent_id)

agent_service = AgentService()
