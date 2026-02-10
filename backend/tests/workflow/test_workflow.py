import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.workflow.app_workflow import AppWorkflow
import json

@pytest.mark.asyncio
async def test_workflow_static_run():
    with patch("app.workflow.app_workflow.rag_retrieve_step", new_callable=AsyncMock) as mock_retrieve, \
         patch("app.workflow.app_workflow.agent_execute_step", new_callable=AsyncMock) as mock_execute, \
         patch("app.workflow.app_workflow.persist_step", new_callable=AsyncMock) as mock_persist:
         
        wf = AppWorkflow(session_id="test", mode="static")
        
        # Mock steps
        mock_retrieve.side_effect = lambda c: c
        
        async def mock_exec_impl(c):
            # Generator for output stream
            async def gen():
                yield {"type": "content", "content": "hello"}
            c.output_stream = gen()
            return c
        mock_execute.side_effect = mock_exec_impl
        
        mock_persist.side_effect = lambda c: c
        
        result = await wf.run("hi")
        assert result == "hello"
        
        mock_retrieve.assert_called_once()
        mock_execute.assert_called_once()
        mock_persist.assert_called_once()

@pytest.mark.asyncio
async def test_workflow_dynamic_run():
    with patch("app.workflow.app_workflow.plan_step", new_callable=AsyncMock) as mock_plan, \
         patch("app.workflow.app_workflow.rag_retrieve_step", new_callable=AsyncMock) as mock_retrieve, \
         patch("app.workflow.app_workflow.agent_execute_step", new_callable=AsyncMock) as mock_execute, \
         patch("app.workflow.app_workflow.persist_step", new_callable=AsyncMock) as mock_persist:
         
        wf = AppWorkflow(session_id="test", mode="dynamic")
        
        # Mock sequence: Plan(retrieve) -> Retrieve -> Plan(execute) -> Execute -> Plan(finish)
        
        async def plan_side_effect(c):
            if not c.next_step:
                c.next_step = "retrieve"
            elif c.next_step == "retrieve":
                c.next_step = "execute"
            elif c.next_step == "execute":
                c.next_step = "finish"
            return c
        mock_plan.side_effect = plan_side_effect
        
        mock_retrieve.side_effect = lambda c: c
        mock_execute.side_effect = lambda c: c
        
        # Just run streaming to trigger loop
        async for _ in wf.run_stream("hi"):
            pass
            
        assert mock_plan.call_count >= 3
        mock_retrieve.assert_called_once()
        mock_execute.assert_called_once()
