import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag.context import context_loader
from app.models.skill import Skill
from unittest.mock import AsyncMock, MagicMock
# import pytest

# Client is now provided via fixture in conftest.py
# client = TestClient(app) 

def test_create_skill(client):
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
    # return data["id"] # Removed return to avoid pytest warning

def test_read_skills(client):
    # Ensure a skill exists (since tests might run in random order, create one first)
    client.post(
        "/api/v1/skills/",
        json={
            "name": "Test Skill 2",
            "description": "A test skill",
            "content": "You are a test skill.",
            "version": "1.0.0"
        }
    )
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
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        # sid = test_create_skill(client)
        # test_read_skills(client)
        test_context_loader()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
