import logging
import asyncio
from typing import AsyncGenerator, Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_plan import AgentTask, TaskStatus
from app.services.eah_agent.core.control_plane import AgnoControlPlane

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """
    Agent responsible for executing specific tasks assigned by the PlannerAgent.
    """
    def __init__(self, agent_manager, db: AsyncSession):
        self.agent_manager = agent_manager
        self.db = db
        
    async def execute_task(self, task: AgentTask, context: Optional[Dict] = None):
        """
        Execute a specific task.
        """
        logger.info(f"ExecutorAgent running task {task.id}: {task.name}")
        
        task.status = TaskStatus.RUNNING
        await self.db.commit()
        
        try:
            # Simulate execution delay
            await asyncio.sleep(2)
            
            # TODO: Real execution logic based on task.assigned_agent_role
            # For now, just mark as completed
            
            task.status = TaskStatus.COMPLETED
            task.result = f"Executed {task.name} successfully."
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await self.db.commit()
            raise e

class WorkflowExecutor:
    """
    Wraps AgnoControlPlane to provide an execution interface compatible with AgentWorkflow.
    """
    def __init__(self, mode: str, session_id: str, db: Optional[AsyncSession] = None):
        self.mode = mode
        self.session_id = session_id
        self.db = db
        self.control_plane = AgnoControlPlane()

    async def execute(self, message: str, agent_id: str = None, history: List[Dict] = None, **kwargs) -> Any:
        """
        Execute workflow synchronously.
        """
        full_response = ""
        try:
            # We ignore 'history' as AgnoControlPlane loads it from DB if db/session_id provided.
            # We pass db and session_id to process_stream.
            async for chunk in self.control_plane.process_stream(message, db=self.db, session_id=self.session_id):
                if chunk.get("type") == "content":
                    content = chunk.get("content")
                    if isinstance(content, str):
                        full_response += content
                elif chunk.get("type") == "error":
                    full_response += f"\n[Error: {chunk.get('content')}]"
            
            return full_response
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise e
        finally:
            await self.control_plane.stop()

    async def stream(self, message: str, agent_id: str = None, history: List[Dict] = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute workflow and stream results.
        """
        try:
            async for chunk in self.control_plane.process_stream(message, db=self.db, session_id=self.session_id):
                yield chunk
        except Exception as e:
            logger.error(f"Workflow stream failed: {e}")
            yield {"type": "error", "content": str(e)}
        finally:
             await self.control_plane.stop()

def get_executor(mode: str, session_id: str, db: Optional[AsyncSession] = None) -> WorkflowExecutor:
    return WorkflowExecutor(mode, session_id, db)
