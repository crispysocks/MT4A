import pytest
from app.agent.tools.file import run_read, run_write, run_edit
import tempfile
import os
from pathlib import Path

WORKDIR = Path.cwd()

def test_read_file():
    with tempfile.TemporaryDirectory(dir=WORKDIR, suffix='.txt') as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        with open(path, 'w') as f:
            f.write("test content")
        result = run_read(path)
        assert "test content" in result

def test_write_file():
    with tempfile.TemporaryDirectory(dir=WORKDIR) as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        result = run_write(path, "hello")
        assert "Wrote" in result

def test_edit_file():
    with tempfile.TemporaryDirectory(dir=WORKDIR) as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        with open(path, 'w') as f:
            f.write("old text")
        result = run_edit(path, "old", "new")
        assert "Edited" in result
        with open(path) as f:
            assert "new text" in f.read()