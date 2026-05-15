import json
import tempfile
from pathlib import Path
from app.agent.session import SessionManager

def test_create_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        session_id = sm.create_session()
        assert session_id is not None
        assert len(session_id) > 0

def test_get_session_returns_empty_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        session_id = sm.create_session()
        messages = sm.get_session(session_id)
        assert messages == []

def test_save_and_load_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        session_id = sm.create_session()
        messages = sm.get_session(session_id)
        messages.append({"role": "user", "content": "hello"})
        sm.save_session(session_id)
        
        # 新建实例测试磁盘加载
        sm2 = SessionManager(Path(tmpdir))
        loaded = sm2.get_session(session_id)
        assert len(loaded) == 1
        assert loaded[0]["content"] == "hello"

def test_list_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        sm.create_session()
        sm.create_session()
        sessions = sm.list_sessions()
        assert len(sessions) == 2
        assert all("id" in s and "created_at" in s for s in sessions)

def test_delete_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionManager(Path(tmpdir))
        session_id = sm.create_session()
        sm.delete_session(session_id)
        assert sm.get_session(session_id) is None
