import multiprocessing
import yaml
import time
from typing import Dict, Any, Optional
import pathway as pw
from app.services.pathway.core.config import PathwayJobConfig
from app.services.pathway.connectors.source import get_source
from app.services.pathway.connectors.sink import get_sink
from app.services.pathway.operators.cleaning import apply_operator
from app.services.pathway.operators.udf import apply_udf
from app.services.pathway.core.exceptions import ConfigurationError, PathwayException
from app.core.logger import logger

class PathwayEngine:
    def __init__(self):
        self.active_jobs: Dict[str, multiprocessing.Process] = {}

    def start_job(self, job_config: PathwayJobConfig):
        """Start a pathway job in a separate process."""
        if job_config.name in self.active_jobs:
            if self.active_jobs[job_config.name].is_alive():
                raise PathwayException(f"Job {job_config.name} is already running")
            else:
                # Cleanup dead process
                del self.active_jobs[job_config.name]

        process = multiprocessing.Process(
            target=self._run_job,
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

    def _run_job(self, config: PathwayJobConfig):
        """The actual pathway execution logic running in a child process."""
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
                if op_conf.type == "udf":
                    current_table = apply_udf(current_table, op_conf.config)
                else:
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


# Singleton instance
engine = PathwayEngine()
