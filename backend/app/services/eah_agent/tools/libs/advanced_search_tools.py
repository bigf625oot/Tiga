from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Brave Search
try:
    from agno.tools.bravesearch import BraveSearchTools as AgnoBraveSearchTools
except ImportError:
    class AgnoBraveSearchTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("brave-search is required for BraveSearchTools.")

class BraveSearchTools(AgnoBraveSearchTools):
    _name = "brave_search"
    _label = "Brave 搜索"
    _description = "保护隐私的网络搜索"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Brave Search API Key")

# Google Search
try:
    from agno.tools.google import GoogleSearchTools as AgnoGoogleSearchTools
except ImportError:
    class AgnoGoogleSearchTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("google-api-python-client is required for GoogleSearchTools.")

class GoogleSearchTools(AgnoGoogleSearchTools):
    _name = "google_search"
    _label = "谷歌搜索 (Google)"
    _description = "Google 自定义搜索引擎"
    
    def __init__(self, api_key: str, cse_id: str):
        super().__init__(api_key=api_key, cse_id=cse_id)

    class Config(BaseModel):
        api_key: str = Field(..., description="Google API Key")
        cse_id: str = Field(..., description="Custom Search Engine ID")

# SerpApi
try:
    from agno.tools.serpapi import SerpApiTools as AgnoSerpApiTools
except ImportError:
    class AgnoSerpApiTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("google-search-results is required for SerpApiTools.")

class SerpApiTools(AgnoSerpApiTools):
    _name = "serpapi"
    _label = "SERP API"
    _description = "搜索引擎结果页面 API"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="SerpApi Key")

# Serper
try:
    from agno.tools.serper import SerperTools as AgnoSerperTools
except ImportError:
    class AgnoSerperTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("requests is required for SerperTools.")

class SerperTools(AgnoSerperTools):
    _name = "serper"
    _label = "Serper"
    _description = "快速、便宜的 Google 搜索 API"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Serper API Key")

# Searxng
try:
    from agno.tools.searxng import SearxngTools as AgnoSearxngTools
except ImportError:
    class AgnoSearxngTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("requests is required for SearxngTools.")

class SearxngTools(AgnoSearxngTools):
    _name = "searxng"
    _label = "SearxNG"
    _description = "开源元搜索引擎"
    
    def __init__(self, host: str):
        super().__init__(host=host)

    class Config(BaseModel):
        host: str = Field(..., description="SearxNG Host URL")
