import json
import logging
import os
import time

import aiofiles
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.services.data.vanna.models import DbConnectionConfig, VannaRequest
from app.services.data.vanna.service import data_query_service

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
    return StreamingResponse(data_query_service.query(request.question), media_type="text/plain")


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
