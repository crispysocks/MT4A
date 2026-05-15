from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routes import chat, sessions

app = FastAPI(title="mt4a Agent API")

app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "mt4a Agent API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok"}