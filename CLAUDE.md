# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude AI agent toolkit (`mt4a` - maybe "model toolkit for agents"). It provides a standalone coding agent with tool use, task tracking, and conversation context management.

## Running the Agent

```bash
# Configure .env with LLM credentials (see .env.example)
# Run the agent REPL
python main.py
# or directly:
python agent/agent.py
```

## Development Commands

```bash
# Install dependencies
uv sync

# Add new dependency (use uv, NOT pip)
uv add <package>

# Run the agent REPL
python main.py
```

## Architecture

**`agent/agent.py`** is the core - a self-contained REPL agent with:

- **Agent Loop** (`agent_loop`): main event loop that alternates between LLM calls and tool execution
- **Base Tools**: `bash`, `read_file`, `write_file`, `edit_file` - file/project manipulation with path safety checks
- **Todo Manager**: in-memory task tracking with nag reminders after 3 rounds without updates
- **Skill Loader**: loads `.md` files from `skills/` directory with YAML frontmatter metadata
- **Context Compression**: micro-compact (clears old tool results) + auto-compact (summarizes conversation to file) when token threshold exceeded

**`main.py`** is a minimal entry point that just calls `agent_loop`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_BASE_URL` | API endpoint (e.g., `https://dashscope.aliyuncs.com/apps/anthropic`) |
| `LLM_AUTH_TOKEN` | API key |
| `MODEL_ID` | Model identifier (e.g., `qwen3.6-plus`) |

## Skills System

Skills are `.md` files in `skills/` directory with YAML frontmatter:
```markdown
---
name: skill-name
description: What this skill does
---
(skill body content)
```

Loaded via `load_skill` tool, with metadata injected into system prompt and body delivered on demand.