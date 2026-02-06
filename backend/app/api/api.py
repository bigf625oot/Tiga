from fastapi import APIRouter

from app.api.endpoints import (
    agents,
    chat,
    data_query,
    data_source,
    graph_export,
    health,
    indicators,
    knowledge,
    llm,
    mcp,
    metrics_tool,
    rag,
    recordings,
    render_data,
    user_script,
    workflow,
    skills,
)
from app.api.endpoints.search_agent import news

api_router = APIRouter()
api_router.include_router(graph_export.router, prefix="/graph_export", tags=["graph_export"])
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
api_router.include_router(data_query.router, prefix="/data_query", tags=["data_query"])
api_router.include_router(data_source.router, prefix="/data-sources", tags=["data-sources"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
