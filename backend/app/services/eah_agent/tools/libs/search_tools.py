from typing import Optional, List
try:
    from agno.tools.exa import ExaTools as AgnoExaTools
except ImportError:
    class AgnoExaTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("exa-py is required. Please install it.")
try:
    from agno.tools.tavily import TavilyTools as AgnoTavilyTools
except ImportError:
    class AgnoTavilyTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("tavily-python is required. Please install it.")
from pydantic import BaseModel, Field

class ExaTools(AgnoExaTools):
    _name = "exa"
    _label = "Exa 搜索"
    _description = "强大的 AI 搜索引擎"
    """
    使用 ExaTools 进行语义搜索。
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Exa API Key")

class TavilyTools(AgnoTavilyTools):
    _name = "tavily"
    _label = "Tavily 搜索"
    _description = "针对 LLM 优化的搜索引擎"
    """
    使用 TavilyTools 进行搜索。
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Tavily API Key")
