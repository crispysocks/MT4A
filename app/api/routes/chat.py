import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agent.session import SessionManager
from app.agent.core import agent_loop

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
    
    # 加载或创建会话
    if conversation_id:
        messages = session_manager.get_session(conversation_id)
        if messages is None:
            conversation_id = session_manager.create_session()
            messages = session_manager.get_session(conversation_id)
    else:
        conversation_id = session_manager.create_session()
        messages = session_manager.get_session(conversation_id)
    
    # 追加用户消息
    messages.append({"role": "user", "content": message})
    
    # 使用 asyncio.Queue 实现真正的流式传输
    queue = asyncio.Queue()
    
    def stream_callback(text: str):
        asyncio.get_event_loop().call_soon_threadsafe(
            queue.put_nowait, {"type": "content", "content": text}
        )
    
    async def event_stream():
        import threading
        
        # 在后台线程运行 agent_loop
        def run_agent():
            try:
                agent_loop(messages, stream_callback=stream_callback)
            except Exception as e:
                queue.put_nowait({"type": "error", "content": str(e)})
            finally:
                queue.put_nowait({"type": "done"})
        
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
        
        # 发送 conversation_id
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation_id})}\n\n"
        
        # 从队列读取并发送
        while True:
            item = await queue.get()
            if item["type"] == "done":
                # 保存会话
                session_manager.save_session(conversation_id)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            elif item["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': item['content']})}\n\n"
                break
            else:
                yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
