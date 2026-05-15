from fastapi.testclient import TestClient
from app.api.main import app
import json

client = TestClient(app)

def test_sessions_endpoint():
    """测试会话列表端点"""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_session_lifecycle():
    """测试会话生命周期"""
    # 创建会话通过直接调用 SessionManager
    from app.agent.session import SessionManager
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        
        # 创建
        sid = sm.create_session()
        assert sid is not None
        
        # 获取
        messages = sm.get_session(sid)
        assert messages == []
        
        # 添加消息
        messages.append({"role": "user", "content": "hello"})
        
        # 保存
        sm.save_session(sid)
        
        # 重新加载
        sm2 = SessionManager(Path(tmpdir))
        loaded = sm2.get_session(sid)
        assert len(loaded) == 1
        assert loaded[0]["content"] == "hello"
        
        # 列表
        sessions = sm2.list_sessions()
        assert len(sessions) == 1
        
        # 删除
        sm2.delete_session(sid)
        assert sm2.get_session(sid) is None
