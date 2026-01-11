from fastapi import APIRouter
from app.api.endpoints import recordings, llm
from app.api.endpoints.search_agent import news
from app.api.endpoints import metrics_tool
from app.api.endpoints import chat, knowledge, agents, mcp, workflow
from app.api.endpoints import user_script
from app.api.endpoints import render_data

api_router = APIRouter()
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(news.router, prefix="/news_search", tags=["news_search"])
api_router.include_router(metrics_tool.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(workflow.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(render_data.router, tags=["render_data"])
api_router.include_router(user_script.router, tags=["user_script"])
