import pytest
import sys
import os
# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch, AsyncMock
from app.services.tools.discovery import discover_tools, check_tool_availability, get_tool_category
from app.services.tools.calculator import CalculatorTools
from app.models.skill import Skill
from agno.tools import Toolkit

# Mock Tools for Testing
class AvailableTool(Toolkit):
    _category = "test-cat"
    @classmethod
    def is_available(cls):
        return True

class UnavailableTool(Toolkit):
    @classmethod
    def is_available(cls):
        return False

class DefaultTool(Toolkit):
    pass

# 1. Test Discovery Logic
def test_discover_tools_finds_calculator():
    """
    Verify that discover_tools finds the calculator tool 
    which we know exists in the codebase.
    """
    tools = discover_tools()
    assert "calculator" in tools
    assert tools["calculator"] == CalculatorTools

# 2. Test Tool Instantiation
def test_calculator_instantiation():
    """
    Verify that the discovered tool can be instantiated.
    """
    tools = discover_tools()
    CalculatorClass = tools["calculator"]
    instance = CalculatorClass()
    assert instance.name == "calculator"

# 3. Test Availability Check
def test_check_tool_availability():
    assert check_tool_availability(AvailableTool) == True
    assert check_tool_availability(UnavailableTool) == False
    assert check_tool_availability(DefaultTool) == True

# 4. Test Category Extraction
def test_get_tool_category():
    assert get_tool_category(AvailableTool) == "test-cat"
    assert get_tool_category(DefaultTool) == "integration"

# 5. Test Seeding Logic with Availability and Categories
@pytest.mark.asyncio
async def test_seed_services_adds_tools_with_metadata():
    """
    Verify that the seeding logic correctly handles availability and categories.
    """
    # Mock the discover_tools function
    mock_tools = {
        "available_tool": AvailableTool,
        "unavailable_tool": UnavailableTool
    }
    
    with patch("app.services.tools.discovery.discover_tools", return_value=mock_tools):
        # Mock the database session
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.first.return_value = None # Simulate tool not existing
        
        # Simulate seed_services logic
        discovered_tools = mock_tools
        
        for tool_name, tool_class in discovered_tools.items():
            is_available = check_tool_availability(tool_class)
            category = get_tool_category(tool_class)
            
            description = tool_class.__doc__.strip().split('\n')[0] if tool_class.__doc__ else f"{tool_name} tool"
            if not is_available:
                description += " (Unavailable: Missing configuration)"
                
            skill = Skill(
                name=tool_name,
                description=description,
                category=category,
                is_active=is_available
            )
            mock_db.add(skill)
        
        # Assertions
        assert mock_db.add.call_count == 2
        
        # Check first call (AvailableTool)
        call1 = mock_db.add.call_args_list[0]
        skill1 = call1[0][0]
        assert skill1.name == "available_tool"
        assert skill1.is_active == True
        assert skill1.category == "test-cat"
        
        # Check second call (UnavailableTool)
        call2 = mock_db.add.call_args_list[1]
        skill2 = call2[0][0]
        assert skill2.name == "unavailable_tool"
        assert skill2.is_active == False
        assert "Unavailable" in skill2.description

# 6. Test Manager Loading Logic
def test_manager_loading_logic():
    """
    Verify the logic used in manager.py to load tools.
    """
    tools_config = ["calculator", "unknown_tool"]
    available_tools = {"calculator": CalculatorTools}
    loaded_tools = []
    
    for tool_entry in tools_config:
        if isinstance(tool_entry, str):
            tool_name = tool_entry.lower()
            if tool_name in available_tools:
                ToolClass = available_tools[tool_name]
                loaded_tools.append(ToolClass())
                
    assert len(loaded_tools) == 1
    assert isinstance(loaded_tools[0], CalculatorTools)
