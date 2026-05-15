import pytest
from app.agent.tools.bash import run_bash

def test_bash_simple():
    result = run_bash("echo hello")
    assert "hello" in result

def test_bash_blocked():
    result = run_bash("rm -rf /")
    assert "blocked" in result.lower() or "error" in result.lower()