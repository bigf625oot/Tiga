from fastapi import APIRouter
from app.api.endpoints import recordings, llm

api_router = APIRouter()
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
