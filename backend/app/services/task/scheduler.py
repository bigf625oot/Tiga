import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Set
from app.crud.crud_task import task as crud_task
from app.crud.crud_task import sub_task as crud_sub_task
from app.core.queue import TaskQueue
from app.schemas.task import SubTaskUpdate

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.queue = TaskQueue()

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
                    # Update status in DB
                    await crud_sub_task.update(db, t, SubTaskUpdate(status='QUEUED'))
                    
                    # Push to Redis Queue
                    # We push minimal info needed for worker
                    task_payload = {
                        "sub_task_id": t.id,
                        "parent_task_id": t.parent_id,
                        "task_type": t.task_type,
                        "input_context": t.input_context,
                        "name": t.name
                    }
                    await self.queue.push(task_payload)
                    logger.info(f"Task {t.name} ({t.id}) queued for execution.")
                    queued_count += 1
        
        # Check if all tasks are completed to update parent status
        if all(t.status == 'COMPLETED' for t in sub_tasks):
            # Update parent task status
            parent_task = await crud_task.get(db, parent_task_id)
            if parent_task and parent_task.status != 'COMPLETED':
                 # Use a schema or direct update? CRUD uses schema usually
                 # But here we can't easily import TaskUpdate due to circular imports?
                 # No, schemas are fine.
                 from app.schemas.task import TaskUpdate
                 await crud_task.update(db, parent_task, TaskUpdate(status='COMPLETED'))
                 logger.info(f"Parent task {parent_task_id} COMPLETED.")

        return queued_count

scheduler = Scheduler()
