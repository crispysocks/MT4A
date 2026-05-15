from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_list_sessions_empty():
    """测试空会话列表"""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_session_not_found():
    """测试获取不存在的会话"""
    response = client.get("/api/sessions/nonexistent-id")
    assert response.status_code == 200
    assert "error" in response.json()
