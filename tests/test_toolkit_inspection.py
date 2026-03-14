import sys
import os
import json
from pydantic import BaseModel, Field

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.eah_agent.tools.libs.duckduckgo import DuckDuckGoTools

def inspect_toolkit():
    ddg = DuckDuckGoTools()
    print(f"Toolkit: {ddg}")
    print(f"Dir: {dir(ddg)}")
    
    # Check if there is a method to get tools
    if hasattr(ddg, "get_tools"):
        tools = ddg.get_tools()
        print(f"get_tools() returned {len(tools)} tools")
        for t in tools:
            print(f" - Name: {t.name}")
            print(f" - Description: {t.description}")
            print(f" - Function: {t.func}")
            
            # Check if we can get schema
            if hasattr(t, "to_openai_function"):
                print(f" - Schema: {json.dumps(t.to_openai_function(), indent=2)}")
            elif hasattr(t, "to_openai_schema"):
                print(f" - Schema: {json.dumps(t.to_openai_schema(), indent=2)}")
                
    # Check for functions map
    if hasattr(ddg, "functions"):
         print(f"functions: {ddg.functions}")

if __name__ == "__main__":
    inspect_toolkit()
