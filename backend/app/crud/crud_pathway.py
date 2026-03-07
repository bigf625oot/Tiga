from typing import List, Optional, Dict, Any
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from cryptography.fernet import Fernet
import os

from app.models.pathway import PathwaySource, PathwayJob, PathwayJobStatus
from app.core.config import settings

# In a real app, KEY should be in env vars or KMS
# Generate a key if not exists or use a fixed one for dev
_FERNET_KEY = os.getenv("PATHWAY_ENCRYPTION_KEY", Fernet.generate_key().decode())
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

# Job CRUD (Legacy + DAG)
async def create_job(
    db: AsyncSession, 
    name: str, 
    source_id: Optional[int] = None, 
    operators: Optional[List[Dict]] = None, 
    sinks: Optional[List[Dict]] = None,
    dag_config: Optional[Dict] = None
) -> PathwayJob:
    db_job = PathwayJob(
        name=name,
        source_id=source_id,
        operators_config=operators or [],
        sinks_config=sinks or [],
        dag_config=dag_config,
        status=PathwayJobStatus.CREATED
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

async def get_job(db: AsyncSession, job_id: int) -> Optional[PathwayJob]:
    result = await db.execute(select(PathwayJob).filter(PathwayJob.id == job_id))
    return result.scalars().first()

async def get_job_by_name(db: AsyncSession, name: str) -> Optional[PathwayJob]:
    result = await db.execute(select(PathwayJob).filter(PathwayJob.name == name))
    return result.scalars().first()

async def list_jobs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PathwayJob]:
    result = await db.execute(select(PathwayJob).offset(skip).limit(limit))
    return result.scalars().all()

async def update_job(db: AsyncSession, job_id: int, dag_config: Dict) -> Optional[PathwayJob]:
    job = await get_job(db, job_id)
    if job:
        job.dag_config = dag_config
        await db.commit()
        await db.refresh(job)
    return job

async def delete_job(db: AsyncSession, job_id: int) -> bool:
    job = await get_job(db, job_id)
    if job:
        await db.delete(job)
        await db.commit()
        return True
    return False

async def update_job_status(db: AsyncSession, job_id: int, status: str, pid: int = None, error: str = None):
    job = await get_job(db, job_id)
    if job:
        job.status = status
        if pid is not None:
            job.pid = pid
        if error is not None:
            job.error_message = error
        await db.commit()
        await db.refresh(job)
    return job
