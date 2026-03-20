from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    icon: Optional[str] = None
    mode: str = "coordinate"
    leader_id: Optional[str] = None
    members: List[str] = []
    team_config: Dict[str, Any] = {}
    extra_metadata: Dict[str, Any] = {}
    is_readonly: bool = False
    is_template: bool = False
    is_active: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    icon: Optional[str] = None
    mode: Optional[str] = None
    leader_id: Optional[str] = None
    members: Optional[List[str]] = None
    team_config: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    is_readonly: Optional[bool] = None
    is_template: Optional[bool] = None
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: int
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
