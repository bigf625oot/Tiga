import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.async_task import async_task, async_task_log
from app.schemas.async_task import (
    AsyncTaskCreate,
    AsyncTaskCreateResponse,
    AsyncTaskListResponse,
    AsyncTaskProgressUpdate,
    AsyncTaskResponse,
)
from app.core.task_progress import task_progress
from app.core.websocket_manager import ws_manager

from app.services.platform.task_engine.service import task_engine_service
from app.services.platform.task_engine.models import TaskEngineType, TaskRunContext
from app.services.platform.task_engine.adapters.async_task import AsyncTaskAdapter
from app.services.platform.task_engine.adapters.execution import ExecutionTaskAdapter
from app.services.platform.task_engine.adapters.pathway import PathwayAdapter
from app.services.platform.task_engine.adapters.celery import CeleryAdapter, CELERY_AVAILABLE

router = APIRouter()
logger = logging.getLogger(__name__)

# 注册底层适配器
task_engine_service.register_adapter(TaskEngineType.ASYNC_TASK, AsyncTaskAdapter())
task_engine_service.register_adapter(TaskEngineType.EXECUTION, ExecutionTaskAdapter())
task_engine_service.register_adapter(TaskEngineType.PATHWAY, PathwayAdapter())
if CELERY_AVAILABLE:
    task_engine_service.register_adapter(TaskEngineType.CELERY, CeleryAdapter())


@router.post("/", response_model=AsyncTaskCreateResponse, status_code=202)
async def create_task_run(
    payload: AsyncTaskCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Query(None, description="用户ID"),
):
    task = await async_task.create(db, payload, user_id=user_id)

    await task_progress.set_progress(
        task_id=task.id,
        percent=0,
        status="PENDING",
        msg="任务已提交，等待分发",
        step="submitted",
    )
    await task_progress.publish_update(task.id, user_id or "anonymous")

    # 根据 payload.task_type 决定使用哪种底层引擎 (简单映射逻辑)
    engine_type = TaskEngineType.ASYNC_TASK
    if payload.task_type.upper() == "EXECUTION":
        engine_type = TaskEngineType.EXECUTION
    elif payload.task_type.upper() == "PATHWAY":
        engine_type = TaskEngineType.PATHWAY
    elif payload.task_type.upper() == "CELERY":
        engine_type = TaskEngineType.CELERY

    context = TaskRunContext(
        task_id=task.id,
        engine_type=engine_type,
        user_id=user_id or "anonymous",
        priority=payload.priority,
        config=payload.context or {}
    )
    
    # 提交给统一任务引擎服务
    await task_engine_service.start_task(context)

    return AsyncTaskCreateResponse(task_id=task.id, estimate_time=60, message="任务已提交分发")


@router.get("/", response_model=AsyncTaskListResponse)
async def list_task_runs(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    tasks, total = await async_task.get_multi(db, user_id=user_id, status=status, page=page, page_size=page_size)
    items = [
        AsyncTaskResponse(
            id=t.id,
            name=t.name,
            task_type=t.task_type,
            status=t.status,
            progress=t.progress,
            msg=t.msg,
            step=t.step,
            priority=t.priority,
            user_id=t.user_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
            result=t.result,
        )
        for t in tasks
    ]
    return AsyncTaskListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=AsyncTaskResponse)
async def get_task_run(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await async_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    redis_progress = await task_progress.get_progress(task_id)
    if redis_progress and task.status == "RUNNING":
        task.progress = redis_progress["percent"]
        task.msg = redis_progress["msg"]
        task.step = redis_progress["step"]

    return AsyncTaskResponse(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        msg=task.msg,
        step=task.step,
        priority=task.priority,
        user_id=task.user_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        result=task.result,
    )


@router.patch("/{task_id}/progress")
async def update_task_run_progress(task_id: str, payload: AsyncTaskProgressUpdate, db: AsyncSession = Depends(get_db)):
    task = await async_task.update_progress(
        db,
        task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_progress.set_progress(
        task_id=task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend,
    )
    await task_progress.publish_update(task_id, task.user_id or "anonymous")
    await async_task_log.create(
        db,
        task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend,
    )
    return {"success": True}


@router.delete("/completed")
async def delete_completed_task_runs(user_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    status_list = ["SUCCESS", "FAILED"]
    count = await async_task.soft_delete_by_status(db, user_id, status_list)
    return {"success": True, "deleted_count": count}


@router.delete("/{task_id}")
async def delete_task_run(task_id: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await async_task.soft_delete(db, task_id)
    except Exception as e:
        logger.error(f"Failed to soft delete task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while deleting task: {str(e)}")

    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_progress.delete_progress(task_id)
    return {"success": True}


@router.websocket("/ws")
async def task_run_websocket(websocket: WebSocket, user_id: str = Query(...)):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from {user_id}: {data}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
        await ws_manager.disconnect(user_id, websocket)

