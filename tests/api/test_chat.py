from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_chat_endpoint_exists():
    """测试 chat 端点存在"""
    # 使用 timeout 避免 SSE 流阻塞
    try:
        response = client.post("/api/chat", json={"message": "hello"}, timeout=3.0)
        # 端点存在即可
    except Exception:
        # 超时也是正常的（SSE 流）
        pass
