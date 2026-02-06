from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = "1.0.0"
    content: Optional[str] = None
    tools_config: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True


class SkillCreate(SkillBase):
    pass


class SkillUpdate(SkillBase):
    name: Optional[str] = None


class Skill(SkillBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
