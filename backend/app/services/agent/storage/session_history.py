import logging
import uuid
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

    async def ensure_session(self, session_id: str, *, user_id: str, agent_id: Optional[str] = None) -> ChatSession:
        session = await self.get_session(session_id)
        if session:
            dirty = False
            if user_id and not session.user_id:
                session.user_id = user_id
                dirty = True
            if agent_id is not None and session.agent_id != agent_id:
                session.agent_id = agent_id
                dirty = True
            if not session.mode:
                session.mode = "chat"
                dirty = True
            if dirty:
                await self.db.commit()
                await self.db.refresh(session)
            return session

        session = ChatSession(
            id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            title=_("New Chat"),
            mode="chat",
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

    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        message_type: str = "text", 
        meta_data: Optional[Dict] = None,
        reasoning_content: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None
    ) -> ChatMessage:
        """
        Adds a message to the session history with full Agno support.
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            meta_data=meta_data,
            reasoning_content=reasoning_content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Retrieves the most recent `limit` messages for a session, ordered chronologically.
        Why subquery: push LIMIT to the DB engine to avoid O(n) Python-side memory scan on long sessions.
        """
        from sqlalchemy import desc
        inner = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
            .subquery()
        )
        stmt = select(ChatMessage).from_statement(
            select(inner).order_by(inner.c.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_session_title(self, session_id: str, title: str):
        session = await self.get_session(session_id)
        if session:
            session.title = title
            await self.db.commit()
