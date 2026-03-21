import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
# Import agents and others to ensure tables are registered in Base.metadata
import app.models.agent
import app.models.chat
import app.models.system_config
from app.models.chat import ChatMessage, ChatSession
from app.models.system_config import SystemConfig
from app.schemas.system_config import ContextMemoryConfig
from app.services.eah_agent.handlers.team_handler import TeamHandler


@pytest.mark.asyncio
async def test_system_config_table_creates():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as conn:
        result = await conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='system_configs'")
        assert result.first() is not None


@pytest.mark.asyncio
async def test_team_handler_uses_system_history_limit():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as db:
        db.add(ChatSession(id="s1", mode="team"))
        await db.commit()

        for i in range(5):
            db.add(ChatMessage(session_id="s1", role="user", content=f"m{i}"))
        await db.commit()

        db.add(
            SystemConfig(
                key="context-memory",
                value={
                    "version": 1,
                    "context": {"history_limit": 2, "compression_threshold": 200000, "enable_graph_memory": False, "graph_hop_depth": 1},
                    "memory": {"enable_session_kb": True, "embedding_model_id": "text-embedding-3-small", "memory_extraction_interval": 10},
                },
                version=1,
            )
        )
        await db.commit()

        handler = TeamHandler(llm_model=None)
        messages, was_compressed = await handler._get_history_messages(db, "s1", current_query="")
        assert was_compressed is False
        assert len(messages) == 2
        assert messages[0]["content"] == "m3"
        assert messages[1]["content"] == "m4"

