import logging
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage
from app.core.i18n import _

logger = logging.getLogger(__name__)

class SessionHistory:
    """
    Manages chat session history and persistence.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: str, agent_id: Optional[str] = None, title: Optional[str] = None) -> ChatSession:
        """
        Creates a new chat session.
        """
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agent_id=agent_id,
            title=title or _("New Chat"),
            mode="chat"
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Retrieves a chat session by ID.
        """
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def add_message(self, session_id: str, role: str, content: str, message_type: str = "text", meta_data: Optional[Dict] = None) -> ChatMessage:
        """
        Adds a message to the session history.
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            meta_data=meta_data
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Retrieves recent messages for a session.
        """
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())
        
        # If we want to limit, we might need to do it differently to get the LATEST N messages
        # but ordered ascendingly for context window.
        # Subquery approach:
        # subq = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(limit).subquery()
        # stmt = select(subq).order_by(subq.c.created_at.asc())
        
        # For simplicity now, just get all and slice in memory or assume limit is large enough
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        
        if len(messages) > limit:
            return messages[-limit:]
        return messages

    async def update_session_title(self, session_id: str, title: str):
        session = await self.get_session(session_id)
        if session:
            session.title = title
            await self.db.commit()
