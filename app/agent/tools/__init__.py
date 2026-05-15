from .registry import registry, tool, ToolRegistry
from .bash import run_bash
from .file import run_read, run_write, run_edit
from .rag import knowledge_search
from .db import db_query

registry.register(
    "bash",
    run_bash,
    {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    "Run a shell command."
)
registry.register(
    "read_file",
    run_read,
    {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]},
    "Read file contents."
)
registry.register(
    "write_file",
    run_write,
    {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    "Write content to file."
)
registry.register(
    "edit_file",
    run_edit,
    {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]},
    "Replace exact text in file."
)
registry.register(
    "knowledge_search",
    knowledge_search,
    {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]},
    "Search knowledge base for relevant information."
)
registry.register(
    "db_query",
    db_query,
    {"type": "object", "properties": {"operation": {"type": "string"}, "table": {"type": "string"}, "conditions": {"type": "string"}, "data": {"type": "object"}}, "required": ["operation", "table"]},
    "Query or modify database (courses, events, registrations)."
)

__all__ = ["registry", "tool", "ToolRegistry"]