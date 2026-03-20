import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.db.base import Base
from app.models.agent import Agent
from app.models.llm_model import LLMModel
from app.models.chat import ChatMessage
from app.crud.crud_chat import chat as crud_chat
from app.services.eah_agent.core.agent_control_plane import AgnoControlPlane, OrchestrationContext


@pytest.mark.asyncio
async def test_control_plane_init_history_persists_user_message():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as db:
        control_plane = AgnoControlPlane(llm_model=None)
        ctx = OrchestrationContext(user_input="hello", db=db, session_id="s1", kwargs={})
        await control_plane._init_history(ctx)

        rows = await db.execute(select(ChatMessage).where(ChatMessage.session_id == "s1"))
        messages = rows.scalars().all()
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "hello"

        session = await crud_chat.get(db, "s1")
        assert session is not None
        assert len(session.messages) == 1
