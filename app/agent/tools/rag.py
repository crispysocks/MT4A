import app.rag.router as rag_router
import app.rag.faq_index as faq_index

_engine = None


def set_rag_engine(engine):
    global _engine
    _engine = engine


def knowledge_search(query: str, top_k: int = 5) -> str:
    global _engine
    kr = rag_router.knowledge_router

    faq_answer = None
    if kr and kr.faq_roles:
        role = kr.soul_manager.current_role
        if role in kr.faq_roles:
            faq_answer = faq_index.search(query, score_diff_threshold=5.0)

    if faq_answer:
        return (
            "【常见问题参考】\n"
            f"标准答案：{faq_answer}\n\n"
            "请以客服助手人设，将上述信息自然地回复给用户。"
        )

    if _engine is None or kr is None:
        return ""

    kb_names = kr.get_allowed_kbs()
    results = _engine.query(query, kb_names=kb_names, top_k=top_k)

    if not results:
        return ""

    lines = ["Knowledge search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] (score: {r['score']})")
        lines.append(r["content"][:2000])
    return "\n".join(lines)
