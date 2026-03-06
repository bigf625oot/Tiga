import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Set, Any
from app.crud.crud_task import task as crud_task
from app.crud.crud_task import sub_task as crud_sub_task
from app.core.task_stream import TaskStream
from app.schemas.task import SubTaskUpdate, TaskUpdate
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.stream = TaskStream()

    def _resolve_context_variables(self, context: Any, outputs: Dict[str, Any]) -> Any:
        """
        Recursively resolve {{task_name.output}} variables in context.
        outputs: {task_name: output_dict}
        """
        if isinstance(context, dict):
            return {k: self._resolve_context_variables(v, outputs) for k, v in context.items()}
        elif isinstance(context, list):
            return [self._resolve_context_variables(item, outputs) for item in context]
        elif isinstance(context, str):
            if "{{" in context and "}}" in context:
                try:
                    from jinja2 import Template
                    return Template(context).render(**outputs)
                except Exception as e:
                    logger.warning(f"Failed to render template {context}: {e}")
                    return context
            return context
        return context

    async def check_ready_tasks(self, db: AsyncSession, parent_task_id: str):
        """
        Check all subtasks for a given parent task.
        If a subtask is PENDING and all its dependencies are COMPLETED,
        mark it as QUEUED and push to Redis.
        """
        # Get all subtasks for this parent
        sub_tasks = await crud_sub_task.get_by_parent(db, parent_task_id)
        
        # Build a map of task name -> status/id for dependency resolution
        # Assuming dependencies are stored as list of names
        task_status_map: Dict[str, str] = {t.name: t.status for t in sub_tasks}
        
        queued_count = 0
        
        for t in sub_tasks:
            if t.status == 'PENDING':
                dependencies = t.dependencies or []
                is_ready = True
                
                # Check if all dependencies are COMPLETED
                for dep_name in dependencies:
                    dep_status = task_status_map.get(dep_name)
                    if dep_status != 'COMPLETED':
                        is_ready = False
                        break
                
                if is_ready:
                    # Resolve inputs using dependency outputs
                    dependency_outputs = {}
                    for dep_name in dependencies:
                        dep_task = next((dt for dt in sub_tasks if dt.name == dep_name), None)
                        if dep_task and dep_task.output_result:
                            dependency_outputs[dep_name] = dep_task.output_result
                            
                    resolved_input = self._resolve_context_variables(t.input_context, dependency_outputs)

                    # Update status in DB
                    # We optionally update input_context in DB if we want to persist resolved state
                    # But usually we keep template. Let's just pass resolved to worker.
                    await crud_sub_task.update(db, t, SubTaskUpdate(status='QUEUED'))
                    
                    # Push to Redis Queue
                    task_payload = {
                        "sub_task_id": t.id,
                        "parent_task_id": t.parent_id,
                        "task_type": t.task_type,
                        "input_context": resolved_input,
                        "name": t.name
                    }
                    await self.stream.push_task(task_payload)
                    logger.info(f"Task {t.name} ({t.id}) queued for execution.")
                    queued_count += 1
        
        # Check if all tasks are completed to update parent status
        if all(t.status == 'COMPLETED' for t in sub_tasks):
            # Update parent task status
            parent_task = await crud_task.get(db, parent_task_id)
            if parent_task and parent_task.status != 'COMPLETED':
                 await crud_task.update(db, parent_task, TaskUpdate(status='COMPLETED'))
                 logger.info(f"Parent task {parent_task_id} COMPLETED.")

        return queued_count

scheduler = Scheduler()
