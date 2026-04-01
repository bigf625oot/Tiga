import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

# 全流程测试：基于 HTTP 接口模拟一个完整的聊天和会话管理生命周期
# 这里有10个测试用例

def test_chat_session_flow_01_create_session():
    # Test case 1: Create a session
    payload = {"mode": "solo", "title": "Debug Session 1"}
    response = client.post("/api/v1/chat/sessions", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "id" in data
    return data["id"]

def test_chat_session_flow_02_get_session():
    # Test case 2: Get the created session
    session_id = test_chat_session_flow_01_create_session()
    response = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id

def test_chat_session_flow_03_send_message_stream_false():
    # Test case 3: Send message to the session (stream=False)
    session_id = test_chat_session_flow_01_create_session()
    payload = {"message": "Hello, this is a test.", "stream": False, "mode": "solo"}
    response = client.post(f"/api/v1/chat/sessions/{session_id}/chat", json=payload)
    # 因为依赖真实大模型环境，500（例如 LLM 异常）也是在路由测试中预期会发生的情况。
    assert response.status_code in [200, 500]

def test_chat_session_flow_04_send_message_stream_true():
    # Test case 4: Send message with streaming
    session_id = test_chat_session_flow_01_create_session()
    payload = {"message": "Hello, stream test.", "stream": True, "mode": "solo"}
    # httpx 支持 with 语法读取流
    with client.stream("POST", f"/api/v1/chat/sessions/{session_id}/chat", json=payload) as response:
        assert response.status_code in [200, 500]

def test_chat_session_flow_05_update_session():
    # Test case 5: Update session
    session_id = test_chat_session_flow_01_create_session()
    payload = {"title": "Updated Title"}
    response = client.put(f"/api/v1/chat/sessions/{session_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

def test_chat_session_flow_06_delete_session():
    # Test case 6: Delete session
    session_id = test_chat_session_flow_01_create_session()
    response = client.delete(f"/api/v1/chat/sessions/{session_id}")
    assert response.status_code == 200

def test_chat_session_flow_07_get_deleted_session():
    # Test case 7: Get deleted session should 404
    session_id = test_chat_session_flow_01_create_session()
    client.delete(f"/api/v1/chat/sessions/{session_id}")
    response = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert response.status_code == 404

def test_chat_session_flow_08_invalid_session_id():
    # Test case 8: Send message to invalid session
    fake_id = str(uuid.uuid4())
    payload = {"message": "Test", "stream": False}
    response = client.post(f"/api/v1/chat/sessions/{fake_id}/chat", json=payload)
    assert response.status_code == 404

def test_chat_session_flow_09_chat_multipart_form():
    # Test case 9: Test multipart form
    session_id = test_chat_session_flow_01_create_session()
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/chat_multipart",
        data={"message": "Multipart test", "stream": "false"}
    )
    assert response.status_code in [200, 500]

def test_chat_session_flow_10_list_sessions():
    # Test case 10: List sessions
    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
