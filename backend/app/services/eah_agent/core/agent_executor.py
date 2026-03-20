import logging
import asyncio
from typing import AsyncGenerator, Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent_plan import AgentTask, TaskStatus
from app.services.eah_agent.core.agent_builder import AgentAssembler

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """
    负责执行 AgentTask 的核心类。
    使用 AgentAssembler 创建底层 Agent。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_task(self, session_id: str, task: AgentTask) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes a single task.
        """
        logger.info(f"Executing task: {task.name} ({task.id})")
        
        task.status = TaskStatus.RUNNING
        await self.db.commit()
        
        # 1. Resolve which agent to use based on assigned_agent_role or default
        # For phase 1, we just pick the first available active agent or a specific one if configured.
        agent_id = task.assigned_agent_id
        
        if not agent_id:
            # Fallback logic to find a suitable agent based on role
            from sqlalchemy import select
            from app.models.agent import Agent as AgentModel
            stmt = select(AgentModel).filter(AgentModel.is_active == True)
            if task.assigned_agent_role and task.assigned_agent_role != "general":
                # In a real app, you might map roles to categories or descriptions
                stmt = stmt.filter(AgentModel.category == task.assigned_agent_role)
            
            result = await self.db.execute(stmt)
            agent_record = result.scalars().first()
            if not agent_record:
                # Absolute fallback: just get any active agent
                result = await self.db.execute(select(AgentModel).filter(AgentModel.is_active == True))
                agent_record = result.scalars().first()
                
            if agent_record:
                agent_id = agent_record.id
            else:
                yield {"type": "error", "content": "No active agent found to execute the task."}
                task.status = TaskStatus.FAILED
                task.error_message = "No active agent found"
                await self.db.commit()
                return

        # 2. Instantiate the agent using AgentAssembler
        try:
            builder = AgentAssembler(self.db, agent_id)
            agno_agent = await builder.build(session_id=session_id)
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            yield {"type": "error", "content": f"Failed to initialize executor agent: {str(e)}"}
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await self.db.commit()
            return

        # 3. Prepare the execution prompt
        prompt = f"Please execute the following task:\n\nTask Name: {task.name}\nDescription: {task.description}\n\nProvide the final result when done."
        
        # 4. Stream execution
        try:
            # Note: In a full implementation, you would stream the response 
            # and format it similarly to QuickHandler._handle_chunk
            yield {"type": "status", "content": f"正在执行: {task.name}"}
            response = await agno_agent.arun(prompt)
            yield {"type": "content", "content": response.content}
            
            task.status = TaskStatus.COMPLETED
            task.result = response.content
            await self.db.commit()
        except Exception as e:
            logger.exception(f"Error executing task {task.id}")
            yield {"type": "error", "content": f"Execution failed: {str(e)}"}
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await self.db.commit()

class WorkflowExecutor:
    """
    Wraps AgnoControlPlane to provide an execution interface compatible with AgentWorkflow.
    """
    def __init__(self, mode: str, session_id: str, db: Optional[AsyncSession] = None):
        self.mode = mode
        self.session_id = session_id
        self.db = db
        from app.services.eah_agent.core.agent_control_plane import AgnoControlPlane
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
