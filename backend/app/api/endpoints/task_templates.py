from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.crud.task_mode import task_mode
from app.db.session import get_db
from app.schemas.task_mode import (
    TaskBackupExport,
    TaskBackupImportResult,
    TaskCreate,
    TaskQACreate,
    TaskQAResponse,
    TaskQAUpdate,
    TaskLogResponse,
    TaskResponse,
    TaskStatusChange,
    TaskUpdate,
    TaskVersionResponse,
)

from app.schemas.async_task import AsyncTaskCreateResponse

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
async def create_task_template(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await task_mode.create_task(db, payload)
    await _invalidate_task(task.id)
    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_template(task_id: str, db: AsyncSession = Depends(get_db)):
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


@router.post("/tasks/{task_id}:run", response_model=AsyncTaskCreateResponse, status_code=202)
async def run_task_template(
    task_id: str,
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据任务模板一键发起任务运行实例 (TaskRun)。
    这里将从模板读取配置，并分发给 TaskEngineService。
    """
    task_tpl = await task_mode.get_task(db, task_id)
    if task_tpl is None:
        raise HTTPException(status_code=404, detail="Task template not found")

    from app.crud.async_task import async_task
    from app.schemas.async_task import AsyncTaskCreate
    from app.core.task_progress import task_progress
    from app.services.platform.task_engine.service import task_engine_service
    from app.services.platform.task_engine.models import TaskEngineType, TaskRunContext
    
    # 1. 创建 TaskRun 记录
    # 将模板的属性映射到运行实例，扩展字段中保存模板来源 ref
    payload = AsyncTaskCreate(
        name=f"Run of {task_tpl.name}",
        task_type="GENERAL", # 默认使用异步任务处理模板，若有具体分类可再映射
        priority=task_tpl.priority,
        context={
            "template_id": task_id,
            "description": task_tpl.description, # 注意：此时可能需要解密（已由模型 property 自动处理）
            "source": "task_template"
        }
    )
    
    task_run = await async_task.create(db, payload, user_id=user_id)

    # 2. 初始化进度
    await task_progress.set_progress(
        task_id=task_run.id,
        percent=0,
        status="PENDING",
        msg="模板任务已提交，等待分发",
        step="submitted",
    )
    await task_progress.publish_update(task_run.id, user_id or "anonymous")

    # 3. 分发给统一任务引擎
    context = TaskRunContext(
        task_id=task_run.id,
        engine_type=TaskEngineType.ASYNC_TASK,
        user_id=user_id or "anonymous",
        priority=payload.priority,
        config=payload.context
    )
    await task_engine_service.start_task(context)

    return AsyncTaskCreateResponse(
        task_id=task_run.id, 
        estimate_time=60, 
        message="模板任务已提交分发"
    )

@router.get("/tasks", response_model=List[TaskResponse])
async def list_task_templates(
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
async def update_task_template(task_id: str, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await task_mode.update_task(db, task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return task


@router.post("/tasks/{task_id}/status", response_model=TaskResponse)
async def change_task_template_status(task_id: str, payload: TaskStatusChange, db: AsyncSession = Depends(get_db)):
    task = await task_mode.change_status(db, task_id, payload.status, payload.actor_id, payload.note)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return task


@router.delete("/tasks/{task_id}")
async def delete_task_template(task_id: str, actor_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    ok = await task_mode.delete_task(db, task_id, actor_id=actor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return {"deleted": True}


@router.get("/tasks/{task_id}/versions", response_model=List[TaskVersionResponse])
async def list_task_template_versions(
    task_id: str, skip: int = 0, limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)
):
    cache_key = f"task_mode:versions:{task_id}:{skip}:{limit}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return cached
    versions = await task_mode.list_versions(db, task_id, skip=skip, limit=limit)
    data = [TaskVersionResponse.model_validate(v).model_dump() for v in versions]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.get("/tasks/{task_id}/versions/{version}", response_model=TaskVersionResponse)
async def get_task_template_version(task_id: str, version: int, db: AsyncSession = Depends(get_db)):
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
async def create_task_template_qa(task_id: str, payload: TaskQACreate, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.create_qa(db, task_id, payload)
    if qa is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _invalidate_task(task_id)
    return qa


@router.get("/tasks/{task_id}/qas", response_model=List[TaskQAResponse])
async def list_task_template_qas(
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
async def update_task_template_qa(qa_id: int, payload: TaskQAUpdate, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.update_qa(db, qa_id, payload)
    if qa is None:
        raise HTTPException(status_code=404, detail="QA not found")
    await _invalidate_task(qa.task_id)
    return qa


@router.delete("/qas/{qa_id}")
async def delete_task_template_qa(qa_id: int, actor_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    qa = await task_mode.get_qa(db, qa_id)
    if qa is None:
        raise HTTPException(status_code=404, detail="QA not found")
    ok = await task_mode.delete_qa(db, qa_id, actor_id=actor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="QA not found")
    await _invalidate_task(qa.task_id)
    return {"deleted": True}


@router.get("/tasks/{task_id}/logs", response_model=List[TaskLogResponse])
async def list_task_template_logs(
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
    data = [TaskLogResponse.model_validate(log_entry).model_dump() for log_entry in logs]
    await cache.set_json(cache_key, data, ttl_seconds=settings.TASK_MODE_CACHE_TTL_SECONDS)
    return data


@router.get("/logs", response_model=List[TaskLogResponse])
async def list_task_template_logs_global(
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
async def purge_task_template_logs(db: AsyncSession = Depends(get_db)):
    deleted = await task_mode.purge_expired_logs(db)
    return {"deleted": deleted}


@router.get("/backup/export", response_model=TaskBackupExport)
async def export_task_templates(task_id: Optional[str] = None, include_logs: bool = True, db: AsyncSession = Depends(get_db)):
    tasks, versions, qas, logs = await task_mode.export_backup(db, task_id=task_id, include_logs=include_logs)
    return TaskBackupExport(exported_at=datetime.utcnow(), tasks=tasks, versions=versions, qas=qas, logs=logs)


@router.post("/backup/import", response_model=TaskBackupImportResult)
async def import_task_templates(payload: Dict[str, Any], overwrite: bool = False, db: AsyncSession = Depends(get_db)):
    result = await task_mode.import_backup(db, payload=payload, overwrite=overwrite)
    return TaskBackupImportResult(**result)

