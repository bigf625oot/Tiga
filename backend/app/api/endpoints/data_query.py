import json
import logging
import os
import time
import uuid

import aiofiles
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.services.data.vanna.models import (
    DataQueryMessageResponse,
    DataQuerySessionCreate,
    DataQuerySessionResponse,
    DataQuerySessionUpdate,
    DbConnectionConfig,
    VannaRequest,
)
from app.services.data.vanna.service import data_query_service

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()
CONFIG_FILE = "vanna_config.json"

# In-memory job status store (Simple implementation)
conversion_jobs = {}

def update_job_status(job_id, status, progress, message):
    conversion_jobs[job_id] = {
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": time.time()
    }

@router.post("/connect")
async def connect_database(config: DbConnectionConfig, request: Request):
    """
    Connect to a database using the provided configuration.
    Executes the blocking connection logic in a separate thread to avoid blocking the event loop.
    """
    start_time = time.time()
    client_host = request.client.host
    logger.info(f"[{client_host}] Received connect request for DB type: {config.type}")

    try:
        # Use run_in_threadpool to execute blocking IO operations
        logger.info(f"Initiating connection to {config.host}:{config.port}...")
        # connect_db is now async and handles threadpool internally for heavy lifting
        await data_query_service.connect_db(config)

        duration = (time.time() - start_time) * 1000
        logger.info(f"Connection established successfully in {duration:.2f}ms")
        return {"message": "Successfully connected to database", "duration_ms": duration}

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Connection failed after {duration:.2f}ms. Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tables")
async def get_tables():
    """
    Get all table names from the connected database.
    """
    try:
        tables = await run_in_threadpool(data_query_service.get_tables)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/table/{table_name}/data")
async def get_table_data(table_name: str, limit: int = 100, offset: int = 0):
    """
    Get data from a specific table.
    """
    try:
        result = await run_in_threadpool(data_query_service.get_table_data, table_name, limit, offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/table/{table_name}/convert_to_graph")
async def convert_table_to_graph(table_name: str, background_tasks: BackgroundTasks):
    """
    Start a background task to convert table data to Knowledge Graph.
    """
    job_id = str(uuid.uuid4())
    update_job_status(job_id, "pending", 0, "任务已创建")

    background_tasks.add_task(
        data_query_service.convert_table_to_graph_task,
        job_id,
        table_name,
        update_job_status
    )

    return {"job_id": job_id, "message": "转换任务已开始"}


@router.get("/conversion_status/{job_id}")
async def get_conversion_status(job_id: str):
    """
    Get the status of a conversion task.
    """
    status = conversion_jobs.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.post("/query")
async def query_data(request: VannaRequest):
    """
    Query the database using natural language.
    Returns a streaming response with the answer, SQL, and potential visualization data.
    """
    logger.info(f"Received query: {request.question}")
    return StreamingResponse(
        data_query_service.query(request.question, session_id=request.session_id),
        media_type="text/plain",
    )


@router.post("/config/save")
async def save_config(config: DbConnectionConfig):
    """
    Save the database configuration to a file.
    """
    try:
        async with aiofiles.open(CONFIG_FILE, mode="w") as f:
            await f.write(config.model_dump_json(indent=2))
        return {"message": "Configuration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@router.get("/config")
async def get_config():
    """
    Load the database configuration from a file.
    """
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        async with aiofiles.open(CONFIG_FILE, mode="r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


# ----- Session Endpoints -----
@router.post("/sessions", response_model=DataQuerySessionResponse)
async def create_session(payload: DataQuerySessionCreate):
    try:
        s = await data_query_service.create_session(
            title=payload.title or "New Chat",
            user_id=payload.user_id or "default_user",
        )
        return DataQuerySessionResponse(
            id=s.id,
            title=s.title,
            user_id=s.user_id,
            is_active=s.is_active,
            is_archived=s.is_archived,
            is_pinned=s.is_pinned,
            is_deleted=s.is_deleted,
            created_at=str(s.created_at) if s.created_at else None,
            updated_at=str(s.updated_at) if s.updated_at else None,
            message_count=0,
            last_message_preview=None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def list_sessions(status: str = "active", limit: int = 20, offset: int = 0, user_id: str = "default_user"):
    try:
        sessions = await data_query_service.list_sessions(user_id=user_id, status=status, limit=limit, offset=offset)
        out = []
        for s in sessions:
            # Compute preview info
            messages = await data_query_service.get_messages(s.id)
            count = len(messages)
            preview = None
            if messages:
                last = messages[-1]
                content = last.content or last.sql_query or ""
                preview = (content[:50] + "...") if len(content) > 50 else content
            out.append(
                DataQuerySessionResponse(
                    id=s.id,
                    title=s.title,
                    user_id=s.user_id,
                    is_active=s.is_active,
                    is_archived=s.is_archived,
                    is_pinned=s.is_pinned,
                    is_deleted=s.is_deleted,
                    created_at=str(s.created_at) if s.created_at else None,
                    updated_at=str(s.updated_at) if s.updated_at else None,
                    message_count=count,
                    last_message_preview=preview,
                ).model_dump()
            )
        return {"items": out, "limit": limit, "offset": offset, "count": len(out)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}", response_model=DataQuerySessionResponse)
async def get_session(session_id: str):
    s = await data_query_service.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await data_query_service.get_messages(s.id)
    count = len(messages)
    preview = None
    if messages:
        last = messages[-1]
        content = last.content or last.sql_query or ""
        preview = (content[:50] + "...") if len(content) > 50 else content
    return DataQuerySessionResponse(
        id=s.id,
        title=s.title,
        user_id=s.user_id,
        is_active=s.is_active,
        is_archived=s.is_archived,
        is_pinned=s.is_pinned,
        is_deleted=s.is_deleted,
        created_at=str(s.created_at) if s.created_at else None,
        updated_at=str(s.updated_at) if s.updated_at else None,
        message_count=count,
        last_message_preview=preview,
    )


@router.patch("/sessions/{session_id}", response_model=DataQuerySessionResponse)
async def update_session(session_id: str, payload: DataQuerySessionUpdate):
    s = await data_query_service.update_session(
        session_id,
        **{k: v for k, v in payload.model_dump().items() if v is not None},
    )
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await data_query_service.get_messages(s.id)
    count = len(messages)
    preview = None
    if messages:
        last = messages[-1]
        content = last.content or last.sql_query or ""
        preview = (content[:50] + "...") if len(content) > 50 else content
    return DataQuerySessionResponse(
        id=s.id,
        title=s.title,
        user_id=s.user_id,
        is_active=s.is_active,
        is_archived=s.is_archived,
        is_pinned=s.is_pinned,
        is_deleted=s.is_deleted,
        created_at=str(s.created_at) if s.created_at else None,
        updated_at=str(s.updated_at) if s.updated_at else None,
        message_count=count,
        last_message_preview=preview,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, hard: bool = False):
    await data_query_service.delete_session(session_id, hard=hard)
    return {"ok": True}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    try:
        msgs = await data_query_service.get_messages(session_id)
        return {
            "items": [
                DataQueryMessageResponse(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role,
                    content=m.content,
                    sql_query=m.sql_query,
                    chart_config=m.chart_config,
                    error_message=m.error_message,
                    created_at=str(m.created_at) if m.created_at else None,
                ).model_dump()
                for m in msgs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
