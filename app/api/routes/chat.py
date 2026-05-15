import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

CONVERSATIONS_DIR = Path(".conversations")
CONVERSATIONS_DIR.mkdir(exist_ok=True)


@router.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    messages = body.get("messages", [])

    async def event_stream():
        from app.agent.core import client, MODEL, SYSTEM
        from app.agent.tools import registry

        conversation_id = str(uuid.uuid4())
        collected_content = []

        try:
            response = client.messages.create(
                model=MODEL,
                system=SYSTEM,
                messages=messages,
                tools=registry.list(),
                max_tokens=8000,
                stream=True
            )

            for event in response:
                if event.type == "content_block_delta":
                    try:
                        text = event.delta.text
                        collected_content.append(text)
                        yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"
                    except AttributeError:
                        pass

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Save conversation log after streaming completes
            assistant_message = "".join(collected_content)
            log = {
                "id": conversation_id,
                "model": MODEL,
                "messages": messages + [{"role": "assistant", "content": assistant_message}],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            log_path = CONVERSATIONS_DIR / f"{conversation_id}.json"
            log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False))

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")