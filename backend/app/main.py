import sys
import asyncio

try:
    import duckduckgo_search

    sys.modules["ddgs"] = duckduckgo_search
except ImportError:
    pass

# Set Windows Event Loop Policy to avoid "RuntimeError: Event loop is closed" or anyio issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
from contextlib import asynccontextmanager
from pathlib import Path

# Patch asyncio to allow nested event loops (fixes "NoEventLoopError" in some environments)
import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import global_exception_handler
from app.core.logger import logger, setup_logging

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB, Redis, S3 checks
    logger.info("Starting up...")

    # Create uploads dir if not exists (Use absolute path)
    BACKEND_DIR = Path(__file__).resolve().parents[1]
    UPLOADS_DIR = BACKEND_DIR / "data" / "storage"
    os.makedirs(str(UPLOADS_DIR), exist_ok=True)

    # Create tables (Simple init for SQLite/Dev)
    from app.db.base import Base
    from app.db.session import engine

    # Import models to ensure they are registered
    from app.models import (
        agent,
        agent_plan,
        chat,
        data_source,
        graph_export,
        indicator,
        knowledge,
        llm_model,
        mcp,
        recording,
        service_category,
        skill,
        task_mode,
        tool,
        user,
        user_script,
        user_tool,
        workflow,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.db.session import AsyncSessionLocal

    try:
        from app.crud.crud_task_mode import task_mode as crud_task_mode

        async with AsyncSessionLocal() as db:
            await crud_task_mode.purge_expired_logs(db)
    except Exception as e:
        logger.error(f"Failed to purge expired task logs: {e}")

    # Initialize Knowledge Base with DB Config
    from app.services.rag.knowledge_base import kb_service

    try:
        async with AsyncSessionLocal() as db:
            await kb_service.reload_config(db)
    except Exception as e:
        logger.error(f"Failed to initialize Knowledge Base config: {e}")

    yield
    # Shutdown: Close connections
    logger.info("Shutting down...")


app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json", lifespan=lifespan)

# Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for local access
# Fix: Use absolute path to backend/data/storage for uploads
BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
UPLOADS_DIR = BACKEND_DIR / "data" / "storage"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Welcome to Taichi Agent API"}
