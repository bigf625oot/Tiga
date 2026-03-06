import asyncio
import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional
from logging import Handler
from agno.workflow import Workflow
from app.workflow.context import AgentContext, WorkflowSessionState
from app.workflow.steps.rag_retrieve_step import rag_retrieve_step
from app.workflow.steps.agent_execute_step import agent_execute_step
from app.workflow.steps.persist_step import persist_step
from app.workflow.steps.plan_step import plan_step
from app.core.config import settings

logger = logging.getLogger(__name__)

class AsyncLogHandler(Handler):
    """Captures logs and puts them into an asyncio Queue."""
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.queue = queue
        self.loop = loop

    def emit(self, record):
        try:
            msg = self.format(record)
            # Create JSON event
            # Ensure we only capture relevant logs (info+)
            if record.levelno < logging.INFO:
                return
                
            event = json.dumps({
                "system": True,
                "status": "info" if record.levelno < logging.ERROR else "error",
                "output": msg
            })
            # Schedule putting into queue
            asyncio.run_coroutine_threadsafe(self.queue.put(event), self.loop)
        except Exception:
            self.handleError(record)

class AppWorkflow(Workflow):
    """
    Main application workflow.
    """
    
    def __init__(self, session_id: str, mode: str = "static", **kwargs):
        # Initialize parent if needed, Agno Workflow might accept name etc.
        # super().__init__(**kwargs) 
        # Note: If Workflow is a Pydantic model in Agno, we should use super().__init__ or model_validate.
        # Assuming standard class for now or Pydantic.
        self.session_id = session_id
        self.mode = mode # 'static' or 'dynamic'
        
        # Initialize State
        self.state = WorkflowSessionState(
            session_id=session_id,
            context=AgentContext(session_id=session_id, user_message="")
        )

    async def run(self, user_message: str, agent_id: str = None, history: list = None, **kwargs) -> Any:
        """
        Main entry point for execution (non-streaming).
        """
        # Collect stream output
        final_res = ""
        async for event in self.run_stream(user_message, agent_id, history, **kwargs):
             try:
                 data = json.loads(event)
                 if data.get("step") == "execute" and data.get("status") == "running" and "output" in data:
                     final_res += data["output"]
             except:
                 pass
        return final_res

    async def run_stream(self, user_message: str, agent_id: str = None, history: list = None, **kwargs) -> AsyncGenerator[str, None]:
        """
        Streaming entry point. Yields JSON strings for SSE.
        """
        # 1. Init Context
        self.state.context.user_message = user_message
        self.state.context.agent_id = agent_id
        self.state.context.history = history or []
        self.state.context.meta.update(kwargs)

        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        # Setup Logger to capture tool logs
        log_handler = AsyncLogHandler(queue, loop)
        # Attach to specific loggers
        # We capture logs from tool runner and general workflow
        target_loggers = [
            logging.getLogger("app.services.agent.tools.runner"),
            logging.getLogger("app.workflow"),
            logging.getLogger("app.services.agent.tools.duckduckgo") # If distinct
        ]
        
        for l in target_loggers:
            l.addHandler(log_handler)
            # Ensure level is set to capture info
            # l.setLevel(logging.INFO) 
            
        async def _run_workflow_logic():
            try:
                if self.mode == "static":
                    # Static Flow: Retrieve -> Execute -> Persist
                    
                    # Step 1: Retrieve
                    await queue.put(json.dumps({"step": "retrieve", "status": "running"}))
                    self.state.context = await rag_retrieve_step(self.state.context)
                    refs_count = len(self.state.context.retrieved_references)
                    await queue.put(json.dumps({"step": "retrieve", "status": "success", "output": f"Retrieved {refs_count} docs"}))
                    
                    # Step 2: Execute
                    await queue.put(json.dumps({"step": "execute", "status": "running"}))
                    self.state.context = await agent_execute_step(self.state.context)
                    
                    full_response = ""
                    reasoning_content = ""
                    
                    if self.state.context.output_stream:
                        async for chunk in self.state.context.output_stream:
                            # chunk is dict {'type': ..., 'content': ...}
                            if chunk["type"] == "content":
                                content = chunk["content"]
                                full_response += content
                                # Yield token
                                await queue.put(json.dumps({"step": "execute", "status": "running", "output": content}))
                            elif chunk["type"] == "reasoning":
                                rc = chunk["content"]
                                reasoning_content += rc
                                await queue.put(json.dumps({"step": "execute", "status": "running", "output": f"<think>{rc}</think>", "type": "reasoning"}))
                            elif chunk["type"] == "error":
                                await queue.put(json.dumps({"step": "execute", "status": "failed", "output": chunk["content"]}))
                    
                    self.state.context.final_response = full_response
                    self.state.context.reasoning_content = reasoning_content
                    await queue.put(json.dumps({"step": "execute", "status": "success"}))
                    
                    # Step 3: Persist
                    await queue.put(json.dumps({"step": "persist", "status": "running"}))
                    self.state.context = await persist_step(self.state.context)
                    await queue.put(json.dumps({"step": "persist", "status": "success"}))

                else:
                    # Dynamic Flow
                    await queue.put(json.dumps({"system": "workflow", "status": "info", "output": "Starting Dynamic Workflow"}))
                    steps_limit = 10
                    for i in range(steps_limit):
                         # Plan
                         await queue.put(json.dumps({"step": "plan", "status": "running"}))
                         self.state.context = await plan_step(self.state.context)
                         next_step = self.state.context.next_step
                         
                         current_plan = self.state.context.meta.get("current_plan")
                         
                         await queue.put(json.dumps({
                             "step": "plan", 
                             "status": "success", 
                             "output": f"Next step: {next_step}",
                             "plan": current_plan
                         }))
                         
                         if next_step == "finish":
                             break
                         
                         if next_step == "retrieve":
                             await queue.put(json.dumps({"step": "retrieve", "status": "running"}))
                             self.state.context = await rag_retrieve_step(self.state.context)
                             await queue.put(json.dumps({"step": "retrieve", "status": "success"}))
                             
                         elif next_step == "execute":
                             await queue.put(json.dumps({"step": "execute", "status": "running"}))
                             self.state.context = await agent_execute_step(self.state.context)
                             # Stream output
                             full_response = ""
                             if self.state.context.output_stream:
                                async for chunk in self.state.context.output_stream:
                                    if chunk["type"] == "content":
                                        c = chunk["content"]
                                        full_response += c
                                        await queue.put(json.dumps({"step": "execute", "status": "running", "output": c}))
                                    elif chunk["type"] == "reasoning":
                                        rc = chunk["content"]
                                        await queue.put(json.dumps({"step": "execute", "status": "running", "output": f"<think>{rc}</think>", "type": "reasoning"}))

                             self.state.context.final_response = full_response
                             await queue.put(json.dumps({"step": "execute", "status": "success"}))
                             
                         elif next_step == "persist":
                             await queue.put(json.dumps({"step": "persist", "status": "running"}))
                             self.state.context = await persist_step(self.state.context)
                             await queue.put(json.dumps({"step": "persist", "status": "success"}))
                    
            except Exception as e:
                logger.error(f"Workflow stream failed: {e}")
                await queue.put(json.dumps({"system": "workflow", "status": "failed", "output": str(e)}))
            finally:
                await queue.put("[DONE]")

        # Start workflow in background
        task = asyncio.create_task(_run_workflow_logic())
        
        try:
            while True:
                event = await queue.get()
                if event == "[DONE]":
                    break
                yield event
        finally:
            # Cleanup
            for l in target_loggers:
                l.removeHandler(log_handler)
            if not task.done():
                task.cancel()
