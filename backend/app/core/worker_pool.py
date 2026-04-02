import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

class AsyncTaskWorkerPool:
    """
    P10 Architecture: Bounded Async Task Worker Pool
    
    Replaces the unbounded FastAPI BackgroundTasks for CPU/IO heavy tasks (like RAG indexing).
    - Prevents OOM by limiting concurrent heavy tasks.
    - Provides graceful shutdown capabilities.
    - Future-proofs the migration to Celery/Temporal by decoupling task submission from HTTP request context.
    """
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue()
        self.workers = []
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        logger.info(f"AsyncTaskWorkerPool started with {self.max_concurrent} workers.")

    async def stop(self):
        self._running = False
        for _ in range(self.max_concurrent):
            await self.queue.put(None) # Sentinel to stop workers
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        logger.info("AsyncTaskWorkerPool stopped.")

    async def _worker(self, worker_id: int):
        logger.debug(f"Worker {worker_id} started.")
        while self._running:
            try:
                task = await self.queue.get()
                if task is None: # Shutdown signal
                    self.queue.task_done()
                    break
                
                func, args, kwargs = task
                try:
                    logger.info(f"Worker {worker_id} executing task {func.__name__}")
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Worker {worker_id} task failed: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered an error: {e}", exc_info=True)

    async def submit_task(self, func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs):
        """
        Submit a background task to the bounded queue.
        """
        await self.queue.put((func, args, kwargs))
        logger.debug(f"Task {func.__name__} submitted. Queue size: {self.queue.qsize()}")

# Global instance
task_pool = AsyncTaskWorkerPool(max_concurrent=3)
