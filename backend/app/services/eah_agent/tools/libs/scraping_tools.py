from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Firecrawl
try:
    from agno.tools.firecrawl import FirecrawlTools as AgnoFirecrawlTools
except ImportError:
    class AgnoFirecrawlTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("firecrawl is required for FirecrawlTools.")

class FirecrawlTools(AgnoFirecrawlTools):
    _name = "firecrawl"
    _label = "Firecrawl"
    _description = "强大的网页爬虫"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Firecrawl API Key")

# Crawl4AI
try:
    from agno.tools.crawl4ai import Crawl4AiTools as AgnoCrawl4AiTools
except ImportError:
    class AgnoCrawl4AiTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("crawl4ai is required for Crawl4AiTools.")

class Crawl4AiTools(AgnoCrawl4AiTools):
    _name = "crawl4ai"
    _label = "Crawl4AI"
    _description = "开源 AI 网页爬虫"
    
    def __init__(self, max_length: int = 1000):
        super().__init__(max_length=max_length)

# Spider
try:
    from agno.tools.spider import SpiderTools as AgnoSpiderTools
except ImportError:
    class AgnoSpiderTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("spider-client is required for SpiderTools.")

class SpiderTools(AgnoSpiderTools):
    _name = "spider"
    _label = "Spider"
    _description = "将网页转换为 LLM 可读格式"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Spider API Key")

# Apify
try:
    from agno.tools.apify import ApifyTools as AgnoApifyTools
except ImportError:
    class AgnoApifyTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("apify-client is required for ApifyTools.")

class ApifyTools(AgnoApifyTools):
    _name = "apify"
    _label = "Apify"
    _description = "运行 Apify 爬虫 Actors"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Apify API Key")
