import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.storage.session_history import SessionHistory
from app.services.llm.resolver import resolve_fast_llm_model
from app.services.llm.factory import ModelFactory
from app.core.i18n import _

logger = logging.getLogger(__name__)

class TitleGenerator:
    """
    Service to automatically generate chat session titles based on conversation content.
    """
    
    @staticmethod
    async def generate_title(session_id: str, db: AsyncSession):
        """
        Generates a title for the session if it meets criteria (e.g., first turn, default title).
        This method is designed to be called as a background task.
        """
        try:
            history = SessionHistory(db)
            session = await history.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for title generation.")
                return

            # Get messages (limit to first few for context)
            messages = await history.get_messages(session_id, limit=5)
            if not messages or len(messages) < 2:
                # Need at least user message and assistant response to generate a good title
                return

            # Check if title needs update
            # Criteria: Title is default OR title matches truncated first message
            current_title = session.title
            first_msg_content = messages[0].content if messages else ""
            
            is_default = current_title in ["New Chat", "新对话", "新任务"]
            is_truncated = first_msg_content and current_title == first_msg_content[:50]
            is_truncated_short = first_msg_content and current_title == first_msg_content[:20] # Frontend truncation
            
            # If title seems manually set (different from default/truncated), skip
            # Unless we want to force update on first turn? 
            # Let's be conservative: only update if it looks like an auto-generated/default title.
            if not (is_default or is_truncated or is_truncated_short):
                return

            # Resolve LLM Model, explicitly use fast model to avoid slow reasoning models
            llm_model = await resolve_fast_llm_model(db)
            if not llm_model:
                logger.warning("No LLM model available for title generation.")
                return

            # Create Model Instance
            model = ModelFactory.create_model(llm_model)
            
            # Prepare Prompt
            conversation_text = ""
            for msg in messages[:3]: # Use first 3 messages for context
                role = "User" if msg.role == "user" else "Assistant"
                content = msg.content or ""
                # Truncate long content
                if len(content) > 500:
                    content = content[:500] + "..."
                conversation_text += f"{role}: {content}\n"

            prompt = f"""
            Summarize the following conversation into a concise title (max 15 characters).
            The title should capture the main topic or user intent.
            Output ONLY the title text, no quotes or explanations.
            Language: Chinese (Simplified).

            Conversation:
            {conversation_text}
            """

            # Call LLM
            response = model.response(messages=[{"role": "user", "content": prompt}])
            new_title = response.content.strip().replace('"', '').replace("'", "").replace("。", "")
            
            if len(new_title) > 20:
                new_title = new_title[:20]

            if new_title and new_title != current_title:
                logger.info(f"Updating session {session_id} title from '{current_title}' to '{new_title}'")
                await history.update_session_title(session_id, new_title)

        except Exception as e:
            logger.error(f"Error generating title for session {session_id}: {e}")
