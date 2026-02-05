from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from app.services.vanna.service import data_query_service
from app.services.vanna.models import DbConnectionConfig, VannaRequest
from starlette.concurrency import run_in_threadpool
import json
import os
import aiofiles
import logging
import time

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()
CONFIG_FILE = "vanna_config.json"

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
        await run_in_threadpool(data_query_service.connect_db, config)
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"Connection established successfully in {duration:.2f}ms")
        return {"message": "Successfully connected to database", "duration_ms": duration}
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Connection failed after {duration:.2f}ms. Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query")
async def query_data(request: VannaRequest):
    """
    Query the database using natural language.
    Returns a streaming response with the answer, SQL, and potential visualization data.
    """
    logger.info(f"Received query: {request.question}")
    return StreamingResponse(
        data_query_service.query(request.question),
        media_type="text/plain"
    )

@router.post("/config/save")
async def save_config(config: DbConnectionConfig):
    """
    Save the database configuration to a file.
    """
    try:
        async with aiofiles.open(CONFIG_FILE, mode='w') as f:
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
        async with aiofiles.open(CONFIG_FILE, mode='r') as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")

@router.post("/export")
async def export_dataset(schema: str | None = Query(default=None, description="可选 schema")):
    """
    触发导出当前连接数据库的所有表为 JSON/NDJSON，并增量更新 GraphML 图谱。
    """
    try:
        result = await run_in_threadpool(data_query_service.export_dataset_and_update_graph, schema)
        return {"message": "导出完成", **result}
    except Exception as e:
        logger.error(f"导出失败：{e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export/stats")
async def export_stats():
    """
    返回当前图谱中由结构化数据库生成的节点与边统计。
    """
    try:
        result = await run_in_threadpool(data_query_service.get_db_graph_stats)
        return result
    except Exception as e:
        logger.error(f"统计失败：{e}")
        raise HTTPException(status_code=400, detail=str(e))
