import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_task_mode import task_mode
from app.models.task_mode import TaskLog, TaskQA, TaskVersion
from app.schemas.task_mode import TaskCreate, TaskQACreate, TaskUpdate


@pytest.mark.asyncio
async def test_task_create_update_versioning(db: AsyncSession):
    created = await task_mode.create_task(
        db,
        TaskCreate(
            name="T1",
            description="desc",
            status="open",
            priority=3,
            assignee_id="u1",
            created_by="u0",
        ),
    )
    assert created.id is not None
    assert created.description == "desc"
    assert created.current_version == 1

    versions = await task_mode.list_versions(db, created.id, skip=0, limit=10)
    assert len(versions) == 1
    assert versions[0].version == 1

    logs = await task_mode.list_logs(db, task_id=created.id, skip=0, limit=50)
    assert any(l.action_type == "task.create" for l in logs)

    updated = await task_mode.update_task(
        db,
        created.id,
        TaskUpdate(
            name="T1-upd",
            description="desc2",
            priority=2,
            actor_id="u0",
            change_summary="edit",
        ),
    )
    assert updated is not None
    assert updated.name == "T1-upd"
    assert updated.description == "desc2"
    assert updated.current_version == 2

    versions2 = await task_mode.list_versions(db, created.id, skip=0, limit=10)
    assert {v.version for v in versions2} == {1, 2}


@pytest.mark.asyncio
async def test_qa_crud_and_logging(db: AsyncSession):
    task = await task_mode.create_task(db, TaskCreate(name="T2", description=None, created_by="u0"))
    qa = await task_mode.create_qa(db, task.id, TaskQACreate(question="Q1", answer="A1", user_id="u0"))
    assert qa is not None
    assert qa.question == "Q1"
    assert qa.answer == "A1"

    qas = await task_mode.list_qas(db, task_id=task.id, skip=0, limit=10)
    assert len(qas) == 1

    logs = await task_mode.list_logs(db, task_id=task.id, skip=0, limit=50)
    assert any(l.action_type == "qa.create" for l in logs)

    ok = await task_mode.delete_qa(db, qa.id, actor_id="u0")
    assert ok is True
    qas2 = await task_mode.list_qas(db, task_id=task.id, skip=0, limit=10)
    assert len(qas2) == 0


@pytest.mark.asyncio
async def test_log_purge(db: AsyncSession):
    task = await task_mode.create_task(db, TaskCreate(name="T3", created_by="u0"))
    logs = await task_mode.list_logs(db, task_id=task.id, skip=0, limit=10)
    assert logs

    result = await db.execute(select(TaskLog).where(TaskLog.task_id == task.id).limit(1))
    log = result.scalars().first()
    log.expires_at = log.created_at.replace(year=2000)
    await db.commit()

    deleted = await task_mode.purge_expired_logs(db)
    assert deleted >= 1


@pytest.mark.asyncio
async def test_backup_export_import_roundtrip(db: AsyncSession):
    t = await task_mode.create_task(db, TaskCreate(name="T4", description="d", created_by="u0"))
    await task_mode.create_qa(db, t.id, TaskQACreate(question="Q", answer="A", user_id="u0"))
    exported_tasks, exported_versions, exported_qas, exported_logs = await task_mode.export_backup(db, task_id=t.id)
    payload = {
        "tasks": exported_tasks,
        "versions": exported_versions,
        "qas": exported_qas,
        "logs": exported_logs,
    }

    await task_mode.delete_task(db, t.id, actor_id="u0")
    result = await task_mode.import_backup(db, payload=payload, overwrite=True)
    assert result["tasks_created"] == 1
    assert result["versions_created"] >= 1
    assert result["qas_created"] == 1

    restored_versions = await task_mode.list_versions(db, t.id, skip=0, limit=10)
    assert len(restored_versions) >= 1
