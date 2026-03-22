from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_system_config import system_config as crud_system_config
from app.db.session import get_db
from app.schemas.system_config import ContextMemoryConfig, BasicSettingsConfig


router = APIRouter()

CONTEXT_MEMORY_KEY = "context-memory"
BASIC_SETTINGS_KEY = "basic-settings"


@router.get(f"/{CONTEXT_MEMORY_KEY}", response_model=ContextMemoryConfig)
async def get_context_memory_config(db: AsyncSession = Depends(get_db)):
    row = await crud_system_config.get_by_key(db, CONTEXT_MEMORY_KEY)
    if not row or not row.value:
        return ContextMemoryConfig()

    try:
        return ContextMemoryConfig.model_validate(row.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid stored config: {e}")


@router.put(f"/{CONTEXT_MEMORY_KEY}", response_model=ContextMemoryConfig)
async def upsert_context_memory_config(payload: ContextMemoryConfig, db: AsyncSession = Depends(get_db)):
    await crud_system_config.upsert(db, key=CONTEXT_MEMORY_KEY, value=payload.model_dump(), version=payload.version)
    return payload


@router.delete(f"/{CONTEXT_MEMORY_KEY}", response_model=ContextMemoryConfig)
async def reset_context_memory_config(db: AsyncSession = Depends(get_db)):
    await crud_system_config.delete_by_key(db, CONTEXT_MEMORY_KEY)
    return ContextMemoryConfig()


@router.get(f"/{BASIC_SETTINGS_KEY}", response_model=BasicSettingsConfig)
async def get_basic_settings_config(db: AsyncSession = Depends(get_db)):
    row = await crud_system_config.get_by_key(db, BASIC_SETTINGS_KEY)
    if not row or not row.value:
        return BasicSettingsConfig()

    try:
        return BasicSettingsConfig.model_validate(row.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid stored config: {e}")

@router.put(f"/{BASIC_SETTINGS_KEY}", response_model=BasicSettingsConfig)
async def upsert_basic_settings_config(payload: BasicSettingsConfig, db: AsyncSession = Depends(get_db)):
    await crud_system_config.upsert(db, key=BASIC_SETTINGS_KEY, value=payload.model_dump(), version=payload.version)
    return payload

@router.delete(f"/{BASIC_SETTINGS_KEY}", response_model=BasicSettingsConfig)
async def reset_basic_settings_config(db: AsyncSession = Depends(get_db)):
    await crud_system_config.delete_by_key(db, BASIC_SETTINGS_KEY)
    return BasicSettingsConfig()

