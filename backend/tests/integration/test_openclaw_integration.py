import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.openclaw.gateway.service import OpenClawService
from app.services.openclaw.task.execution import OpenClawTaskWorker
from app.models.openclaw_task import OpenClawTask

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    # Mock commit/rollback
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_tools():
    with patch("app.services.openclaw.gateway.service.OpenClawTools") as MockTools:
        instance = MockTools.return_value
        instance.client = AsyncMock()
        instance.client.is_connected = True
        instance._execute_ws = AsyncMock(return_value={"ok": True, "result": "success"})
        instance.aclose = AsyncMock()
        yield instance

@pytest.mark.asyncio
async def test_create_task_flow(mock_db_session, mock_tools):
    # Mock parse_task_intent
    with patch("app.services.openclaw.gateway.service.parse_task_intent") as mock_parse:
        mock_parse.return_value = {
            "intent_type": "task",
            "command": "crawl example.com",
            "schedule": "0 9 * * *"
        }
        
        # Mock Task CRUD
        with patch("app.services.openclaw.gateway.service.OpenClawTaskCRUD") as MockCRUD:
            mock_task = OpenClawTask(task_id="test-task-1", status="PENDING")
            mock_task.is_pending = lambda: True
            MockCRUD.create_task = AsyncMock(return_value=(mock_task, True))
            
            # Mock Worker dispatch
            with patch("app.services.openclaw.gateway.service.task_worker") as mock_worker:
                mock_worker.dispatch_task = AsyncMock()
                
                service = OpenClawService()
                service.tools = mock_tools # Inject mock tools
                
                # Execute
                result = await service.create_task("crawl example.com", mock_db_session)
                
                # Verify
                assert result["task_id"] == "test-task-1"
                assert result["status"] == "PENDING"
                
                # Verify worker dispatch called
                mock_worker.dispatch_task.assert_called_once()
                
                # Verify parse called
                mock_parse.assert_called_once()

@pytest.mark.asyncio
async def test_create_task_chat_intent(mock_db_session, mock_tools):
    # Mock parse_task_intent for chat
    with patch("app.services.openclaw.gateway.service.parse_task_intent") as mock_parse:
        mock_parse.return_value = {
            "intent_type": "chat",
            "command": "chat hello"
        }
        
        service = OpenClawService()
        service.tools = mock_tools
        # Mock chat completion
        service.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": "Hi there!"}}]})
        
        # Execute
        result = await service.create_task("hello", mock_db_session)
        
        # Verify
        assert result["status"] == "SKIPPED"
        assert result["chat_response"] == "Hi there!"
