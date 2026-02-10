import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Import all models to ensure they are registered with Base.metadata
from app.models.agent import Agent
from app.models.user_script import UserScript
from app.models.tool import Tool
from app.models.user_tool import UserTool
from app.models.user import User
from app.models.mcp import MCPServer
from app.models.skill import Skill
from app.models.service_category import ServiceCategory
from app.models.graph_export import GraphExportConfig
from app.models.data_source import DataSource
from app.models.recording import Recording
from app.models.chat import ChatSession, ChatMessage
from app.models.llm_model import LLMModel
from app.models.knowledge import KnowledgeDocument, KnowledgeChat
from app.models.workflow import Workflow
from app.models.indicator import Indicator
from app.models.task_mode import Task, TaskLog, TaskQA, TaskVersion

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db) -> TestClient:
    """
    Create a TestClient that uses the test database.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
