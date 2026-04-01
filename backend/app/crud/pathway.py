from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from cryptography.fernet import Fernet
import os
from pathlib import Path
import logging

from app.models.pathway_db import PathwaySource, PathwayJob, PathwayJobStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

_FERNET_KEY = os.getenv("PATHWAY_ENCRYPTION_KEY")
if not _FERNET_KEY:
    backend_dir = Path(__file__).resolve().parents[2]
    key_path = backend_dir / "data" / "keys" / "pathway_fernet.key"
    try:
        if key_path.exists():
            _FERNET_KEY = key_path.read_text(encoding="utf-8").strip()
        else:
            if not (settings.DEBUG or settings.USE_SQLITE):
                raise RuntimeError("PATHWAY_ENCRYPTION_KEY 未配置，且未找到持久化 key 文件")
            _FERNET_KEY = Fernet.generate_key().decode()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(_FERNET_KEY, encoding="utf-8")
            logger.warning("PATHWAY_ENCRYPTION_KEY 未配置：已生成并写入本地 key 文件，仅适用于开发环境")
    except Exception as e:
        raise RuntimeError(f"Pathway secrets 加密初始化失败: {e}") from e
cipher_suite = Fernet(_FERNET_KEY.encode())

def encrypt_secrets(secrets: Dict[str, Any]) -> str:
    if not secrets:
        return None
    return cipher_suite.encrypt(json.dumps(secrets).encode()).decode()

def decrypt_secrets(encrypted_data: str) -> Dict[str, Any]:
    if not encrypted_data:
        return {}
    return json.loads(cipher_suite.decrypt(encrypted_data.encode()).decode())

# Source CRUD
async def create_source(db: AsyncSession, name: str, type: str, config: Dict, secrets: Dict = None) -> PathwaySource:
    db_source = PathwaySource(
        name=name,
        type=type,
        config=config,
        secrets_encrypted=encrypt_secrets(secrets)
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

async def get_source(db: AsyncSession, source_id: int) -> Optional[PathwaySource]:
    result = await db.execute(select(PathwaySource).filter(PathwaySource.id == source_id))
    return result.scalars().first()

async def get_source_by_name(db: AsyncSession, name: str) -> Optional[PathwaySource]:
    result = await db.execute(select(PathwaySource).filter(PathwaySource.name == name))
    return result.scalars().first()

async def list_sources(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PathwaySource]:
    result = await db.execute(select(PathwaySource).offset(skip).limit(limit))
    return result.scalars().all()

async def update_source(
    db: AsyncSession,
    source_id: int,
    name: Optional[str] = None,
    type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    secrets: Optional[Dict[str, Any]] = None,
) -> Optional[PathwaySource]:
    source = await get_source(db, source_id)
    if not source:
        return None
    if name is not None:
        source.name = name
    if type is not None:
        source.type = type
    if config is not None:
        source.config = config
    if secrets is not None:
        source.secrets_encrypted = encrypt_secrets(secrets)
    await db.commit()
    await db.refresh(source)
    return source

async def delete_source(db: AsyncSession, source_id: int) -> bool:
    source = await get_source(db, source_id)
    if not source:
        return False
    used = await db.execute(select(func.count()).select_from(PathwayJob).where(PathwayJob.source_id == source_id))
    if (used.scalar() or 0) > 0:
        raise ValueError("Source is referenced by existing jobs")
    await db.delete(source)
    await db.commit()
    return True

# Job CRUD (Legacy + DAG)
async def create_job(
    db: AsyncSession, 
    name: str, 
    source_id: Optional[int] = None, 
    operators: Optional[List[Dict]] = None, 
    sinks: Optional[List[Dict]] = None,
    dag_config: Optional[Dict] = None,
    description: Optional[str] = None,
    schedule_config: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> PathwayJob:
    db_job = PathwayJob(
        name=name,
        source_id=source_id,
        operators_config=operators or [],
        sinks_config=sinks or [],
        dag_config=dag_config,
        status=PathwayJobStatus.CREATED,
        description=description,
        schedule_config=schedule_config or {},
        settings=settings or {},
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

async def get_job(db: AsyncSession, job_id: int) -> Optional[PathwayJob]:
    result = await db.execute(select(PathwayJob).filter(PathwayJob.id == job_id))
    return result.scalars().first()

async def get_job_by_name(db: AsyncSession, name: str) -> Optional[PathwayJob]:
    result = await db.execute(select(PathwayJob).filter(PathwayJob.name == name, PathwayJob.is_deleted == False))
    return result.scalars().first()

async def list_jobs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PathwayJob]:
    result = await db.execute(
        select(PathwayJob)
        .where(PathwayJob.is_deleted == False)
        .order_by(PathwayJob.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def list_deleted_jobs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PathwayJob]:
    result = await db.execute(
        select(PathwayJob)
        .where(PathwayJob.is_deleted == True)
        .order_by(PathwayJob.deleted_at.desc().nullslast(), PathwayJob.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_job(
    db: AsyncSession,
    job_id: int,
    dag_config: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    schedule_config: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> Optional[PathwayJob]:
    job = await get_job(db, job_id)
    if not job or job.is_deleted:
        return None
    if dag_config is not None:
        job.dag_config = dag_config
    if description is not None:
        job.description = description
    if schedule_config is not None:
        job.schedule_config = schedule_config
    if settings is not None:
        job.settings = settings
    await db.commit()
    await db.refresh(job)
    return job

async def delete_job(db: AsyncSession, job_id: int) -> bool:
    job = await get_job(db, job_id)
    if not job or job.is_deleted:
        return False
    job.is_deleted = True
    job.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)
    return True

async def restore_job(db: AsyncSession, job_id: int) -> Optional[PathwayJob]:
    job = await get_job(db, job_id)
    if not job or not job.is_deleted:
        return None
    job.is_deleted = False
    job.deleted_at = None
    await db.commit()
    await db.refresh(job)
    return job

async def update_job_status(
    db: AsyncSession,
    job_id: int,
    status: PathwayJobStatus,
    pid: Optional[int] = None,
    monitoring_port: Optional[int] = None,
    error: Optional[str] = None,
):
    job = await get_job(db, job_id)
    if job:
        job.status = status
        if pid is not None:
            job.pid = pid
        if monitoring_port is not None:
            job.monitoring_port = monitoring_port
        if error is not None:
            job.error_message = error
        if status == PathwayJobStatus.RUNNING:
            job.last_run_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)
    return job
