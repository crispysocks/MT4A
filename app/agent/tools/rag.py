from app.rag.store import ChromaStore
from app.rag.router import knowledge_router

_store = None

def get_store():
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store

def knowledge_search(query: str, top_k: int = 5) -> str:
    """Search knowledge base for relevant information."""
    store = get_store()
    where_filter = knowledge_router.build_where_filter() if knowledge_router else None
    results = store.query(query, top_k=top_k, where=where_filter)
    if not results:
        return "No relevant knowledge found."
    lines = ["Knowledge search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] (relevance: {1-r['distance']:.2f})")
        lines.append(r["content"][:500])
    return "\n".join(lines)