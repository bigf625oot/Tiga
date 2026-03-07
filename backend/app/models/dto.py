from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional, AsyncGenerator

class MetadataModel(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class DataChunk(BaseModel):
    data: List[Dict[str, Any]]
    count: int
    offset: Optional[int] = None
    has_more: bool = False
    metadata: Optional[Dict[str, Any]] = None
