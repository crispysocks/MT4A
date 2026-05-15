from app.rag.store import ChromaStore

_store = None

def get_store():
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store

def knowledge_search(query: str, top_k: int = 5) -> str:
    """Search knowledge base for relevant information."""
    store = get_store()
    results = store.query(query, top_k=top_k)
    if not results:
        return "No relevant knowledge found."
    lines = ["Knowledge search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] (relevance: {1-r['distance']:.2f})")
        lines.append(r["content"][:500])
    return "\n".join(lines)