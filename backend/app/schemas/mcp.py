from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.models.mcp import MCPTransportType, MCPServerStatus

class MCPServerBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    transport_type: MCPTransportType = MCPTransportType.STDIO
    config: Dict[str, Any] = {}
    env_vars: Optional[Dict[str, str]] = {}
    category: Optional[str] = None
    author: Optional[str] = "System"
    is_official: bool = False
    downloads: int = 0
    is_active: bool = True
    status: MCPServerStatus = MCPServerStatus.INACTIVE

class MCPServerCreate(MCPServerBase):
    pass

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    transport_type: Optional[MCPTransportType] = None
    config: Optional[Dict[str, Any]] = None
    env_vars: Optional[Dict[str, str]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[MCPServerStatus] = None

class MCPServer(MCPServerBase):
    id: Any  # UUID
    capabilities_cache: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    last_connected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
