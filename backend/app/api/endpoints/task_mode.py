from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.crud.crud_task_mode import task_mode
from app.db.session import get_db
from app.schemas.task_mode import (
    TaskBackupExport,
    TaskBackupImportResult,
    TaskCreate,
    TaskQAResponse,
    TaskQACreate,
    TaskQAUpdate,
    TaskLogResponse,
    TaskResponse,
    TaskStatusChange,
    TaskUpdate,
    TaskVersionResponse,
)


router = APIRouter()


def _key(prefix: str, parts: Dict[str, Any]) -> str:
    raw = "|".join([f"{k}={parts[k]}" for k in sorted(parts.keys())])
    return f"task_mode:{prefix}:{raw}"


async def _invalidate_task(task_id: str) -> None:
    await cache.delete(f"task_mode:task:{task_id}")
    await cache.delete(f"task_mode:versions:{task_id}")
    await cache.delete(f"task_mode:qas:{task_id}")
    await cache.delete(f"task_mode:logs:{task_id}")


@router.post("/tasks", response_model=TaskResponse)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await task_mode.create_task(db, payload)
    await _invalidate_task(task.id)
    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    cache_key = f"task_mode:task:{task_id}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    task = await task_mode.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    data = TaskResponse.model_validate(task).model_dump()
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    assignee_id: Optional[str] = None,
    created_by: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = Query(None, ge=1, le=5),
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = _key(
        "tasks",
        {
            "skip": skip,
            "limit": limit,
            "assignee_id": assignee_id,
            "created_by": created_by,
            "status": status,
            "priority": priority,
            "created_from": created_from.isoformat() if created_from else None,
            "created_to": created_to.isoformat() if created_to else None,
            "updated_from": updated_from.isoformat() if updated_from else None,
            "updated_to": updated_to.isoformat() if updated_to else None,
        },
    )
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    tasks = await task_mode.list_tasks(
        db,
        skip=skip,
        limit=limit,
        assignee_id=assignee_id,
        created_by=created_by,
        status=status,
        priority=priority,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
    )
    data = [TaskResponse.model_validate(t).model_dump() for t in tasks]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await task_mode.update_task(db, task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return task


@router.post("/tasks/{task_id}/status", response_model=TaskResponse)
async def change_task_status(task_id: str, payload: TaskStatusChange, db: AsyncSession = Depends(get_db)):
    task = await task_mode.change_status(db, task_id, payload.status, payload.actor_id, payload.note)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, actor_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    ok = await task_mode.delete_task(db, task_id, actor_id=actor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return {"deleted": True}


@router.get("/tasks/{task_id}/versions", response_model=List[TaskVersionResponse])
async def list_versions(task_id: str, skip: int = 0, limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    cache_key = f"task_mode:versions:{task_id}:{skip}:{limit}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached
    versions = await task_mode.list_versions(db, task_id, skip=skip, limit=limit)
    data = [TaskVersionResponse.model_validate(v).model_dump() for v in versions]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.get("/tasks/{task_id}/versions/{version}", response_model=TaskVersionResponse)
async def get_version(task_id: str, version: int, db: AsyncSession = Depends(get_db)):
    cache_key = f"task_mode:version:{task_id}:{version}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached
    v = await task_mode.get_version(db, task_id, version)
    if v is None:
        raise HTTPException(status_code=404, detail="Task version not found")
    data = TaskVersionResponse.model_validate(v).model_dump()
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.post("/tasks/{task_id}/qas", response_model=TaskQAResponse)
async def create_qa(task_id: str, payload: TaskQACreate, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.create_qa(db, task_id, payload)
    if qa is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return qa


@router.get("/tasks/{task_id}/qas", response_model=List[TaskQAResponse])
async def list_qas(
    task_id: str,
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = _key(
        f"qas:{task_id}",
        {
            "skip": skip,
            "limit": limit,
            "user_id": user_id,
            "created_from": created_from.isoformat() if created_from else None,
            "created_to": created_to.isoformat() if created_to else None,
        },
    )
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached
    qas = await task_mode.list_qas(
        db,
        task_id=task_id,
        skip=skip,
        limit=limit,
        user_id=user_id,
        created_from=created_from,
        created_to=created_to,
    )
    data = [TaskQAResponse.model_validate(q).model_dump() for q in qas]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.put("/qas/{qa_id}", response_model=TaskQAResponse)
async def update_qa(qa_id: int, payload: TaskQAUpdate, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.update_qa(db, qa_id, payload)
    if qa is None:
        raise HTTPException(status_code=404, detail="QA not found")
    await _invalidate_task(qa.task_id)
    return qa


@router.delete("/qas/{qa_id}")
async def delete_qa(qa_id: int, actor_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.get_qa(db, qa_id)
    if qa is None:
        raise HTTPException(status_code=404, detail="QA not found")
    ok = await task_mode.delete_qa(db, qa_id, actor_id=actor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="QA not found")
    await _invalidate_task(qa.task_id)
    return {"deleted": True}


@router.get("/tasks/{task_id}/logs", response_model=List[TaskLogResponse])
async def list_task_logs(
    task_id: str,
    skip: int = 0,
    limit: int = Query(200, ge=1, le=500),
    actor_id: Optional[str] = None,
    action_type: Optional[str] = None,
    importance: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = _key(
        f"logs:{task_id}",
        {
            "skip": skip,
            "limit": limit,
            "actor_id": actor_id,
            "action_type": action_type,
            "importance": importance,
            "created_from": created_from.isoformat() if created_from else None,
            "created_to": created_to.isoformat() if created_to else None,
        },
    )
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached

    logs = await task_mode.list_logs(
        db,
        task_id=task_id,
        actor_id=actor_id,
        action_type=action_type,
        importance=importance,
        created_from=created_from,
        created_to=created_to,
        skip=skip,
        limit=limit,
    )
    data = [TaskLogResponse.model_validate(l).model_dump() for l in logs]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.get("/logs", response_model=List[TaskLogResponse])
async def list_logs(
    skip: int = 0,
    limit: int = Query(200, ge=1, le=500),
    task_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    action_type: Optional[str] = None,
    importance: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    logs = await task_mode.list_logs(
        db,
        task_id=task_id,
        actor_id=actor_id,
        action_type=action_type,
        importance=importance,
        created_from=created_from,
        created_to=created_to,
        skip=skip,
        limit=limit,
    )
    return logs


@router.post("/logs/purge")
async def purge_logs(db: AsyncSession = Depends(get_db)):
    deleted = await task_mode.purge_expired_logs(db)
    return {"deleted": deleted}


@router.get("/backup/export", response_model=TaskBackupExport)
async def export_backup(
    task_id: Optional[str] = None,
    include_logs: bool = True,
    db: AsyncSession = Depends(get_db),
):
    tasks, versions, qas, logs = await task_mode.export_backup(db, task_id=task_id, include_logs=include_logs)
    return TaskBackupExport(exported_at=datetime.utcnow(), tasks=tasks, versions=versions, qas=qas, logs=logs)


@router.post("/backup/import", response_model=TaskBackupImportResult)
async def import_backup(
    payload: Dict[str, Any],
    overwrite: bool = False,
    db: AsyncSession = Depends(get_db),
):
    result = await task_mode.import_backup(db, payload=payload, overwrite=overwrite)
    return TaskBackupImportResult(**result)

