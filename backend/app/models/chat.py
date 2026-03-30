import uuid
from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, 
    String, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.llm_model import LLMModel

class ChatSession(Base):
    """
    会话表：管理对话上下文
    - id: 会话唯一标识符
    - title: 会话标题
    - user_id: 会话所属用户ID
    - agent_id: 会话关联的智能体ID
    - tenant_id: 会话所属租户ID（非必填，用于多租户场景）
    - llm_model_id: 会话关联的LLM模型ID
    - mode: 会话模式（quick, workflow, solo,team）
    - workflow_state: 会话复杂任务的中间状态
    - total_tokens: 会话消耗的Token数
    - total_cost: 会话消耗的总成本
    - created_at: 会话创建时间
    - updated_at: 会话最后更新时间
    """
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    user_id = Column(String(50), nullable=True, index=True)
    tenant_id = Column(String(50), nullable=True, index=True)  # 非必填，用于多租户场景
    
    # 关联
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)
    llm_model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=True)
    
    mode = Column(String(50), default="quick")  # quick, workflow, solo, team
    workflow_state = Column(JSON, nullable=True)  # 存储复杂任务的中间状态

    # 统计信息
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    agent = relationship("Agent", backref="sessions")
    llm_model = relationship("LLMModel", backref="sessions")


class ChatMessage(Base):
    """
    消息表：深度适配 Agno 的消息结构
    - id: 消息唯一标识符
    - session_id: 会话ID，关联到ChatSession
    - role: 消息角色（system, user, assistant, tool）
    - content: 消息内容（最终回答或用户输入）
    - reasoning_content: 推理模型的思维链内容（Thought）
    - tool_calls: 工具调用（Agno 核心）
    - tool_call_id: 当 role=tool 时，关联对应的调用 ID
    - message_type: 消息类型（text, image, file, chart）
    - meta_data: 消息元数据（UI 渲染需要的配置）
    - prompt_tokens: 提示Token数
    - completion_tokens: 完成Token数
    - total_tokens: 总Token数
    - cost: 消息成本
    - raw_response: 原始响应（生产环境调试非常有价值）
    - created_at: 消息创建时间
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # 角色: system, user, assistant, tool
    role = Column(String(20), nullable=False)
    
    # 内容区
    content = Column(Text, nullable=True)           # 最终回答或用户输入
    reasoning_content = Column(Text, nullable=True) # 针对推理模型的思维链内容 (Thought)
    
    # 工具调用 (Agno 核心)
    # 格式: [{"call_id": "...", "function": {"name": "..."}, "args": "{...}"}]
    tool_calls = Column(JSON, nullable=True) 
    tool_call_id = Column(String(100), nullable=True) # 当 role=tool 时，关联对应的调用 ID

    # 消息元数据
    message_type = Column(String(20), default="text") # text, image, file, chart
    meta_data = Column(JSON, nullable=True)           # 存储 UI 渲染需要的配置

    # 消耗统计
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Numeric(10, 6), default=0.0)

    # 原始响应 (生产环境调试非常有价值)
    raw_response = Column(JSON, nullable=True)

    # 树状对话结构 (用于支持 Regenerate 多版本分支)
    parent_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1) # 1 为当前激活分支，0 为历史分支

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    session = relationship("ChatSession", back_populates="messages")
    parent = relationship("ChatMessage", remote_side=[id], backref="children")