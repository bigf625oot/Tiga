import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from app.services.eah_agent.core.nlu import NluService, IntentResult
from app.models.llm_model import LLMModel

class TestNluService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.llm_model = LLMModel(model_id="test-model", provider="openai", api_key="test-key")
        self.nlu = NluService(self.llm_model)
        
        # Mock the model factory or the model instance inside NluService
        # Since NluService creates self.model in __init__, we need to mock it after creation or patch ModelFactory
        self.mock_model = MagicMock()
        self.nlu.model = self.mock_model

    async def test_analyze_chat_intent(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "intent": "chat",
            "confidence": 0.95,
            "task_params": None
        })
        self.mock_model.response.return_value = mock_response

        # Execute
        result = await self.nlu.analyze("Hello, how are you?")

        # Verify
        self.assertEqual(result.intent, "chat")
        self.assertEqual(result.confidence, 0.95)
        self.assertIsNone(result.task_params)

    async def test_analyze_task_intent(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "intent": "task",
            "confidence": 0.98,
            "task_params": {
                "task_type": "crawler",
                "target": "https://example.com"
            }
        })
        self.mock_model.response.return_value = mock_response

        # Execute
        result = await self.nlu.analyze("Crawl https://example.com for me")

        # Verify
        self.assertEqual(result.intent, "task")
        self.assertEqual(result.task_params["task_type"], "crawler")
        self.assertEqual(result.task_params["target"], "https://example.com")

    async def test_analyze_team_intent(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "intent": "team",
            "confidence": 0.9,
            "task_params": {
                "team_type": "research",
                "roles": ["researcher", "writer"]
            }
        })
        self.mock_model.response.return_value = mock_response

        # Execute
        result = await self.nlu.analyze("Assemble a research team to write a report")

        # Verify
        self.assertEqual(result.intent, "team")
        self.assertEqual(result.task_params["team_type"], "research")
        self.assertIn("writer", result.task_params["roles"])

    async def test_analyze_workflow_intent(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "intent": "workflow",
            "confidence": 0.92,
            "task_params": {
                "workflow_name": "report_generation"
            }
        })
        self.mock_model.response.return_value = mock_response

        # Execute
        result = await self.nlu.analyze("Start the report generation workflow")

        # Verify
        self.assertEqual(result.intent, "workflow")
        self.assertEqual(result.task_params["workflow_name"], "report_generation")

    async def test_analyze_failure_fallback(self):
        # Setup mock to raise exception
        self.mock_model.response.side_effect = Exception("Model error")

        # Execute
        result = await self.nlu.analyze("Some input")

        # Verify fallback
        self.assertEqual(result.intent, "chat")
        self.assertEqual(result.confidence, 0.0)

if __name__ == '__main__':
    unittest.main()
