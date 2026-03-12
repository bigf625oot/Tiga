from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user_tool import UserTool
from app.services.eah_agent.tools.registry import discover_tools

router = APIRouter()

@router.get("/available")
async def list_available_tools():
    """
    List all available tools and their configuration schemas.
    """
    return discover_tools(include_metadata=True)

@router.post("/{tool_id}/invoke")
async def invoke_tool(
    tool_id: str,
    user_tool: UserTool = Depends(deps.get_current_user_tools)
):
    """
    Invoke a tool. Requires permission.
    """
    return {"status": "success", "message": f"Tool {tool_id} invoked", "granted_by": user_tool.granted_by}

@router.get("/{tool_id}/config")
async def get_tool_config(
    tool_id: str,
    user_tool: UserTool = Depends(deps.get_current_user_tools)
):
    """
    Get tool configuration. Requires permission.
    """
    return {"tool_id": tool_id, "config": "secret_config"}
