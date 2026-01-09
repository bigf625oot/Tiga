from app.core.config import settings
from app.schemas.search_agent.search_schemas import SearchResponse
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Aliyun SDK ---
try:
    import os
    from alibabacloud_tea_openapi.models import Config
    from alibabacloud_searchplat20240529.client import Client
    from alibabacloud_searchplat20240529.models import GetWebSearchRequest, GetWebSearchRequestHistory
    from alibabacloud_tea_util.models import RuntimeOptions
    
    ALIBABA_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Alibaba Cloud SDK not available: {e}")
    ALIBABA_SDK_AVAILABLE = False

# --- Tavily SDK ---
try:
    try:
        from tavily import TavilyClient
    except ModuleNotFoundError:
        TavilyClient = None
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

async def perform_search(query: str, service_name: str = "default", app_name: str = "ops-web-search-001") -> SearchResponse:
    """
    执行网络搜索的内部函数 (Aliyun)
    """
    if not ALIBABA_SDK_AVAILABLE:
        return SearchResponse(
            success=False,
            message="Alibaba Cloud SDK not available. Please install required dependencies."
        )
    
    if not settings.ALIBABA_CLOUD_BEARER_TOKEN:
        return SearchResponse(
            success=False,
            message="Alibaba Cloud Bearer Token not configured."
        )

    try:
        # 使用配置文件中的设置
        api_key = settings.ALIBABA_CLOUD_BEARER_TOKEN
        endpoint = settings.ALIBABA_CLOUD_ENDPOINT
        protocol = settings.ALIBABA_CLOUD_PROTOCOL
        
        # 配置客户端
        config = Config(
            bearer_token=api_key,
            endpoint=endpoint,
            protocol=protocol
        )
        client = Client(config=config)
        
        # 创建消息历史
        messages = [GetWebSearchRequestHistory(content="", role="user")]
        
        # 创建搜索请求
        search_request = GetWebSearchRequest(query=query, history=messages)
        
        # 配置运行时选项，设置超时时间为 30000 毫秒 (30秒)
        runtime = RuntimeOptions(
            read_timeout=30000,
            connect_timeout=10000
        )
        headers = {}

        # 执行搜索
        # Note: Client.get_web_search_with_options is synchronous in the SDK version used in source
        # If it blocks, we might need to run it in executor. For now assuming it's fast enough or threaded.
        response = client.get_web_search_with_options(service_name, app_name, search_request, headers, runtime)
        
        return SearchResponse(
            success=True,
            data=response.to_map(),  # 转换为字典格式
            message="Search completed successfully"
        )
    except Exception as e:
        # 打印完整的错误堆栈以便调试
        traceback.print_exc()
        # 返回错误而不是抛出异常，这样调用者可以处理错误
        return SearchResponse(
            success=False,
            message=f"Search failed: {str(e)}"
        )

def perform_tavily_search(
    query: str, 
    search_depth: str = "advanced", 
    include_domains: Optional[List[str]] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    使用Tavily API执行高级搜索
    """
    results = []
    
    if not TAVILY_AVAILABLE:
        print("Tavily SDK not installed.")
        return results
        
    if not settings.TAVILY_API_KEY:
        print("Tavily API key not configured.")
        return results

    try:
        tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # 调用Tavily搜索API
        response = tavily.search(
            query=query,
            search_depth=search_depth,
            include_domains=include_domains,
            max_results=max_results
        )
        
        # 统一返回格式
        for res in response.get('results', []):
            results.append({
                "url": res.get('url'),
                "title": res.get('title'),
                "content": res.get('content', ''),
                "published_date": res.get('published_date', datetime.now().strftime("%Y-%m-%d")),
                "score": res.get('score', 0)
            })
            
    except Exception as e:
        print(f"Tavily search failed: {e}")
        
    return results
