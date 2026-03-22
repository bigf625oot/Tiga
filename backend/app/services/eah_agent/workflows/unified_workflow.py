import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func

from app.services.eah_agent.workflows.base import EAHWorkflow, EAHWorkflowState
from app.services.eah_agent.utils.session_kb import SessionKnowledgeManager
from app.services.eah_agent.core.agent_planner import PlannerAgent
from app.models.agent_plan import AgentPlan, AgentTask, TaskStatus
from app.core.context_compressor import ContextCompressor
from app.core.shared_state import StateManager, SharedState
from app.core.i18n import _

# Agno imports
from agno.agent import Agent
from agno.models.openai import OpenAIChat
try:
    from agno.tools.e2b import E2BTools
except ImportError:
    E2BTools = None

logger = logging.getLogger(__name__)

class UnifiedWorkflowState(EAHWorkflowState):
    plan_id: Optional[str] = None
    images: List[str] = []
    
class UnifiedAgentWorkflow(EAHWorkflow):
    """
    Unified Agent Workflow that integrates Planning, Execution, RAG, Multimodal, and Sandbox capabilities.
    Inherits from EAHWorkflow (Agno Workflow).
    """
    def __init__(self, session_id: str, db: AsyncSession, user_goal: str, images: Optional[List[str]] = None, **kwargs):
        super().__init__(session_id=session_id, **kwargs)
        self.db = db
        self.user_goal = user_goal
        self.input_images = images or []
        
        # Initialize Helpers
        self.kb_manager = SessionKnowledgeManager(session_id)
        self.compressor = ContextCompressor()
        self.state_manager = StateManager.get_instance()
        
        # Initialize State
        if not hasattr(self, "state") or self.state is None:
             self.state = UnifiedWorkflowState(session_id=session_id, images=self.input_images, context={"history": []})
        elif isinstance(self.state, EAHWorkflowState) and not isinstance(self.state, UnifiedWorkflowState):
             # Upgrade state if needed
             self.state = UnifiedWorkflowState(**self.state.dict(), images=self.input_images)
             if "history" not in self.state.context:
                 self.state.context["history"] = []

    async def _process_files(self, images: List[str]) -> List[Dict[str, Any]]:
        """
        Process images for the workflow.
        Returns a list of image content blocks for the LLM.
        """
        processed_images = []
        if not images:
            return processed_images
            
        logger.info(f"Processing {len(images)} images for workflow {self.session_id}")
        for img_path in images:
            # Assuming local paths are valid for the Agent or handled by Agno
            processed_images.append({"type": "image_url", "image_url": {"url": img_path}}) 
            
        return processed_images

    async def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError("Use run_stream() for this workflow.")

    async def run_stream(self, *args, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the unified workflow with streaming feedback.
        """
        try:
            # 1. Initialize RAG
            yield {"type": "status", "content": _("Initializing Knowledge Base...")}
            kb = self.kb_manager.get_knowledge_base()
            
            # 2. Process Multimodal Inputs
            processed_images = await self._process_files(self.input_images)
            
            # 3. State Management: Set Mode
            await self.state_manager.update_mode(self.session_id, "workflow")
            
            # 4. Planning Phase
            # We can optionally accept a model_id from kwargs if passed by AgentWorkflowEngine for retries
            fallback_model_id = kwargs.get("planner_model_id")
            planner = PlannerAgent(self.db, model_id=fallback_model_id)
            
            yield {"type": "status", "content": _("Planning tasks...")}
            
            # Assuming planner.create_plan returns plan_id
            plan_id = await planner.create_plan(self.session_id, self.user_goal)
            self.state.plan_id = plan_id
            self.state.current_step = "planning"
            
            # 5. Execution Loop
            plan = await self._get_plan(plan_id)
            if not plan:
                yield {"type": "error", "content": _("Failed to create execution plan.")}
                return
                
            # Fetch tasks for the plan to send to frontend
            stmt = select(AgentTask).filter(AgentTask.plan_id == plan_id).order_by(AgentTask.sequence.asc())
            result = await self.db.execute(stmt)
            tasks = result.scalars().all()
            
            plan_dict = {
                "id": str(plan.id),
                "reasoning": getattr(plan, "reasoning", ""),
                "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
                "tasks": [
                    {
                        "id": str(t.id),
                        "name": t.name,
                        "description": t.description,
                        "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                        "assigned_agent_role": t.assigned_agent_role
                    } for t in tasks
                ]
            }

            yield {"type": "plan", "content": plan_id, "plan": plan_dict}

            while True:
                # Fetch next pending task
                task = await self._get_next_task(plan_id)
                if not task:
                    break
                
                # Update State
                self.state.current_step = task.name
                yield {"type": "status", "content": f"正在执行步骤: {task.name}..."}
                
                # Context Compression
                history = self.state.context.get("history", [])
                if history:
                    compressed_history = await self.compressor.compress_context(history)
                    self.state.context["history"] = compressed_history
                
                # Execute Task
                try:
                    executor = await self._create_executor_agent(task, kb)
                    
                    # Update task status
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = func.now()
                    await self.db.commit()
                    
                    # Stream execution
                    response_content = ""
                    
                    task_prompt = (
                        f"Original User Goal: {self.user_goal}\n\n"
                        f"Your Current Task: {task.name}\n"
                        f"Task Details: {task.description}\n\n"
                        f"Please execute this task and respond in the same language as the Original User Goal."
                    )
                    
                    # Agno Agent.arun usage for async streaming:
                    stream_gen = executor.arun(
                        task_prompt, 
                        images=processed_images if self.input_images else None,
                        stream=True
                    )
                    
                    async for chunk in stream_gen:
                        # Aggregate content for history/result
                        if hasattr(chunk, "content") and chunk.content is not None:
                            response_content += str(chunk.content)
                            yield {"type": "content", "content": chunk.content}
                        elif isinstance(chunk, str):
                            response_content += chunk
                            yield {"type": "content", "content": chunk}
                        
                        # Handle tool calls dynamically from event
                        if hasattr(chunk, "event"):
                            event_name = chunk.event
                            # ToolCallStartedEvent or ToolCallCompletedEvent
                            if event_name in ("ToolCallStarted", "ToolCallCompleted") and hasattr(chunk, "tool") and chunk.tool:
                                tool = chunk.tool
                                tool_info = {
                                    "tool_name": tool.tool_name,
                                    "tool_args": tool.tool_args,
                                    "status": "started" if event_name == "ToolCallStarted" else "completed"
                                }
                                if event_name == "ToolCallCompleted" and hasattr(tool, "result"):
                                    tool_info["result"] = str(tool.result)
                                
                                yield {
                                    "type": "tool_call",
                                    "content": f"Tool '{tool.tool_name}' {tool_info['status']}.",
                                    "tool": tool_info
                                }

                    # Mark Task Complete
                    task.status = TaskStatus.COMPLETED
                    task.result = response_content
                    task.completed_at = func.now()
                    await self.db.commit()
                    
                    # Update History
                    if "history" not in self.state.context:
                        self.state.context["history"] = []
                    self.state.context["history"].append({"role": "user", "content": f"Task: {task.name}\n{task.description}"})
                    self.state.context["history"].append({"role": "assistant", "content": task.result})

                    # Persist Intermediate State
                    self.state.steps_completed.append(task.name)
                    await self.state_manager.save_state(
                        self.session_id, 
                        SharedState(
                            session_id=self.session_id, 
                            mode="workflow",
                            ui_state={"current_task": task.id, "progress": len(self.state.steps_completed)}
                        )
                    )

                except Exception as e:
                    logger.error(f"Task {task.name} failed: {e}")
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    await self.db.commit()
                    
                    if self._is_critical_task(task):
                        yield {"type": "error", "content": f"Critical task failed: {e}"}
                        self.state.error = str(e)
                        break
                    else:
                        yield {"type": "status", "content": f"Task failed but skipping: {e}"}
                        # Continue to next task

            # Finalize
            if not self.state.error:
                yield {"type": "status", "content": _("Workflow execution completed.")}
        
        except Exception as e:
            from app.services.eah_agent.core.schema import PlanValidationError
            if isinstance(e, PlanValidationError):
                raise e
            logger.exception(f"Workflow execution failed: {e}")
            yield {"type": "error", "content": f"Workflow execution failed: {e}"}
        finally:
            # Cleanup
            self.kb_manager.cleanup()

    async def _get_plan(self, plan_id: str) -> Optional[AgentPlan]:
        result = await self.db.execute(select(AgentPlan).filter(AgentPlan.id == plan_id))
        return result.scalars().first()

    async def _get_next_task(self, plan_id: str) -> Optional[AgentTask]:
        stmt = select(AgentTask).filter(
            AgentTask.plan_id == plan_id,
            AgentTask.status == TaskStatus.PENDING
        ).order_by(AgentTask.sequence.asc())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _create_executor_agent(self, task: AgentTask, kb: Any) -> Agent:
        """
        Creates an Agno Agent configured for the specific task.
        Enforces Sandbox (E2B) if code execution is likely needed.
        """
        from app.services.llm.resolver import resolve_chat_llm_model
        from app.services.llm.factory import ModelFactory
        
        tools = []
        # Check if task implies code execution
        is_code_task = any(kw in task.description.lower() for kw in ["code", "script", "python", "calculate", "plot", "analyze"])
        
        if is_code_task or "coder" in (task.assigned_agent_role or "").lower():
            if E2BTools:
                api_key = os.getenv("E2B_API_KEY")
                if api_key:
                    tools.append(E2BTools(api_key=api_key))
                else:
                    logger.warning("E2B_API_KEY not found. Skipping E2BTools.")
        
        # Resolve the best available chat model
        llm_model = await resolve_chat_llm_model(self.db)
        model_instance = ModelFactory.create_model(llm_model)

        # Create Agent
        return Agent(
            model=model_instance,
            tools=tools,
            knowledge=kb,
            description=f"You are an expert executor for the task: {task.name}",
            instructions=[
                task.description,
                "IMPORTANT: You must always reply in the same language as the user's original request. If the task or context is in Chinese, you MUST reply in Chinese."
            ],
            markdown=True
        )

    def _is_critical_task(self, task: AgentTask) -> bool:
        return True 
