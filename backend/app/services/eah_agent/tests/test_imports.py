import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parents[4]))

try:
    from app.services.eah_agent.core.agent_manager import AgentManager
    from app.services.eah_agent.skills.manager import Skills
    from app.services.eah_agent.tools.registry import discover_tools
    from app.services.eah_agent.core.service import AgentService
    
    print("Imports successful!")
    
    # Check if tools are discoverable
    tools = discover_tools()
    print(f"Discovered {len(tools)} tools.")
    
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
