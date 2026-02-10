from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class GraphExportConfigBase(BaseModel):
    name: str
    description: Optional[str] = None
    config_json: Dict[str, Any]


class GraphExportConfigCreate(GraphExportConfigBase):
    pass


class GraphExportConfigUpdate(GraphExportConfigBase):
    pass


class GraphExportConfig(GraphExportConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIGenerateRequest(BaseModel):
    data_source_id: Optional[int] = None
    database_url: Optional[str] = None
    existing_config: Optional[Dict[str, Any]] = None
