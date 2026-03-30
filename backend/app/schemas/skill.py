from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    content: Optional[str] = None
    
    # Structural definitions
    tools_config: Optional[Any] = None  # JSONB
    input_schema: Optional[Any] = None  # JSONB
    output_schema: Optional[Any] = None # JSONB
    meta_data: Optional[Dict[str, Any]] = None
    
    category: Optional[str] = None
    execution_mode: str = "sandbox"
    engine_route: Optional[str] = None
    author_id: Optional[str] = "system"
    is_official: bool = False
    downloads: int = 0
    rating: int = 0
    
    is_active: bool = True
    is_public: bool = True


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tools_config: Optional[Any] = None
    input_schema: Optional[Any] = None
    output_schema: Optional[Any] = None
    meta_data: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    execution_mode: Optional[str] = None
    engine_route: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class Skill(SkillBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    # deleted_at is internal

    class Config:
        from_attributes = True
