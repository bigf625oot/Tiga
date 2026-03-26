
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

# Mock settings if needed
import os
os.environ["OPENAI_API_KEY"] = "dummy"

from app.services.agent.tools.tool_factory import ToolFactory

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_tool_factory():
    print("Initializing ToolFactory...")
    ToolFactory.initialize()
    
    print("Available tools:", ToolFactory._tool_classes.keys())
    
    print("\nCreating duckduckgo tool...")
    tool = ToolFactory.create_tool("duckduckgo")
    
    if tool:
        print(f"Success! Tool created: {tool}")
        print(f"Tool methods: {dir(tool)}")
        if hasattr(tool, "web_search"):
             print("web_search method exists.")
    else:
        print("Failed to create tool.")

if __name__ == "__main__":
    asyncio.run(test_tool_factory())
