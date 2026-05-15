from pathlib import Path
from fastapi import APIRouter

from app.agent.session import SessionManager

router = APIRouter()

CONVERSATIONS_DIR = Path(".conversations")
session_manager = SessionManager(CONVERSATIONS_DIR)


@router.get("/sessions")
async def list_sessions():
    """获取所有会话列表"""
    return session_manager.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话的消息历史"""
    messages = session_manager.get_session(session_id)
    if messages is None:
        return {"error": "Session not found"}
    
    meta = session_manager._metadata.get(session_id, {})
    return {
        "id": session_id,
        "messages": messages,
        "created_at": meta.get("created_at"),
        "updated_at": meta.get("updated_at"),
    }
