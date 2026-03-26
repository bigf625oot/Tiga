import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.async_task import async_task, async_task_log
from app.schemas.async_task import (
    AsyncTaskCreate,
    AsyncTaskResponse,
    AsyncTaskListResponse,
    AsyncTaskCreateResponse,
    AsyncTaskProgressUpdate,
    WebSocketMessage,
)
from app.core.task_progress import task_progress
from app.core.websocket_manager import ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=AsyncTaskCreateResponse, status_code=202)
async def create_async_task(
    payload: AsyncTaskCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Query(None, description="用户ID"),
):
    task = await async_task.create(db, payload, user_id=user_id)

    await task_progress.set_progress(
        task_id=task.id,
        percent=0,
        status="PENDING",
        msg="任务已提交，等待处理",
        step="submitted"
    )

    await task_progress.publish_update(task.id, user_id or "anonymous")

    from app.core.worker_pool import task_pool
    await task_pool.submit_task(process_task_background, task.id, task.task_type)

    return AsyncTaskCreateResponse(
        task_id=task.id,
        estimate_time=60,
        message="任务已提交"
    )


async def process_task_background(task_id: str, task_type: str):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await async_task.update_progress(
                db, task_id, 10, "RUNNING", "开始处理", "initializing"
            )
            await task_progress.set_progress(task_id, 10, "RUNNING", "开始处理", "initializing")
            await task_progress.publish_update(task_id, "system")

            await async_task_log.create(db, task_id, 10, "RUNNING", "开始处理", "initializing")

            for i in range(20, 100, 20):
                await async_task.update_progress(
                    db, task_id, i, "RUNNING", f"处理中... {i}%", f"step_{i}"
                )
                await task_progress.set_progress(task_id, i, "RUNNING", f"处理中... {i}%", f"step_{i}")
                await task_progress.publish_update(task_id, "system")
                await async_task_log.create(db, task_id, i, "RUNNING", f"处理中", f"step_{i}")
                import asyncio
                await asyncio.sleep(0.5)

            await async_task.update_status(
                db, task_id, "SUCCESS",
                progress=100,
                msg="任务完成",
                result={"download_url": f"/uploads/{task_id}.zip"}
            )
            await task_progress.set_progress(task_id, 100, "SUCCESS", "任务完成", "completed")
            await task_progress.publish_update(task_id, "system")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await async_task.update_status(
                db, task_id, "FAILED",
                error_message=str(e)
            )
            await task_progress.set_progress(task_id, 0, "FAILED", f"任务失败: {str(e)}", "error")
            await task_progress.publish_update(task_id, "system")


@router.get("/", response_model=AsyncTaskListResponse)
async def list_async_tasks(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    tasks, total = await async_task.get_multi(
        db, user_id=user_id, status=status, page=page, page_size=page_size
    )

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
async def get_async_task(task_id: str, db: AsyncSession = Depends(get_db)):
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
async def update_task_progress(
    task_id: str,
    payload: AsyncTaskProgressUpdate,
    db: AsyncSession = Depends(get_db),
):
    task = await async_task.update_progress(
        db, task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_progress.set_progress(
        task_id=task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend
    )

    await task_progress.publish_update(task_id, task.user_id or "anonymous")

    await async_task_log.create(
        db, task_id,
        percent=payload.percent,
        status=payload.status,
        msg=payload.msg,
        step=payload.step,
        extend=payload.extend
    )

    return {"success": True}


@router.delete("/{task_id}")
async def delete_async_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await async_task.soft_delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_progress.delete_progress(task_id)

    return {"success": True}


@router.delete("/")
async def delete_async_tasks(
    statuses: str = Query(..., description="状态列表，逗号分隔，如: SUCCESS,FAILED"),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    status_list = [s.strip().upper() for s in statuses.split(",")]
    count = await async_task.soft_delete_by_status(db, user_id, status_list)
    return {"success": True, "deleted_count": count}


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
):
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