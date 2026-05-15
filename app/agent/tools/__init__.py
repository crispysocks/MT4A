from .registry import registry, tool, ToolRegistry
from .bash import run_bash
from .file import run_read, run_write, run_edit

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

__all__ = ["registry", "tool", "ToolRegistry"]