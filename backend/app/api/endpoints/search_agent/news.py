from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.search_agent.news_schemas import NewsSearchRequest, NewsSearchResponse, CustomNewsSearchRequest
from app.services.search_agent.news_service import search_news, execute_custom_news_search, execute_custom_news_search_stream

# 创建API路由器
router = APIRouter()

# 通用新闻搜索端点
@router.post("/search", response_model=NewsSearchResponse)
async def search_news_api(request: NewsSearchRequest):
    """
    通用新闻搜索功能
    """
    return await search_news(request)

# 自定义新闻搜索端点
@router.post("/custom_search", response_model=NewsSearchResponse)
async def custom_search_news_api(request: CustomNewsSearchRequest):
    """
    Custom news search with specific prompt strategy
    """
    return await execute_custom_news_search(request)

# 自定义新闻搜索流式端点
@router.post("/custom_search_stream")
async def custom_search_news_stream_api(request: CustomNewsSearchRequest):
    """
    Stream custom news search results
    """
    return StreamingResponse(
        execute_custom_news_search_stream(request),
        media_type="application/x-ndjson"
    )
