"""
Data Source Endpoint
前端接口：
- HTTP POST `/data_source/`  接口作用：创建新的数据来源
- HTTP GET `/data_source/` 接口作用：获取所有数据来源
- HTTP GET `/data_source/{data_source_id}` 接口作用：获取指定数据来源详情
- HTTP PUT `/data_source/{data_source_id}` 接口作用：更新指定数据来源
- HTTP DELETE `/data_source/{data_source_id}` 接口作用：删除指定数据来源
前端功能：
- 管理和配置数据来源
- 支持不同类型的数据来源（如数据库、文件等）
- 提供数据来源的连接测试和验证
前端文件：
- `app/frontend/src/pages/DataSource.vue`
功能模块：
- 数据来源管理
"""
from typing import Any, List, Optional
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
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
        
        # Merge nested config if exists (important for database type overrides)
        if config.config and isinstance(config.config, dict):
            cfg.update(config.config)
        
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


@router.get("/{id}/tables/{table_name}/columns", response_model=List[str])
async def fetch_columns(
    id: int,
    table_name: str,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Fetch columns for a specific table in a data source.
    """
    ds = await crud_data_source.get(db, id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    cfg = _get_strategy_config(ds)
    
    try:
        strategy = get_strategy(ds.type, cfg)
        # Use fetch_data with limit 1 to infer columns from result keys
        # Ideally, we should have a dedicated method in strategy like `fetch_columns` or `inspect_table`
        # But `fetch_data` returns a generator of DataChunk.
        
        # We need to run this asynchronously
        columns = []
        async for chunk in strategy.fetch_data(table_name=table_name, limit=1):
            if chunk.data and len(chunk.data) > 0:
                columns = list(chunk.data[0].keys())
                break # We only need the first chunk
        
        return columns
    except Exception as e:
        # Log error but return empty list to avoid breaking UI
        print(f"Error fetching columns: {e}")
        return []

@router.get("/{id}/tables/{table_name}/preview", response_model=List[dict])
async def preview_table(
    id: int,
    table_name: str,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Preview data from a specific table.
    Returns a standard JSON list (not a stream) for easier UI consumption.
    """
    ds = await crud_data_source.get(db, id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    cfg = _get_strategy_config(ds)
    
    try:
        strategy = get_strategy(ds.type, cfg)
        
        # Collect data until limit is reached
        rows = []
        async for chunk in strategy.fetch_data(table_name=table_name, limit=limit):
            if chunk.data:
                rows.extend(chunk.data)
                if len(rows) >= limit:
                    break
        
        return rows[:limit]
    except Exception as e:
        # Log error
        print(f"Error previewing data: {e}")
        # Return empty list or raise 500? Raising 500 is better for UI feedback
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.post("/{id}/query/preview", response_model=List[dict])
async def preview_query(
    id: int,
    query: str = Body(..., embed=True),
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Execute a raw SQL query and return preview results.
    """
    ds = await crud_data_source.get(db, id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    cfg = _get_strategy_config(ds)
    
    try:
        strategy = get_strategy(ds.type, cfg)
        
        # Collect data until limit is reached
        rows = []
        # Pass query to fetch_data
        async for chunk in strategy.fetch_data(query=query, limit=limit):
            if chunk.data:
                rows.extend(chunk.data)
                if len(rows) >= limit:
                    break
        
        return rows[:limit]
    except Exception as e:
        # Log error
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

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
