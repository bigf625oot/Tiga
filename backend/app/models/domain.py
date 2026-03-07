from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MetadataModel(BaseModel):
    """
    Domain model representing metadata from a data source.
    """
    name: str
    type: str
    description: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class DataChunk(BaseModel):
    """
    Domain model representing a chunk of data streamed from a source.
    """
    data: List[Dict[str, Any]]
    count: int
    offset: Optional[int] = None
    has_more: bool = False
    metadata: Optional[Dict[str, Any]] = None
