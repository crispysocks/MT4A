from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
from app.agent.core import agent_loop

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    async def event_stream():
        from app.agent.core import client, MODEL, SYSTEM
        from app.agent.tools import registry

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
                    text = event.delta.text if hasattr(event, 'delta') else str(event)
                    yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")