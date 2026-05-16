from app.rag.store import ChromaStore
import app.rag.router as rag_router
import app.rag.faq_index as faq_index

_store = None

def get_store():
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store

def knowledge_search(query: str, top_k: int = 5) -> str:
    """Search knowledge base for relevant information."""
    store = get_store()
    kr = rag_router.knowledge_router

    faq_answer = None
    if kr and kr.faq_roles:
        role = kr.soul_manager.current_role
        if role in kr.faq_roles:
            faq_answer = faq_index.search(query, score_diff_threshold=5.0)

    if faq_answer:
        context = (
            f"【常见问题参考】\n"
            f"标准答案：{faq_answer}\n\n"
            f"请以客服助手人设，将上述信息自然地回复给用户。"
        )
        return context

    where_filter = kr.build_where_filter() if kr else None
    results = store.query(query, top_k=top_k, where=where_filter)
    if not results:
        return "No relevant knowledge found."
    lines = ["Knowledge search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] (relevance: {1-r['distance']:.2f})")
        lines.append(r["content"][:500])
    return "\n".join(lines)