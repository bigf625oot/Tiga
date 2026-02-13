import pytest
import logging
import json
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.schemas.chat import ChatSessionResponse, ChatMessageResponse

# Mock data for session
MOCK_SESSION_ID = "test_session_iso"

@pytest.mark.asyncio
async def test_task_space_read_isolation(client, caplog):
    """
    Verify that reading task space data (session details) does not trigger system logs.
    Requirement 1: Task space refresh/pagination/filtering (read operations) should not trigger extra logs.
    """
    # Create a proper Pydantic model for the return value to satisfy FastAPI validation
    mock_session_data = {
        "id": MOCK_SESSION_ID,
        "title": "Isolation Test",
        "agent_id": "test_agent",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "workflow_state": {"tasks": [], "logs": []},
        "messages": []
    }
    
    # We patch the CRUD get method
    with patch("app.api.endpoints.chat.crud_chat.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_session_data
        
        # Clear existing logs
        caplog.clear()
        
        # Set level to INFO to capture relevant app logs
        with caplog.at_level(logging.INFO):
            response = client.get(f"/api/v1/chat/sessions/{MOCK_SESSION_ID}")
            
            # Verify request success
            assert response.status_code == 200, f"Request failed: {response.text}"
            
            # Assert NO logs were captured during the read operation from our app
            # Filter for app-specific logs to avoid noise
            app_logs = [r for r in caplog.records if r.name.startswith("app.")]
            assert len(app_logs) == 0, f"Expected no app logs, got: {[r.message for r in app_logs]}"

@pytest.mark.asyncio
async def test_log_decoupling_structure(client):
    """
    Verify that the system returns distinct structures for Task Updates vs System Logs.
    Requirement: Display data (step, status, output) is decoupled from system logs.
    """
    # Define the mock generator properly
    async def mock_run_stream_gen(*args, **kwargs):
        # 1. System Log Event
        yield json.dumps({
            "system": True, 
            "status": "info", 
            "output": "[System] Initializing..."
        })
        # 2. Task Update Event (Display Data)
        yield json.dumps({
            "step": "execute", 
            "status": "running", 
            "output": "Task execution output"
        })
        # 3. Another System Log
        yield json.dumps({
            "system": True,
            "status": "warning",
            "output": "[System] Memory warning"
        })

    # Patch AppWorkflow class
    with patch("app.api.endpoints.agent_workflow.AppWorkflow") as MockWorkflowClass:
        # Configure the instance returned by the class
        mock_instance = MockWorkflowClass.return_value
        # Assign the generator function to run_stream
        mock_instance.run_stream = mock_run_stream_gen
        
        # We also need to mock crud_chat dependencies used in the endpoint
        with patch("app.api.endpoints.agent_workflow.crud_chat") as mock_crud:
            mock_crud.create_message = AsyncMock()
            mock_crud.get_history = AsyncMock(return_value=[])
            
            response = client.post(
                "/api/v1/agent-workflows/run_stream",
                json={
                    "session_id": "test_session_decouple", 
                    "message": "start task",
                    "mode": "static"
                }
            )
            
            assert response.status_code == 200
            
            # Parse SSE output
            content = response.content.decode("utf-8")
            lines = [l for l in content.split("\n\n") if l.strip()]
            data_lines = [l for l in lines if l.startswith("data: ") and "[DONE]" not in l]
            
            events = [json.loads(l.replace("data: ", "")) for l in data_lines]
            
            assert len(events) == 3, f"Expected 3 events, got {len(events)}: {events}"
            
            # Check Decoupling:
            # Event 0: System Log
            assert events[0].get("system") is True
            assert "[System]" in events[0].get("output")
            
            # Event 1: Task Update
            # Ensure it has step/status/output for UI
            assert events[1].get("step") == "execute"
            assert events[1].get("output") == "Task execution output"
            # Ensure it does NOT look like a system log
            assert not events[1].get("system")
            
            # Event 2: System Log
            assert events[2].get("system") is True

@pytest.mark.asyncio
async def test_log_writing_performance_mock(client):
    """
    Verify high concurrency log writing does not significantly block.
    Requirement 2: High concurrency log writing time deviation.
    """
    from app.workflow.app_workflow import AsyncLogHandler
    
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    handler = AsyncLogHandler(queue, loop)
    
    # Measure time to emit 10000 logs
    start = time.time()
    for i in range(10000):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg=f"Log {i}", args=(), exc_info=None
        )
        handler.emit(record)
    end = time.time()
    
    duration = end - start
    # Should be extremely fast because it just puts to queue (or schedules task)
    assert duration < 1.0, f"Log emission took too long: {duration}s"
    
    # Allow some time for async tasks to process
    await asyncio.sleep(0.1) 
    assert not queue.empty()
