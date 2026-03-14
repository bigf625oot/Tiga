"""
Tools Endpoint
前端接口：
- HTTP GET `/tools/available` 接口作用：获取所有可用工具
- HTTP POST `/tools/{tool_id}/invoke` 接口作用：调用指定工具
- HTTP GET `/tools/{tool_id}/config` 接口作用：获取指定工具配置
前端功能：
- 管理和配置工具
- 支持工具的查询、调用和配置
前端文件：
- `app/frontend/src/pages/Tools.vue`
功能模块：
- 工具管理
"""
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
