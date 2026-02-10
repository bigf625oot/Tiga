from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IndicatorBase(BaseModel):
    group: str
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    advanced_options: Optional[dict] = None


class IndicatorCreate(IndicatorBase):
    pass


class IndicatorUpdate(BaseModel):
    group: Optional[str] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    advanced_options: Optional[dict] = None
    is_deleted: Optional[bool] = None


class IndicatorResponse(IndicatorBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
