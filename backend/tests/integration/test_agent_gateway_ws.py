import pytest
import time
import hmac
import hashlib
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture
def client():
    return TestClient(app)

def generate_auth_headers(api_key, api_secret):
    nonce = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    payload = f"{api_key}{timestamp}{nonce}".encode("utf-8")
    signature = hmac.new(
        api_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return {
        "X-Agno-Key": api_key,
        "X-Agno-Signature": signature,
        "X-Agno-Timestamp": timestamp,
        "X-Agno-Nonce": nonce,
    }

def test_websocket_connection_success(client):
    headers = generate_auth_headers("test-key", "test-secret")
    with client.websocket_connect("/api/v1/agent", headers=headers, subprotocols=["oc.agent.v1"]) as websocket:
        # Send Ping
        websocket.send_json({
            "jsonrpc": "2.0",
            "method": "ping",
            "id": "1"
        })
        data = websocket.receive_json()
        assert data["result"] == "pong"

def test_websocket_connection_auth_fail(client):
    headers = generate_auth_headers("test-key", "wrong-secret")
    with pytest.raises(Exception): # WebSocketDisconnect or similar
        with client.websocket_connect("/api/v1/agent", headers=headers, subprotocols=["oc.agent.v1"]) as websocket:
            pass

def test_websocket_task_execution(client):
    headers = generate_auth_headers("test-key", "test-secret")
    with client.websocket_connect("/api/v1/agent", headers=headers, subprotocols=["oc.agent.v1"]) as websocket:
        # Send Execute
        websocket.send_json({
            "jsonrpc": "2.0",
            "method": "execute",
            "id": "2",
            "params": {
                "task_type": "crawler",
                "target": "http://example.com"
            }
        })
        
        # Expect Ack
        ack = websocket.receive_json()
        assert ack["result"]["status"] == "pending"
        task_id = ack["result"]["task_id"]
        
        # Expect Started
        started = websocket.receive_json()
        assert started["method"] == "task_started"
        assert started["params"]["task_id"] == task_id
        
        # Expect Completed/Failed (random in mock)
        result = websocket.receive_json()
        assert result["method"] in ["task_completed", "task_failed"]
        assert result["params"]["task_id"] == task_id
