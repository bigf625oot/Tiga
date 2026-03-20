import uuid
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum as SQLEnum, Index, UniqueConstraint, JSON
from sqlalchemy.sql import func
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

# MCP 传输类型
class MCPTransportType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"

# 服务器状态
class MCPServerStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    INACTIVE = "inactive"

class MCPServer(Base):
    """
    MCP 服务器模型
    - id: 服务器唯一标识符
    - slug: 服务器唯一标识符 (如 "github-mcp")
    - name: 服务器名称
    - description: 服务器描述
    - version: 服务器版本
    - transport_type: 传输类型 (stdio/sse)
    - config: 服务器配置 (根据类型不同)
    - env_vars: 环境变量 (敏感信息加密存储)
    - capabilities_cache: 能力缓存 (Tools/Resources/Prompts 预览)
    - category: 服务器类别
    - author: 服务器作者
    - is_official: 是否官方服务器
    - downloads: 下载次数
    - status: 服务器状态
    - last_error: 上次错误信息
    - last_connected_at: 上次连接时间
    - is_active: 是否活跃
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    __tablename__ = "mcp_servers"

    # 基础信息
    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String, index=True, unique=True, nullable=False)  # 唯一标识符 (如 "github-mcp")
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0.0")

    # 核心配置
    transport_type = Column(SQLEnum(MCPTransportType), nullable=False, default=MCPTransportType.STDIO)
    config = Column(JSON, nullable=False, server_default='{}')  # stdio: {command, args}, sse: {url}
    env_vars = Column(JSON, nullable=True, server_default='{}') # 敏感环境变量 (建议加密存储)

    # 能力缓存 (Tools/Resources/Prompts 预览，减少连接开销)
    capabilities_cache = Column(JSON, nullable=True, server_default='{"tools": [], "resources": [], "prompts": []}')

    # 业务元数据
    category = Column(String, index=True, nullable=True)
    author = Column(String, default="System", index=True)
    is_official = Column(Boolean, default=False, index=True)
    downloads = Column(Integer, default=0, server_default="0")
    
    # 状态监控
    status = Column(SQLEnum(MCPServerStatus), default=MCPServerStatus.INACTIVE)
    last_error = Column(String, nullable=True)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    
    # 审计字段
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    __table_args__ = (
        Index('ix_mcp_official_active', 'is_official', 'is_active'),
        UniqueConstraint('slug', 'author', name='_mcp_slug_author_uc'),
    )

    def __repr__(self):
        return f"<MCPServer(slug={self.slug}, type={self.transport_type}, status={self.status})>"
