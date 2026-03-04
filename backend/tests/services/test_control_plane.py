import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agent.control_plane import AgnoControlPlane
from app.services.agent.nlu import IntentResult

@pytest.mark.asyncio
async def test_control_plane_chat_intent():
    # Mock NLU
    mock_nlu_result = IntentResult(intent="chat", confidence=0.9, task_params=None)
    
    with patch("app.services.agent.control_plane.NluService") as MockNlu:
        instance = MockNlu.return_value
        instance.analyze = AsyncMock(return_value=mock_nlu_result)
        # Mock Chat Response
        instance.model.response.return_value.content = "Hello there!"
        
        cp = AgnoControlPlane()
        response = await cp.process_input("Hello")
        
        assert response == "Hello there!"
        instance.analyze.assert_called_once()

@pytest.mark.asyncio
async def test_control_plane_task_intent():
    # Mock NLU
    mock_nlu_result = IntentResult(
        intent="task", 
        confidence=0.95, 
        task_params={"task_type": "crawler", "target": "http://example.com"}
    )
    
    with patch("app.services.agent.control_plane.NluService") as MockNlu:
        nlu_instance = MockNlu.return_value
        nlu_instance.analyze = AsyncMock(return_value=mock_nlu_result)
        
        # Mock Client
        with patch("app.services.agent.control_plane.AgnoGatewayClient") as MockClient:
            client_instance = MockClient.return_value
            client_instance.is_connected = True
            client_instance.execute_task = AsyncMock(return_value={
                "method": "task_completed",
                "params": {"result": "Success"}
            })
            
            cp = AgnoControlPlane()
            cp.client = client_instance # Inject mock
            
            response = await cp.process_input("Crawl example.com")
            
            assert "Task completed successfully" in response
            client_instance.execute_task.assert_called_once()

@pytest.mark.asyncio
async def test_control_plane_reconnect_logic():
    # Test auto-connect if disconnected
    mock_nlu_result = IntentResult(
        intent="task", 
        confidence=0.95, 
        task_params={"task_type": "crawler", "target": "http://example.com"}
    )
    
    with patch("app.services.agent.control_plane.NluService") as MockNlu:
        nlu_instance = MockNlu.return_value
        nlu_instance.analyze = AsyncMock(return_value=mock_nlu_result)
        
        with patch("app.services.agent.control_plane.AgnoGatewayClient") as MockClient:
            client_instance = MockClient.return_value
            # Initially disconnected, then connected
            client_instance.is_connected = False
            
            async def mock_connect():
                client_instance.is_connected = True
            
            client_instance.connect = AsyncMock(side_effect=mock_connect)
            client_instance.execute_task = AsyncMock(return_value={
                "method": "task_completed",
                "params": {"result": "Success"}
            })
            
            cp = AgnoControlPlane()
            cp.client = client_instance
            
            response = await cp.process_input("Crawl example.com")
            
            assert "Task completed successfully" in response
            client_instance.connect.assert_called_once()
