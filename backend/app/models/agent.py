import uuid
from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text, Integer, Index
from sqlalchemy.sql import func
from app.db.base import Base

class Agent(Base):
    """
    存储智能体（AgnoAgent）配置，用于在运行时实例化 Agno 智能体对象。
    字段：
    - id: 代理的唯一标识符，默认使用 UUID 生成。
    - user_id: 关联的用户 ID，用于标识代理所属用户。
    - tenant_id: 关联的租户 ID，用于标识代理所属租户。可选字段。
    - name: 智能体的名称，用于显示和识别。
    - description: 智能体的描述，用于详细说明智能体的功能和用途。
    - icon: 智能体的图标，用于在界面上显示。
    - category: 智能体的分类，用于组织和管理。
    - provider: 智能体使用的 LLM 提供方，默认使用 OpenAI。
    - model_id: 智能体使用的 LLM 模型 ID，用于指定具体的模型。
    - model_config: 智能体使用的 LLM 模型配置，用于调整模型行为。
    - system_prompt: 智能体的系统提示，用于设置模型的初始行为。
    - instructions: 智能体的指令，用于定义模型的响应行为。
    - enable_react: 是否启用 React 模式，默认启用。
    - enable_cot: 是否启用 Chain of Thought 模式，默认启用。
    - show_tool_calls: 是否显示工具调用，默认显示。
    - enable_markdown: 是否启用 Markdown 渲染，默认启用。
    - role: 智能体的角色，默认使用 "general"。
    - version: 智能体的版本，默认使用 1。
    - is_active: 是否激活智能体，默认激活。
    - is_template: 是否为模板智能体，默认不是。
    - memory_config: 智能体的内存配置，用于存储和管理智能体的状态。
    - storage_config: 智能体的存储配置，用于存储和管理智能体的状态。
    - tools_config: 智能体的工具配置，用于定义智能体可以调用的工具。
    - mcp_config: 智能体的 MCP 配置，用于定义智能体的多轮对话行为。
    - skills_config: 智能体的技能配置，用于定义智能体的特殊能力。
    - knowledge_config: 智能体的知识库配置，用于定义智能体的知识库。
    - document_ids: 知识库文档 ID 列表，用于指定智能体可以访问的知识库文档。
    - knowledge_base_ids: 知识库 ID 列表，用于指定智能体可以访问的知识库。
    """
    __tablename__ = "agents"

    # --- 1. Identity ---
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=True) 
    tenant_id = Column(String, index=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True, default="/agent/agent_1.svg")
    category = Column(String, index=True, nullable=True)

    # --- 2. LLM Config ---
    provider = Column(String, default="openai", nullable=False)
    model_id = Column(String, nullable=False)
    model_config = Column(JSON, nullable=True, default={})

    # --- 3. Prompts ---
    system_prompt = Column(Text, nullable=True)
    instructions = Column(JSON, nullable=True) 

    # --- 4. Framework Toggles ---
    enable_react = Column(Boolean, default=True)
    enable_cot = Column(Boolean, default=True)
    show_tool_calls = Column(Boolean, default=False)
    enable_markdown = Column(Boolean, default=True)

    # --- 5. Capabilities ---
    tools_config = Column(JSON, nullable=True, default=[])
    mcp_config = Column(JSON, nullable=True, default=[])
    skills_config = Column(JSON, nullable=True, default={})
    knowledge_config = Column(JSON, nullable=True, default={})

    # --- 6. Storage & Memory ---
    memory_config = Column(JSON, nullable=True)
    storage_config = Column(JSON, nullable=True)

    # --- 7. Metadata ---
    role = Column(String, default="general", nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_agent_user_active", "user_id", "is_active"),
        Index("idx_agent_category", "category"),
    )