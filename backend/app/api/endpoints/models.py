"""
LLM Model Endpoint
前端接口：
- HTTP POST `/llm/models/` 接口作用：创建新的LLM模型
- HTTP GET `/llm/models/` 接口作用：获取所有LLM模型
- HTTP GET `/llm/models/{model_id}` 接口作用：获取指定LLM模型详情
- HTTP PATCH `/llm/models/{model_id}` 接口作用：更新指定LLM模型
- HTTP DELETE `/llm/models/{model_id}` 接口作用：删除指定LLM模型
前端功能：
- 管理和配置LLM模型
- 支持模型的创建、更新、删除和查询
前端文件：
- `app/frontend/src/pages/LLMModels.vue`
功能模块：
- LLM模型管理
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.llm_model import LLMModel
from app.schemas.llm_model import LLMModelCreate, LLMModelResponse, LLMModelUpdate

router = APIRouter()


@router.get("/", response_model=List[LLMModelResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMModel).order_by(LLMModel.id))
    return result.scalars().all()


@router.post("/", response_model=LLMModelResponse)
async def create_model(model_in: LLMModelCreate, db: AsyncSession = Depends(get_db)):
    # If this is the first model, make it active by default
    result = await db.execute(select(LLMModel))
    first_model = result.scalars().first()

    if not first_model:
        model_in.is_active = True
    elif model_in.is_active:
        # Deactivate others if this one is active
        await db.execute(select(LLMModel).filter(LLMModel.is_active == True))
        active_models = (await db.execute(select(LLMModel).filter(LLMModel.is_active == True))).scalars().all()
        for m in active_models:
            m.is_active = False

    db_model = LLMModel(**model_in.model_dump())
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model


@router.put("/{model_id}", response_model=LLMModelResponse)
async def update_model(model_id: int, model_in: LLMModelUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMModel).filter(LLMModel.id == model_id))
    db_model = result.scalars().first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_in.is_active:
        # Deactivate others
        active_models = (await db.execute(select(LLMModel).filter(LLMModel.is_active == True))).scalars().all()
        for m in active_models:
            if m.id != model_id:
                m.is_active = False

    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_model, field, value)

    await db.commit()
    await db.refresh(db_model)
    return db_model


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMModel).filter(LLMModel.id == model_id))
    db_model = result.scalars().first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(db_model)
    await db.commit()
    return {"ok": True}


@router.post("/{model_id}/activate", response_model=LLMModelResponse)
async def activate_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMModel).filter(LLMModel.id == model_id))
    db_model = result.scalars().first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Deactivate all others
    active_models = (await db.execute(select(LLMModel).filter(LLMModel.is_active == True))).scalars().all()
    for m in active_models:
        m.is_active = False

    db_model.is_active = True
    await db.commit()
    await db.refresh(db_model)
    return db_model
