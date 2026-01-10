try:
    from agno.tools.duckduckgo import DuckDuckGo
    print("agno.tools.duckduckgo found")
except ImportError:
    print("agno.tools.duckduckgo NOT found")

try:
    from agno.tools.mcp import McpToolkit
    print("agno.tools.mcp found")
except ImportError:
    print("agno.tools.mcp NOT found")
