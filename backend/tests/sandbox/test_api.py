import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app

# --- Fixtures ---

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_codebox_service():
    with patch("app.api.endpoints.sandbox.codebox_service") as mock_service:
        yield mock_service

# --- Tests ---

def test_api_001_run_code_sync(client, mock_codebox_service):
    """API-001: POST /run (Sync Execution)"""
    mock_codebox_service.execute = AsyncMock(return_value={
        "status": "success",
        "content": "Hello World",
        "type": "text",
        "files": [],
        "session_id": "test-session"
    })
    
    response = client.post("/api/v1/sandbox/run", json={
        "code": "print('Hello World')",
        "session_id": "test-session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["content"] == "Hello World"
    
    mock_codebox_service.execute.assert_called_once()

def test_api_002_run_code_missing_param(client):
    """API-002: POST /run (Missing Code)"""
    response = client.post("/api/v1/sandbox/run", json={
        "session_id": "test-session"
    })
    
    # Expect 400 Bad Request (Manual validation in endpoint)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_api_003_ws_execution(client, mock_codebox_service):
    """API-003: WS /ws/{id} (Streaming Execution)"""
    
    # Mock execute to simulate streaming callbacks
    async def mock_execute(code, session_id, on_stdout=None, on_stderr=None):
        if on_stdout:
            # The endpoint passes a sync callback (on_stdout) which uses loop.call_soon_threadsafe
            # We call it with a string
            on_stdout("Hello ")
            on_stdout("World")
            
            # Important: Yield control to event loop to allow call_soon_threadsafe callbacks 
            # to populate the queue before we return the final result.
            import asyncio
            await asyncio.sleep(0.01)
            
        return {
            "status": "success",
            "content": "Hello World",
            "type": "text",
            "files": [],
            "session_id": session_id
        }
    
    mock_codebox_service.execute.side_effect = mock_execute
    
    session_id = "ws-test-session"
    
    with client.websocket_connect(f"/api/v1/sandbox/ws/{session_id}") as websocket:
        # Send execution request
        websocket.send_json({
            "action": "execute",
            "code": "print('Hello World')"
        })
        
        # Expect start status
        msg_start = websocket.receive_json()
        assert msg_start["type"] == "status"
        assert msg_start["content"] == "running"

        # Expect streaming messages
        msg1 = websocket.receive_json()
        assert msg1["type"] == "stdout"
        assert msg1["content"] == "Hello \n"
        
        msg2 = websocket.receive_json()
        assert msg2["type"] == "stdout"
        assert msg2["content"] == "World\n"
        
        # Expect final result
        msg3 = websocket.receive_json()
        assert msg3["type"] == "result"
        assert msg3["result"]["status"] == "success"
        
        # Expect status done
        msg4 = websocket.receive_json()
        assert msg4["type"] == "status"
        assert msg4["content"] == "success"

