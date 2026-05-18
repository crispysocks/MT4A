from pathlib import Path

from app.rag.engine import RAGEngine
from app.rag.ingest import ingest_all, KB_CONFIG


def ingest():
    engine = RAGEngine()
    print(f"Persist dir: {engine.persist_dir}")
    print(f"KB config: {list(KB_CONFIG.keys())}")

    existing = engine.list_kbs()
    if existing:
        print(f"Warning: existing KBs will be replaced: {existing}")
        for kb in existing:
            engine.delete_kb(kb)

    ingest_all(engine)

    created = engine.list_kbs()
    print(f"\nCreated KBs: {created}")
    for kb in created:
        kb_path = Path(engine.persist_dir) / kb
        print(f"  {kb} -> {kb_path}")


if __name__ == "__main__":
    ingest()
