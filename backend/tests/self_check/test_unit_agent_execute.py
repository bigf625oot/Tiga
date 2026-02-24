import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.workflow.steps.agent_execute_step import agent_execute_step
from app.workflow.context import AgentContext

@pytest.mark.asyncio
async def test_agent_execute_step_success():
    # 1. Setup Context
    context = AgentContext(
        session_id="test-session",
        agent_id="test-agent",
        user_message="Hello",
        history=[],
        state={}
    )
    
    # 2. Mock AgentManager and Agent
    mock_agent = MagicMock()
    mock_agent.name = "Test Agent"
    mock_agent.instructions = "You are a helper."
    mock_agent.tools = []
    mock_agent.model = MagicMock()
    mock_agent.model.id = "gpt-4o"
    
    # Mock arun to return a coroutine that returns an async generator
    async def mock_arun_wrapper(*args, **kwargs):
        async def async_gen():
            yield MagicMock(content="Response")
        return async_gen()
    
    mock_agent.arun.side_effect = mock_arun_wrapper

    # 3. Patch dependencies
    with patch("app.services.agent.manager.AgentManager.create_agno_agent", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_agent
        
        # We also need to patch AsyncSessionLocal to avoid DB connection
        with patch("app.workflow.steps.agent_execute_step.AsyncSessionLocal") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_db_ctx.return_value.__aenter__.return_value = mock_db
            
            # Mock DB execute for agent lookup
            mock_result = MagicMock()
            mock_result.scalars().first.return_value = MagicMock(model_config={})
            mock_db.execute.return_value = mock_result
            
            # 4. Execute Step
            result_context = await agent_execute_step(context)
            
            # 5. Verify
            assert result_context.output_stream is not None
            # Consume the stream to verify content
            content = ""
            async for chunk in result_context.output_stream:
                if isinstance(chunk, dict) and chunk.get("type") == "content":
                    content += chunk.get("content")
            
            assert "Response" in content

@pytest.mark.asyncio
async def test_agent_execute_step_failure():
    context = AgentContext(
        session_id="test-session",
        agent_id="test-agent",
        user_message="Hello"
    )
    
    with patch("app.services.agent.manager.AgentManager.create_agno_agent", side_effect=Exception("Load Failed")):
         with patch("app.workflow.steps.agent_execute_step.AsyncSessionLocal") as mock_db_ctx:
             # Expect it to raise WorkflowStepError or handle it
             # The current implementation catches exception and re-raises as WorkflowStepError
             from app.workflow.exceptions import WorkflowStepError
             
             with pytest.raises(WorkflowStepError):
                 await agent_execute_step(context)
