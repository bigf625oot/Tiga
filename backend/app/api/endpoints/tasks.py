from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, AsyncSessionLocal
from app.schemas.task import TaskCreate, TaskResponse, SubTaskResponse
from app.crud.crud_task import task as crud_task
from app.crud.crud_task import sub_task as crud_sub_task
from app.services.task.service import task_service

router = APIRouter()

async def run_in_background(task_id: str, prompt: str):
    async with AsyncSessionLocal() as db:
        await task_service.process_task_creation(task_id, prompt, db)

@router.post("/", response_model=TaskResponse)
async def create_task(
    payload: TaskCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    task = await crud_task.create(db, payload)
    background_tasks.add_task(run_in_background, task.id, task.original_prompt)
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
