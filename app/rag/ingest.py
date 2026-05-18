from pathlib import Path

WORKDIR = Path.cwd()

KB_CONFIG = {
    "public": {
        "sources": [
            str(WORKDIR / "knowledge" / "raw" / "公司信息" / "常见问答对.md"),
            str(WORKDIR / "knowledge" / "raw" / "公司信息" / "企业信息.md"),
        ],
        "roles": ["student", "employee", "guest"],
    },
    "internal": {
        "sources": [
            str(WORKDIR / "knowledge" / "raw" / "公司信息" / "公司新人指南.md"),
        ],
        "roles": ["employee"],
    },
    "business": {
        "sources": [
            str(WORKDIR / "knowledge" / "raw" / "公司业务"),
        ],
        "roles": ["student", "employee", "guest"],
    },
    "policy": {
        "sources": [
            str(WORKDIR / "knowledge" / "raw" / "留学政策"),
        ],
        "roles": ["student", "employee"],
    },
}


def ingest_all(engine):
    for kb_name, cfg in KB_CONFIG.items():
        engine.create_kb(kb_name, cfg["sources"])


if __name__ == "__main__":
    from app.rag.engine import RAGEngine
    engine = RAGEngine()
    ingest_all(engine)
