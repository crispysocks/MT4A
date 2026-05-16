from __future__ import annotations
from typing import Callable, Any

class ToolDef:
    def __init__(self, name: str, handler: Callable, schema: dict, description: str):
        self.name = name
        self.handler = handler
        self.schema = schema
        self.description = description

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, name: str, handler: Callable, schema: dict, description: str):
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = ToolDef(name, handler, schema, description)

    def list(self, allowed_tools: list[str] = None) -> list[dict]:
        tools = self._tools.values()
        if allowed_tools is not None:
            tools = [t for t in tools if t.name in allowed_tools]
        return [
            {"name": t.name, "description": t.description, "input_schema": t.schema}
            for t in tools
        ]

    def clear(self):
        """Clear all registered tools for role switching"""
        self._tools.clear()

    def register_all(self, tool_defs: dict, enabled: list[str]):
        """Batch register tools after clearing existing ones"""
        self.clear()
        for name in enabled:
            if name in tool_defs:
                handler, schema, desc = tool_defs[name]
                self.register(name, handler, schema, desc)

    def get_handler(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler

# Global registry instance
registry = ToolRegistry()

def tool(name: str, description: str, schema: dict):
    """Decorator to register a tool function."""
    def decorator(fn: Callable) -> Callable:
        registry.register(name, fn, schema, description)
        return fn
    return decorator