from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


class CRUDChat:
    """
    聊天会话的 CRUD 操作
    """
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 20) -> List[ChatSession]:
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: ChatSessionCreate) -> ChatSession:
        db_obj = ChatSession(title=obj_in.title or "New Chat", agent_id=obj_in.agent_id, mode=obj_in.mode or "chat")
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Re-fetch to load options properly
        return await self.get(db, db_obj.id)

    async def get(self, db: AsyncSession, id: str) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession).options(selectinload(ChatSession.messages)).filter(ChatSession.id == id)
        )
        session = result.scalars().first()
        if session and session.messages:
            session.messages.sort(key=lambda m: m.created_at)
        return session

    async def update(self, db: AsyncSession, db_obj: ChatSession, obj_in: ChatSessionUpdate) -> ChatSession:
        if obj_in.title is not None:
            db_obj.title = obj_in.title
        if obj_in.agent_id is not None:
            db_obj.agent_id = obj_in.agent_id
        if obj_in.mode is not None:
            db_obj.mode = obj_in.mode
        if obj_in.workflow_state is not None:
            db_obj.workflow_state = obj_in.workflow_state
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: str) -> Optional[ChatSession]:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def create_message(
        self, 
        db: AsyncSession, 
        session_id: str, 
        role: str, 
        content: Optional[str] = None,
        meta_data: Optional[Dict] = None,
        reasoning_content: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tools: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
        message_type: str = "text",
        parent_id: Optional[int] = None,
    ) -> ChatMessage:
        """
        Create a new chat message.
        """
        # If this message is a user message and has a parent_id,
        # it means it's a regenerated branch. We should update is_active
        # of other siblings to 0, though a full branch management logic is better.
        # For now, we just insert with parent_id.
        
        # Calculate version if parent_id exists
        from sqlalchemy import func
        version = 1
        if parent_id:
            stmt = select(func.max(ChatMessage.version)).where(
                ChatMessage.parent_id == parent_id,
                ChatMessage.role == role
            )
            result = await db.execute(stmt)
            max_version = result.scalar()
            if max_version is not None:
                version = max_version + 1

        db_msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            meta_data=meta_data,
            tool_calls=tool_calls,
            tools=tools,
            tool_call_id=tool_call_id,
            reasoning_content=reasoning_content,
            message_type=message_type,
            parent_id=parent_id,
            version=version,
            is_active=1
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        return db_msg

    async def get_history(self, db: AsyncSession, session_id: str) -> List[ChatMessage]:
        result = await db.execute(
            select(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        )
        return result.scalars().all()

    async def delete_message(self, db: AsyncSession, session_id: str, message_id: int) -> bool:
        result = await db.execute(
            select(ChatMessage).filter(ChatMessage.session_id == session_id, ChatMessage.id == message_id)
        )
        msg = result.scalars().first()
        if msg:
            await db.delete(msg)
            await db.commit()
            return True
        return False

    async def update_message_meta(self, db: AsyncSession, session_id: str, meta: dict, message_id: Optional[str] = None):
        if message_id:
            result = await db.execute(select(ChatMessage).filter(ChatMessage.id == message_id))
            msg = result.scalars().first()
        else:
            result = await db.execute(
                select(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.created_at))
            )
            msg = result.scalars().first()
            
        if msg:
            base = msg.meta_data or {}
            for k, v in meta.items():
                base[k] = v
            msg.meta_data = base
            db.add(msg)
            await db.commit()


chat = CRUDChat()
