# 应用所有必要的启动补丁和配置
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.api import api_router
from app.core.bootstrap import apply_patches
from app.core.config import settings
from app.core.exceptions import global_exception_handler
from app.core.logger import logger, setup_logging
from app.core.i18n import _

apply_patches()

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB, Redis, S3 checks
    logger.info(_("Starting up..."))

    # Create uploads dir if not exists (Use absolute path)
    BACKEND_DIR = Path(__file__).resolve().parents[1]
    UPLOADS_DIR = BACKEND_DIR / "data" / "storage"
    os.makedirs(str(UPLOADS_DIR), exist_ok=True)

    # Create tables (Simple init for SQLite/Dev)
    from app.db.base import Base
    from app.db.session import engine

    # Import models to ensure they are registered
    from app.models.loader import import_all_models
    import_all_models()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "sqlite" in str(settings.database_url or ""):
            from app.db.schema_compat import ensure_sqlite_schema_compat
            await ensure_sqlite_schema_compat(conn)

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

    # Start Node Monitoring Task
    from app.services.openclaw.node.monitor import node_monitor
    await node_monitor.start()

    # Start Task Worker
    from app.services.openclaw.task.execution import task_worker
    await task_worker.start()

    # Initialize Redis Streams
    from app.core.task_stream import task_stream
    await task_stream.ensure_infrastructure()
    logger.info(_("Redis Task Stream infrastructure initialized."))

    yield
    # Shutdown: Close connections
    logger.info(_("Shutting down..."))
    await task_worker.stop()
    await node_monitor.stop()


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = trace_id
        response.headers["X-Process-Time"] = str(process_time)
        return response

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json", lifespan=lifespan)

# Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Trace ID Middleware
app.add_middleware(TraceIDMiddleware)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载上传目录以本地访问
# 修复：使用绝对路径 backend/data/storage 作为上传目录
BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
UPLOADS_DIR = BACKEND_DIR / "data" / "storage"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": _("Welcome to Agentic：国产信创版Manus API")}
