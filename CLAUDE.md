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

# Run tests
uv run pytest tests/ -v
```

## Architecture

The refactored architecture follows a layered structure:

```
app/
├── api/                  # FastAPI layer
│   ├── main.py           # FastAPI app entry
│   ├── routes/
│   │   └── chat.py      # SSE chat endpoint
│   └── static/          # Frontend assets
├── agent/                # Agent core
│   ├── core.py          # agent_loop, TodoManager, SkillLoader, context compression
│   └── tools/          # Tool implementations
│       ├── registry.py # Tool registration system
│       ├── bash.py     # Shell command tool
│       ├── file.py     # File operations tool
│       ├── rag.py      # RAG knowledge search
│       └── db.py       # Database query tool
├── db/                  # Database layer
│   ├── models.py        # SQLModel models (Course, Event, Registration)
│   └── connection.py   # MySQL connection management
└── rag/                 # RAG layer
    ├── embedder.py     # DashScope embedding
    └── store.py        # Chroma vector store
```

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

## Skills System

Skills are `.md` files in `skills/` directory with YAML frontmatter:
```markdown
---
name: skill-name
description: What this skill does
---
(skill body content)
```

Loaded via the `load_skill` tool, with metadata injected into system prompt and body delivered on demand.