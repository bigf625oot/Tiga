from typing import List, Optional, Dict, Any
import json
from sqlalchemy.orm import Session
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
def create_source(db: Session, name: str, type: str, config: Dict, secrets: Dict = None) -> PathwaySource:
    db_source = PathwaySource(
        name=name,
        type=type,
        config=config,
        secrets_encrypted=encrypt_secrets(secrets)
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

def get_source(db: Session, source_id: int) -> Optional[PathwaySource]:
    return db.query(PathwaySource).filter(PathwaySource.id == source_id).first()

def get_source_by_name(db: Session, name: str) -> Optional[PathwaySource]:
    return db.query(PathwaySource).filter(PathwaySource.name == name).first()

def list_sources(db: Session, skip: int = 0, limit: int = 100) -> List[PathwaySource]:
    return db.query(PathwaySource).offset(skip).limit(limit).all()

# Job CRUD
def create_job(db: Session, name: str, source_id: int, operators: List[Dict], sinks: List[Dict]) -> PathwayJob:
    db_job = PathwayJob(
        name=name,
        source_id=source_id,
        operators_config=operators,
        sinks_config=sinks,
        status=PathwayJobStatus.CREATED
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_job(db: Session, job_id: int) -> Optional[PathwayJob]:
    return db.query(PathwayJob).filter(PathwayJob.id == job_id).first()

def get_job_by_name(db: Session, name: str) -> Optional[PathwayJob]:
    return db.query(PathwayJob).filter(PathwayJob.name == name).first()

def update_job_status(db: Session, job_id: int, status: str, pid: int = None, error: str = None):
    job = get_job(db, job_id)
    if job:
        job.status = status
        if pid is not None:
            job.pid = pid
        if error is not None:
            job.error_message = error
        db.commit()
        db.refresh(job)
    return job
