from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class UserScriptBase(BaseModel):
    agent_id: str
    title: str
    content: str
    sort_order: int = 0

    @field_validator("title")
    def validate_title(cls, v):
        if not v or len(v) > 50:
            raise ValueError("title length must be <= 50 and not empty")
        return v

    @field_validator("content")
    def validate_content(cls, v):
        if not v or len(v) > 500:
            raise ValueError("content length must be <= 500 and not empty")
        return v


class UserScriptCreate(UserScriptBase):
    pass


class UserScriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None


class UserScriptResponse(UserScriptBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
