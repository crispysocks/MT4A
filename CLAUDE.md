# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude AI agent toolkit (`mt4a` - "model toolkit for agents"). It provides a standalone coding agent with tool use, task tracking, and conversation context management. The architecture has been refactored to a multi-layer structure with FastAPI, RAG, and database support.

## Running the Agent

```bash
# Install dependencies
uv sync

# Start the API server
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## Development Commands

```bash
# Install dependencies
uv sync

# Add new dependency (use uv, NOT pip)
uv add <package>

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/agent/test_core.py -v

# Run a specific test
uv run pytest tests/agent/test_core.py::test_name -v
```

## Architecture

The refactored architecture follows a layered structure:

```
app/
├── api/                  # FastAPI layer
│   ├── main.py           # FastAPI app entry
│   ├── routes/
│   │   ├── chat.py      # SSE chat endpoint (uses SessionManager)
│   │   └── sessions.py  # Session management endpoints
│   └── static/          # Frontend assets (stateless UI with sidebar)
├── agent/                # Agent core
│   ├── core.py          # agent_loop (streaming support), TodoManager, SkillLoader, context compression
│   ├── session.py       # SessionManager (memory + disk persistence)
│   └── tools/           # Tool implementations
│       ├── registry.py  # Tool registration system
│       ├── bash.py      # Shell command tool
│       ├── file.py      # File operations tool
│       ├── rag.py       # RAG knowledge search
│       └── db.py        # Database query tool
├── db/                  # Database layer
│   ├── models.py        # SQLModel models (Course, Event, Registration)
│   └── connection.py   # MySQL connection management
└── rag/                 # RAG layer
    ├── embedder.py     # DashScope embedding
    └── store.py        # Chroma vector store
```

**Session Management**: `SessionManager` in `app/agent/session.py` handles conversation lifecycle. Memory cache for active sessions, auto-persist to `.conversations/{id}.json`. Frontend is stateless — backend maintains all conversation state.

**Streaming**: `agent_loop(messages, stream_callback=...)` supports real-time token streaming via callback. The chat route uses `asyncio.Queue` + background thread to stream LLM output to SSE clients.

**API Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message, receive SSE stream |
| `/api/sessions` | GET | List all conversations |
| `/api/sessions/{id}` | GET | Load conversation history |

**Tool Registry**: Tools are registered via the `ToolRegistry` class and the `@tool` decorator. Available tools: `bash`, `read_file`, `write_file`, `edit_file`, `knowledge_search`, `db_query`, `TodoWrite`, `load_skill`, `compress`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_BASE_URL` | API endpoint (e.g., `https://dashscope.aliyuncs.com/apps/anthropic`) |
| `LLM_AUTH_TOKEN` | API key |
| `MODEL_ID` | Model identifier (e.g., `qwen3.6-plus`) |
| `DATABASE_HOST` | MySQL host (default: localhost) |
| `DATABASE_PORT` | MySQL port (default: 3306) |
| `DATABASE_USER` | MySQL user (default: root) |
| `DATABASE_PASSWORD` | MySQL password |
| `DATABASE_NAME` | MySQL database name (default: mt4a) |
| `DASHSCOPE_API_KEY` | API key for DashScope embedding |

**Frontend**: Static assets served from `app/api/static/` including the web UI at `/`.

**Skills System**: Skills are loaded dynamically at runtime by the `SkillLoader` class in `app/agent/core.py`. The skills/ directory does not exist on disk — skill content is resolved dynamically when the `load_skill` tool is invoked.