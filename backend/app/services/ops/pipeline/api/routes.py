from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import asyncio
import os
import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.ops.pipeline.core.config import PathwayJobConfig, SourceConfig
from app.services.ops.pipeline.core.models import DAGPipeline, DAGNode
from app.services.ops.pipeline.core.engine import engine
from app.services.ops.pipeline.core.exceptions import PathwayException
from app.services.ops.pipeline.core.dag_builder import build_dag_pipeline_from_config
from app.services.ops.pipeline.core.runtime import allocate_log_file, allocate_monitoring_port, tail_log_entries
from app.crud import pathway as crud_pathway
from app.models.pathway_db import PathwayJobStatus
from app.schemas.pathway import PipelineCreate, PipelineUpdate, PipelineResponse, PipelineRunResponse
from app.services.ops.pipeline.connectors.source import get_source as get_source_connector
from app.db.session import AsyncSessionLocal

router = APIRouter()

async def _monitor_pipeline_until_exit(pipeline_id: int, job_name: str) -> None:
    while True:
        try:
            status = engine.get_job_status(job_name)
            if status == "running":
                await asyncio.sleep(2)
                continue

            exitcode = engine.get_job_exitcode(job_name)
            final_status = PathwayJobStatus.STOPPED if (exitcode in (0, None) or status in {"stopped", "not_found"}) else PathwayJobStatus.FAILED

            async with AsyncSessionLocal() as db:
                job = await crud_pathway.get_job(db, pipeline_id)
                if not job or job.is_deleted:
                    return
                err = None
                log_file = (job.settings or {}).get("log_file")
                if final_status == PathwayJobStatus.FAILED and log_file:
                    entries = await anyio.to_thread.run_sync(lambda: tail_log_entries(log_file, limit=50))
                    err = "\n".join(e.get("message", "") for e in entries[-10:])
                await crud_pathway.update_job_status(db, pipeline_id, final_status, error=err)
            return
        except Exception:
            return

# -----------------------------------------------------------------------------
# Sources API
# -----------------------------------------------------------------------------
@router.post("/sources", status_code=201)
async def create_source(
    name: str, 
    type: str, 
    config: Dict[str, Any], 
    secrets: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Register a new data source."""
    if await crud_pathway.get_source_by_name(db, name):
        raise HTTPException(status_code=400, detail="Source with this name already exists")
    
    source = await crud_pathway.create_source(db, name, type, config, secrets)
    return {"id": source.id, "name": source.name, "type": source.type}

@router.get("/sources")
async def list_sources(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List registered data sources."""
    sources = await crud_pathway.list_sources(db, skip, limit)
    return [{"id": s.id, "name": s.name, "type": s.type} for s in sources]

@router.get("/sources/{source_id}")
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await crud_pathway.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"id": source.id, "name": source.name, "type": source.type, "config": source.config}

@router.put("/sources/{source_id}")
async def update_source(
    source_id: int,
    name: Optional[str] = None,
    type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    secrets: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        source = await crud_pathway.update_source(db, source_id, name=name, type=type, config=config, secrets=secrets)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return {"id": source.id, "name": source.name, "type": source.type, "config": source.config}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    try:
        ok = await crud_pathway.delete_source(db, source_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Source not found")
        return {"message": "Source deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sources/discover")
async def discover_source_schema(
    type: str, 
    config: Dict[str, Any], 
    secrets: Dict[str, Any] = None,
):
    """
    Discover schema for a given source configuration without saving it.
    """
    try:
        source = get_source_connector(type)
        full_config = {**(config or {}), **(secrets or {})}
        discover_fn = getattr(source, "discover_schema", None)
        if not callable(discover_fn):
            raise HTTPException(status_code=400, detail="该数据源类型不支持 schema 探测")
        schema = await anyio.to_thread.run_sync(lambda: discover_fn(full_config))
        return {"status": "success", "schema": schema}
    except HTTPException:
        raise
    except PathwayException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Pipelines (DAG) API
# -----------------------------------------------------------------------------

@router.post("/pipelines", response_model=PipelineResponse, status_code=201)
async def create_pipeline(pipeline: PipelineCreate, db: AsyncSession = Depends(get_db)):
    """Create a new DAG pipeline."""
    try:
        if await crud_pathway.get_job_by_name(db, pipeline.name):
            raise HTTPException(status_code=400, detail="Pipeline with this name already exists")
        
        db_job = await crud_pathway.create_job(
            db, 
            name=pipeline.name, 
            dag_config=pipeline.dag_config,
            description=pipeline.description,
            schedule_config=pipeline.schedule_config.model_dump() if pipeline.schedule_config else {},
        )
        return db_job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating pipeline: {str(e)}")

@router.get("/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all pipelines."""
    return await crud_pathway.list_jobs(db, skip, limit)

@router.get("/pipelines/trash", response_model=List[PipelineResponse])
async def list_deleted_pipelines(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud_pathway.list_deleted_jobs(db, skip, limit)

@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Get pipeline details."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    # Check if job is running and inject metrics
    # Note: We need to check if engine actually has the job running
    engine_status = engine.get_job_status(db_job.name)
    
    if db_job.dag_config and "nodes" in db_job.dag_config:
        nodes = db_job.dag_config["nodes"]
        if engine_status == "running":
            metrics = engine.get_job_metrics(db_job.name) or {}
            for node in nodes:
                if "data" not in node:
                    node["data"] = {}
                node["data"]["status"] = "running"
                node["data"]["metrics"] = {
                    "eps": metrics.get("global_eps", 0),
                    "latency": metrics.get("global_latency", 0),
                } if metrics else None
        else:
            for node in nodes:
                if "data" in node:
                    node["data"]["status"] = "idle"
                    node["data"]["metrics"] = None
            
    return db_job

@router.put("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(pipeline_id: int, pipeline: PipelineUpdate, db: AsyncSession = Depends(get_db)):
    """Update pipeline configuration."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    db_job = await crud_pathway.update_job(
        db,
        pipeline_id,
        dag_config=pipeline.dag_config,
        description=pipeline.description,
        schedule_config=pipeline.schedule_config.model_dump() if pipeline.schedule_config else None,
    )
    
    return db_job

@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a pipeline."""
    success = await crud_pathway.delete_job(db, pipeline_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"message": "Pipeline deleted"}

@router.post("/pipelines/{pipeline_id}/restore", response_model=PipelineResponse)
async def restore_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    job = await crud_pathway.restore_job(db, pipeline_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return job

@router.post("/pipelines/{pipeline_id}/clone", response_model=PipelineResponse, status_code=201)
async def clone_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    job = await crud_pathway.get_job(db, pipeline_id)
    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    base_name = f"{job.name}_copy"
    name = base_name
    suffix = 1
    while await crud_pathway.get_job_by_name(db, name):
        suffix += 1
        name = f"{base_name}{suffix}"

    new_job = await crud_pathway.create_job(
        db,
        name=name,
        dag_config=job.dag_config,
        description=job.description,
        schedule_config=job.schedule_config or {},
        settings=job.settings or {},
    )
    return new_job

@router.get("/pipelines/{pipeline_id}/export")
async def export_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    job = await crud_pathway.get_job(db, pipeline_id)
    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {
        "name": job.name,
        "description": job.description,
        "dag_config": job.dag_config,
        "schedule_config": job.schedule_config or {},
    }

@router.post("/pipelines/import", response_model=PipelineResponse, status_code=201)
async def import_pipeline(pipeline: PipelineCreate, db: AsyncSession = Depends(get_db)):
    name = pipeline.name
    if await crud_pathway.get_job_by_name(db, name):
        base_name = f"{name}_import"
        name = base_name
        suffix = 1
        while await crud_pathway.get_job_by_name(db, name):
            suffix += 1
            name = f"{base_name}{suffix}"

    job = await crud_pathway.create_job(
        db,
        name=name,
        dag_config=pipeline.dag_config,
        description=pipeline.description,
        schedule_config=pipeline.schedule_config.model_dump() if pipeline.schedule_config else {},
    )
    return job

@router.post("/pipelines/{pipeline_id}/run", response_model=PipelineRunResponse)
async def run_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Run a pipeline."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if not db_job.dag_config:
        raise HTTPException(status_code=400, detail="Pipeline has no DAG configuration")

    try:
        monitoring_port = (db_job.settings or {}).get("monitoring_port") or allocate_monitoring_port()
        log_file = (db_job.settings or {}).get("log_file") or allocate_log_file(db_job.id, db_job.name)
        settings = {**(db_job.settings or {}), "monitoring_port": monitoring_port, "log_file": log_file}
        await crud_pathway.update_job(db, db_job.id, settings=settings)

        dag_pipeline = build_dag_pipeline_from_config(
            pipeline_id=str(db_job.id),
            name=db_job.name,
            dag_config=db_job.dag_config,
            settings=settings,
            description=db_job.description,
        )

        pid = engine.start_job(dag_pipeline)
        await crud_pathway.update_job_status(
            db,
            db_job.id,
            PathwayJobStatus.RUNNING,
            pid=pid,
            monitoring_port=monitoring_port,
        )
        asyncio.create_task(_monitor_pipeline_until_exit(db_job.id, db_job.name))
        
        return {"pipeline_id": db_job.id, "status": "running", "message": "Pipeline started"}
        
    except Exception as e:
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")

@router.post("/pipelines/{pipeline_id}/stop")
async def stop_pipeline_run(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Stop a running pipeline."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    try:
        try:
            engine.stop_job(db_job.name)
        except Exception:
            if db_job.pid:
                try:
                    os.kill(db_job.pid, 15)
                except Exception:
                    pass
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
        return {"message": "Pipeline stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipelines/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    engine_status = engine.get_job_status(db_job.name)
    exitcode = engine.get_job_exitcode(db_job.name)
    if db_job.status == PathwayJobStatus.RUNNING and engine_status != "running":
        alive = False
        if db_job.pid:
            try:
                os.kill(db_job.pid, 0)
                alive = True
            except Exception:
                alive = False
        if not alive:
            await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
            db_job = await crud_pathway.get_job(db, pipeline_id)
    return {
        "id": db_job.id,
        "name": db_job.name,
        "db_status": db_job.status,
        "engine_status": engine_status,
        "exitcode": exitcode,
        "pid": db_job.pid,
        "monitoring_port": getattr(db_job, "monitoring_port", None),
        "error_message": db_job.error_message,
        "updated_at": db_job.updated_at,
    }

@router.get("/pipelines/{pipeline_id}/logs")
async def get_pipeline_logs(
    pipeline_id: int,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job or db_job.is_deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    log_file = (db_job.settings or {}).get("log_file")
    if not log_file:
        return []
    try:
        return await anyio.to_thread.run_sync(lambda: tail_log_entries(log_file, limit=limit))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Jobs API (Legacy Linear)
# -----------------------------------------------------------------------------
@router.post("/jobs", status_code=201)
async def create_job(
    name: str, 
    source_name: str,
    operators: List[Dict[str, Any]], 
    sinks: List[Dict[str, Any]],
    settings: Dict[str, Any] = {},
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new Pathway integration job using a registered source.
    """
    # 1. Fetch Source
    source = await crud_pathway.get_source_by_name(db, source_name)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if await crud_pathway.get_job_by_name(db, name):
         raise HTTPException(status_code=400, detail="Job with this name already exists")

    # 2. Persist Job
    log_file = allocate_log_file(0, name)
    full_settings = {**(settings or {}), "log_file": log_file}
    db_job = await crud_pathway.create_job(db, name, source.id, operators, sinks, settings=full_settings)

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
        settings=full_settings
    )

    # 4. Start Engine
    try:
        pid = engine.start_job(pathway_config)
        # Update status
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.RUNNING, pid=pid)
        return {"id": db_job.id, "name": db_job.name, "status": "running"}
    except PathwayException as e:
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{name}")
async def get_job_status(name: str, db: AsyncSession = Depends(get_db)):
    """
    Get the status of a Pathway job (sync with DB).
    """
    # Check memory status
    engine_status = engine.get_job_status(name)
    
    # Check DB status
    db_job = await crud_pathway.get_job_by_name(db, name)
    if not db_job:
         raise HTTPException(status_code=404, detail=f"Job {name} not found in DB")

    # Sync DB if needed (e.g. if engine says stopped but DB says running)
    if engine_status == "not_found" and db_job.status == PathwayJobStatus.RUNNING:
         await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
         return {"name": name, "status": "stopped", "detail": "Process not found"}

    return {"name": name, "status": engine_status, "db_status": db_job.status}

@router.delete("/jobs/{name}")
async def stop_job(name: str, db: AsyncSession = Depends(get_db)):
    """
    Stop a Pathway job.
    """
    db_job = await crud_pathway.get_job_by_name(db, name)
    
    try:
        engine.stop_job(name)
        if db_job:
            await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
        return {"message": f"Job {name} stopped"}
    except PathwayException as e:
        if "not found" in e.message and db_job:
             # Cleanup DB if process is gone
             await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
             return {"message": f"Job {name} already stopped"}
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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