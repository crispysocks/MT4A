import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

class SessionManager:
    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, list] = {}
        self._metadata: dict[str, dict] = {}
        self._load_all_metadata()

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        self._metadata[session_id] = {
            "id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[tuple[list, Optional[str]]]:
        if session_id in self._sessions:
            return self._sessions[session_id], None
        
        path = self.persist_dir / f"{session_id}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            messages = data.get("messages", [])
            system_prompt = None
            if messages and messages[0].get("role") == "system":
                system_prompt = messages[0].get("content")
                messages = messages[1:]
            self._sessions[session_id] = messages
            self._metadata[session_id] = {
                "id": session_id,
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "role": data.get("role"),
            }
            return messages, system_prompt
        
        return None, None

    def get_messages(self, session_id: str) -> Optional[list]:
        result = self.get_session(session_id)
        if result is None:
            return None
        return result[0]

    def save_session(self, session_id: str, system_prompt: Optional[str] = None) -> None:
        if session_id not in self._sessions:
            return
        
        messages = self._sessions[session_id]
        meta = self._metadata.get(session_id, {})
        
        all_messages = [{"role": "system", "content": system_prompt or ""}] + messages
        data = {
            "id": session_id,
            "model": "qwen3.6-plus",
            "messages": all_messages,
            "created_at": meta.get("created_at"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        path = self.persist_dir / f"{session_id}.json"
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"Failed to save session {session_id}: {e}")

    def list_sessions(self) -> list[dict]:
        return [
            {
                "id": sid,
                "created_at": meta.get("created_at"),
                "updated_at": meta.get("updated_at"),
                "message_count": len(self._sessions.get(sid, [])),
            }
            for sid, meta in sorted(
                self._metadata.items(),
                key=lambda x: x[1].get("updated_at") or "",
                reverse=True,
            )
        ]

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._metadata.pop(session_id, None)
        path = self.persist_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()

    def _load_all_metadata(self) -> None:
        for path in self.persist_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session_id = data.get("id", path.stem)
                self._metadata[session_id] = {
                    "id": session_id,
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                }
            except Exception:
                pass
