from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class MCPServerBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    type: str  # "stdio" or "sse"
    config: Dict[str, Any]
    category: Optional[str] = None
    author: Optional[str] = "User"
    is_official: bool = False
    downloads: int = 0
    is_active: bool = True

class MCPServerCreate(MCPServerBase):
    pass

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class MCPServer(MCPServerBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
