from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

class AlertLevel(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

class NodeBase(BaseModel):
    name: str
    platform: str
    ip_address: Optional[str] = None
    version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    group: Optional[str] = None
    tags: Optional[List[str]] = []

class NodeCreate(NodeBase):
    pass

class NodeUpdate(NodeBase):
    status: Optional[NodeStatus] = None

class NodeInDBBase(NodeBase):
    id: str
    status: NodeStatus
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Node(NodeInDBBase):
    pass

class NodeMetricBase(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: float
    network_out: float
    latency: Optional[float] = None
    packet_loss: Optional[float] = None

class NodeMetricCreate(NodeMetricBase):
    pass

class NodeMetric(NodeMetricBase):
    id: int
    node_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    level: AlertLevel
    message: str
    status: str = "active"

class AlertCreate(AlertBase):
    node_id: Optional[str] = None

class Alert(AlertBase):
    id: int
    node_id: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CommandRequest(BaseModel):
    command: str
    params: Dict[str, Any] = {}
    target_nodes: Optional[List[str]] = None
    target_group: Optional[str] = None
    target_tags: Optional[List[str]] = None
