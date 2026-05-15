from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    async def event_stream():
        yield f"data: {json.dumps({'type': 'status', 'content': 'Processing...'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'content': 'Agent response placeholder'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")