"""
Quick Handler:
Handles 'quick' intent: fast Q&A, chit-chat, simple queries.
是一种特殊的Agent，用于处理用户简单的查询和互动。本质就是reasoning = True/False，默认False。
核心功能：
1. 快速响应用户简单查询（如“你好”、“天气”等）。
2. 支持异步操作，确保在高并发场景下的响应速度。
3. 提供基础的错误处理机制，避免系统崩溃。
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, ToolConfig
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.i18n import _
from app.models.llm_model import LLMModel
from agno.agent import Agent

logger = logging.getLogger(__name__)

class QuickHandler(BaseHandler):
    """
    Handles 'chat' intent: fast Q&A, chit-chat, simple queries.
    Upgraded to use AgnoAgent for history and basic RAG support.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.agent: Optional[Agent] = None

    async def _ensure_agent_initialized(self, db: Optional[AsyncSession] = None):
        if not self.agent and self.llm_model:
            try:
                # Default tools for Quick Agent (e.g. Search, RAG)
                # We can load these from a default config or hardcode common ones
                tools = []
                # Example: Add search if available
                # tools.append(ToolConfig(name="duckduckgo_search", enabled=True))
                
                config = AgentConfig(
                    name="QuickAgent",
                    role="You are a helpful and concise assistant.",
                    instructions=["Answer directly.", "Be polite."],
                    tools=tools,
                    reasoning=False, # Quick mode usually disables heavy reasoning
                    model_params={"temperature": 0.7}
                )
                
                self.agent = await AgentFactory.create_agent(config, db=db, llm_model=self.llm_model)
            except Exception as e:
                logger.error(f"Failed to create agent for QuickHandler: {e}")
                self.agent = None

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        session_id = kwargs.get("session_id")
        
        await self._ensure_agent_initialized(db)
        
        if not self.agent:
            yield {"type": "error", "content": _("Agent not initialized for QuickHandler.")}
            return

        try:
            # Load History
            history_messages = []
            if db and session_id:
                history = SessionHistory(db)
                # Get last 10 messages for context
                msgs = await history.get_messages(session_id, limit=10)
                # Convert to Agno format (dicts or objects)
                # Exclude the current user message which is input_text (already saved?)
                # Actually input_text is passed here. SessionHistory.get_messages might include it if called after saving.
                # Agno expects: [{"role": "user", "content": "..."}, ...]
                for m in msgs:
                    # Skip if it's the current message (simple check by content or we assume it's history)
                    # For now, just include everything. Agno handles dedupe if we pass it as 'messages'
                    history_messages.append({"role": m.role, "content": m.content})

            # Stream response
            response_stream = self.agent.run(input_text, messages=history_messages, stream=True)
            
            for chunk in response_stream:
                content = getattr(chunk, 'content', None)
                if content:
                     yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                     yield {"type": "content", "content": chunk}
            
        except Exception as e:
            logger.error(f"QuickHandler processing failed: {e}")
            yield {"type": "error", "content": _("I'm having trouble thinking right now.")}
