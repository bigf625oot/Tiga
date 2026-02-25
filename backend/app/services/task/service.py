import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_task import task as crud_task
from app.crud.crud_task import sub_task as crud_sub_task
from app.schemas.task import TaskUpdate
from app.services.task.splitter import TaskSplitter
from app.services.task.scheduler import Scheduler

logger = logging.getLogger(__name__)

class TaskService:
    async def process_task_creation(self, task_id: str, prompt: str, db: AsyncSession):
        try:
            logger.info(f"Starting processing for task {task_id}")
            # Update status to SPLITTING
            task = await crud_task.get(db, task_id)
            if not task: 
                logger.error(f"Task {task_id} not found during processing")
                return

            await crud_task.update(db, task, TaskUpdate(status='SPLITTING'))
            
            # Call Splitter
            logger.info(f"Splitting task {task_id}...")
            splitter = TaskSplitter()
            sub_tasks_data = await splitter.split(prompt)
            logger.info(f"Split task {task_id} into {len(sub_tasks_data)} subtasks")
            
            # Save SubTasks
            for st_data in sub_tasks_data:
                await crud_sub_task.create(db, st_data, parent_id=task_id)
            
            # Update status to READY
            await crud_task.update(db, task, TaskUpdate(status='READY'))
            
            # Trigger Scheduler
            logger.info(f"Scheduling task {task_id}...")
            scheduler = Scheduler()
            queued_count = await scheduler.check_ready_tasks(db, task_id)
            logger.info(f"Queued {queued_count} initial subtasks for task {task_id}")
            
        except Exception as e:
            logger.error(f"Task creation processing failed: {e}", exc_info=True)
            try:
                # Re-fetch in case of session issues, though we are in the same session
                task = await crud_task.get(db, task_id)
                if task:
                    await crud_task.update(db, task, TaskUpdate(status='FAILED'))
            except Exception as e2:
                logger.error(f"Failed to update task status to FAILED: {e2}")

task_service = TaskService()
