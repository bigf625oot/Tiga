import asyncio
import json
import logging
import traceback
import socket
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.core.task_stream import TaskStream
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
        db_task = None
        try:
            # Update status to RUNNING
            db_task = await crud_sub_task.get(db, sub_task_id)
            if not db_task:
                logger.error(f"Task {sub_task_id} not found in DB")
                return

            # Use UTC now
            now = datetime.now(timezone.utc)
            # Make start_time offset-naive if DB expects it, or keep aware. 
            # SQLAlchemy usually handles it based on column type. 
            # Assuming it handles timezone-aware datetimes correctly or converts them.
            # If previous code used datetime.utcnow(), it was naive. 
            # datetime.now(timezone.utc) is aware.
            # Let's stick to what was there or improve. Previous was datetime.now(timezone.utc) in my read?
            # Wait, line 32 in read output: now = datetime.now(timezone.utc)
            
            await crud_sub_task.update(db, db_task, SubTaskUpdate(status='RUNNING', start_time=now))
            
            # TODO: Execute actual logic based on task_type
            # For now, simulate execution
            await asyncio.sleep(2) 
            result = {"status": "success", "message": "Task executed successfully (Simulated)"}
            
            # Update status to COMPLETED
            end_now = datetime.now(timezone.utc)
            # Re-fetch or use same object? 
            # If update returns new object, use that. crud_sub_task.update usually returns updated obj.
            db_task = await crud_sub_task.update(db, db_task, SubTaskUpdate(status='COMPLETED', output_result=result, end_time=end_now))
            
            # Trigger Scheduler for dependents
            # Scheduler now uses TaskStream, so it will push next tasks to Redis Stream
            scheduler = Scheduler()
            await scheduler.check_ready_tasks(db, parent_task_id)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            traceback.print_exc()
            if db_task:
                 await crud_sub_task.update(db, db_task, SubTaskUpdate(status='FAILED'))
            # Re-raise to prevent ACK in worker loop
            raise e

async def worker_loop():
    stream = TaskStream()
    await stream.ensure_infrastructure()
    
    # Generate unique consumer name
    consumer_name = f"worker-{socket.gethostname()}-{id(stream)}"
    logger.info(f"Worker {consumer_name} started. Listening for tasks on {stream.stream_key}...")
    
    while True:
        try:
            # Block for 5 seconds waiting for a task
            msg_id, task_data = await stream.pop_task(consumer_name, block=5000)
            
            if msg_id and task_data:
                logger.info(f"Received task {msg_id}")
                try:
                    await process_task(task_data)
                    await stream.ack_task(msg_id)
                    logger.info(f"Task {msg_id} acknowledged")
                except Exception as e:
                    logger.error(f"Task {msg_id} processing failed: {e}")
                    # Do NOT ack, so it remains in PEL for retry/claiming
                    
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    # Ensure proper python path if running as script
    import sys
    import os
    sys.path.append(os.getcwd())
    
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
