from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.pathway.core.config import PathwayJobConfig, SourceConfig
from app.services.pathway.core.engine import engine
from app.services.pathway.core.exceptions import PathwayException
from app.crud import crud_pathway
from app.models.pathway import PathwayJobStatus

router = APIRouter()

# -----------------------------------------------------------------------------
# Sources API
# -----------------------------------------------------------------------------
@router.post("/sources", status_code=201)
def create_source(
    name: str, 
    type: str, 
    config: Dict[str, Any], 
    secrets: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Register a new data source."""
    if crud_pathway.get_source_by_name(db, name):
        raise HTTPException(status_code=400, detail="Source with this name already exists")
    
    source = crud_pathway.create_source(db, name, type, config, secrets)
    return {"id": source.id, "name": source.name, "type": source.type}

@router.get("/sources")
def list_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List registered data sources."""
    sources = crud_pathway.list_sources(db, skip, limit)
    return [{"id": s.id, "name": s.name, "type": s.type} for s in sources]

from app.services.pathway.connectors.source import get_source as get_source_connector

# ... (inside router)

@router.post("/sources/discover")
def discover_source_schema(
    type: str, 
    config: Dict[str, Any], 
    secrets: Dict[str, Any] = None,
):
    """
    Discover schema for a given source configuration without saving it.
    """
    try:
        source_conn = get_source_connector(type)
        full_config = {**config, **(secrets or {})}
        
        # Check if discovery is implemented
        return source_conn.discover_schema(full_config)
             
    except PathwayException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# -----------------------------------------------------------------------------
# Jobs API
# -----------------------------------------------------------------------------
@router.post("/jobs", status_code=201)
async def create_job(
    name: str, 
    source_name: str,
    operators: List[Dict[str, Any]], 
    sinks: List[Dict[str, Any]],
    settings: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """
    Start a new Pathway integration job using a registered source.
    """
    # 1. Fetch Source
    source = crud_pathway.get_source_by_name(db, source_name)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if crud_pathway.get_job_by_name(db, name):
         raise HTTPException(status_code=400, detail="Job with this name already exists")

    # 2. Persist Job
    db_job = crud_pathway.create_job(db, name, source.id, operators, sinks)

    # 3. Construct Pathway Config
    # Decrypt secrets
    secrets = crud_pathway.decrypt_secrets(source.secrets_encrypted)
    
    # Merge config and secrets
    full_source_config = {**source.config, **secrets}
    
    pathway_config = PathwayJobConfig(
        name=name,
        sources=[SourceConfig(type=source.type, config=full_source_config)],
        operators=operators, # Need pydantic conversion if strict
        sinks=sinks,
        settings=settings
    )

    # 4. Start Engine
    try:
        engine.start_job(pathway_config)
        # Update status
        crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.RUNNING)
        return {"id": db_job.id, "name": db_job.name, "status": "running"}
    except PathwayException as e:
        crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{name}")
async def get_job_status(name: str, db: Session = Depends(get_db)):
    """
    Get the status of a Pathway job (sync with DB).
    """
    # Check memory status
    engine_status = engine.get_job_status(name)
    
    # Check DB status
    db_job = crud_pathway.get_job_by_name(db, name)
    if not db_job:
         raise HTTPException(status_code=404, detail=f"Job {name} not found in DB")

    # Sync DB if needed (e.g. if engine says stopped but DB says running)
    if engine_status == "not_found" and db_job.status == PathwayJobStatus.RUNNING:
         crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
         return {"name": name, "status": "stopped", "detail": "Process not found"}

    return {"name": name, "status": engine_status, "db_status": db_job.status}

@router.delete("/jobs/{name}")
async def stop_job(name: str, db: Session = Depends(get_db)):
    """
    Stop a Pathway job.
    """
    db_job = crud_pathway.get_job_by_name(db, name)
    
    try:
        engine.stop_job(name)
        if db_job:
            crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
        return {"message": f"Job {name} stopped"}
    except PathwayException as e:
        if "not found" in e.message and db_job:
             # Cleanup DB if process is gone
             crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get("/metrics/prometheus")
async def get_metrics():
    """
    Expose metrics for Prometheus.
    This is a placeholder. In a real scenario, you would aggregate metrics 
    from running Pathway instances or proxy to their metrics endpoints.
    """
    # Assuming we want to expose metrics from the main app or specific jobs
    # For now, we return a simple up metric
    return "pathway_up 1\n"
