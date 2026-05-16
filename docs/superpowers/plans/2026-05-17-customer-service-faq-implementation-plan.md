# 客服 FAQ 快速匹配实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 guest 角色（客服Agent）实现 FAQ 快速匹配，命中 BM25 索引时以标准答案作为 context 交给 LLM 包装，未命中时正常走 RAG。

**Architecture:** 在 `knowledge_search` 前串接 BM25 FAQ 通道；仅 `tool_config.yaml` 的 `faq_roles` 中列出的角色触发 BM25；BM25 top-1 与 top-2 分数差 > 5 才走 FAQ，否则 fallback RAG；FAQ answer 包装为 context 格式交给 LLM。

**Tech Stack:** rank_bm25（BM25实现），Python re（FAQ解析），现有 ChromaStore/RAG 基础设施

---

## 文件变更概览

| 文件 | 改动 |
|------|------|
| `pyproject.toml` | 新增 `rank-bm25` 依赖 |
| `souls/tool_config.yaml` | 新增 `faq_roles: [guest]` |
| `app/rag/router.py` | `KnowledgeRouter` 增加 `faq_roles` 属性，从 tool_config 读取 |
| `app/rag/faq_index.py` | 新建：BM25 索引封装，build() / search() / parse_faq() |
| `app/agent/tools/rag.py` | `knowledge_search` 串接 BM25 通道 |
| `app/api/main.py` | startup_event 调用 `FaqIndex.build()` |
| `tests/rag/test_faq_index.py` | 新建：FaqIndex 单元测试 |

---

## Task 1: 添加 rank-bm25 依赖

**Files:**
- Modify: `pyproject.toml:11-20`

- [ ] **Step 1: 添加 rank-bm25 到 dependencies**

```toml
dependencies = [
    "anthropic>=0.102.0",
    "bcrypt>=5.0.0",
    "chromadb>=1.5.9",
    "fastapi>=0.136.1",
    "mysql-connector-python>=9.7.0",
    "pyjwt>=2.10.0",
    "python-dotenv>=1.2.2",
    "sqlmodel>=0.0.38",
    "rank-bm25>=0.2.2",
]
```

- [ ] **Step 2: 安装依赖**

Run: `uv sync`

Expected: `rank-bm25` added to lock file

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add rank-bm25 for FAQ fast matching"
```

---

## Task 2: 创建 app/rag/faq_index.py

**Files:**
- Create: `app/rag/faq_index.py`

- [ ] **Step 1: 写 FaqIndex 类**

```python
import re
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

WORKDIR = Path.cwd()
FAQ_PATH = WORKDIR / "knowledge" / "processed" / "company" / "public" / "faq.md"

_index: Optional[BM25Okapi] = None
_faqs: list[dict] = []  # [{"question": ..., "answer": ...}, ...]


def parse_faq(md_path: Path) -> list[dict]:
    """
    Parse FAQ markdown file.
    Format: ## question title\nanswer text\n\n
    Returns list of {"question": str, "answer": str}.
    """
    content = md_path.read_text(encoding="utf-8")
    # Split by ## (level 2 headings)
    sections = re.split(r"\n(?=## )", content)

    faqs = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        # Extract heading (question)
        heading_match = re.match(r"## (.+)", section)
        if not heading_match:
            continue
        question = heading_match.group(1).strip()
        # Everything after the heading is the answer
        body = section[heading_match.end():].strip()
        if body and question:
            faqs.append({"question": question, "answer": body})
    return faqs


def build():
    """Build BM25 index from FAQ file. Called at app startup."""
    global _index, _faqs
    _faqs = parse_faq(FAQ_PATH)
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
```

- [ ] **Step 2: Commit**

```bash
git add app/rag/faq_index.py
git commit -m "feat: add FaqIndex with BM25 FAQ matching"
```

---

## Task 3: 修改 KnowledgeRouter 支持 faq_roles

**Files:**
- Modify: `app/rag/router.py:1-27`

- [ ] **Step 1: 写测试**

```python
# tests/rag/test_faq_index.py
import pytest
from app.rag.faq_index import parse_faq, build, search
from pathlib import Path

def test_parse_faq():
    faqs = parse_faq(Path("knowledge/processed/company/public/faq.md"))
    assert len(faqs) > 0
    assert "question" in faqs[0]
    assert "answer" in faqs[0]

def test_search_returns_answer_when_diff_above_threshold():
    build()
    result = search("公司简称什么", score_diff_threshold=5.0)
    assert result is not None
    assert "粤教服务" in result

def test_search_returns_none_when_diff_below_threshold():
    build()
    result = search("今天天气怎么样", score_diff_threshold=5.0)
    # fuzzy/unrelated query should return None
    assert result is None
```

- [ ] **Step 2: 运行测试验证测试框架正常**

Run: `uv run pytest tests/rag/test_faq_index.py -v`
Expected: 3 tests collected (may fail on implementation, that's expected)

- [ ] **Step 3: 修改 router.py**

在 `tool_config.yaml` 中，`SoulManager.load()` 已经把 `faq_roles` 读进来了（通过 `_load_tool_config`）。需要在 `KnowledgeRouter` 中新增属性并传递给 `faq_index.search()` 调用。

但 `KnowledgeRouter.__init__` 只接收 `soul_manager`，而 `_load_tool_config` 是在 `SoulManager.load()` 里做的。

最简单的做法：在 `KnowledgeRouter` 中增加一个 `faq_roles` 属性，`chat.py` 初始化 `KnowledgeRouter(soul_manager)` 后，再把 `soul_manager._tool_config.get("faq_roles", [])` 赋值给 `router.faq_roles`。

```python
# app/rag/router.py
class KnowledgeRouter:
    def __init__(self, soul_manager, role_bases: dict = None):
        self.soul_manager = soul_manager
        self.role_bases = role_bases or ROLE_KNOWLEDGE_BASES
        self.faq_roles: list[str] = []

    def get_allowed_bases(self) -> List[str]:
        if self.soul_manager.is_active():
            role = self.soul_manager.current_role
            return self.role_bases.get(role, self.role_bases.get("guest", []))
        return self.role_bases.get("guest", [])
```

然后修改 `chat.py:15`：

```python
rag_router.knowledge_router = KnowledgeRouter(soul_manager)
rag_router.knowledge_router.faq_roles = soul_manager._tool_config.get("faq_roles", [])
```

- [ ] **Step 4: 验证测试通过**

Run: `uv run pytest tests/rag/test_faq_index.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/rag/router.py app/api/routes/chat.py
git commit -m "feat: add faq_roles config to KnowledgeRouter"
```

---

## Task 4: 集成 BM25 到 knowledge_search

**Files:**
- Modify: `app/agent/tools/rag.py:1-23`

- [ ] **Step 1: 写测试**

```python
# tests/agent/tools/test_rag.py 新增一个 test
def test_knowledge_search_guest_uses_faq(monkeypatch):
    """guest role should try BM25 first before RAG"""
    from unittest.mock import MagicMock
    from app.rag import router as rag_router_module
    from app.agent.soul import SoulManager

    # setup: mock knowledge_router with guest role
    sm = SoulManager()
    sm._active_soul = {"tools": ["knowledge_search"]}
    sm.current_role = "guest"
    sm._tool_config = {"faq_roles": ["guest"]}

    kr = MagicMock()
    kr.soul_manager = sm
    kr.faq_roles = ["guest"]

    mock_router = MagicMock()
    mock_router.knowledge_router = kr
    monkeypatch.setattr(rag_router_module, "knowledge_router", mock_router)
    monkeypatch.setattr(rag_router_module, "knowledge_search", None)  # prevent recursion

    # import after monkeypatch
    from app.agent.tools.rag import knowledge_search

    # This test verifies the code path exists without erroring
```

实际不需要写这么复杂的 mock 测试。核心逻辑在 `knowledge_search` 内部，验证方式通过 Task 6 的端到端测试。

- [ ] **Step 2: 修改 rag.py**

```python
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
```

- [ ] **Step 3: 验证测试通过**

Run: `uv run pytest tests/ -v`
Expected: 36 passed, 1 skipped (embedder)

- [ ] **Step 4: Commit**

```bash
git add app/agent/tools/rag.py
git commit -m "feat: integrate BM25 FAQ matching into knowledge_search"
```

---

## Task 5: 启动时构建 BM25 索引

**Files:**
- Modify: `app/api/main.py:50-54`

- [ ] **Step 1: 修改 startup_event**

```python
@app.on_event("startup")
async def startup_event():
    from app.db.connection import init_db_on_startup
    from app.rag.faq_index import build as build_faq_index
    init_db_on_startup()
    build_faq_index()
    print("[INFO] mt4a Agent API started")
```

- [ ] **Step 2: 验证启动不报错**

Run: `uv run python -c "from app.api.main import app; print('import ok')"`
Expected: import ok (no errors about rank_bm25 or FaqIndex)

- [ ] **Step 3: Commit**

```bash
git add app/api/main.py
git commit -m "feat: build BM25 FAQ index at startup"
```

---

## Task 6: 更新 tool_config.yaml 添加 faq_roles

**Files:**
- Modify: `souls/tool_config.yaml:47-50`

- [ ] **Step 1: 添加 faq_roles 配置**

在 `guest:` 条目下、工具列表之后，加上：

```yaml
guest:
  - knowledge_search
  - TodoWrite
  - compress

faq_roles:
  - guest
```

注意：`faq_roles` 是顶层 key，与 student/employee/guest 同级，不是嵌套在 guest 下面。

- [ ] **Step 2: Commit**

```bash
git add souls/tool_config.yaml
git commit -m "feat: add faq_roles config for guest agent"
```

---

## Task 7: 端到端验证

**Files:**
- None (verification only)

- [ ] **Step 1: 验证 FAQ 命中**

Run:
```bash
uv run python -c "
from app.agent.soul import SoulManager
from app.rag.router import KnowledgeRouter
import app.rag.router as rag_router

sm = SoulManager()
sm.load('guest')
sm._tool_config = {'faq_roles': ['guest']}

rag_router.knowledge_router = KnowledgeRouter(sm)
rag_router.knowledge_router.faq_roles = ['guest']

from app.agent.tools.rag import knowledge_search

result = knowledge_search('公司简称什么')
print('FAQ result:', '粤教服务' in result)
print(result[:200])
"
```
Expected: `True` (FAQ命中，answer含"粤教服务")

- [ ] **Step 2: 验证 FAQ 未命中走 RAG**

Run:
```bash
uv run python -c "
from app.agent.soul import SoulManager
from app.rag.router import KnowledgeRouter
import app.rag.router as rag_router

sm = SoulManager()
sm.load('guest')
sm._tool_config = {'faq_roles': ['guest']}

rag_router.knowledge_router = KnowledgeRouter(sm)
rag_router.knowledge_router.faq_roles = ['guest']

from app.agent.tools.rag import knowledge_search

result = knowledge_search('今天天气怎么样')
print('Fallback result:', 'No relevant knowledge' in result or 'Knowledge search results' in result)
"
```
Expected: `True` (走RAG，返回no relevant knowledge或results)

- [ ] **Step 3: 验证 employee 角色不触发 FAQ**

Run:
```bash
uv run python -c "
from app.agent.soul import SoulManager
from app.rag.router import KnowledgeRouter
import app.rag.router as rag_router

sm = SoulManager()
sm.load('employee')
sm._tool_config = {'faq_roles': ['guest']}

rag_router.knowledge_router = KnowledgeRouter(sm)
rag_router.knowledge_router.faq_roles = ['guest']

from app.agent.tools.rag import knowledge_search

result = knowledge_search('公司简称什么')
# employee不在faq_roles，所以走RAG，不走BM25
print('Employee result:', 'Knowledge search results' in result)
"
```
Expected: `True` (employee不在faq_roles，走RAG)

- [ ] **Step 4: 运行全测试**

Run: `uv run pytest tests/ -v`
Expected: 36 passed, 1 skipped

---

## 自检清单

- [ ] SPEC coverage: 每个设计要求都有对应 task 实现
- [ ] 无 placeholder: 无 "TBD"、"TODO"、"实现细节待补充"
- [ ] 类型一致: `faq_index.search()` 返回 `Optional[str]`，`knowledge_search` 正确处理 `None` vs `str`
- [ ] 依赖已添加: `rank-bm25` 在 `pyproject.toml` 中
- [ ] 配置正确: `faq_roles` 为 `souls/tool_config.yaml` 顶层 key