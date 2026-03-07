from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class DataSourceBase(BaseModel):
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    database: Optional[str] = None
    db_schema: Optional[str] = None
    description: Optional[str] = None
    
    # New fields
    url: Optional[str] = None
    config: Optional[Any] = None


class DataSourceCreate(DataSourceBase):
    password: Optional[str] = None
    api_key: Optional[str] = None
    private_key: Optional[str] = None
    token: Optional[str] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    db_schema: Optional[str] = None
    description: Optional[str] = None
    
    url: Optional[str] = None
    api_key: Optional[str] = None
    private_key: Optional[str] = None
    token: Optional[str] = None
    config: Optional[Any] = None


class DataSourceOut(DataSourceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataSourceTest(DataSourceCreate):
    pass


class DataSourceTestResult(BaseModel):
    success: bool
    message: str
    error_type: Optional[str] = None
