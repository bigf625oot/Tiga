import pytest
from unittest.mock import patch
from sqlalchemy import select
from app.schemas.agent import AgentCreate
from app.crud.crud_agent import agent as crud_agent
from app.models.user_script import UserScript
from app.models.agent import Agent

@pytest.mark.asyncio
async def test_create_agent_with_user_script(db):
    from app.services.agent.service import agent_service
    agent_in = AgentCreate(
        name="Test Agent",
        description="A test agent",
        agent_model_config={"model_id": "gpt-4", "reasoning": False}
    )
    
    # Use service instead of CRUD directly
    agent = await agent_service.create_agent(db=db, obj_in=agent_in)
    
    assert agent.id is not None
    assert agent.name == "Test Agent"
    
    # Check if user script was created
    result = await db.execute(select(UserScript).filter(UserScript.agent_id == agent.id))
    script = result.scalars().first()
    
    assert script is not None
    assert script.title == "默认剧本"
    assert script.agent_id == agent.id

@pytest.mark.asyncio
async def test_create_agent_rollback(db):
    from app.services.agent.service import agent_service
    agent_in = AgentCreate(
        name="Rollback Agent",
        description="Should not exist",
    )
    
    # We simulate a failure by mocking UserScript to raise an exception
    # Note: UserScript is imported in service.py now
    with patch("app.services.agent.service.UserScript", side_effect=Exception("Simulated Failure")):
        with pytest.raises(Exception, match="Simulated Failure"):
            await agent_service.create_agent(db=db, obj_in=agent_in)
            
    # Since the operation failed before commit, we manually rollback the test session 
    # to ensure we are looking at clean state (and to clear the flushed but not committed agent)
    await db.rollback()
    
    result = await db.execute(select(Agent).filter(Agent.name == "Rollback Agent"))
    agent = result.scalars().first()
    assert agent is None
