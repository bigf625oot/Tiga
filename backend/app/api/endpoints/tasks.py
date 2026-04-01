"""
Execution Tasks Endpoint
对外接口（当前挂载在 /api/v1/executions）：
- HTTP POST `/executions/`：创建执行任务（ExecutionTask）
- HTTP GET `/executions/{task_id}`：获取执行任务详情（含子任务）
功能模块：
- 执行编排引擎（任务拆分、子任务调度）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, AsyncSessionLocal
from app.schemas.task import TaskCreate, TaskResponse, SubTaskResponse
from app.crud.task import task as crud_task
from app.crud.task import sub_task as crud_sub_task
from app.services.ops.task.service import task_service

router = APIRouter()

async def run_in_background(task_id: str, prompt: str):
    async with AsyncSessionLocal() as db:
        await task_service.process_task_creation(task_id, prompt, db)

@router.post("/", response_model=TaskResponse)
async def create_task(
    payload: TaskCreate, 
    db: AsyncSession = Depends(get_db)
):
    task = await crud_task.create(db, payload)
    from app.core.worker_pool import task_pool
    await task_pool.submit_task(run_in_background, task.id, task.original_prompt)
    return task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await crud_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    sub_tasks = await crud_sub_task.get_by_parent(db, task_id)
    
    # We need to manually construct the response because sub_tasks relationship might not be loaded eagerly
    # and we want to use the Pydantic model structure
    task_data = TaskResponse.model_validate(task)
    task_data.sub_tasks = [SubTaskResponse.model_validate(st) for st in sub_tasks]
    
    return task_data
