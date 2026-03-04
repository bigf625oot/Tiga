import asyncio
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.agent.nlu import NluService, IntentResult
from app.services.openclaw.clients.agno import AgnoGatewayClient
from app.models.llm_model import LLMModel

logger = logging.getLogger("agno.control_plane")

class AgnoControlPlane:
    """
    Agno Intelligent Agent as the sole control plane.
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.nlu = NluService(llm_model)
        
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

    async def process_input(self, user_input: str) -> str:
        """
        Main entry point for user interaction.
        1. Understand Intent (NLU)
        2. Chat -> Generate Reply
        3. Task -> Execute on Gateway
        """
        
        # 1. Intent Understanding
        result: IntentResult = await self.nlu.analyze(user_input)
        logger.info(f"Intent Analysis: {result}")

        # 2. Chat Branch
        if result.intent == "chat" or result.confidence < 0.85:
            return await self._handle_chat(user_input)

        # 3. Task Branch
        if result.intent == "task":
            return await self._handle_task(result.task_params)

        return "I'm not sure what you mean."

    async def _handle_chat(self, user_input: str) -> str:
        # Simple chat response using the same model or a dedicated one
        try:
            response = self.nlu.model.response(user_input)
            return response.content
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return "I'm having trouble thinking right now."

    async def _handle_task(self, params: Dict[str, Any]) -> str:
        if not self.client.is_connected:
            # Auto-connect if not connected
            await self.start()
            if not self.client.is_connected:
                 return "Service temporarily unavailable (Gateway disconnected)."

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
                return f"Task completed successfully: {event.get('params', {}).get('result')}"
            elif method == "task_failed":
                error = event.get('params', {}).get('error', {})
                code = error.get('code')
                msg = error.get('message')
                # Auto-retry logic could be here if not handled by gateway, 
                # but requirement says "agno auto parses error_code, decides retry or human"
                return f"Task failed (Code {code}): {msg}"
            else:
                return f"Task finished with status: {method}"

        except TimeoutError:
            return "Task execution timed out."
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return f"An error occurred while executing the task: {str(e)}"

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
