from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class OpenClawNode(BaseModel):
    id: str
    name: str
    platform: str
    status: str
    version: Optional[str] = None
    address: Optional[str] = None

class OpenClawActivity(BaseModel):
    id: str
    name: str
    type: str  # crawl, screenshot, monitor, cron
    status: str
    schedule: Optional[str] = None
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    description: Optional[str] = None

class OpenClawStat(BaseModel):
    label: str
    count: int
    trend: str
    trendUp: bool
    accentColor: Optional[str] = None

class OpenClawPlugin(BaseModel):
    name: str
    version: Optional[str] = None
    status: str
    description: Optional[str] = None

class CreateTaskRequest(BaseModel):
    prompt: str

class OpenClawHealth(BaseModel):
    available: bool
    version: Optional[str] = None
    base_url: str
    tools_enabled: List[str]
    metrics: Dict[str, Any]
    fallback_enabled: bool

class OpenClawInfo(BaseModel):
    gateway_url: Optional[str] = None
    websocket_url: Optional[str] = None
    gateway_token: Optional[str] = None
    session_secret: Optional[str] = None
    status: str
    version: Optional[str] = None
