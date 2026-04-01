import logging
import asyncio
from app.services.platform.task_engine.adapters.base import BaseTaskAdapter
from app.services.platform.task_engine.models import TaskRunContext, TaskEvent
from app.services.ops.pipeline.core.engine import engine as pathway_engine
from app.services.ops.pipeline.core.models import DAGPipeline
from app.services.ops.pipeline.core.dag_builder import build_dag_pipeline_from_config
from app.services.ops.pipeline.core.runtime import allocate_log_file, allocate_monitoring_port
from app.db.session import AsyncSessionLocal
from app.crud import pathway as crud_pathway
from app.models.pathway_db import PathwayJobStatus

logger = logging.getLogger(__name__)

class PathwayAdapter(BaseTaskAdapter):
    """
    流水线作业适配器。
    将 PathwayEngine 的子进程作业包装为标准 TaskRun。
    """
    
    async def start_task(self, context: TaskRunContext) -> bool:
        pipeline_id = context.config.get("pipeline_id")
        if not pipeline_id:
            logger.error("PathwayAdapter requires pipeline_id in config")
            return False
        pipeline_id = int(pipeline_id)
            
        try:
            # 异步查询 DB 并构建 DAGPipeline (简化了原 routes 中的构建逻辑)
            async with AsyncSessionLocal() as db:
                db_job = await crud_pathway.get_job(db, pipeline_id)
                if not db_job or db_job.is_deleted or not db_job.dag_config:
                    raise ValueError("Invalid pipeline or missing DAG config")
                
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

                pid = pathway_engine.start_job(dag_pipeline)
                await crud_pathway.update_job_status(
                    db,
                    db_job.id,
                    PathwayJobStatus.RUNNING,
                    pid=pid,
                    monitoring_port=monitoring_port,
                )
                
            # 启动一个异步监听器定期拉取引擎指标并抛出 TaskEvent
            asyncio.create_task(self._monitor_pathway_job(context, pipeline_id, db_job.name))
            return True
            
        except Exception as e:
            logger.error(f"Failed to start pathway task: {e}")
            await self.emit_event(TaskEvent(
                task_id=context.task_id,
                status="FAILED",
                progress=0,
                message=f"流水线启动失败: {str(e)}",
                step="start_error"
            ))
            return False

    async def stop_task(self, task_id: str) -> bool:
        # 这里需要某种映射关系找到 job_name
        # 简化版：假定能通过外部存储找到对应 job_name 然后 stop_job
        logger.warning(f"Pathway stop for {task_id} not fully wired in adapter yet")
        return False

    async def get_status(self, task_id: str) -> TaskEvent:
        # 同上，需从 job_name 查 pathway_engine
        return TaskEvent(task_id=task_id, status="UNKNOWN")
        
    async def _monitor_pathway_job(self, context: TaskRunContext, pipeline_id: int, job_name: str):
        """定期拉取 PathwayEngine 状态，回写到统一任务中心"""
        while True:
            try:
                status = pathway_engine.get_job_status(job_name)
                if status == "running":
                    metrics = pathway_engine.get_job_metrics(job_name)
                    await self.emit_event(TaskEvent(
                        task_id=context.task_id,
                        status="RUNNING",
                        progress=50, # 持续运行作业可以视为永远50%，或按处理批次算
                        message=f"处理中 (EPS: {metrics.get('global_eps', 0)})",
                        step="streaming",
                        extend_data=metrics
                    ))
                    await asyncio.sleep(5)
                else:
                    # 停止或完成
                    async with AsyncSessionLocal() as db:
                        await crud_pathway.update_job_status(
                            db,
                            pipeline_id,
                            PathwayJobStatus.STOPPED if status in {"stopped", "not_found"} else PathwayJobStatus.FAILED,
                        )
                    await self.emit_event(TaskEvent(
                        task_id=context.task_id,
                        status="SUCCESS" if status in {"stopped", "not_found"} else "FAILED",
                        progress=100,
                        message=f"流水线已结束 ({status})",
                        step="completed"
                    ))
                    break
            except Exception as e:
                logger.error(f"Error monitoring pathway job {job_name}: {e}")
                break
