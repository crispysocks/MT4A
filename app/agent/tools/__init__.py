from .registry import registry, tool, ToolRegistry
from .bash import run_bash
from .file import run_read, run_write, run_edit
from .rag import knowledge_search
from .db import db_query

# ---------------------------------------------------------------------------
# Edit this list to control which tools are available to the LLM.
# Remove a name to disable, add a name (plus its definition below) to enable.
# ---------------------------------------------------------------------------
ENABLED_TOOLS = [
    # "bash",
    "read_file",
    # "write_file",
    # "edit_file",
    "knowledge_search",
    "db_query",
    "TodoWrite",
    "load_skill",
    "compress",
]

# ---------------------------------------------------------------------------
# Core tool handlers (depend on core.py objects, imported lazily)
# ---------------------------------------------------------------------------
def _todo_write_handler(items: list) -> str:
    from app.agent.core import TODO
    return TODO.update(items)


def _load_skill_handler(name: str) -> str:
    from app.agent.core import SKILLS
    return SKILLS.load(name)


def _compress_handler() -> str:
    return "Compressing..."

# ---------------------------------------------------------------------------
# Tool definitions: name -> (handler, schema, description)
# ---------------------------------------------------------------------------
_TOOL_DEFS: dict = {
    "bash": (
        run_bash,
        {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        "Run a shell command.",
    ),
    "read_file": (
        run_read,
        {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]},
        "Read file contents.",
    ),
    "write_file": (
        run_write,
        {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
        "Write content to file.",
    ),
    "edit_file": (
        run_edit,
        {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]},
        "Replace exact text in file.",
    ),
    "knowledge_search": (
        knowledge_search,
        {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]},
        "Search knowledge base for relevant information.",
    ),
    "db_query": (
        db_query,
        {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["select", "insert", "update", "delete"], "description": "Database operation to perform"},
                "table": {"type": "string", "enum": ["courses", "events", "registrations"], "description": "Table to query or modify"},
                "conditions": {"type": "string", "description": "JSON string of field=value filters, e.g. '{\"status\": \"active\"}'"},
                "data": {"type": "object", "description": "Field values for insert/update operations"},
            },
            "required": ["operation", "table"],
        },
        "Query or modify database. Use operation='select' with optional conditions (JSON string) to filter results. Use operation='insert' with data dict to add records. Use operation='update' with conditions and data to modify records. Use operation='delete' with conditions to remove records.",
    ),
    "TodoWrite": (
        _todo_write_handler,
        {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                            "activeForm": {"type": "string"},
                        },
                        "required": ["content", "status", "activeForm"],
                    },
                }
            },
            "required": ["items"],
        },
        "Update task tracking list.",
    ),
    "load_skill": (
        _load_skill_handler,
        {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        "Load specialized knowledge by name.",
    ),
    "compress": (
        _compress_handler,
        {"type": "object", "properties": {}},
        "Manually compress conversation context.",
    ),
}

# ---------------------------------------------------------------------------
# Register only enabled tools
# ---------------------------------------------------------------------------
for _name in ENABLED_TOOLS:
    if _name in _TOOL_DEFS:
        _handler, _schema, _desc = _TOOL_DEFS[_name]
        registry.register(_name, _handler, _schema, _desc)

__all__ = ["registry", "tool", "ToolRegistry", "ENABLED_TOOLS"]
