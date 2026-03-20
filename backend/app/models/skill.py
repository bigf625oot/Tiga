import uuid
from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text, Integer, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Skill(Base):
    """
    技能表：定义系统中的可执行操作或任务
    - id: 技能唯一标识符
    - slug: 技能唯一标识符 (如 "image-generator")
    - name: 技能名称
    - description: 技能描述
    - version: 技能版本
    - category: 技能类别
    - author_id: 技能作者ID
    - is_official: 是否官方技能
    - downloads: 下载次数
    - rating: 技能评分
    - is_active: 是否活跃
    - is_public: 是否公开
    - created_at: 创建时间
    - updated_at: 更新时间
    - deleted_at: 删除时间
    """
    __tablename__ = "skills"

    # 基础信息
    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String, index=True, unique=True, nullable=False)  # 唯一标识符 (如 "image-generator")
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0.0", nullable=False)

    # 核心内容
    content = Column(Text, nullable=True)  # Prompt 模板
    
    # 结构化定义 (JSONB)
    tools_config = Column(JSON, nullable=True)  # 绑定的工具函数定义
    input_schema = Column(JSON, nullable=True)  # 输入参数 Schema
    output_schema = Column(JSON, nullable=True) # 输出格式 Schema
    meta_data = Column(JSON, server_default='{}') 
    
    # 业务元数据
    category = Column(String, index=True, nullable=True)
    author_id = Column(String, index=True, default="system")
    is_official = Column(Boolean, default=False, index=True)
    downloads = Column(Integer, default=0, server_default="0")
    rating = Column(Integer, default=0)
    
    # 状态控制
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, index=True) # 区分私有/公共
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True) # 软删除

    __table_args__ = (
        UniqueConstraint('slug', 'version', name='_slug_version_uc'),
        Index('ix_skills_official_active', 'is_official', 'is_active'),
    )

    def __repr__(self):
        return f"<Skill(name={self.name}, version={self.version})>"
