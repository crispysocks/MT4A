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

    def list(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "input_schema": t.schema}
            for t in self._tools.values()
        ]

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