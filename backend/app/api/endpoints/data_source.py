from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud.crud_data_source import data_source as crud_data_source
from app.schemas.data_source import DataSourceCreate, DataSourceOut, DataSourceTest, DataSourceUpdate
from app.services.data.vanna.models import DbConnectionConfig
from app.services.data.vanna.service import data_query_service

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
    # Optional: Test connection before saving?
    # For now, we assume user tested it via /test endpoint
    return await crud_data_source.create(db, obj_in=data_source_in)


@router.post("/test", response_model=bool)
async def test_connection(
    *,
    config: DataSourceTest,
) -> Any:
    """
    Test database connection.
    """
    # Convert schema to service config
    service_config = DbConnectionConfig(
        type=config.type.lower(),
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        database=config.database,
        db_schema=config.db_schema,
    )

    try:
        # We need to implement this method in service
        success = data_query_service.test_connection(service_config)
        if not success:
            raise HTTPException(status_code=400, detail="Connection failed")
        return True
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


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


@router.post("/{id}/connect")
async def connect_data_source(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Connect to a specific data source (set as active).
    """
    data_source_obj = await crud_data_source.get(db, id)
    if not data_source_obj:
        raise HTTPException(status_code=404, detail="Data source not found")

    # Decrypt password
    from app.core.security import decrypt_password

    password = decrypt_password(data_source_obj.password_encrypted) if data_source_obj.password_encrypted else None

    config = DbConnectionConfig(
        type=data_source_obj.type.lower(),
        host=data_source_obj.host,
        port=data_source_obj.port,
        user=data_source_obj.username,
        password=password,
        database=data_source_obj.database,
        db_schema=data_source_obj.db_schema,
    )

    try:
        data_query_service.connect_db(config)
        return {"message": f"Successfully connected to {data_source_obj.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")
