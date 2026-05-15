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
    {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["select", "insert", "update", "delete"],
                "description": "Database operation to perform"
            },
            "table": {
                "type": "string",
                "enum": ["courses", "events", "registrations"],
                "description": "Table to query or modify"
            },
            "conditions": {
                "type": "string",
                "description": "JSON string of field=value filters, e.g. '{\"status\": \"active\"}'"
            },
            "data": {
                "type": "object",
                "description": "Field values for insert/update operations"
            }
        },
        "required": ["operation", "table"]
    },
    "Query or modify database. Use operation='select' with optional conditions (JSON string) to filter results. Use operation='insert' with data dict to add records. Use operation='update' with conditions and data to modify records. Use operation='delete' with conditions to remove records."
)

__all__ = ["registry", "tool", "ToolRegistry"]