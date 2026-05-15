import pytest
from app.rag.embedder import Embedder

def test_embedder_init():
    import os
    if not os.getenv("DASHSCOPE_API_KEY"):
        pytest.skip("No API key")
    e = Embedder()
    assert e.model == "text-embedding-v3"