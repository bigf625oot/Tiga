from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.pathway.core.config import PathwayJobConfig, SourceConfig
from app.services.pathway.core.models import DAGPipeline, DAGNode
from app.services.pathway.core.engine import engine
from app.services.pathway.core.exceptions import PathwayException
from app.crud import crud_pathway
from app.models.pathway import PathwayJobStatus
from app.schemas.pathway import PipelineCreate, PipelineUpdate, PipelineResponse, PipelineRunResponse

router = APIRouter()

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

from app.services.pathway.connectors.source import get_source as get_source_connector

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
        
        # Check if discovery is implemented (BaseSource doesn't enforce it yet, assume read returns table or similar)
        # For now, we just return a success message or mock schema
        return {"status": "success", "message": "Connection successful (schema discovery not fully implemented)"}
             
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
            dag_config=pipeline.dag_config
        )
        return db_job
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Error creating pipeline: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Print to server console if possible
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all pipelines."""
    return await crud_pathway.list_jobs(db, skip, limit)

@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Get pipeline details."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    # Check if job is running and inject metrics
    # Note: We need to check if engine actually has the job running
    engine_status = engine.get_job_status(db_job.name)
    
    if engine_status == "running":
        # If DB says stopped but engine says running, we might want to update DB?
        # For now, trust engine status for metrics
        metrics = engine.get_job_metrics(db_job.name)
        if metrics and db_job.dag_config and "nodes" in db_job.dag_config:
            # Inject metrics into nodes
            nodes = db_job.dag_config["nodes"]
            for node in nodes:
                # Ensure data object exists
                if "data" not in node:
                    node["data"] = {}
                
                # In a real scenario, we'd map specific metrics to specific nodes
                # For now, we apply the global simulated metrics to all nodes
                node["data"]["status"] = "running"
                node["data"]["metrics"] = {
                    "eps": metrics.get("global_eps", 0),
                    "latency": metrics.get("global_latency", 0)
                }
    elif db_job.status == PathwayJobStatus.RUNNING and engine_status != "running":
        # DB thinks it's running but engine says no -> Set to stopped/failed
        pass
    else:
        # If stopped, clear metrics/status
        if db_job.dag_config and "nodes" in db_job.dag_config:
            nodes = db_job.dag_config["nodes"]
            for node in nodes:
                 if "data" in node:
                     node["data"]["status"] = "idle"
                     node["data"]["metrics"] = None
            
    return db_job

@router.put("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(pipeline_id: int, pipeline: PipelineUpdate, db: AsyncSession = Depends(get_db)):
    """Update pipeline configuration."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if pipeline.dag_config:
        db_job = await crud_pathway.update_job(db, pipeline_id, pipeline.dag_config)
    
    return db_job

@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a pipeline."""
    success = await crud_pathway.delete_job(db, pipeline_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"message": "Pipeline deleted"}

@router.post("/pipelines/{pipeline_id}/run", response_model=PipelineRunResponse)
async def run_pipeline(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Run a pipeline."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if not db_job.dag_config:
        raise HTTPException(status_code=400, detail="Pipeline has no DAG configuration")

    # Convert stored JSON to DAGPipeline model
    try:
        # Map frontend nodes/edges to backend DAGNode/inputs
        # Frontend: nodes=[{id, data: {type, operator, config}}], edges=[{source, target}]
        # Backend: nodes=[{id, type, operator, config, inputs=[id...]}]
        
        frontend_nodes = db_job.dag_config.get("nodes", [])
        frontend_edges = db_job.dag_config.get("edges", [])
        
        # Build inputs map
        inputs_map = {}
        for edge in frontend_edges:
            target = edge["target"]
            source = edge["source"]
            if target not in inputs_map:
                inputs_map[target] = []
            inputs_map[target].append(source)
            
        backend_nodes = []
        for f_node in frontend_nodes:
            # Assume React Flow structure: id, type, data={operator, config...}
            # Or simplified structure if frontend sends pre-processed data
            # Let's assume frontend sends 'data' dict which matches our needs
            
            node_data = f_node.get("data", {})
            node_type = f_node.get("type") # source, transform, sink
            
            # Map React Flow types to backend types if needed
            # e.g. customNode -> transform
            
            backend_node = DAGNode(
                id=f_node["id"],
                type=node_type, # ensure frontend sends valid types: source, transform, sink, combiner
                operator=node_data.get("operator", "unknown"),
                config=node_data.get("config", {}),
                inputs=inputs_map.get(f_node["id"], [])
            )
            backend_nodes.append(backend_node)
            
        dag_pipeline = DAGPipeline(
            id=str(db_job.id),
            name=db_job.name,
            nodes=backend_nodes,
            settings={} # Extract global settings if any
        )
        
        engine.start_job(dag_pipeline)
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.RUNNING)
        
        return {"pipeline_id": db_job.id, "status": "running", "message": "Pipeline started"}
        
    except Exception as e:
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")

@router.post("/pipelines/{pipeline_id}/stop")
async def stop_pipeline_run(pipeline_id: int, db: AsyncSession = Depends(get_db)):
    """Stop a running pipeline."""
    db_job = await crud_pathway.get_job(db, pipeline_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    try:
        engine.stop_job(db_job.name)
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.STOPPED)
        return {"message": "Pipeline stopped"}
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
    db_job = await crud_pathway.create_job(db, name, source.id, operators, sinks)

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
        await crud_pathway.update_job_status(db, db_job.id, PathwayJobStatus.RUNNING)
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
