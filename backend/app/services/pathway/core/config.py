from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    type: str
    config: Dict[str, Any]

class OperatorConfig(BaseModel):
    type: str
    config: Dict[str, Any]

class SinkConfig(BaseModel):
    type: str
    config: Dict[str, Any]

class PathwayJobConfig(BaseModel):
    name: str
    sources: List[SourceConfig]
    operators: List[OperatorConfig] = []
    sinks: List[SinkConfig]
    settings: Dict[str, Any] = Field(default_factory=dict)
