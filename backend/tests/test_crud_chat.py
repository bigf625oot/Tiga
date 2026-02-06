import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_chat import chat
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


@pytest.mark.asyncio
async def test_create_session(db: AsyncSession):
    session_in = ChatSessionCreate(title="Test Session", agent_id="test-agent")
    session = await chat.create(db, session_in)
    assert session.title == "Test Session"
    assert session.agent_id == "test-agent"
    assert session.id is not None


@pytest.mark.asyncio
async def test_get_session(db: AsyncSession):
    session_in = ChatSessionCreate(title="Get Session", agent_id="test-agent")
    created = await chat.create(db, session_in)
    fetched = await chat.get(db, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == created.title


@pytest.mark.asyncio
async def test_update_session(db: AsyncSession):
    session_in = ChatSessionCreate(title="Update Session", agent_id="test-agent")
    created = await chat.create(db, session_in)
    update_in = ChatSessionUpdate(title="Updated Title")
    updated = await chat.update(db, created, update_in)
    assert updated.title == "Updated Title"


@pytest.mark.asyncio
async def test_delete_session(db: AsyncSession):
    session_in = ChatSessionCreate(title="Delete Session", agent_id="test-agent")
    created = await chat.create(db, session_in)
    await chat.remove(db, created.id)
    fetched = await chat.get(db, created.id)
    assert fetched is None
