import re
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

WORKDIR = Path.cwd()
FAQ_PATH = WORKDIR / "knowledge" / "raw" / "公司信息" / "常见问答对.md"

_index: Optional[BM25Okapi] = None
_faqs: list[dict] = []


def parse_faq(md_path: Path) -> list[dict]:
    """
    Parse FAQ markdown file.
    Supports both markdown table (| 问题 | 答案 |) and ## heading format.
    Returns list of {"question": str, "answer": str}.
    """
    content = md_path.read_text(encoding="utf-8")

    faqs = []
    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        if "---" in line:
            continue
        cols = [c.strip() for c in line[1:-1].split("|")]
        if len(cols) >= 2 and cols[0] not in ("问题", "Sheet1"):
            faqs.append({"question": cols[0], "answer": cols[-1]})

    if faqs:
        return faqs

    # Fallback: old ## heading format
    sections = re.split(r"\n(?=#{2,3} )", content)
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"#{2,3} (.+)", section)
        if not heading_match:
            continue
        question = heading_match.group(1).strip()
        body = section[heading_match.end():].strip()
        if body and question:
            faqs.append({"question": question, "answer": body})
    return faqs


def build():
    """Build BM25 index from FAQ file. Called at app startup."""
    global _index, _faqs
    _faqs = parse_faq(FAQ_PATH)
    if not _faqs:
        print("[FAQ] Warning: no FAQ entries parsed")
        return
    tokenized = [f["question"] for f in _faqs]
    _index = BM25Okapi(tokenized)


def search(query: str, score_diff_threshold: float = 5.0) -> Optional[str]:
    """
    Search FAQ by query.
    Returns answer string if top-1 score - top-2 score > threshold, else None.
    """
    global _index, _faqs
    if _index is None or not _faqs:
        return None

    tokenized_query = query.split()
    scores = _index.get_scores(tokenized_query)
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    if len(sorted_indices) < 2:
        return None

    top1_score = scores[sorted_indices[0]]
    top2_score = scores[sorted_indices[1]]
    score_diff = top1_score - top2_score

    if score_diff > score_diff_threshold:
        return _faqs[sorted_indices[0]]["answer"]
    return None