import uuid
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Integer, func, Index
from app.db.base import Base

class Workflow(Base):
    __tablename__ = "workflows"

    # 每次修改并发布都会生成新的主键 ID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 逻辑上的唯一标识：同一套工作流的不同版本，其 original_id 相同
    original_id = Column(String(36), index=True, nullable=False, comment="溯源ID")
    
    name = Column(String(255), nullable=False)
    version = Column(Integer, default=1, server_default="1", nullable=False)
    
    # 状态控制
    is_latest = Column(Boolean, default=True, server_default="1", comment="是否为当前最新发布版")
    is_draft = Column(Boolean, default=False, server_default="0", comment="是否为草稿")
    
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=False, comment="工作流节点和连线逻辑")
    
    # 版本变更说明
    change_log = Column(String(500), nullable=True, comment="本版本修改了什么")
    
    # 其他配置保持不变
    input_variables = Column(JSON, nullable=True)
    runtime_config = Column(JSON, nullable=True)
    user_id = Column(String(100), index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 索引优化：方便快速找到某个工作流的最新的已发布版本
    __table_args__ = (
        Index("ix_workflow_lookup", "original_id", "is_latest"),
    )