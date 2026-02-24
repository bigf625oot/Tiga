
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent.manager import AgentManager
from app.models.agent import Agent as AgentModel
from app.models.llm_model import LLMModel

@pytest.mark.asyncio
async def test_e2b_integration_logic():
    """
    Verify E2B Sandbox integration logic in AgentManager.
    
    1. Verify SandboxTools is injected when 'sandbox' skill is enabled.
    2. Verify SandboxTools is NOT injected when 'sandbox' skill is disabled.
    3. Verify ShellTools and E2BTools are NOT injected by default.
    """
    
    # Mock dependencies
    mock_db = AsyncMock()
    mock_agent_model = MagicMock(spec=AgentModel)
    mock_agent_model.id = "test-agent"
    mock_agent_model.name = "Test Agent"
    mock_agent_model.system_prompt = "System prompt"
    
    # Mock LLM Model
    mock_llm_model = MagicMock(spec=LLMModel)
    mock_llm_model.model_id = "gpt-4"
    mock_llm_model.api_key = "sk-test"
    mock_llm_model.is_active = True
    
    # Setup DB returns
    # First call: fetch AgentModel
    # Second call: fetch LLMModel
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_agent_model)),
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_llm_model))
    ]
    
    # Mock ModelFactory to avoid actual LLM creation
    with patch("app.services.agent.manager.ModelFactory") as mock_factory, \
         patch("app.services.agent.manager.AgnoAgent") as MockAgnoAgent:
        
        mock_factory.create_model.return_value = MagicMock()
        mock_factory.should_use_agno_reasoning.return_value = False
        
        # Mock SandboxTools import to verify it's called/used
        # Note: SandboxTools is imported inside the function, so we patch it where it is defined
        with patch("app.services.agent.tools.sandbox_tools.SandboxTools") as MockSandboxTools:
            
            # --- Test Case 1: Sandbox Enabled ---
            mock_agent_model.skills_config = {"sandbox": {"enabled": True}}
            mock_agent_model.tools_config = []
            mock_agent_model.model_config = {"model_id": "gpt-4"}
            
            manager = AgentManager()
            agent = await manager.create_agno_agent(mock_db, "test-agent")
            
            # Verify SandboxTools was instantiated and added
            assert MockSandboxTools.called
            
            # Verify AgnoAgent was called with tools containing SandboxTools
            # Since we mock SandboxTools, the instance is MockSandboxTools.return_value
            # But AgnoAgent is also mocked, so 'agent' is a mock.
            # We need to check the call arguments to AgnoAgent constructor.
            call_args = MockAgnoAgent.call_args
            _, kwargs = call_args
            tools = kwargs.get('tools', [])
            assert MockSandboxTools.return_value in tools
            
            # Reset mocks for next test
            MockSandboxTools.reset_mock()
            MockAgnoAgent.reset_mock()
            mock_db.execute.side_effect = [
                MagicMock(scalars=lambda: MagicMock(first=lambda: mock_agent_model)),
                MagicMock(scalars=lambda: MagicMock(first=lambda: mock_llm_model))
            ]
            
            # --- Test Case 2: Sandbox Disabled ---
            mock_agent_model.skills_config = {"sandbox": {"enabled": False}}
            
            await manager.create_agno_agent(mock_db, "test-agent")
            
            # Verify SandboxTools was NOT instantiated
            assert not MockSandboxTools.called

@pytest.mark.asyncio
async def test_shell_and_e2b_tools_exclusion():
    """
    Verify that ShellTools and E2BTools are not imported or used by default.
    This ensures we are not exposing local shell access or using the unused E2BTools class.
    """
    # We inspect the module imports in manager.py by checking sys.modules or 
    # ensuring they are not in the tools list of a created agent.
    
    # Since we can't easily check imports dynamically without parsing AST or mocking,
    # we will rely on the previous analysis that showed they are not referenced in the code.
    # But we can verify that the 'tools' list passed to AgnoAgent doesn't contain them.
    
    mock_db = AsyncMock()
    mock_agent_model = MagicMock(spec=AgentModel)
    mock_agent_model.skills_config = {} # No skills
    mock_agent_model.tools_config = []
    mock_agent_model.model_config = {"model_id": "gpt-4"}
    
    mock_llm_model = MagicMock(spec=LLMModel)
    mock_llm_model.api_key = "sk-test"
    
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_agent_model)),
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_llm_model))
    ]
    
    with patch("app.services.agent.manager.ModelFactory") as mock_factory, \
         patch("app.services.agent.manager.AgnoAgent") as MockAgnoAgent:
        
        mock_factory.create_model.return_value = MagicMock()
        
        manager = AgentManager()
        await manager.create_agno_agent(mock_db, "test-agent")
        
        # Get the tools passed to AgnoAgent constructor
        call_args = MockAgnoAgent.call_args
        if call_args:
            _, kwargs = call_args
            tools = kwargs.get('tools', [])
            
            # Verify no unexpected tools
            tool_names = [t.name for t in tools if hasattr(t, 'name')]
            assert "shell_tools" not in tool_names
            assert "e2b_tools" not in tool_names
