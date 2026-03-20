from sqlalchemy import Boolean, Column, DateTime, Integer, String, Float, JSON, Numeric
from sqlalchemy.sql import func
from app.db.base import Base

class LLMModel(Base):
    """
    存储 LLM 模型配置，用于在运行时实例化 LLM 模型对象。
    字段：
    - id: 模型的唯一标识符，默认使用自增整数。
    - name: 模型的名称，用于显示和识别。
    - alias: 模型的别名，用于在配置中引用。
    - description: 模型的描述，用于详细说明模型的功能和用途。
    - base_url: 模型的基础 URL，用于指定模型的访问地址。
    - api_key: 模型使用的 API 密钥，用于身份验证。
    - api_version: 模型使用的 API 版本，用于指定 API 调用的版本。
    - provider: 模型使用的 LLM 提供方，如 "openai", "aliyun", "Deepseek", "MinMax","GLM"。
    - model_id: 模型使用的 LLM 模型 ID，用于指定具体的模型。
    - model_type: 模型的类型，默认使用 "text"。
    - context_length: 模型的上下文长度，默认使用 4096。
    - max_output_tokens: 模型的最大输出 tokens 数量，默认使用 2048。
    - supports_vision: 模型是否支持看图，默认使用 False。
    - supports_tools: 模型是否支持函数调用，默认使用 True。
    - supports_json_mode: 模型是否支持结构化输出，默认使用 True。
    - temperature: 模型的温度参数，默认使用 0.7。
    - top_p: 模型的 top_p 参数，默认使用 1.0。
    - presence_penalty: 模型的 presence_penalty 参数，默认使用 0.0。
    - frequency_penalty: 模型的 frequency_penalty 参数，默认使用 0.0。
    """
    
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 别名，如 "生产环境GPT4"
    provider = Column(String, nullable=False) # openai, aliyun, azure, ollama
    model_id = Column(String, nullable=False) # gpt-4o, qwen-max-latest
    model_type = Column(String, default="text") 
    
    # --- 连接配置 ---
    api_key = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    api_version = Column(String, nullable=True) # 针对 Azure 特别有用

    # --- 能力约束 (Agno 路由关键) ---
    context_length = Column(Integer, default=4096) # 上下文限制
    max_output_tokens = Column(Integer, default=2048) # 输出限制
    supports_vision = Column(Boolean, default=False)  # 是否能看图
    supports_tools = Column(Boolean, default=True)    # 是否支持函数调用
    supports_json_mode = Column(Boolean, default=True) # 是否支持结构化输出
    supports_reasoning = Column(Boolean, default=False) # 是否支持推理 (Native Reasoning)
    use_agno_cot = Column(Boolean, default=True) # 是否使用 Agno 的思维链 (CoT)

    # --- 默认推理参数 ---
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    # 存储特定厂商的私有配置，如 {"presence_penalty": 0.1}
    extra_params = Column(JSON, default={}) 

    # --- 成本管理 ---
    input_token_price = Column(Numeric(10, 6), default=0.0)  # 每 1k tokens 价格
    output_token_price = Column(Numeric(10, 6), default=0.0)

    # --- 状态与元数据 ---
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0) # 优先级，用于故障转移 (Failover)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    def filter_active(cls):
        return cls.is_active == True

    @classmethod
    def filter_has_api_key(cls):
        return cls.api_key.is_not(None)
    
    @classmethod
    def filter_fast_models(cls):
        return cls.supports_reasoning == False

    @property
    def is_reasoning_model(self) -> bool:
        return self.supports_reasoning == True

    def to_agno_model_kwargs(self):
        """
        生成传给 Agno 模型构造函数的参数字典
        """
        kwargs = {
            "id": self.model_id,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }
        # 将 JSON 字段中的额外参数合并进去
        if self.extra_params:
            kwargs.update(self.extra_params)
        return kwargs