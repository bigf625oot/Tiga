import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user_id, get_db
from app.models.user_tool import UserTool
from app.models.user import User
from app.models.tool import Tool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
import uuid
from datetime import datetime, timedelta, timezone

# Mock Auth
async def override_get_current_user_id():
    return "test_user_id"

@pytest.fixture
def mock_auth():
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    yield
    app.dependency_overrides.pop(get_current_user_id, None)

@pytest.fixture
async def async_client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)

@pytest.mark.asyncio
async def test_invoke_tool_permission(db: AsyncSession, mock_auth, async_client):
    # Setup
    user_id = "test_user_id"
    tool_id = str(uuid.uuid4())
    
    # Clean up potentially existing data (if session is reused/dirty)
    # But usually fixture rollback handles it. 
    # Just in case, we can try to use unique IDs if we suspect persistence.
    # But let's trust rollback for now, just flush instead of commit.
    
    # 1. Create User & Tool
    user = User(id=user_id, username="test")
    tool = Tool(id=tool_id, name="test_tool")
    db.add(user)
    db.add(tool)
    await db.flush()

    # 2. Create UserTool entry
    user_tool = UserTool(
        user_id=user_id,
        tool_id=tool_id,
        granted_by="admin"
    )
    db.add(user_tool)
    await db.flush()
    
    # 3. Test Success
    response = await async_client.post(f"/api/v1/tools/{tool_id}/invoke")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_invoke_tool_forbidden(db: AsyncSession, mock_auth, async_client):
    tool_id = str(uuid.uuid4())
    # No UserTool entry
    
    response = await async_client.post(f"/api/v1/tools/{tool_id}/invoke")
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_invoke_tool_expired(db: AsyncSession, mock_auth, async_client):
    user_id = "test_user_id"
    tool_id = str(uuid.uuid4())
    
    # Need to create user/tool again because rollback happened (hopefully)
    # If not rolled back, user might exist.
    # Check if user exists
    existing_user = await db.get(User, user_id)
    if not existing_user:
        user = User(id=user_id, username="test_expired")
        db.add(user)
    
    tool = Tool(id=tool_id, name="expired_tool")
    db.add(tool)
    await db.flush()

    # Expired entry
    user_tool = UserTool(
        user_id=user_id,
        tool_id=tool_id,
        granted_by="admin",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.add(user_tool)
    await db.flush()
    
    response = await async_client.post(f"/api/v1/tools/{tool_id}/invoke")
    
    assert response.status_code == 403
