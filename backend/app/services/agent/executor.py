import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_plan import AgentTask, TaskStatus
from app.services.agent.manager import AgentManager

logger = logging.getLogger(__name__)

class ExecutorAgent:
    def __init__(self, agent_manager: AgentManager, db: AsyncSession):
        self.agent_manager = agent_manager
        self.db = db

    async def execute_task(self, task: AgentTask) -> str:
        """
        Executes a specific AgentTask.
        1. Loads the appropriate Agno Agent based on task.assigned_agent_role.
        2. Runs the agent with task.description.
        3. Updates the task status and result in DB.
        """
        logger.info(f"Executing task {task.id}: {task.name}")
        
        # 1. Update status to IN_PROGRESS
        task.status = TaskStatus.IN_PROGRESS
        await self.db.commit()

        try:
            # 2. Find suitable agent
            # For now, we hardcode some role -> agent_id mappings or use a default one.
            # In a real system, we'd query the 'agents' table for `role=task.assigned_agent_role`.
            
            # Use a default agent ID or the first available one for simplicity in Phase 1
            # We assume agent_manager has a way to get a default agent or search by role.
            # Since manager.py doesn't have `get_agent_by_role`, we'll just pick a default one if possible.
            # But `create_agno_agent` needs an ID.
            
            # HACK: For now, we just use a placeholder result to simulate execution
            # In Phase 2, we will integrate `manager.create_agno_agent` here.
            
            result = f"Executed task '{task.name}' successfully. (Simulated)"
            
            # If it's a coding task, we might want to call the Sandbox tool (Phase 2)
            if task.assigned_agent_role == "coder":
                result += "\n[Code execution result would appear here]"
            elif task.assigned_agent_role == "researcher":
                result += "\n[Search results would appear here]"

            # 3. Update task success
            task.result = result
            task.status = TaskStatus.COMPLETED
            await self.db.commit()
            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.error = str(e)
            task.status = TaskStatus.FAILED
            await self.db.commit()
            raise e
