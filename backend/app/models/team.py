import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Enum, func
from app.db.base import Base

# 1. 使用枚举类定义团队模式，增加代码可读性和约束
class TeamMode(str, enum.Enum):
    COORDINATE = "coordinate"
    ROUTE = "route"
    BROADCAST = "broadcast"
    TASKS = "tasks"

class Team(Base):
    """
    Agno Agent Team Model
    用于存储 AI 团队的配置、成员信息及运行模式
    """
    __tablename__ = "team"

    # 基本信息
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0", nullable=False)
    icon = Column(String(500), nullable=True)  # 存储图标 URL 或样式名
    
    # 核心逻辑配置
    # 使用 Enum 类型在数据库层面做约束
    mode = Column(
        Enum(TeamMode), 
        nullable=False, 
        default=TeamMode.COORDINATE,
        server_default=TeamMode.COORDINATE.value
    )
    
    # 权限与归属
    user_id = Column(String(100), index=True, nullable=True, comment="创建者ID")
    is_readonly = Column(Boolean, default=False, server_default="0")
    is_template = Column(Boolean, default=False, server_default="0")
    is_active = Column(Boolean, default=True, server_default="1")

    # 成员管理
    # leader_id 对应 Agno 中的 leader 角色
    leader_id = Column(String(100), index=True, nullable=True)
    # members 存储成员 Agent 的 ID 列表
    members = Column(JSON, nullable=False, default=[], server_default='[]')
    
    # Agno 运行参数 (非常重要)
    # 存储如 max_loops, show_tool_calls, instructions 等团队级特定参数
    team_config = Column(JSON, nullable=False, default={}, server_default='{}')
    
    # 扩展元数据 (用于存储前端自定义 UI 配置或临时标签)
    extra_metadata = Column(JSON, nullable=False, default={}, server_default='{}')

    # 时间审计 (使用 server_default 确保由数据库生成时间，避免时区偏差)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', mode='{self.mode}')>"

    def to_dict(self):
        """便捷转换方法"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "mode": self.mode.value if isinstance(self.mode, TeamMode) else self.mode,
            "leader_id": self.leader_id,
            "members": self.members,
            "config": self.team_config,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }