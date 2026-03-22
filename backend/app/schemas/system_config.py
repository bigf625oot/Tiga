from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ContextManagementConfig(BaseModel):
    history_limit: int = Field(default=10, ge=0, le=200) # Short-term working memory limit
    compression_threshold: int = Field(default=3000, ge=0, le=200_000) # Kept for backward compatibility but deprecated
    enable_graph_memory: bool = Field(default=True, description="Enable Graph-based long term memory")
    graph_hop_depth: int = Field(default=1, ge=1, le=3, description="Hop depth for graph memory retrieval")

class MemoryManagementConfig(BaseModel):
    enable_session_kb: bool = True
    embedding_model_id: str = "text-embedding-3-small"
    memory_extraction_interval: int = Field(default=10, ge=1, le=100, description="Messages interval to trigger graph memory extraction")


class ContextMemoryConfig(BaseModel):
    version: int = Field(default=1, ge=1)
    context: ContextManagementConfig = Field(default_factory=ContextManagementConfig)
    memory: MemoryManagementConfig = Field(default_factory=MemoryManagementConfig)


class EmailServerConfig(BaseModel):
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 465
    mail_server: str = ""
    mail_from_name: str = "Tiga System"
    mail_starttls: bool = False
    mail_ssl_tls: bool = True

class BasicSettingsConfig(BaseModel):
    version: int = Field(default=1, ge=1)
    email: EmailServerConfig = Field(default_factory=EmailServerConfig)

class SystemConfigResponse(BaseModel):
    key: str
    value: Dict[str, Any]
    version: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
