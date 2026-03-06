from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataSourceBase(BaseModel):
    name: str
    type: str
    host: str
    port: int
    username: Optional[str] = None
    database: str
    db_schema: Optional[str] = None
    description: Optional[str] = None


class DataSourceCreate(DataSourceBase):
    password: Optional[str] = None


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


class DataSourceOut(DataSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataSourceTest(DataSourceCreate):
    pass
