import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import jwt
import os

from app.agent.session import SessionManager
from app.agent.core import agent_loop, soul_manager
from app.agent.auth import SECRET_KEY
from app.rag.router import KnowledgeRouter
import app.rag.router as rag_router

rag_router.knowledge_router = KnowledgeRouter(soul_manager)

router = APIRouter()

CONVERSATIONS_DIR = Path(".conversations")
CONVERSATIONS_DIR.mkdir(exist_ok=True)

session_manager = SessionManager(CONVERSATIONS_DIR)


@router.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    message = body.get("message", "")
    conversation_id = body.get("conversation_id")

    # Parse JWT token from Authorization header
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Load appropriate SOUL based on token
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            role = payload.get("role", "guest")
            if not soul_manager.is_active() or soul_manager.current_role != role:
                soul_manager.load(role)
        except jwt.PyJWTError:
            raise HTTPException(401, "Invalid token")
    else:
        if not soul_manager.is_active():
            soul_manager.load("guest")

    # Load or create session
    if conversation_id:
        messages = session_manager.get_session(conversation_id)
        if messages is None:
            conversation_id = session_manager.create_session()
            messages = session_manager.get_session(conversation_id)
    else:
        conversation_id = session_manager.create_session()
        messages = session_manager.get_session(conversation_id)

    messages.append({"role": "user", "content": message})

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def stream_callback(text: str):
        loop.call_soon_threadsafe(
            queue.put_nowait, {"type": "content", "content": text}
        )

    async def event_stream():
        import threading

        def run_agent():
            try:
                agent_loop(messages, stream_callback=stream_callback)
            except Exception as e:
                queue.put_nowait({"type": "error", "content": str(e)})
            finally:
                queue.put_nowait({"type": "done"})

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

        # Send role info first, then conversation_id
        yield f"data: {json.dumps({'type': 'role', 'role': soul_manager.current_role or 'guest'})}\n\n"
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation_id})}\n\n"

        while True:
            item = await queue.get()
            if item["type"] == "done":
                session_manager.save_session(conversation_id)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            elif item["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': item['content']})}\n\n"
                break
            else:
                yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
