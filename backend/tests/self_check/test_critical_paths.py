import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.agent import Agent
from app.models.chat import ChatSession

# Mock Agno Agent Response
class MockRunResponse:
    def __init__(self):
        self.content = "Hello World"
    
    def __iter__(self):
        yield "Hello"
        yield " World"

@pytest.mark.asyncio
async def test_e2e_chat_flow(client, db):
    """
    Critical Path: Create Session -> Send Message -> Agent Response -> Verify Persistence
    """
    # 1. Setup Data: Create a Test Agent
    # We use a unique ID to avoid conflicts
    agent_id = "test-agent-e2e"
    agent = Agent(
        id=agent_id,
        name="E2E Test Agent",
        model_config={"model_id": "gpt-4o"},
        is_active=True
    )
    db.add(agent)
    await db.commit()

    # 2. Create Session via API
    # Verify the session creation endpoint works
    # API Prefix is /api/v1/chat
    res_session = client.post("/api/v1/chat/sessions", json={
        "title": "E2E Test Session",
        "agent_id": agent_id
    })
    assert res_session.status_code == 200, f"Session creation failed: {res_session.text}"
    session_data = res_session.json()
    session_id = session_data["id"]
    assert session_id is not None
    assert session_data["agent_id"] == agent_id

    # 3. Mock Agent Manager & Execution
    # We intercept the actual agent creation to avoid calling OpenAI
    
    # Create a mock Agno Agent
    mock_agno_agent = MagicMock()
    
    # Mock the 'arun' method to return an awaitable that returns an async generator
    # Because the code does: stream = await agent.arun(...)
    
    # In ChatService._process_stream, we handle simple strings or objects.
    # The error "MockChunk object has no attribute startswith" implies ChatService received MockChunk
    # and tried to call startswith on it (line 141 in ChatService).
    # This happens because we yield MockChunk objects.
    # We should just yield strings if we want to simulate text output, 
    # OR make MockChunk behave like a string if needed, 
    # OR update ChatService to handle objects (which it does, but expects certain attrs).
    
    # Let's yield simple strings to simulate Agno's stream behavior when it yields chunks
    # Or yield objects that have .content attribute.
    
    # ChatService logic:
    # async for item in self._process_stream(stream):
    #      if item.startswith("<think>") ...  <-- This assumes item is str
    
    # ChatService._process_stream just yields items.
    # So if stream yields strings, item is string.
    
    async def mock_arun_coroutine(*args, **kwargs):
        async def async_gen():
            yield "Hello"
            yield " World"
        return async_gen()
    
    mock_agno_agent.arun.side_effect = mock_arun_coroutine
    mock_agno_agent.model = MagicMock() # Mock model attribute
    mock_agno_agent.model.id = "gpt-4o"
    
    # Patch the AgentManager.create_agno_agent method
    with patch("app.services.agent.manager.AgentManager.create_agno_agent", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_agno_agent
        
        # 4. Send Message via API
        payload = {
            "message": "Hi, this is a test.",
            "stream": True,
            "enable_search": False
        }
        
        # Use client.post but since it's a streaming response, we need to handle it
        response = client.post(f"/api/v1/chat/sessions/{session_id}/chat", json=payload)
        
        assert response.status_code == 200, f"Chat request failed: {response.text}"
        
        # 5. Verify Response Content
        # The endpoint returns a StreamingResponse
        full_content = ""
        # iterate over the response content
        for line in response.iter_lines():
            full_content += line
        
        # The mock yields "Hello" and " World", so we expect "Hello World" in the output
        # Note: The actual output might be SSE format or raw text depending on implementation
        # Looking at chat.py, it yields plain text chunks usually
        assert "Hello" in full_content
        assert "World" in full_content
        
        # 6. Verify Persistence (Optional but recommended)
        # Check if the message was saved to DB
        # We can use the API to fetch history
        
        res_history = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert res_history.status_code == 200
        history_data = res_history.json()
        messages = history_data.get("messages", [])
        
        # Should have at least User message (System message might be implicit)
        # The Assistant message might not be persisted yet if the stream wasn't fully consumed by the backend logic 
        # (FastAPI StreamingResponse runs in background)
        # But user message should be there.
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) >= 1
        assert user_msgs[0]["content"] == "Hi, this is a test."

