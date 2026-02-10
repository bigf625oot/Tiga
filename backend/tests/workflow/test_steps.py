import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.workflow.context import AgentContext
from app.workflow.steps.rag_retrieve_step import rag_retrieve_step
from app.workflow.steps.plan_step import plan_step
from app.workflow.steps.persist_step import persist_step
from app.workflow.steps.agent_execute_step import agent_execute_step

@pytest.mark.asyncio
async def test_rag_retrieve_step():
    context = AgentContext(session_id="test", user_message="hello", doc_ids=["1"])
    
    with patch("app.workflow.steps.rag_retrieve_step.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock the Result object returned by await execute()
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result
        
        # Mock scalars().all()
        mock_result.scalars.return_value.all.return_value = []
        
        with patch("app.workflow.steps.rag_retrieve_step.kb_service") as mock_kb:
            mock_kb.search = MagicMock(return_value=([{"title": "doc1"}], []))
            
            # Since logic uses asyncio.to_thread, we might need to mock that or ensure kb_service.search is callable
            # The code does import asyncio inside.
            
            new_context = await rag_retrieve_step(context)
            assert len(new_context.retrieved_references) == 1
            assert new_context.retrieved_references[0]["title"] == "doc1"

@pytest.mark.asyncio
async def test_plan_step():
    context = AgentContext(session_id="test", user_message="search for something")
    
    with patch("app.workflow.steps.plan_step.Agent") as mock_agent_cls:
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        
        mock_response = MagicMock()
        mock_response.content.next_step = "retrieve"
        mock_response.content.reasoning = "need info"
        mock_agent.run.return_value = mock_response
        
        new_context = await plan_step(context)
        assert new_context.next_step == "retrieve"

@pytest.mark.asyncio
async def test_persist_step():
    context = AgentContext(
        session_id="test", 
        user_message="hi", 
        final_response="response", 
        reasoning_content="reasoning"
    )
    
    with patch("app.workflow.steps.persist_step.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session
        
        with patch("app.workflow.steps.persist_step.crud_chat") as mock_crud:
            mock_crud.create_message = AsyncMock()
            mock_crud.update_message_meta = AsyncMock()
            
            await persist_step(context)
            
            mock_crud.create_message.assert_called_once()

@pytest.mark.asyncio
async def test_agent_execute_step():
    context = AgentContext(session_id="test", user_message="hello", agent_id="agent1")
    
    with patch("app.workflow.steps.agent_execute_step.AsyncSessionLocal") as mock_db, \
         patch("app.workflow.steps.agent_execute_step.agent_manager") as mock_manager:
         
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session
        
        # Mock agent loading
        mock_agent_instance = MagicMock()
        mock_manager.create_agno_agent = AsyncMock(return_value=mock_agent_instance)
        
        # Mock DB agent object retrieval (for deepseek check)
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result
        mock_agent_obj = MagicMock()
        mock_agent_obj.model_config = {"model_id": "gpt-4"}
        mock_result.scalars.return_value.first.return_value = mock_agent_obj
        
        # Mock agent run generator
        # Agno agent.run(stream=True) returns a generator
        def mock_run(*args, **kwargs):
            yield MagicMock(content="chunk1", delta=None)
            yield MagicMock(content="chunk2", delta=None)
        mock_agent_instance.run.side_effect = mock_run
        
        new_context = await agent_execute_step(context)
        
        assert new_context.output_stream is not None
        
        # Consume stream
        chunks = []
        async for chunk in new_context.output_stream:
            chunks.append(chunk)
            
        assert len(chunks) == 2
        assert chunks[0]["content"] == "chunk1"
        assert chunks[1]["content"] == "chunk2"
