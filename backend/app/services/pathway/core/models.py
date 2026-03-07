from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class DAGNode(BaseModel):
    id: str
    type: str  # "source", "transform", "sink"
    operator: str  # e.g., "kafka", "text_process", "s3", "union"
    config: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[str] = Field(default_factory=list)  # List of node IDs that provide input to this node
    description: Optional[str] = None

class DAGPipeline(BaseModel):
    id: str
    name: str
    nodes: List[DAGNode]
    settings: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
