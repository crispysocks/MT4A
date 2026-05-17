from .registry import registry, tool, ToolRegistry
from .bash import run_bash
from .file import run_read, run_write, run_edit
from .rag import knowledge_search
from .dbman import dbman

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
    "dbman": (
        dbman,
        {
            "type": "object",
            "properties": {
                "nl": {
                    "type": "string",
                    "description": "用自然语言描述你想查询或操作的数据，例如：'帮我查一下张三的最近跟进记录'",
                },
            },
            "required": ["nl"],
        },
        "数据库操作工具，支持自然语言查询和修改。可以说'查一下所有待审批的请假'或'把李四的投诉改为已解决'。",
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
# Register all defined tools (role filtering done via tool_config.yaml)
# ---------------------------------------------------------------------------
for _name, (_handler, _schema, _desc) in _TOOL_DEFS.items():
    registry.register(_name, _handler, _schema, _desc)

__all__ = ["registry", "tool", "ToolRegistry"]
