from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user_tool import UserTool

router = APIRouter()

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
