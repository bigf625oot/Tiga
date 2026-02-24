from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_agent import agent as crud_agent
from app.db.session import get_db
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter()


@router.get("/", response_model=List[AgentResponse])
async def read_agents(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Retrieve agents.
    """
    from app.services.agent.service import agent_service
    agents = await agent_service.get_agents(db, skip=skip, limit=limit)
    return agents


@router.post("/", response_model=AgentResponse)
async def create_agent(*, db: AsyncSession = Depends(get_db), agent_in: AgentCreate):
    """
    Create new agent.
    """
    from app.services.agent.service import agent_service
    agent = await agent_service.create_agent(db, agent_in)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def read_agent(*, db: AsyncSession = Depends(get_db), agent_id: str):
    """
    Get agent by ID.
    """
    from app.services.agent.service import agent_service
    agent = await agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(*, db: AsyncSession = Depends(get_db), agent_id: str, agent_in: AgentUpdate):
    """
    Update an agent.
    """
    from app.services.agent.service import agent_service
    agent = await agent_service.update_agent(db, agent_id, agent_in)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", response_model=AgentResponse)
async def delete_agent(*, db: AsyncSession = Depends(get_db), agent_id: str):
    """
    Delete an agent.
    """
    from app.services.agent.service import agent_service
    agent = await agent_service.delete_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
