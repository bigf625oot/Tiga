from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import encrypt_json, encrypt_text
from app.models.task_mode import Task, TaskLog, TaskQA, TaskVersion
from app.schemas.task_mode import TaskCreate, TaskQACreate, TaskQAUpdate, TaskUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _expires_at(importance: str) -> Optional[datetime]:
    if importance == "important":
        return _utcnow() + timedelta(days=settings.TASK_MODE_LOG_RETENTION_IMPORTANT_DAYS)
    if importance == "normal":
        return _utcnow() + timedelta(days=settings.TASK_MODE_LOG_RETENTION_NORMAL_DAYS)
    return None


def _task_state(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assignee_id": task.assignee_id,
        "created_by": task.created_by,
        "current_version": task.current_version,
    }


class CRUDTaskMode:
    async def create_task(self, db: AsyncSession, obj_in: TaskCreate) -> Task:
        task = Task(
            name=obj_in.name,
            description_enc=encrypt_text(obj_in.description),
            status=obj_in.status,
            priority=obj_in.priority,
            assignee_id=obj_in.assignee_id,
            created_by=obj_in.created_by,
            current_version=1,
        )
        db.add(task)
        await db.flush()

        db.add(
            TaskVersion(
                task_id=task.id,
                version=1,
                name=task.name,
                description_enc=task.description_enc,
                status=task.status,
                priority=task.priority,
                assignee_id=task.assignee_id,
                changed_by=obj_in.created_by,
                change_summary="create",
            )
        )

        db.add(
            TaskLog(
                task_id=task.id,
                actor_id=obj_in.created_by,
                action_type="task.create",
                importance="important",
                content_enc=encrypt_text("create"),
                before_state_enc=None,
                after_state_enc=encrypt_json(_task_state(task)),
                expires_at=_expires_at("important"),
            )
        )

        await db.commit()
        await db.refresh(task)
        return task

    async def get_task(self, db: AsyncSession, task_id: str) -> Optional[Task]:
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()

    async def list_tasks(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        assignee_id: Optional[str] = None,
        created_by: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        updated_from: Optional[datetime] = None,
        updated_to: Optional[datetime] = None,
    ) -> List[Task]:
        conditions = []
        if assignee_id is not None:
            conditions.append(Task.assignee_id == assignee_id)
        if created_by is not None:
            conditions.append(Task.created_by == created_by)
        if status is not None:
            conditions.append(Task.status == status)
        if priority is not None:
            conditions.append(Task.priority == priority)
        if created_from is not None:
            conditions.append(Task.created_at >= created_from)
        if created_to is not None:
            conditions.append(Task.created_at <= created_to)
        if updated_from is not None:
            conditions.append(Task.updated_at >= updated_from)
        if updated_to is not None:
            conditions.append(Task.updated_at <= updated_to)

        query = select(Task).order_by(Task.updated_at.desc()).offset(skip).limit(limit)
        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return result.scalars().all()

    async def update_task(self, db: AsyncSession, task_id: str, obj_in: TaskUpdate) -> Optional[Task]:
        task = await self.get_task(db, task_id)
        if task is None:
            return None

        before = _task_state(task)
        actor_id = obj_in.actor_id

        if obj_in.name is not None:
            task.name = obj_in.name
        if obj_in.description is not None:
            task.description_enc = encrypt_text(obj_in.description)
        if obj_in.status is not None:
            task.status = obj_in.status
        if obj_in.priority is not None:
            task.priority = obj_in.priority
        if obj_in.assignee_id is not None:
            task.assignee_id = obj_in.assignee_id

        task.current_version = int(task.current_version or 0) + 1
        await db.flush()

        db.add(
            TaskVersion(
                task_id=task.id,
                version=task.current_version,
                name=task.name,
                description_enc=task.description_enc,
                status=task.status,
                priority=task.priority,
                assignee_id=task.assignee_id,
                changed_by=actor_id,
                change_summary=obj_in.change_summary,
            )
        )

        after = _task_state(task)
        db.add(
            TaskLog(
                task_id=task.id,
                actor_id=actor_id,
                action_type="task.update",
                importance="important",
                content_enc=encrypt_text(obj_in.change_summary or "update"),
                before_state_enc=encrypt_json(before),
                after_state_enc=encrypt_json(after),
                expires_at=_expires_at("important"),
            )
        )

        await db.commit()
        await db.refresh(task)
        return task

    async def delete_task(self, db: AsyncSession, task_id: str, actor_id: Optional[str] = None) -> bool:
        task = await self.get_task(db, task_id)
        if task is None:
            return False

        before = _task_state(task)

        db.add(
            TaskLog(
                task_id=task.id,
                actor_id=actor_id,
                action_type="task.delete",
                importance="important",
                content_enc=encrypt_text("delete"),
                before_state_enc=encrypt_json(before),
                after_state_enc=None,
                expires_at=_expires_at("important"),
            )
        )
        await db.flush()
        await db.delete(task)
        await db.commit()
        return True

    async def change_status(
        self, db: AsyncSession, task_id: str, status: str, actor_id: Optional[str], note: Optional[str]
    ) -> Optional[Task]:
        upd = TaskUpdate(status=status, actor_id=actor_id, change_summary=note or "status change")
        return await self.update_task(db, task_id, upd)

    async def list_versions(self, db: AsyncSession, task_id: str, skip: int = 0, limit: int = 50) -> List[TaskVersion]:
        result = await db.execute(
            select(TaskVersion)
            .where(TaskVersion.task_id == task_id)
            .order_by(TaskVersion.version.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_version(self, db: AsyncSession, task_id: str, version: int) -> Optional[TaskVersion]:
        result = await db.execute(
            select(TaskVersion).where(and_(TaskVersion.task_id == task_id, TaskVersion.version == version))
        )
        return result.scalars().first()

    async def create_qa(self, db: AsyncSession, task_id: str, obj_in: TaskQACreate) -> Optional[TaskQA]:
        task = await self.get_task(db, task_id)
        if task is None:
            return None

        qa = TaskQA(
            task_id=task_id,
            user_id=obj_in.user_id,
            question_enc=encrypt_text(obj_in.question),
            answer_enc=encrypt_text(obj_in.answer),
        )
        db.add(qa)
        await db.flush()

        db.add(
            TaskLog(
                task_id=task_id,
                actor_id=obj_in.user_id,
                action_type="qa.create",
                importance="normal",
                content_enc=encrypt_text("qa create"),
                before_state_enc=None,
                after_state_enc=encrypt_json({"qa_id": qa.id}),
                expires_at=_expires_at("normal"),
            )
        )

        await db.commit()
        await db.refresh(qa)
        return qa

    async def list_qas(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
    ) -> List[TaskQA]:
        conditions = [TaskQA.task_id == task_id]
        if user_id is not None:
            conditions.append(TaskQA.user_id == user_id)
        if created_from is not None:
            conditions.append(TaskQA.created_at >= created_from)
        if created_to is not None:
            conditions.append(TaskQA.created_at <= created_to)

        result = await db.execute(
            select(TaskQA).where(and_(*conditions)).order_by(TaskQA.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_qa(self, db: AsyncSession, qa_id: int) -> Optional[TaskQA]:
        result = await db.execute(select(TaskQA).where(TaskQA.id == qa_id))
        return result.scalars().first()

    async def update_qa(self, db: AsyncSession, qa_id: int, obj_in: TaskQAUpdate) -> Optional[TaskQA]:
        qa = await self.get_qa(db, qa_id)
        if qa is None:
            return None

        before = {"qa_id": qa.id, "question": qa.question, "answer": qa.answer, "user_id": qa.user_id}

        if obj_in.question is not None:
            qa.question_enc = encrypt_text(obj_in.question)
        if obj_in.answer is not None:
            qa.answer_enc = encrypt_text(obj_in.answer)
        if obj_in.user_id is not None:
            qa.user_id = obj_in.user_id
        await db.flush()

        after = {"qa_id": qa.id, "question": qa.question, "answer": qa.answer, "user_id": qa.user_id}
        db.add(
            TaskLog(
                task_id=qa.task_id,
                actor_id=obj_in.user_id,
                action_type="qa.update",
                importance="normal",
                content_enc=encrypt_text("qa update"),
                before_state_enc=encrypt_json(before),
                after_state_enc=encrypt_json(after),
                expires_at=_expires_at("normal"),
            )
        )

        await db.commit()
        await db.refresh(qa)
        return qa

    async def delete_qa(self, db: AsyncSession, qa_id: int, actor_id: Optional[str] = None) -> bool:
        qa = await self.get_qa(db, qa_id)
        if qa is None:
            return False

        before = {"qa_id": qa.id, "user_id": qa.user_id}

        db.add(
            TaskLog(
                task_id=qa.task_id,
                actor_id=actor_id,
                action_type="qa.delete",
                importance="normal",
                content_enc=encrypt_text("qa delete"),
                before_state_enc=encrypt_json(before),
                after_state_enc=None,
                expires_at=_expires_at("normal"),
            )
        )
        await db.flush()
        await db.delete(qa)
        await db.commit()
        return True

    async def list_logs(
        self,
        db: AsyncSession,
        *,
        task_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        action_type: Optional[str] = None,
        importance: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[TaskLog]:
        conditions = []
        if task_id is not None:
            conditions.append(TaskLog.task_id == task_id)
        if actor_id is not None:
            conditions.append(TaskLog.actor_id == actor_id)
        if action_type is not None:
            conditions.append(TaskLog.action_type == action_type)
        if importance is not None:
            conditions.append(TaskLog.importance == importance)
        if created_from is not None:
            conditions.append(TaskLog.created_at >= created_from)
        if created_to is not None:
            conditions.append(TaskLog.created_at <= created_to)

        query = select(TaskLog).order_by(TaskLog.created_at.desc()).offset(skip).limit(limit)
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query)
        return result.scalars().all()

    async def purge_expired_logs(self, db: AsyncSession) -> int:
        result = await db.execute(
            delete(TaskLog)
            .where(and_(TaskLog.expires_at.is_not(None), TaskLog.expires_at < func.now()))
            .execution_options(synchronize_session=False)
        )
        await db.commit()
        return int(result.rowcount or 0)

    async def export_backup(
        self, db: AsyncSession, *, task_id: Optional[str] = None, include_logs: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        task_conditions = []
        if task_id is not None:
            task_conditions.append(Task.id == task_id)
        tasks = (await db.execute(select(Task).where(and_(*task_conditions)) if task_conditions else select(Task))).scalars().all()
        task_ids = [t.id for t in tasks]

        versions = []
        qas = []
        logs = []
        if task_ids:
            versions = (await db.execute(select(TaskVersion).where(TaskVersion.task_id.in_(task_ids)))).scalars().all()
            qas = (await db.execute(select(TaskQA).where(TaskQA.task_id.in_(task_ids)))).scalars().all()
            if include_logs:
                logs = (await db.execute(select(TaskLog).where(TaskLog.task_id.in_(task_ids)))).scalars().all()

        tasks_payload = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "assignee_id": t.assignee_id,
                "created_by": t.created_by,
                "current_version": t.current_version,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tasks
        ]
        versions_payload = [
            {
                "task_id": v.task_id,
                "version": v.version,
                "name": v.name,
                "description": v.description,
                "status": v.status,
                "priority": v.priority,
                "assignee_id": v.assignee_id,
                "changed_by": v.changed_by,
                "change_summary": v.change_summary,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]
        qas_payload = [
            {
                "id": q.id,
                "task_id": q.task_id,
                "user_id": q.user_id,
                "question": q.question,
                "answer": q.answer,
                "created_at": q.created_at.isoformat() if q.created_at else None,
                "updated_at": q.updated_at.isoformat() if q.updated_at else None,
            }
            for q in qas
        ]
        logs_payload = [
            {
                "id": l.id,
                "task_id": l.task_id,
                "actor_id": l.actor_id,
                "action_type": l.action_type,
                "importance": l.importance,
                "content": l.content,
                "before_state": l.before_state,
                "after_state": l.after_state,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            }
            for l in logs
        ]
        return tasks_payload, versions_payload, qas_payload, logs_payload

    async def import_backup(
        self, db: AsyncSession, *, payload: Dict[str, Any], overwrite: bool = False
    ) -> Dict[str, int]:
        tasks = payload.get("tasks") or []
        versions = payload.get("versions") or []
        qas = payload.get("qas") or []
        logs = payload.get("logs") or []

        created = {"tasks_created": 0, "versions_created": 0, "qas_created": 0, "logs_created": 0}

        if overwrite:
            task_ids = [t.get("id") for t in tasks if t.get("id")]
            if task_ids:
                await db.execute(delete(TaskLog).where(TaskLog.task_id.in_(task_ids)).execution_options(synchronize_session=False))
                await db.execute(delete(TaskQA).where(TaskQA.task_id.in_(task_ids)).execution_options(synchronize_session=False))
                await db.execute(
                    delete(TaskVersion).where(TaskVersion.task_id.in_(task_ids)).execution_options(synchronize_session=False)
                )
                await db.execute(delete(Task).where(Task.id.in_(task_ids)).execution_options(synchronize_session=False))

        for t in tasks:
            task = Task(
                id=t.get("id"),
                name=t.get("name") or "Untitled",
                description_enc=encrypt_text(t.get("description")),
                status=t.get("status") or "open",
                priority=int(t.get("priority") or 3),
                assignee_id=t.get("assignee_id"),
                created_by=t.get("created_by"),
                current_version=int(t.get("current_version") or 1),
            )
            db.add(task)
            created["tasks_created"] += 1

        for v in versions:
            ver = TaskVersion(
                task_id=v.get("task_id"),
                version=int(v.get("version") or 1),
                name=v.get("name") or "Untitled",
                description_enc=encrypt_text(v.get("description")),
                status=v.get("status") or "open",
                priority=int(v.get("priority") or 3),
                assignee_id=v.get("assignee_id"),
                changed_by=v.get("changed_by"),
                change_summary=v.get("change_summary"),
            )
            db.add(ver)
            created["versions_created"] += 1

        for q in qas:
            qa = TaskQA(
                id=q.get("id"),
                task_id=q.get("task_id"),
                user_id=q.get("user_id"),
                question_enc=encrypt_text(q.get("question") or ""),
                answer_enc=encrypt_text(q.get("answer") or ""),
            )
            db.add(qa)
            created["qas_created"] += 1

        for l in logs:
            log = TaskLog(
                id=l.get("id"),
                task_id=l.get("task_id"),
                actor_id=l.get("actor_id"),
                action_type=l.get("action_type") or "import",
                importance=l.get("importance") or "normal",
                content_enc=encrypt_text(l.get("content")),
                before_state_enc=encrypt_json(l.get("before_state")),
                after_state_enc=encrypt_json(l.get("after_state")),
            )
            db.add(log)
            created["logs_created"] += 1

        await db.commit()

        return created


task_mode = CRUDTaskMode()
