from typing import List, Dict, Any, Optional
import logging
from app.services.llm.factory import ModelFactory
from app.models.llm_model import LLMModel
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.db.session import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger(__name__)

class ContextCompressor:
    def __init__(self, model: Optional[LLMModel] = None):
        self.model = model
        self.agent = None
        if model:
             # Create a specialized summarizer agent
             self.agent = Agent(
                 model=ModelFactory.create_model(model),
                 instructions="You are a concise summarizer. Summarize the provided conversation history focusing on key facts, user preferences, and important decisions. Keep it brief.",
                 # show_tool_calls=False,
                 markdown=True
             )

    async def compress_context(self, history: List[Dict[str, Any]], max_tokens: int = 4000) -> List[Dict[str, Any]]:
        """
        Compress context by summarizing older messages if token limit is exceeded.
        """
        # 1. Check if compression is needed
        current_tokens = self._estimate_tokens(history)
        if current_tokens <= max_tokens:
            return history
            
        logger.info(f"Context size ({current_tokens}) exceeds limit ({max_tokens}). Triggering compression.")
        
        # 2. Split history into to-be-summarized and recent
        # Strategy: Keep the last 50% of the token window for raw messages
        recent_limit = max_tokens // 2
        recent_history = []
        recent_tokens = 0
        summary_history = []
        
        # Iterate backwards to keep most recent
        for msg in reversed(history):
            # Skip system messages in calculation if we handle them separately, 
            # but usually we want to keep the main system prompt. 
            # Here we assume history contains user/assistant messages.
            
            tokens = self._estimate_tokens([msg])
            if recent_tokens + tokens < recent_limit:
                recent_history.insert(0, msg)
                recent_tokens += tokens
            else:
                summary_history.insert(0, msg)
                
        if not summary_history:
            return recent_history

        # 3. Generate Summary
        # If no agent is initialized, try to load default model
        if not self.agent:
            await self._init_default_agent()
            
        if self.agent:
            try:
                # Prepare text for summarization
                text_to_summarize = ""
                for m in summary_history:
                    role = m.get("role", "unknown")
                    content = m.get("content", "")
                    text_to_summarize += f"{role}: {content}\n"
                
                if not text_to_summarize.strip():
                     return recent_history

                summary_prompt = f"Please summarize the following conversation history concisely:\n\n{text_to_summarize}"
                
                # Use arun to get response asynchronously
                # Note: Agno Agent.arun returns a RunResponse or similar
                response = await self.agent.arun(summary_prompt)
                
                # Handle different response types from Agno
                summary_text = ""
                if hasattr(response, "content"):
                    summary_text = response.content
                elif isinstance(response, str):
                    summary_text = response
                else:
                    summary_text = str(response)
                
                logger.info(f"Generated summary of length {len(summary_text)}")
                
                # 4. Create new history with summary
                # We inject the summary as a System message or a special User message
                # Usually best as a System message at the start, or appended to existing System prompt
                
                # Here we create a specific system message for the summary
                summary_msg = {
                    "role": "system", 
                    "content": f"Prior Conversation Summary: {summary_text}"
                }
                
                # Combine: [Summary] + [Recent History]
                new_history = [summary_msg] + recent_history
                return new_history
                
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                # Fallback: just return recent history (truncation)
                return recent_history 
        else:
             logger.warning("No agent available for summarization. Falling back to truncation.")
             return recent_history
        
    def _estimate_tokens(self, history):
        count = 0
        for msg in history:
            content = str(msg.get("content", ""))
            count += len(content) // 4 + 4 # Approx 4 chars per token + overhead
        return count

    async def _init_default_agent(self):
        """Initialize a default agent if none was provided"""
        try:
            async with AsyncSessionLocal() as db:
                # Find active model
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.api_key != None)
                    .order_by(LLMModel.updated_at.desc())
                )
                active_model = res.scalars().first()
                
                if active_model:
                     self.agent = Agent(
                         model=ModelFactory.create_model(active_model),
                         instructions="You are a concise summarizer.",
                         # show_tool_calls=False # Agno < 2.0 or diff syntax
                     )
        except Exception as e:
            logger.error(f"Failed to init default summarizer agent: {e}")
