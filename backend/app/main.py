import sys
try:
    import duckduckgo_search
    sys.modules['ddgs'] = duckduckgo_search
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.api import api_router
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB, Redis, S3 checks
    print("Starting up...")
    
    # Create uploads dir if not exists
    os.makedirs("uploads", exist_ok=True)
    
    # Create tables (Simple init for SQLite/Dev)
    from app.db.session import engine
    from app.db.base import Base
    # Import models to ensure they are registered
    from app.models.recording import Recording 
    from app.models.llm_model import LLMModel
    from app.models.agent import Agent
    from app.models.user_script import UserScript
    from app.models.data_source import DataSource
    from app.models.indicator import Indicator
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Knowledge Base with DB Config
    from app.services.knowledge_base import kb_service
    from app.db.session import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await kb_service.reload_config(db)
    except Exception as e:
        print(f"Failed to initialize Knowledge Base config: {e}")
        
    yield
    # Shutdown: Close connections
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for local access
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Taichi Agent API"}
