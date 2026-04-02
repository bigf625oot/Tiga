import multiprocessing
import time
from typing import Dict, Any, Union
import pathway as pw
import logging
from app.services.ops.pipeline.core.config import PathwayJobConfig
from app.services.ops.pipeline.core.models import DAGPipeline
from app.services.ops.pipeline.connectors.source import get_source
from app.services.ops.pipeline.connectors.sink import get_sink
from app.services.ops.pipeline.operators.cleaning import apply_operator
# Import udf and structuring modules to ensure registration of operators
from app.services.ops.pipeline.core.parser import DAGParser
from app.services.ops.pipeline.core.exceptions import ConfigurationError, PathwayException
from app.core.logger import logger
from app.services.ops.pipeline.core.runtime import allocate_monitoring_port


def _setup_job_file_logging(settings: Union[Dict[str, Any], None]) -> None:
    log_file = (settings or {}).get("log_file")
    if not log_file:
        return
    try:
        root = logging.getLogger()
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(root.level or logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        root.addHandler(handler)
    except Exception:
        return

def _run_dag(pipeline: DAGPipeline):
    """Run a DAG-based pipeline."""
    from app.core.logger import setup_logging
    setup_logging()
    
    try:
        _setup_job_file_logging(pipeline.settings)
        logger.info(f"Pathway DAG job starting: {pipeline.name}")
        parser = DAGParser()
        parser.parse(pipeline)
        
        with_http_server = bool((pipeline.settings or {}).get("with_http_server", True))
        logger.info(f"Pathway DAG job running: {pipeline.name} (with_http_server={with_http_server})")
        pw.run(with_http_server=with_http_server)
    except Exception as e:
        logger.error(f"Pathway DAG job {pipeline.name} failed: {e}", exc_info=True)

def _run_job(config: PathwayJobConfig):
    """The actual pathway execution logic running in a child process (Legacy/Linear)."""
    # Re-initialize logger in child process
    from app.core.logger import setup_logging
    setup_logging()
    
    try:
        _setup_job_file_logging(config.settings)
        logger.info(f"Pathway job starting: {config.name}")
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
        with_http_server = bool((config.settings or {}).get("with_http_server", True))
        logger.info(f"Pathway job running: {config.name} (with_http_server={with_http_server})")
        pw.run(with_http_server=with_http_server)

    except Exception as e:
        logger.error(f"Pathway job {config.name} failed: {e}", exc_info=True)
        # We don't re-raise here because it would just crash the process silently
        # Logging is enough

class PathwayEngine:
    def __init__(self):
        self.active_jobs: Dict[str, multiprocessing.Process] = {}

    def start_job(self, job_config: Union[PathwayJobConfig, DAGPipeline]) -> int:
        """Start a pathway job in a separate process."""
        if job_config.name in self.active_jobs:
            if self.active_jobs[job_config.name].is_alive():
                raise PathwayException(f"Job {job_config.name} is already running")
            else:
                # Cleanup dead process
                del self.active_jobs[job_config.name]

        if isinstance(job_config, DAGPipeline):
            settings = dict(job_config.settings or {})
            settings.setdefault("monitoring_port", allocate_monitoring_port())
            job_config = job_config.model_copy(update={"settings": settings})
            target_func = _run_dag
        else:
            settings = dict(job_config.settings or {})
            settings.setdefault("monitoring_port", allocate_monitoring_port())
            job_config = job_config.model_copy(update={"settings": settings})
            target_func = _run_job

        process = multiprocessing.Process(
            target=target_func,
            args=(job_config,),
            name=f"pathway-{job_config.name}",
            daemon=False
        )
        process.start()
        self.active_jobs[job_config.name] = process
        logger.info(f"Started Pathway job: {job_config.name} (PID: {process.pid})")
        return int(process.pid or 0)

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

    def get_job_exitcode(self, job_name: str) -> int | None:
        if job_name in self.active_jobs:
            return self.active_jobs[job_name].exitcode
        return None

    def get_job_metrics(self, job_name: str) -> Dict[str, Any]:
        import random
        status = self.get_job_status(job_name)
        if status != "running":
            return {}
        
        # Simulate realistic metrics
        return {
            "timestamp": time.time(),
            "status": "running",
            "global_eps": random.randint(50, 500),
            "global_latency": round(random.uniform(5.0, 50.0), 2)
        }


# Singleton instance
engine = PathwayEngine()
