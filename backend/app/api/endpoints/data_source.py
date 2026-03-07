from typing import Any, List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.crud_data_source import data_source as crud_data_source
from app.schemas.data_source import DataSourceCreate, DataSourceOut, DataSourceTest, DataSourceUpdate, DataSourceTestResult
from app.strategies import get_strategy
from app.models.domain import MetadataModel, DataChunk

router = APIRouter()


@router.get("/", response_model=List[DataSourceOut])
async def read_data_sources(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve data sources.
    """
    return await crud_data_source.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=DataSourceOut)
async def create_data_source(
    *,
    db: AsyncSession = Depends(deps.get_db),
    data_source_in: DataSourceCreate,
) -> Any:
    """
    Create new data source.
    """
    return await crud_data_source.create(db, obj_in=data_source_in)


@router.post("/test", response_model=DataSourceTestResult)
async def test_connection(
    *,
    config: DataSourceTest,
) -> Any:
    """
    Test connection using strategy pattern.
    """
    try:
        # Construct config dict from input
        cfg = config.model_dump()
        
        # Determine strategy
        strategy = get_strategy(config.type, cfg)
        return await strategy.test_connection()
    except Exception as e:
        return {
            "success": False,
            "error_type": "UNKNOWN",
            "message": f"Connection failed: {str(e)}"
        }


@router.put("/{id}", response_model=DataSourceOut)
async def update_data_source(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    data_source_in: DataSourceUpdate,
) -> Any:
    """
    Update a data source.
    """
    data_source_obj = await crud_data_source.get(db, id)
    if not data_source_obj:
        raise HTTPException(status_code=404, detail="Data source not found")
    return await crud_data_source.update(db, db_obj=data_source_obj, obj_in=data_source_in)


@router.delete("/{id}", response_model=DataSourceOut)
async def delete_data_source(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete a data source.
    """
    data_source_obj = await crud_data_source.get(db, id)
    if not data_source_obj:
        raise HTTPException(status_code=404, detail="Data source not found")
    return await crud_data_source.delete(db, id)


def _get_strategy_config(ds: Any) -> dict:
    cfg = {
        "host": ds.host,
        "port": ds.port,
        "username": ds.username,
        "password_encrypted": ds.password_encrypted,
        "database": ds.database,
        "db_schema": ds.db_schema,
        "url": ds.url,
        "api_key_encrypted": ds.encrypted_api_key,
        "private_key_encrypted": ds.encrypted_private_key,
        "token_encrypted": ds.encrypted_token,
    }
    if ds.config:
        cfg.update(ds.config)
    return cfg


@router.get("/{id}/metadata", response_model=List[MetadataModel])
async def fetch_metadata(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Fetch metadata from the data source.
    """
    ds = await crud_data_source.get(db, id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    cfg = _get_strategy_config(ds)
        
    try:
        strategy = get_strategy(ds.type, cfg)
        return await strategy.fetch_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata fetch failed: {str(e)}")


@router.get("/{id}/data")
async def fetch_data(
    id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    limit: int = 1000,
    offset: int = 0,
    endpoint: Optional[str] = None, # For API
    filename: Optional[str] = None, # For SFTP
    table_name: Optional[str] = None, # For Database
) -> StreamingResponse:
    """
    Stream data from the data source.
    Returns NDJSON (Newline Delimited JSON).
    """
    ds = await crud_data_source.get(db, id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
        
    cfg = _get_strategy_config(ds)
    
    # Pass kwargs for strategy-specific parameters
    kwargs = {
        "limit": limit,
        "offset": offset,
        "endpoint": endpoint,
        "filename": filename,
        "table_name": table_name
    }
    # Filter out None values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    async def data_generator():
        try:
            strategy = get_strategy(ds.type, cfg)
            async for chunk in strategy.fetch_data(**kwargs):
                # Serialize chunk to JSON and yield line
                yield json.dumps(chunk.model_dump(), default=str) + "\n"
        except Exception as e:
            # In a real stream, we might want to yield a specific error object
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(data_generator(), media_type="application/x-ndjson")
