from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud import crud_agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

router = APIRouter()

@router.get("/", response_model=List[AgentResponse])
async def read_agents(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve agents.
    """
    agents = await crud_agent.agent.get_multi(db, skip=skip, limit=limit)
    return agents

@router.post("/", response_model=AgentResponse)
async def create_agent(
    *,
    db: AsyncSession = Depends(get_db),
    agent_in: AgentCreate
):
    """
    Create new agent.
    """
    agent = await crud_agent.agent.create(db=db, obj_in=agent_in)
    return agent

@router.get("/{agent_id}", response_model=AgentResponse)
async def read_agent(
    *,
    db: AsyncSession = Depends(get_db),
    agent_id: str
):
    """
    Get agent by ID.
    """
    agent = await crud_agent.agent.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    *,
    db: AsyncSession = Depends(get_db),
    agent_id: str,
    agent_in: AgentUpdate
):
    """
    Update an agent.
    """
    agent = await crud_agent.agent.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = await crud_agent.agent.update(db=db, db_obj=agent, obj_in=agent_in)
    return agent

@router.delete("/{agent_id}", response_model=AgentResponse)
async def delete_agent(
    *,
    db: AsyncSession = Depends(get_db),
    agent_id: str
):
    """
    Delete an agent.
    """
    agent = await crud_agent.agent.get(db=db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await crud_agent.agent.delete(db=db, id=agent_id)
    return agent
