import re
from pathlib import Path
from typing import List, Tuple

from app.rag.store import ChromaStore

PROCESSED_DIR = Path.cwd() / "knowledge" / "processed"

SOURCE_MAP = {
    "company/public": "company/public",
    "company/internal": "company/internal",
    "business": "business",
    "policy": "policy",
}


def find_md_files(root: Path) -> List[Tuple[Path, str]]:
    """Walk processed/ dir, return (filepath, source) for each .md file."""
    result = []
    for md_file in root.rglob("*.md"):
        rel_dir = md_file.parent.relative_to(root)
        source = SOURCE_MAP.get(str(rel_dir).replace("\\", "/"))
        if source is None:
            print(f"  [SKIP] unknown source for: {md_file}")
            continue
        result.append((md_file, source))
    return result


def chunk_markdown(content: str, filename: str) -> List[Tuple[str, str]]:
    """
    Split markdown by ## headings. Returns list of (chunk_title, chunk_text).
    First chunk covers content before any ## heading.
    """
    # Extract # title (first line starting with single #)
    title_match = re.match(r"^# (.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else filename

    # Split on ## headings (level 2 only)
    sections = re.split(r"\n(?=## )", content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        # Extract section heading
        heading_match = re.match(r"## (.+)", section)
        if heading_match:
            heading = heading_match.group(1).strip()
            body = section[heading_match.end():].strip()
        else:
            heading = doc_title
            body = section

        if not body:
            continue

        # Build rich chunk with document context
        chunk_text = f"# {doc_title}\n## {heading}\n\n{body}"
        chunks.append((heading, chunk_text))

    return chunks


def ingest():
    files = find_md_files(PROCESSED_DIR)
    print(f"Found {len(files)} markdown files to ingest\n")

    store = ChromaStore()
    all_ids = []
    all_texts = []
    all_metadatas = []

    for filepath, source in sorted(files):
        rel_path = str(filepath.relative_to(PROCESSED_DIR)).replace("\\", "/")
        print(f"  Processing: {rel_path}  (source: {source})")

        content = filepath.read_text(encoding="utf-8")
        chunks = chunk_markdown(content, filepath.stem)

        for i, (heading, chunk_text) in enumerate(chunks):
            chunk_id = f"{source}/{filepath.stem}#chunk{i}"
            all_ids.append(chunk_id)
            all_texts.append(chunk_text)
            all_metadatas.append({
                "source": source,
                "filename": rel_path,
                "title": heading,
            })

        print(f"    -> {len(chunks)} chunks")

    print(f"\nTotal: {len(all_texts)} chunks across {len(files)} files")
    print("Generating embeddings and storing to ChromaDB...")
    store.add_documents(texts=all_texts, ids=all_ids, metadatas=all_metadatas)
    print(f"Done. Collection 'knowledge' populated in {store.persist_dir}")


if __name__ == "__main__":
    ingest()
