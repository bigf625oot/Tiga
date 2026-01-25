from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_indicator():
    response = client.post(
        "/api/v1/indicators/",
        json={"group": "Test Group", "name": "Test Indicator", "description": "Test Desc"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Indicator"
    assert "id" in data

def test_read_indicators():
    response = client.get("/api/v1/indicators/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_duplicate_indicator():
    # Ensure cleanup or unique name
    name = "Unique Indicator"
    client.post(
        "/api/v1/indicators/",
        json={"group": "Test Group", "name": name}
    )
    response = client.post(
        "/api/v1/indicators/",
        json={"group": "Test Group", "name": name}
    )
    assert response.status_code == 400

def test_update_indicator():
    # Create first
    res = client.post(
        "/api/v1/indicators/",
        json={"group": "Update Group", "name": "To Update"}
    )
    ind_id = res.json()["id"]
    
    response = client.patch(
        f"/api/v1/indicators/{ind_id}",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_indicator():
    # Create first
    res = client.post(
        "/api/v1/indicators/",
        json={"group": "Delete Group", "name": "To Delete"}
    )
    ind_id = res.json()["id"]
    
    response = client.delete(f"/api/v1/indicators/{ind_id}")
    assert response.status_code == 200
    assert response.json()["is_deleted"] == True
