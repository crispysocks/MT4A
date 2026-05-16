import tempfile
from pathlib import Path
from app.agent.soul import SoulManager
from app.agent.tools.registry import registry

SAMPLE_SOUL = """---
name: Test Agent
role: test
---

You are a test agent. Help users with testing.
"""

MOCK_TOOLS = {
    "tool_a": (lambda: None, {}, "Mock tool A"),
    "tool_b": (lambda: None, {}, "Mock tool B"),
}


def _create_tool_config(base_dir: Path):
    """Create test tool_config.yaml"""
    config = base_dir / "tool_config.yaml"
    config.write_text("""
test:
  - tool_a
  - tool_b
test_a:
  - tool_a
  - tool_b
test_b:
  - tool_a
  - tool_b
""", encoding="utf-8")


def _register_mock_tools():
    registry.clear()
    for name, (handler, schema, desc) in MOCK_TOOLS.items():
        registry.register(name, handler, schema, desc)


def test_load_and_parse_soul(tmp_path):
    soul_dir = tmp_path / "souls" / "test"
    soul_dir.mkdir(parents=True)
    (soul_dir / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")
    _create_tool_config(tmp_path / "souls")

    _register_mock_tools()
    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("test")

    assert mgr.is_active() is True
    assert mgr.current_role == "test"
    assert "test agent" in mgr.get_system_prompt().lower()
    assert mgr.get_tools() == ["tool_a", "tool_b"]


def test_unload_soul(tmp_path):
    soul_dir = tmp_path / "souls" / "test"
    soul_dir.mkdir(parents=True)
    (soul_dir / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")
    _create_tool_config(tmp_path / "souls")

    _register_mock_tools()
    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("test")
    assert mgr.is_active() is True

    mgr.unload()
    assert mgr.is_active() is False
    assert mgr.current_role is None


def test_load_nonexistent_soul(tmp_path):
    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("nonexistent")

    assert mgr.is_active() is False
    assert mgr.current_role is None


def test_singleton_reset(tmp_path):
    soul_dir = tmp_path / "souls"
    (soul_dir / "test_a").mkdir(parents=True)
    (soul_dir / "test_b").mkdir(parents=True)
    (soul_dir / "test_a" / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")
    (soul_dir / "test_b" / "SOUL.md").write_text(
        SAMPLE_SOUL.replace("Test Agent", "Test B Agent").replace("test", "test_b"), encoding="utf-8"
    )
    _create_tool_config(soul_dir)

    _register_mock_tools()
    mgr = SoulManager(str(soul_dir))
    mgr.load("test_a")
    assert mgr.current_role == "test_a"

    mgr.load("test_b")
    assert mgr.current_role == "test_b"
