import pytest
from app.agent.tools.registry import ToolRegistry, tool

def test_registry_empty():
    r = ToolRegistry()
    assert r.list() == []

def test_registry_register():
    r = ToolRegistry()
    r.register("test_tool", lambda x: x, {"type": "object"}, "A test tool")
    tools = r.list()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"

def test_registry_decorator():
    from app.agent.tools.registry import registry as global_registry
    global_registry._tools.clear()

    @tool(name="decorated", description="Decorated tool", schema={"type": "object"})
    def my_func():
        return "result"

    assert "decorated" in [t["name"] for t in global_registry.list()]