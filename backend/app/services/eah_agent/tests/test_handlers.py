import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from app.services.eah_agent.handlers.plan_handler import PlanHandler
from app.services.eah_agent.handlers.team_handler import TeamHandler
from app.services.eah_agent.handlers.flow_handler import FlowHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.models.llm_model import LLMModel

class TestPlanHandler(unittest.IsolatedAsyncioTestCase):
    async def test_process_stream(self):
        # Mock AgentFactory
        with patch('app.services.eah_agent.handlers.plan_handler.AgentFactory') as mock_factory:
            # Setup mock agent (MagicMock, not AsyncMock, because run() is sync)
            mock_agent = MagicMock()
            
            # Mock agent.run(stream=True) returning a generator
            def mock_run_stream(*args, **kwargs):
                yield MagicMock(content="Thinking...")
                yield MagicMock(content="Result")
            
            mock_agent.run.side_effect = mock_run_stream
            
            # create_agent is awaited, so it must be AsyncMock returning mock_agent
            mock_factory.create_agent = AsyncMock(return_value=mock_agent)

            handler = PlanHandler(LLMModel(model_id="test", provider="openai"))
            intent = IntentResult(intent="task", confidence=1.0)
            
            # Execute
            results = []
            async for chunk in handler.process("Do X", intent):
                results.append(chunk)

            # Verify
            self.assertTrue(len(results) >= 2)
            self.assertEqual(results[0]["type"], "status")
            self.assertIn("content", results[1])

class TestTeamHandler(unittest.IsolatedAsyncioTestCase):
    async def test_process_stream(self):
        # Mock AgentFactory
        with patch('app.services.eah_agent.handlers.team_handler.AgentFactory') as mock_factory:
            # Setup mock team agent
            mock_team = MagicMock()
            
            def mock_run_stream(*args, **kwargs):
                yield MagicMock(content="Team working...")
                yield MagicMock(content="Done")
            
            mock_team.run.side_effect = mock_run_stream
            
            # create_team is awaited
            mock_factory.create_team = AsyncMock(return_value=mock_team)

            handler = TeamHandler(LLMModel(model_id="test", provider="openai"))
            intent = IntentResult(intent="team", confidence=1.0)
            
            # Execute
            results = []
            async for chunk in handler.process("Build a team", intent, db=MagicMock()):
                results.append(chunk)

            # Verify
            self.assertTrue(len(results) >= 2)
            self.assertEqual(results[0]["type"], "status")
            self.assertIn("content", results[1])

class TestFlowHandler(unittest.IsolatedAsyncioTestCase):
    async def test_process_stream(self):
        # Mock AgentWorkflowEngine
        with patch('app.services.eah_agent.handlers.flow_handler.AgentWorkflowEngine') as MockEngine:
            mock_engine_instance = MockEngine.return_value
            
            async def mock_start_workflow(*args, **kwargs):
                yield {"type": "status", "content": "Starting"}
                yield {"type": "content", "content": "Finished"}
            
            mock_engine_instance.start_workflow.side_effect = mock_start_workflow

            handler = FlowHandler(LLMModel(model_id="test", provider="openai"))
            intent = IntentResult(intent="workflow", confidence=1.0)
            
            # Execute
            results = []
            async for chunk in handler.process("Start flow", intent, db=AsyncMock(), session_id="test-session"):
                results.append(chunk)

            # Verify
            # 1 status from handler + 2 from engine = 3
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0]["content"], "Initializing Workflow Engine...")
            self.assertEqual(results[1]["content"], "Starting")
            self.assertEqual(results[2]["content"], "Finished")

if __name__ == '__main__':
    unittest.main()
