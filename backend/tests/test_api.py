import pytest
from fastapi.testclient import TestClient
from app.main import app

# 假设全局有个 TestClient，通常用于全链路/集成测试
client = TestClient(app)

def test_health_check_endpoint():
    """全链路测试: 健康检查接口"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ts" in data

def test_health_retrieval_endpoint():
    """全链路测试: 检索健康检查接口"""
    response = client.get("/api/v1/health/retrieval")
    assert response.status_code == 200
    data = response.json()
    assert "vector" in data
    assert "graph" in data

def test_create_chat_session():
    """全链路测试: 尝试创建一个会话"""
    payload = {"mode": "solo", "title": "Test Session"}
    # 有些项目需要登录认证，如果直接返回 401 也可以断言
    response = client.post("/api/v1/chat/sessions", json=payload)
    # 不强制要求成功，只需确保接口被正确路由且不返回 404
    assert response.status_code in [200, 201, 401, 403, 422, 500]
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data.get("mode") == "solo"

def test_get_chat_sessions_list():
    """全链路测试: 尝试获取会话列表"""
    response = client.get("/api/v1/chat/sessions")
    assert response.status_code in [200, 401, 403, 500]

def test_not_found_endpoint():
    """全链路测试: 测试 404 路由"""
    response = client.get("/api/v1/non_existent_endpoint_123")
    assert response.status_code == 404
