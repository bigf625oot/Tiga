from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # openai, aliyun, etc.
    model_id = Column(String, nullable=False)  # gpt-4o, qwen-max
    model_type = Column(String, default="text")  # text, image, video, multimodal
    api_key = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_reasoning_model(self) -> bool:
        """
        判断当前模型是否为慢速的推理模型 (如 o1, deepseek-r1, reasoner 等)
        这对于需要低延迟的后台任务 (如 NLU, 压缩上下文) 进行模型过滤非常有用
        """
        if not self.model_id:
            return False
        mid = self.model_id.lower()
        return "reasoner" in mid or "deepseek-r1" in mid or "o1" in mid or "o3" in mid

    @classmethod
    def filter_active(cls):
        """返回基础的活跃模型过滤条件"""
        return cls.is_active == True

    @classmethod
    def filter_has_api_key(cls):
        """返回有 API Key 的模型过滤条件"""
        return (cls.api_key != None) & (cls.api_key != "")

    @classmethod
    def filter_fast_models(cls):
        """
        返回快速模型（非推理模型）的过滤条件
        注：这里使用 notilike 进行数据库层面的过滤，保持与 is_reasoning_model 逻辑一致
        """
        return (
            cls.model_id.notilike("%reasoner%") &
            cls.model_id.notilike("%deepseek-r1%") &
            cls.model_id.notilike("%o1%") &
            cls.model_id.notilike("%o3%") &
            cls.model_type.in_(["text", "multimodal"])
        )
