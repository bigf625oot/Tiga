"""
Workflows Endpoint
前端接口：
- HTTP POST `/workflows/` 接口作用：创建新工作流
- HTTP GET `/workflows/` 接口作用：获取所有工作流
- HTTP GET `/workflows/{workflow_id}` 接口作用：获取指定工作流详情
- HTTP PUT `/workflows/{workflow_id}` 接口作用：更新指定工作流
- HTTP DELETE `/workflows/{workflow_id}` 接口作用：删除指定工作流
前端功能：
- 管理和配置工作流
- 支持工作流的查询、创建、更新和删除
前端文件：
- `app/frontend/src/pages/Workflows.vue`
功能模块：
- 工作流管理
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate

router = APIRouter()

@router.get("/", response_model=List[WorkflowResponse])
async def read_workflows(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(workflow_in: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(**workflow_in.model_dump())
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def read_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).filter(Workflow.id == workflow_id))
    workflow = result.scalars().first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, workflow_in: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).filter(Workflow.id == workflow_id))
    workflow = result.scalars().first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow

@router.delete("/{workflow_id}", response_model=WorkflowResponse)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).filter(Workflow.id == workflow_id))
    workflow = result.scalars().first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    await db.delete(workflow)
    await db.commit()
    return workflow
