import asyncio
import logging
from typing import List, Callable, Coroutine, Any, Dict, Optional

logger = logging.getLogger(__name__)

class SagaStep:
    """
    Represents a single step in a Saga transaction.
    - name: Step identifier
    - execute: The forward action
    - compensate: The rollback action if the saga fails later
    """
    def __init__(
        self, 
        name: str, 
        execute: Callable[..., Coroutine[Any, Any, Any]], 
        compensate: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    ):
        self.name = name
        self.execute = execute
        self.compensate = compensate


class SagaOrchestrator:
    """
    P10 Architecture: Saga Distributed Transaction Compensator
    
    A lightweight, asynchronous Saga orchestrator designed for resilient, 
    multi-step workflows like Knowledge Graph Construction (RAG).
    
    Usage:
    saga = SagaOrchestrator("Document_Indexing_123")
    saga.add_step(
        SagaStep(
            name="Upload_OSS", 
            execute=upload_to_oss, 
            compensate=delete_from_oss
        )
    )
    saga.add_step(
        SagaStep(
            name="Extract_Entities", 
            execute=extract_entities, 
            compensate=None # No side effects if failed
        )
    )
    saga.add_step(
        SagaStep(
            name="Insert_Neo4j", 
            execute=insert_to_neo4j, 
            compensate=delete_from_neo4j
        )
    )
    
    await saga.run(context)
    """
    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self.steps: List[SagaStep] = []
        self.executed_steps: List[SagaStep] = []
        self.context: Dict[str, Any] = {}

    def add_step(self, step: SagaStep):
        self.steps.append(step)

    async def run(self, initial_context: Dict[str, Any] = None) -> bool:
        if initial_context:
            self.context.update(initial_context)
            
        logger.info(f"[Saga {self.saga_id}] Started execution. Total steps: {len(self.steps)}")
        
        for step in self.steps:
            logger.info(f"[Saga {self.saga_id}] Executing step: {step.name}")
            try:
                # Pass context to the step, and step can modify context for downstream steps
                result = await step.execute(self.context)
                self.context[f"{step.name}_result"] = result
                self.executed_steps.append(step)
            except Exception as e:
                logger.error(f"[Saga {self.saga_id}] Step '{step.name}' failed: {e}. Initiating compensation.")
                await self._compensate()
                return False # Saga failed
                
        logger.info(f"[Saga {self.saga_id}] Successfully completed all steps.")
        return True # Saga succeeded

    async def _compensate(self):
        """
        Execute compensating actions in reverse order for all completed steps.
        """
        logger.warning(f"[Saga {self.saga_id}] Starting compensation process.")
        
        # Reverse the executed steps to rollback from the last successful step
        for step in reversed(self.executed_steps):
            if step.compensate:
                logger.info(f"[Saga {self.saga_id}] Compensating step: {step.name}")
                try:
                    await step.compensate(self.context)
                except Exception as e:
                    # Log but DO NOT crash the compensation loop
                    logger.critical(f"[Saga {self.saga_id}] Compensation failed for step '{step.name}': {e}", exc_info=True)
            else:
                logger.debug(f"[Saga {self.saga_id}] Step '{step.name}' has no compensation logic. Skipping.")
                
        logger.warning(f"[Saga {self.saga_id}] Compensation process finished.")
