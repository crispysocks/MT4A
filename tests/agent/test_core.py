import pytest
from app.agent.core import estimate_tokens, microcompact

def test_estimate_tokens():
    messages = [{"role": "user", "content": "hello"}]
    tokens = estimate_tokens(messages)
    assert tokens > 0

def test_microcompact():
    messages = [
        {"role": "user", "content": [{"type": "tool_result", "content": "tool output"}]}
    ]
    microcompact(messages)