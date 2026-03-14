from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.i18n import _
from app.crud.crud_agent import agent as crud_agent
from app.models.user_script import UserScript
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentClone
from app.models.agent import Agent
from typing import List

class AgentService:
    async def clone_agent(self, db: AsyncSession, agent_id: str, clone_in: AgentClone) -> Agent:
        """
        Clone an existing agent.
        """
        original = await self.get_agent(db, agent_id)
        if not original:
            return None
        
        # Create new agent data from original
        # We need to manually copy fields because AgentCreate might not have all fields if they are optional in DB but required in Create
        # Actually AgentCreate is AgentBase, so it should be fine.
        # But let's be safe and dict() it.
        agent_data_dict = {
            "name": clone_in.name if clone_in.name else f"{original.name} (Copy)",
            "description": original.description,
            "icon": original.icon,
            "system_prompt": original.system_prompt,
            "enable_react": original.enable_react,
            "enable_cot": original.enable_cot,
            "agent_model_config": original.agent_model_config,
            "tools_config": original.tools_config,
            "mcp_config": original.mcp_config,
            "skills_config": original.skills_config,
            "knowledge_config": original.knowledge_config,
            "memory_config": original.memory_config,
            "storage_config": original.storage_config,
            "is_active": True,
            "is_template": clone_in.is_template
        }
        
        agent_in = AgentCreate(**agent_data_dict)
        return await self.create_agent(db, agent_in)

    async def delete_agents(self, db: AsyncSession, agent_ids: List[str]) -> List[str]:
        """
        Delete multiple agents.
        """
        deleted_ids = []
        for agent_id in agent_ids:
            result = await self.delete_agent(db, agent_id)
            if result:
                deleted_ids.append(agent_id)
        return deleted_ids

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
            title=_("Default Script"),
            content=_("# Default Script\n\nThis is an auto-generated script template."),
            sort_order=0
        )
        db.add(default_script)
        
        # 3. Commit everything
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_agent(self, db: AsyncSession, agent_id: str) -> Agent:
        return await crud_agent.get(db, agent_id)

    async def get_agents(self, db: AsyncSession, skip: int = 0, limit: int = 100, query: str = None, is_template: bool = None, is_active: bool = None):
        return await crud_agent.get_multi(db, skip=skip, limit=limit, query=query, is_template=is_template, is_active=is_active)

    async def update_agent(self, db: AsyncSession, agent_id: str, obj_in: AgentUpdate) -> Agent:
        db_obj = await crud_agent.get(db, agent_id)
        if not db_obj:
            return None
        return await crud_agent.update(db, db_obj, obj_in)

    async def delete_agent(self, db: AsyncSession, agent_id: str) -> Agent:
        return await crud_agent.delete(db, agent_id)

agent_service = AgentService()
