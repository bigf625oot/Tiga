from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Dalle
try:
    from agno.tools.dalle import DalleTools as AgnoDalleTools
except ImportError:
    class AgnoDalleTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("openai is required for DalleTools.")

class DalleTools(AgnoDalleTools):
    _name = "dalle"
    _label = "图像生成 (DALL-E)"
    _description = "使用 DALL-E 生成图像"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: Optional[str] = Field(None, description="OpenAI API Key")

# Giphy
try:
    from agno.tools.giphy import GiphyTools as AgnoGiphyTools
except ImportError:
    class AgnoGiphyTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("requests is required for GiphyTools.")

class GiphyTools(AgnoGiphyTools):
    _name = "giphy"
    _label = "GIF 搜索 (Giphy)"
    _description = "搜索和获取 GIF 动图"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Giphy API Key")
