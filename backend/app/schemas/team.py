from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    mode: str = "coordinate"
    leader_id: Optional[str] = None
    members: List[str] = []
    is_readonly: bool = False

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    mode: Optional[str] = None
    leader_id: Optional[str] = None
    members: Optional[List[str]] = None
    is_readonly: Optional[bool] = None

class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
