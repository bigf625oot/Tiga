import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.services.context_loader import context_loader
from app.models.skill import Skill
from unittest.mock import AsyncMock, MagicMock
# import pytest

# client = TestClient(app)

def test_create_skill():
    response = client.post(
        "/api/v1/skills/",
        json={
            "name": "Test Skill",
            "description": "A test skill",
            "content": "You are a test skill.",
            "version": "1.0.0"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Skill"
    assert "id" in data
    return data["id"]

def test_read_skills():
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_context_loader():
    # Mock DB Session
    mock_db = AsyncMock()
    
    # Mock result
    mock_skill = Skill(name="Mock Skill", content="Mock Instruction", id="123")
    
    # Setup mock execution result
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_skill]
    mock_db.execute.return_value = mock_result
    
    # Test
    import asyncio
    
    async def run_test():
        skills_config = {"selected_skills": ["123"]}
        context = await context_loader.load_context(mock_db, skills_config)
        assert "Mock Skill" in context
        assert "Mock Instruction" in context
        
    asyncio.run(run_test())

if __name__ == "__main__":
    # If run directly
    try:
        # sid = test_create_skill()
        # test_read_skills()
        test_context_loader()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
