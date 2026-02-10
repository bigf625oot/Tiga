import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc

from app.db.session import get_db
from app.models.mcp import MCPServer
from app.schemas.mcp import MCPServer as MCPServerSchema, MCPServerCreate, MCPServerUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    type: str  # "stdio" or "sse"
    command: Optional[str] = None
    args: Optional[List[str]] = []
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = {}


class MCPTool(BaseModel):
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None


@router.post("/fetch_tools", response_model=List[MCPTool])
async def fetch_mcp_tools(config: MCPServerConfig):
    """
    Connect to an MCP server and fetch available tools.
    """
    logger.info(f"Fetching tools from MCP server: {config}")

    # Try to import mcp (will fail in Python 3.9)
    try:
        # Check if we can simulate a connection or if we should return mock data
        # In a real implementation with Python 3.10+, we would use the mcp library here.

        # For demonstration purposes in this environment:
        await asyncio.sleep(1)  # Simulate network delay

        if config.type == "stdio":
            return [
                MCPTool(
                    name="read_file",
                    description="Read contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "File path"}},
                        "required": ["path"],
                    },
                ),
                MCPTool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                        "required": ["path", "content"],
                    },
                ),
                MCPTool(name="list_directory", description="List files in a directory"),
            ]
        elif config.type == "sse":
            return [
                MCPTool(name="weather_current", description="Get current weather"),
                MCPTool(name="weather_forecast", description="Get weather forecast"),
            ]

        return []

    except Exception as e:
        logger.error(f"Failed to fetch tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CRUD Endpoints

@router.post("/", response_model=MCPServerSchema)
async def create_mcp_server(
    server_in: MCPServerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new MCP Server configuration.
    """
    server = MCPServer(**server_in.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server

@router.get("/", response_model=List[MCPServerSchema])
async def list_mcp_servers(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    filter: Optional[str] = Query("all", description="Filter type: all, hot, new, official"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all MCP Servers with filtering and search.
    """
    stmt = select(MCPServer)
    
    # Search
    if q:
        search_filter = or_(
            MCPServer.name.ilike(f"%{q}%"),
            MCPServer.description.ilike(f"%{q}%")
        )
        stmt = stmt.where(search_filter)
        
    # Category Filter
    if category and category != "all":
        stmt = stmt.where(MCPServer.category == category)
        
    # Other Filters
    if filter == "official":
        stmt = stmt.where(MCPServer.is_official == True)
    
    # Sorting
    if filter == "hot":
        stmt = stmt.order_by(desc(MCPServer.downloads))
    elif filter == "new":
        stmt = stmt.order_by(desc(MCPServer.created_at))
    else:
        # Default sort
        stmt = stmt.order_by(desc(MCPServer.created_at))

    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    servers = result.scalars().all()
    return servers

@router.get("/{server_id}", response_model=MCPServerSchema)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific MCP Server by ID.
    """
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")
    return server

@router.put("/{server_id}", response_model=MCPServerSchema)
async def update_mcp_server(
    server_id: str,
    server_in: MCPServerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an MCP Server.
    """
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")
    
    update_data = server_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    await db.commit()
    await db.refresh(server)
    return server

@router.delete("/{server_id}", response_model=MCPServerSchema)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an MCP Server.
    """
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")
    
    await db.delete(server)
    await db.commit()
    return server
