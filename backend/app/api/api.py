from fastapi import APIRouter
from app.api.endpoints import recordings, llm
from app.api.endpoints.search_agent import news
from app.api.endpoints import metrics_tool

api_router = APIRouter()
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(news.router, prefix="/news_search", tags=["news_search"])
api_router.include_router(metrics_tool.router, prefix="/metrics", tags=["metrics"])
