import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.tools.discovery import discover_tools, TOOLS_DIR
from agno.tools import Toolkit

def test_discover_tools_finds_existing():
    """Test that discovery finds existing tools like calculator."""
    tools = discover_tools()
    print(f"Found tools: {list(tools.keys())}")
    
    assert "calculator" in tools
    assert "duckduckgo" in tools
    assert issubclass(tools["calculator"], Toolkit)

def test_new_tool_discovery():
    """Test that a newly created tool file is discovered."""
    
    # 1. Create a temporary tool file in the tools directory
    new_tool_name = "test_temp_tool"
    tool_file = TOOLS_DIR / f"{new_tool_name}.py"
    
    tool_content = """
from agno.tools import Toolkit

class TestTempTool(Toolkit):
    def __init__(self):
        super().__init__(name="test_temp_tool")
        self.register(self.echo)

    def echo(self, text: str):
        return text
"""
    
    try:
        with open(tool_file, "w") as f:
            f.write(tool_content)
            
        # 2. Clear cache and re-discover
        discover_tools.cache_clear()
        
        # We need to invalidate import caches too for the new module to be picked up?
        # pkgutil.iter_modules should pick it up from disk.
        
        tools = discover_tools()
        
        # 3. Assert it is found
        assert new_tool_name in tools
        assert tools[new_tool_name].__name__ == "TestTempTool"
        
    finally:
        # Cleanup
        if tool_file.exists():
            os.remove(tool_file)
            
        # Clean up sys.modules if needed (though we didn't import it explicitly in test, discover_tools did)
        if f"app.services.tools.{new_tool_name}" in sys.modules:
            del sys.modules[f"app.services.tools.{new_tool_name}"]

if __name__ == "__main__":
    # Manually run if executed as script
    try:
        test_discover_tools_finds_existing()
        print("test_discover_tools_finds_existing passed")
        test_new_tool_discovery()
        print("test_new_tool_discovery passed")
    except Exception as e:
        print(f"Tests failed: {e}")
        import traceback
        traceback.print_exc()
