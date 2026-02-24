import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat.service import ChatService
from app.models.chat import ChatSession, ChatMessage
from app.models.agent import Agent
from app.models.llm_model import LLMModel

@pytest.fixture
def chat_service():
    return ChatService()

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_process_chat_session_not_found(chat_service, mock_db_session):
    # Mock crud_chat.get to return None
    with patch("app.crud.crud_chat.chat.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        generator = chat_service.process_chat("invalid-session", "hello", mock_db_session)
        response = []
        async for chunk in generator:
            response.append(chunk)
            
        assert "Error: Session not found" in response

@pytest.mark.asyncio
async def test_process_chat_success_flow(chat_service, mock_db_session):
    # Setup mocks
    session_id = "test-session"
    mock_session = ChatSession(id=session_id, agent_id="test-agent")
    mock_agent = MagicMock()
    mock_agent.arun = AsyncMock(return_value="Hello World")
    
    # Mock dependencies
    with patch("app.crud.crud_chat.chat.get", new_callable=AsyncMock) as mock_get_session, \
         patch("app.crud.crud_chat.chat.create_message", new_callable=AsyncMock) as mock_create_msg, \
         patch("app.services.chat.service.ChatService._load_agent", new_callable=AsyncMock) as mock_load_agent, \
         patch("app.services.chat.service.ChatService._save_assistant_message", new_callable=AsyncMock) as mock_save, \
         patch("app.services.chat.service.ChatService._build_history", new_callable=AsyncMock) as mock_history, \
         patch("app.services.chat.service.ChatService._get_allowed_docs", new_callable=AsyncMock) as mock_docs:
        
        mock_get_session.return_value = mock_session
        mock_create_msg.return_value = ChatMessage(id="msg-1", role="user", content="hi")
        mock_load_agent.return_value = (mock_agent, MagicMock())
        mock_history.return_value = []
        mock_docs.return_value = ([], False)
        
        # Mock streaming response
        async def mock_stream_gen():
            yield "Hello"
            yield " World"
        
        mock_agent.arun.return_value = mock_stream_gen()

        # Execute
        generator = chat_service.process_chat(session_id, "hi", mock_db_session)
        chunks = []
        async for chunk in generator:
            chunks.append(chunk)
            
        # Verify
        full_response = "".join(chunks)
        assert "Hello World" in full_response
        mock_create_msg.assert_called()
        mock_save.assert_called()

@pytest.mark.asyncio
async def test_detect_deepseek(chat_service):
    # Test case 1: Model ID contains deepseek
    # The ChatService checks:
    # 1. agent_obj.model_config exists
    # 2. agent_obj.model_config.get("model_id") (if dict) or .model_id (if obj)
    
    # Let's use a class that behaves like what Pydantic model dump might look like in the code context
    # or just a simple object with model_config as dict
    
    agent_obj = MagicMock()
    agent_obj.model_config = {"model_id": "deepseek-v3"}
    # We must ensure hasattr(agent_obj, "model_config") is True. MagicMock does this by default.
    # But when accessing agent_obj.model_config, it returns the dict.
    
    # Wait, if we use MagicMock, hasattr usually works.
    # Let's try explicitly mocking the attribute access if previous attempts failed.
    # Actually, the failure might be because I'm passing None as agent, and the code returns False early?
    # No, code: if not agent: return False
    # I WAS PASSING None as agent in the failing test!
    # assert chat_service._detect_deepseek(None, agent_obj) == True
    # The first line of _detect_deepseek is: if not agent: return False
    # So it ALWAYS returns False if agent is None.
    
    # FIX: Pass a dummy agent
    dummy_agent = MagicMock()
    
    class MockAgentObj:
        def __init__(self):
            self.model_config = {"model_id": "deepseek-v3"}
            
    agent_obj = MockAgentObj()
    
    assert chat_service._detect_deepseek(dummy_agent, agent_obj) == True
    
    # Test case 2: Agent model object has provider
    class MockModel:
        def __init__(self):
            self.id = "custom-model"
            self.provider = "aliyun"
            self.base_url = ""
    
    class MockAgent:
        def __init__(self):
            self.model = MockModel()

    agent = MockAgent()
    assert chat_service._detect_deepseek(agent, None) == True
    
    # Test case 3: Negative case
    class MockModelNeg:
        def __init__(self):
            self.id = "gpt-4"
            self.provider = "openai"
            self.base_url = ""

    class MockAgentNeg:
        def __init__(self):
            self.model = MockModelNeg()

    class MockAgentObjNeg:
        def __init__(self):
            self.model_config = {"model_id": "gpt-4"}

    assert chat_service._detect_deepseek(MockAgentNeg(), MockAgentObjNeg()) == False
