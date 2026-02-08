import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent.manager import AgentManager
from app.services.agent.tools.mcp_tool import MCPToolkit
from app.models.agent import Agent as AgentModel
from app.models.llm_model import LLMModel

@pytest.mark.asyncio
async def test_agent_manager_mcp_integration():
    # Mock DB Session
    mock_db = AsyncMock()
    
    # Mock Agent Model
    agent_model = AgentModel(
        id="test_agent",
        name="Test Agent",
        model_config={"model_id": "gpt-4o"},
        mcp_config=[{"url": "ws://mcp-server:8080"}]
    )
    
    # Mock LLM Model
    llm_model = LLMModel(
        model_id="gpt-4o",
        is_active=True,
        api_key="sk-test",
        provider="openai"
    )
    
    # Mock DB results
    # First query: select Agent
    # Second query: select LLMModel
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: agent_model)),
        MagicMock(scalars=lambda: MagicMock(first=lambda: llm_model))
    ]
    
    # Mock MCP Pool
    with patch("app.services.agent.manager.mcp_pool") as mock_pool:
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.list_tools.return_value = [
            {
                "name": "weather_tool",
                "description": "Get weather",
                "inputSchema": {"type": "object"}
            }
        ]
        mock_pool.get_client.return_value = mock_client
        
        # Call create_agno_agent
        manager = AgentManager.get_instance()
        agent = await manager.create_agno_agent(mock_db, "test_agent")
        
        # Verification
        assert agent is not None
        # Check if MCPToolkit is in tools
        has_mcp = False
        for tool in agent.tools:
            if isinstance(tool, MCPToolkit):
                has_mcp = True
                assert tool.client == mock_client
                # Check registered tools
                assert "weather_tool" in tool.tool_map
        
        assert has_mcp
        mock_client.connect.assert_called_once()
        mock_client.list_tools.assert_called_once()
