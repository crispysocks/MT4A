from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from .routes import chat, sessions, notifications_router
from .routes.auth import router as auth_router

app = FastAPI(title="mt4a Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(notifications_router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/login")
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"error": "login page not found"}


@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "mt4a Agent API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    from app.db.connection import init_db_on_startup
    from app.rag.faq_index import build as build_faq_index
    init_db_on_startup()
    build_faq_index()
    print("[INFO] mt4a Agent API started")