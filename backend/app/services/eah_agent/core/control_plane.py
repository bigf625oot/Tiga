import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator

from app.core.config import settings
from app.core.i18n import _
from app.services.eah_agent.core.nlu import NluService, IntentResult
from app.services.openclaw.clients.agno import AgnoGatewayClient
from app.models.llm_model import LLMModel
from app.services.eah_agent.storage.session_history import SessionHistory
from sqlalchemy.ext.asyncio import AsyncSession

# Handlers
from app.services.eah_agent.handlers.quick_handler import QuickHandler
from app.services.eah_agent.handlers.plan_handler import PlanHandler
from app.services.eah_agent.handlers.team_handler import TeamHandler
from app.services.eah_agent.handlers.flow_handler import FlowHandler
from app.services.eah_agent.handlers.data_handler import DataHandler

logger = logging.getLogger("agno.control_plane")

class AgnoControlPlane:
    """
    Agno Intelligent Agent as the sole control plane.
    Refactored to dispatch to specialized handlers.
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        self.nlu = NluService(llm_model)
        
        # Initialize Handlers
        self.quick_handler = QuickHandler(llm_model)
        self.plan_handler = PlanHandler(llm_model)
        self.team_handler = TeamHandler(llm_model)
        self.flow_handler = FlowHandler(llm_model)
        self.data_handler = DataHandler(llm_model)
        
        # Initialize WS Client
        # Using settings or defaults
        gateway_url = settings.OPENCLAW_WS_URL or "ws://localhost:8000"
        api_key = getattr(settings, "OPENCLAW_AGNO_KEY", "test-key")
        api_secret = getattr(settings, "OPENCLAW_AGNO_SECRET", "test-secret")
        
        self.client = AgnoGatewayClient(
            gateway_url=gateway_url,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Register callbacks
        self.client.on_task_event = self._on_task_event

    async def start(self):
        """Starts the control plane (connects to gateway)."""
        await self.client.connect()

    async def stop(self):
        """Stops the control plane."""
        await self.client.close()

    async def process_stream(self, user_input: str, db: Optional[AsyncSession] = None, session_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        New main entry point supporting streaming.
        Dispatches to handlers based on NLU intent.
        """
        # 1. Intent Understanding
        try:
            result: IntentResult = await self.nlu.analyze(user_input)
            logger.info(f"Intent Analysis: {result}")
        except Exception as e:
            logger.error(f"NLU Analysis failed: {e}")
            yield {"type": "error", "content": _("I couldn't understand that.")}
            return

        # 2. Session Persistence (Save User Message)
        history = None
        if db and session_id:
            try:
                history = SessionHistory(db)
                # Check if session exists, if not create
                session = await history.get_session(session_id)
                if not session:
                    # In a real app, user_id should come from auth context
                    await history.create_session(user_id="guest", agent_id=None, title=user_input[:50])
                
                await history.add_message(session_id, "user", user_input)
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")

        # 3. Dispatch & Stream
        full_response = ""
        
        try:
            handler_stream = None
            if result.intent == "chat" or result.confidence < 0.85:
                handler_stream = self.quick_handler.process(user_input, result, db=db, session_id=session_id)
            elif result.intent == "task":
                # Special case for now: _handle_task is blocking
                task_response = await self._handle_task(result.task_params)
                full_response = task_response
                yield {"type": "content", "content": task_response}
                # No stream to iterate
            elif result.intent == "team":
                 handler_stream = self.team_handler.process(user_input, result, db=db, session_id=session_id)
            elif result.intent == "workflow":
                 handler_stream = self.flow_handler.process(user_input, result, db=db, session_id=session_id)
            elif result.intent == "data_query" or result.intent == "kg_qa":
                 handler_stream = self.data_handler.process(user_input, result, db=db, session_id=session_id)
            else:
                handler_stream = self.quick_handler.process(user_input, result, db=db, session_id=session_id)
            
            if handler_stream:
                async for chunk in handler_stream:
                    if chunk.get("type") == "content":
                        content = chunk.get("content")
                        if isinstance(content, str):
                            full_response += content
                    yield chunk

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            yield {"type": "error", "content": _("An error occurred during processing.")}
            full_response += "\n[Error occurred]"
        
        # 4. Session Persistence (Save Assistant Message)
        if history and session_id and full_response:
            try:
                await history.add_message(session_id, "assistant", full_response)
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

    async def process_input(self, user_input: str) -> str:
        """
        Legacy entry point for backward compatibility.
        Consumes the stream and returns full string.
        """
        full_response = ""
        try:
            async for chunk in self.process_stream(user_input):
                if chunk.get("type") == "content":
                    full_response += str(chunk.get("content", ""))
                elif chunk.get("type") == "error":
                    full_response += f"\n[Error: {chunk.get('content')}]"
        except Exception as e:
            logger.error(f"Process input failed: {e}")
            return _("An error occurred.")
            
        return full_response

    async def _handle_task(self, params: Dict[str, Any]) -> str:
        if not self.client.is_connected:
            # Auto-connect if not connected
            await self.start()
            if not self.client.is_connected:
                 return _("Service temporarily unavailable (Gateway disconnected).")

        task_type = params.get("task_type")
        target = params.get("target")
        timeout = params.get("timeout", 60)
        retry_policy = params.get("retry_policy")

        try:
            # Blocking wait for task execution
            event = await self.client.execute_task(
                task_type=task_type,
                target=target,
                payload=params, # Pass all params as payload
                timeout=timeout,
                retry_policy=retry_policy
            )
            
            method = event.get("method")
            if method == "task_completed":
                return _("Task completed successfully: {}").format(event.get('params', {}).get('result'))
            elif method == "task_failed":
                error = event.get('params', {}).get('error', {})
                code = error.get('code')
                msg = error.get('message')
                # Auto-retry logic could be here if not handled by gateway, 
                # but requirement says "agno auto parses error_code, decides retry or human"
                return _("Task failed (Code {}): {}").format(code, msg)
            else:
                return _("Task finished with status: {}").format(method)

        except TimeoutError:
            return _("Task execution timed out.")
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return _("An error occurred while executing the task: {}").format(str(e))

    async def _on_task_event(self, event: Dict):
        """
        Callback for async events from Gateway.
        Updates session context or logs.
        """
        method = event.get("method")
        params = event.get("params", {})
        task_id = params.get("task_id")
        
        logger.info(f"Received event {method} for task {task_id}")
        # Here we could update a database or persistent session state
