import pytest

def test_create_mcp(client):
    response = client.post(
        "/api/v1/mcp/",
        json={
            "name": "Test MCP",
            "description": "A test mcp",
            "type": "stdio",
            "config": {"command": "echo", "args": ["hello"]},
            "category": "test",
            "author": "Tester"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test MCP"
    assert data["type"] == "stdio"
    assert "id" in data
    assert data["category"] == "test"
    assert data["author"] == "Tester"

def test_read_mcp(client):
    # Ensure creation
    client.post(
        "/api/v1/mcp/",
        json={
            "name": "Test MCP 2",
            "description": "A test mcp 2",
            "type": "sse",
            "config": {"url": "http://localhost:8000/sse"},
            "category": "test_cat"
        }
    )
    
    response = client.get("/api/v1/mcp/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check filters
    response_cat = client.get("/api/v1/mcp/?category=test_cat")
    assert response_cat.status_code == 200
    filtered_data = response_cat.json()
    assert len(filtered_data) >= 1
    assert filtered_data[0]["category"] == "test_cat"

def test_delete_mcp(client):
    # Create first
    res = client.post(
        "/api/v1/mcp/",
        json={
            "name": "To Delete",
            "type": "stdio",
            "config": {}
        }
    )
    mcp_id = res.json()["id"]
    
    # Delete
    del_res = client.delete(f"/api/v1/mcp/{mcp_id}")
    assert del_res.status_code == 200
    
    # Verify gone
    # Note: If the API implements GET by ID. If not, we check list.
    # Assuming GET /api/v1/mcp/{id} exists.
    # If not, we might get 404 or 405.
    
    # Let's check if GET /id exists by trying to call it.
    get_res = client.get(f"/api/v1/mcp/{mcp_id}")
    # Ideally 404
    assert get_res.status_code == 404
