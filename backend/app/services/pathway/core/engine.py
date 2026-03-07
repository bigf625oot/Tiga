import multiprocessing
import yaml
import time
from typing import Dict, Any, Optional, Union
import pathway as pw
from app.services.pathway.core.config import PathwayJobConfig
from app.services.pathway.core.models import DAGPipeline
from app.services.pathway.connectors.source import get_source
from app.services.pathway.connectors.sink import get_sink
from app.services.pathway.operators.cleaning import apply_operator
# Import udf and structuring modules to ensure registration of operators
import app.services.pathway.operators.udf 
import app.services.pathway.operators.structuring
import app.services.pathway.operators.ai_operators
import app.services.pathway.operators.logic
from app.services.pathway.core.parser import DAGParser
from app.services.pathway.core.exceptions import ConfigurationError, PathwayException
from app.core.logger import logger

def _run_dag(pipeline: DAGPipeline):
    """Run a DAG-based pipeline."""
    from app.core.logger import setup_logging
    setup_logging()
    
    try:
        parser = DAGParser()
        parser.parse(pipeline)
        
        monitoring_port = pipeline.settings.get("monitoring_port", 8081)
        pw.run(monitoring_dashboard_address=f"0.0.0.0:{monitoring_port}")
    except Exception as e:
        logger.error(f"Pathway DAG job {pipeline.name} failed: {e}", exc_info=True)

def _run_job(config: PathwayJobConfig):
    """The actual pathway execution logic running in a child process (Legacy/Linear)."""
    # Re-initialize logger in child process
    from app.core.logger import setup_logging
    setup_logging()
    
    try:
        # 1. Sources
        tables = []
        for source_conf in config.sources:
            source = get_source(source_conf.type)
            table = source.read(source_conf.config)
            tables.append(table)
        
        if not tables:
            raise ConfigurationError("No sources defined")
        
        # Combine sources (Union)
        # Assuming compatible schemas for now.
        current_table = tables[0]
        for t in tables[1:]:
            current_table += t

        # 2. Operators (Cleaning & Transformation)
        for op_conf in config.operators:
            # Unified operator application via factory/registry
            # apply_operator now uses OperatorRegistry internally
            current_table = apply_operator(current_table, op_conf.dict())

        # 3. Sinks
        for sink_conf in config.sinks:
            sink = get_sink(sink_conf.type)
            sink.write(current_table, sink_conf.config)

        # 4. Run
        monitoring_port = config.settings.get("monitoring_port", 8081)
        pw.run(monitoring_dashboard_address=f"0.0.0.0:{monitoring_port}")

    except Exception as e:
        logger.error(f"Pathway job {config.name} failed: {e}", exc_info=True)
        # We don't re-raise here because it would just crash the process silently
        # Logging is enough

class PathwayEngine:
    def __init__(self):
        self.active_jobs: Dict[str, multiprocessing.Process] = {}

    def start_job(self, job_config: Union[PathwayJobConfig, DAGPipeline]):
        """Start a pathway job in a separate process."""
        if job_config.name in self.active_jobs:
            if self.active_jobs[job_config.name].is_alive():
                raise PathwayException(f"Job {job_config.name} is already running")
            else:
                # Cleanup dead process
                del self.active_jobs[job_config.name]

        target_func = _run_dag if isinstance(job_config, DAGPipeline) else _run_job

        process = multiprocessing.Process(
            target=target_func,
            args=(job_config,),
            name=f"pathway-{job_config.name}",
            daemon=True
        )
        process.start()
        self.active_jobs[job_config.name] = process
        logger.info(f"Started Pathway job: {job_config.name} (PID: {process.pid})")

    def stop_job(self, job_name: str):
        """Stop a running pathway job."""
        if job_name in self.active_jobs:
            process = self.active_jobs[job_name]
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                logger.info(f"Stopped Pathway job: {job_name}")
            del self.active_jobs[job_name]
        else:
            raise PathwayException(f"Job {job_name} not found")

    def get_job_status(self, job_name: str) -> str:
        if job_name in self.active_jobs:
            process = self.active_jobs[job_name]
            return "running" if process.is_alive() else "stopped"
        return "not_found"

    def get_job_metrics(self, job_name: str) -> Dict[str, Any]:
        """
        Get runtime metrics for a running job.
        For now, this returns simulated data for visualization purposes.
        In a real scenario, this would query the Pathway monitoring endpoint.
        """
        import random
        
        status = self.get_job_status(job_name)
        if status != "running":
            return {}
            
        # Simulate metrics for demonstration
        # Returns a dict keyed by node_id (if we knew them) or just generic metrics
        # Since engine doesn't track node IDs directly, we'll return a generic structure
        # that the API layer can map to actual node IDs.
        
        # However, to map to specific nodes, the caller (API) needs to provide node IDs.
        # So we'll return a "generator" function or just raw data that the API can distribute.
        
        # Let's return a simple randomizer helper that the API can use
        return {
            "timestamp": time.time(),
            "status": "running",
            "global_eps": random.randint(50, 500),
            "global_latency": random.uniform(5.0, 50.0)
        }


# Singleton instance
engine = PathwayEngine()
