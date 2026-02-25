import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.core.queue import TaskQueue
from app.crud.crud_task import sub_task as crud_sub_task
from app.schemas.task import SubTaskUpdate
from app.services.task.scheduler import Scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_task(task_data: dict):
    sub_task_id = task_data.get("sub_task_id")
    parent_task_id = task_data.get("parent_task_id")
    
    logger.info(f"Processing task {sub_task_id} ({task_data.get('name')})")
    
    async with AsyncSessionLocal() as db:
        try:
            # Update status to RUNNING
            db_task = await crud_sub_task.get(db, sub_task_id)
            if not db_task:
                logger.error(f"Task {sub_task_id} not found in DB")
                return

            # Use UTC now
            now = datetime.now(timezone.utc)
            await crud_sub_task.update(db, db_task, SubTaskUpdate(status='RUNNING', start_time=now))
            
            # TODO: Execute actual logic based on task_type
            # For now, simulate execution
            await asyncio.sleep(2) 
            result = {"status": "success", "message": "Task executed successfully (Simulated)"}
            
            # Update status to COMPLETED
            end_now = datetime.now(timezone.utc)
            await crud_sub_task.update(db, db_task, SubTaskUpdate(status='COMPLETED', output_result=result, end_time=end_now))
            
            # Trigger Scheduler for dependents
            scheduler = Scheduler()
            await scheduler.check_ready_tasks(db, parent_task_id)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            traceback.print_exc()
            # Re-fetch task to ensure we have attached object if needed, or use ID
            # But db_task should be attached to session if not closed
            if db_task:
                 await crud_sub_task.update(db, db_task, SubTaskUpdate(status='FAILED'))

async def worker_loop():
    queue = TaskQueue()
    logger.info("Worker started. Listening for tasks...")
    
    while True:
        try:
            task_data = await queue.pop(timeout=5)
            if task_data:
                await process_task(task_data)
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    # Ensure proper python path if running as script
    import sys
    import os
    sys.path.append(os.getcwd())
    
    asyncio.run(worker_loop())
