import tempfile
from pathlib import Path
from app.agent.soul import SoulManager

SAMPLE_SOUL = """---
name: Test Agent
role: test
tools: [tool_a, tool_b]
---

You are a test agent. Help users with testing.
"""


def test_load_and_parse_soul(tmp_path):
    soul_dir = tmp_path / "souls" / "test"
    soul_dir.mkdir(parents=True)
    (soul_dir / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")

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


def test_singleton_reset(tmp_path):
    soul_dir = tmp_path / "souls"
    (soul_dir / "test_a").mkdir(parents=True)
    (soul_dir / "test_b").mkdir(parents=True)
    (soul_dir / "test_a" / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")
    (soul_dir / "test_b" / "SOUL.md").write_text(
        SAMPLE_SOUL.replace("test", "test_b").replace("test agent", "test b agent"), encoding="utf-8"
    )

    mgr = SoulManager(str(soul_dir))
    mgr.load("test_a")
    assert mgr.current_role == "test"

    mgr.load("test_b")
    assert mgr.current_role == "test_b"
