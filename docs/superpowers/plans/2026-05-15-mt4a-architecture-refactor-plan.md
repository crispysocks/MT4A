# mt4a 架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单文件 agent 重构为多层架构，支持 FastAPI SSE 对话、RAG 知识库检索、MySQL 数据库操作

**Architecture:** 分层模块化架构 - API 层(FastAPI) / Agent 核心层 / Tool 层 / 数据层(RAG+DB) 分离，Tool 通过注册机制可配置

**Tech Stack:** FastAPI, Anthropic SDK, Chroma, DashScope Embedding, SQLModel, MySQL

---

## 文件结构

```
app/
├── __init__.py
├── main.py                    # FastAPI 入口（重写）
├── api/                       # API 层
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       └── chat.py           # SSE 聊天路由
├── agent/                     # Agent 核心
│   ├── __init__.py
│   ├── core.py               # agent_loop 主逻辑
│   └── tools/
│       ├── __init__.py       # Tool 注册入口
│       ├── registry.py       # Tool 注册表
│       ├── bash.py
│       ├── file.py
│       ├── rag.py
│       └── db.py
├── db/                       # 数据库层
│   ├── __init__.py
│   ├── models.py             # SQLModel 模型（courses, events, registrations）
│   └── connection.py         # MySQL 连接管理
├── rag/                      # RAG 层
│   ├── __init__.py
│   ├── embedder.py          # DashScope embedding
│   └── store.py             # Chroma 存储/检索
└── skills/                   # Skills 文件迁移
    └── SKILL.md
```

---

## Task 1: 创建目录结构

**Files:**
- Create: `app/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/api/routes/__init__.py`
- Create: `app/agent/__init__.py`
- Create: `app/agent/tools/__init__.py`
- Create: `app/db/__init__.py`
- Create: `app/rag/__init__.py`
- Create: `app/skills/` (directory)
- Delete: `agent/agent.py` (原单文件将拆解)

- [ ] **Step 1: 创建所有目录和空 `__init__.py` 文件**

```bash
mkdir -p app/api/routes app/agent/tools app/db app/rag app/skills
touch app/__init__.py app/api/__init__.py app/api/routes/__init__.py app/agent/__init__.py app/agent/tools/__init__.py app/db/__init__.py app/rag/__init__.py
```

- [ ] **Step 2: 验证目录结构**

```bash
find app -type f -name "*.py" | sort
```

Expected output:
```
app/__init__.py
app/api/__init__.py
app/api/routes/__init__.py
app/agent/__init__.py
app/agent/tools/__init__.py
app/db/__init__.py
app/rag/__init__.py
```

- [ ] **Step 3: Commit**

```bash
git add app/ && git commit -m "feat: create directory structure for multi-layer architecture"
```

---

## Task 2: 重构 Agent - Tool 注册机制

**Files:**
- Create: `app/agent/tools/registry.py`
- Create: `app/agent/tools/__init__.py` (exports registry and tool decorator)

**Dependencies:** Task 1 完成

- [ ] **Step 1: 编写 registry.py 测试**

```python
# tests/agent/tools/test_registry.py
import pytest
from app.agent.tools.registry import ToolRegistry, tool

def test_registry_empty():
    r = ToolRegistry()
    assert r.list() == []

def test_registry_register():
    r = ToolRegistry()
    r.register("test_tool", lambda x: x, {"type": "object"}, "A test tool")
    tools = r.list()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"

def test_registry_decorator():
    registry = ToolRegistry()

    @tool(name="decorated", description="Decorated tool", schema={"type": "object"})
    def my_func():
        return "result"

    assert "decorated" in [t["name"] for t in registry.list()]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent/tools/test_registry.py -v
```
Expected: FAIL - module not found

- [ ] **Step 3: 编写 registry.py 实现**

```python
# app/agent/tools/registry.py
from typing import Callable, Any

class ToolDef:
    def __init__(self, name: str, handler: Callable, schema: dict, description: str):
        self.name = name
        self.handler = handler
        self.schema = schema
        self.description = description

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, name: str, handler: Callable, schema: dict, description: str):
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = ToolDef(name, handler, schema, description)

    def list(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "input_schema": t.schema}
            for t in self._tools.values()
        ]

    def get_handler(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler

# Global registry instance
registry = ToolRegistry()

def tool(name: str, description: str, schema: dict):
    """Decorator to register a tool function."""
    def decorator(fn: Callable) -> Callable:
        registry.register(name, fn, schema, description)
        return fn
    return decorator
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent/tools/test_registry.py -v
```
Expected: PASS

- [ ] **Step 5: 编写 `__init__.py` 导出**

```python
# app/agent/tools/__init__.py
from .registry import registry, tool, ToolRegistry

__all__ = ["registry", "tool", "ToolRegistry"]
```

- [ ] **Step 6: Commit**

```bash
git add app/agent/tools/ tests/ && git commit -m "feat: add tool registry with decorator"
```

---

## Task 3: 重构 Agent - Base Tools 实现

**Files:**
- Create: `app/agent/tools/bash.py`
- Create: `app/agent/tools/file.py`
- Modify: `app/agent/tools/__init__.py` (注册 bash 和 file tools)

**Dependencies:** Task 2 完成

- [ ] **Step 1: 编写 bash.py 测试**

```python
# tests/agent/tools/test_bash.py
import pytest
from app.agent.tools.bash import run_bash

def test_bash_simple():
    result = run_bash("echo hello")
    assert "hello" in result

def test_bash_blocked():
    result = run_bash("rm -rf /")
    assert "blocked" in result.lower() or "error" in result.lower()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/agent/tools/test_bash.py -v
```
Expected: FAIL - module not found

- [ ] **Step 3: 编写 bash.py 实现**

```python
# app/agent/tools/bash.py
import subprocess
from pathlib import Path

WORKDIR = Path.cwd()

DANGEROUS_PATTERNS = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]

def run_bash(command: str) -> str:
    """Execute shell command with safety checks."""
    if any(d in command for d in DANGEROUS_PATTERNS):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/agent/tools/test_bash.py -v
```
Expected: PASS

- [ ] **Step 5: 编写 file.py 实现**

```python
# app/agent/tools/file.py
from pathlib import Path

WORKDIR = Path.cwd()

def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_read(path: str, limit: int = None) -> str:
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        fp = safe_path(path)
        c = fp.read_text()
        if old_text not in c:
            return f"Error: Text not found in {path}"
        fp.write_text(c.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 6: 编写 file.py 测试**

```python
# tests/agent/tools/test_file.py
import pytest
from app.agent.tools.file import run_read, run_write, run_edit
import tempfile
import os

def test_read_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        f.flush()
        result = run_read(f.name)
        assert "test content" in result
        os.unlink(f.name)

def test_write_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        result = run_write(path, "hello")
        assert "Wrote" in result

def test_edit_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        with open(path, 'w') as f:
            f.write("old text")
        result = run_edit(path, "old", "new")
        assert "Edited" in result
        with open(path) as f:
            assert "new text" in f.read()
```

- [ ] **Step 7: 运行 file 测试验证通过**

```bash
pytest tests/agent/tools/test_file.py -v
```
Expected: PASS

- [ ] **Step 8: 更新 __init__.py 注册 tools**

```python
# app/agent/tools/__init__.py
from .registry import registry, tool, ToolRegistry
from .bash import run_bash
from .file import run_read, run_write, run_edit

# Register base tools
registry.register(
    "bash",
    run_bash,
    {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    "Run a shell command."
)
registry.register(
    "read_file",
    run_read,
    {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]},
    "Read file contents."
)
registry.register(
    "write_file",
    run_write,
    {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    "Write content to file."
)
registry.register(
    "edit_file",
    run_edit,
    {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]},
    "Replace exact text in file."
)

__all__ = ["registry", "tool", "ToolRegistry"]
```

- [ ] **Step 9: Commit**

```bash
git add app/agent/tools/ tests/ && git commit -m "feat: add bash and file tools"
```

---

## Task 4: 重构 Agent - Core 逻辑迁移

**Files:**
- Create: `app/agent/core.py`
- Modify: `app/main.py` (重写为 FastAPI 入口)
- Modify: `app/skills/SKILL.md` (从 skills/ 迁移)

**Dependencies:** Task 2, Task 3 完成

- [ ] **Step 1: 编写 core.py 实现**

从原 `agent/agent.py` 迁移核心逻辑：
- `agent_loop`: 主循环
- `microcompact`: 每轮清理旧 tool_result
- `auto_compact`: 超阈值时压缩
- `TodoManager`: 任务管理
- `SkillLoader`: Skill 加载

```python
# app/agent/core.py
import json
import time
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

WORKDIR = Path.cwd()
MODEL = __import__('os').environ.get("MODEL_ID", "qwen3.6-plus")

client = Anthropic(
    base_url=__import__('os').getenv("LLM_BASE_URL"),
    api_key=__import__('os').getenv("LLM_AUTH_TOKEN"),
)

SKILLS_DIR = WORKDIR / "skills"
TRANSCRIPT_DIR = WORKDIR / ".transcripts"
TOKEN_THRESHOLD = 100_000

# Import from current module
from app.agent.tools import registry

# ... (migrate remaining code from original agent.py)
```

- [ ] **Step 2: 编写 core.py 测试**

```python
# tests/agent/test_core.py
import pytest
from app.agent.core import estimate_tokens, microcompact

def test_estimate_tokens():
    messages = [{"role": "user", "content": "hello"}]
    tokens = estimate_tokens(messages)
    assert tokens > 0

def test_microcompact():
    messages = [
        {"role": "user", "content": [{"type": "tool_result", "content": "tool output"}]}
    ]
    microcompact(messages)
    # Should not raise
```

- [ ] **Step 3: 运行 core 测试验证**

```bash
pytest tests/agent/test_core.py -v
```
Expected: PASS (or FAIL if integration issues)

- [ ] **Step 4: 迁移 skills/ 下的 SKILL.md**

```bash
# Copy if exists, otherwise create minimal
if [ -f "skills/SKILL.md" ]; then
    cp skills/SKILL.md app/skills/SKILL.md
fi
```

- [ ] **Step 5: Commit**

```bash
git add app/agent/core.py app/main.py app/skills/ && git commit -m "feat: migrate agent core logic to app/agent/core.py"
```

---

## Task 5: 创建 FastAPI + SSE 聊天接口

**Files:**
- Create: `app/api/main.py`
- Create: `app/api/routes/chat.py`
- Modify: `app/__init__.py`

**Dependencies:** Task 4 完成

- [ ] **Step 1: 编写 chat.py 测试**

```python
# tests/api/test_chat.py
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_chat_invalid():
    response = client.post("/chat", json={"messages": []})
    assert response.status_code == 422
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/api/test_chat.py -v
```
Expected: FAIL - module not found

- [ ] **Step 3: 编写 main.py 实现**

```python
# app/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="mt4a Agent API")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "mt4a Agent API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 编写 chat.py 实现**

```python
# app/api/routes/chat.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    async def event_stream():
        # TODO: Integrate with agent.core.agent_loop
        yield f"data: {json.dumps({'type': 'status', 'content': 'Processing...'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'content': 'Agent response placeholder'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 5: 注册 router 到 main.py**

```python
# app/api/main.py (update)
from .routes import chat
app.include_router(chat.router, prefix="/api")
```

- [ ] **Step 6: 运行测试验证**

```bash
pytest tests/api/test_chat.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/api/ tests/api/ && git commit -m "feat: add FastAPI with SSE chat endpoint"
```

---

## Task 6: 集成 RAG 层 - Chroma + DashScope Embedding

**Files:**
- Create: `app/rag/embedder.py`
- Create: `app/rag/store.py`
- Create: `app/agent/tools/rag.py` (RAG tool)
- Modify: `app/agent/tools/__init__.py` (注册 rag tool)
- Modify: `app/api/main.py` (启动时初始化 Chroma)

**Dependencies:** Task 5 完成

- [ ] **Step 1: 编写 embedder.py 测试**

```python
# tests/rag/test_embedder.py
import pytest
from app.rag.embedder import Embedder

def test_embedder_init():
    # Requires DASHSCOPE_API_KEY env var
    import os
    if not os.getenv("DASHSCOPE_API_KEY"):
        pytest.skip("No API key")
    e = Embedder()
    assert e.model == "text-embedding-v3"
```

- [ ] **Step 2: 运行测试（可能skip）**

```bash
pytest tests/rag/test_embedder.py -v
```

- [ ] **Step 3: 编写 embedder.py 实现**

```python
# app/rag/embedder.py
import os
from typing import List

class Embedder:
    def __init__(self, api_key: str = None, model: str = "text-embedding-v3"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def embed(self, texts: List[str]) -> List[List[float]]:
        import httpx
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": {"texts": texts}
        }
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            json=payload,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]
```

- [ ] **Step 4: 编写 store.py 实现**

```python
# app/rag/store.py
import os
from pathlib import Path
from typing import List, Optional

class ChromaStore:
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or str(WORKDIR / ".chroma")
        self._client = None
        self._collection = None

    @property
    def client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection("knowledge")
        return self._collection

    def add_documents(self, texts: List[str], ids: List[str], metadatas: List[dict] = None):
        from app.rag.embedder import Embedder
        embedder = Embedder()
        embeddings = embedder.embed(texts)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts)
        )

    def query(self, query_text: str, top_k: int = 5) -> List[dict]:
        from app.rag.embedder import Embedder
        embedder = Embedder()
        query_embedding = embedder.embed([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return [
            {"content": doc, "distance": dist, "metadata": meta}
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            )
        ]
```

- [ ] **Step 5: 编写 rag.py tool**

```python
# app/agent/tools/rag.py
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
```

- [ ] **Step 6: 更新 __init__.py 注册 rag tool**

```python
# app/agent/tools/__init__.py
from .rag import knowledge_search

registry.register(
    "knowledge_search",
    knowledge_search,
    {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]},
    "Search knowledge base for relevant information."
)
```

- [ ] **Step 7: 编写 rag 测试**

```bash
pytest tests/rag/ -v
```

- [ ] **Step 8: Commit**

```bash
git add app/rag/ app/agent/tools/rag.py tests/rag/ && git commit -m "feat: integrate RAG layer with Chroma and DashScope embedding"
```

---

## Task 7: 集成数据库层 - MySQL + SQLModel

**Files:**
- Create: `app/db/models.py`
- Create: `app/db/connection.py`
- Create: `app/agent/tools/db.py` (db tool)
- Modify: `app/agent/tools/__init__.py` (注册 db tool)
- Modify: `app/api/main.py` (启动时初始化 DB)

**Dependencies:** Task 6 完成

- [ ] **Step 1: 编写 models.py 实现**

```python
# app/db/models.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    type: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    recruitment_group: Optional[str] = Field(default=None, max_length=255)
    duration: Optional[str] = Field(default=None, max_length=100)
    fees: Optional[str] = Field(default=None)
    features: Optional[str] = Field(default=None)
    certification: Optional[str] = Field(default=None, max_length=255)
    allowance: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    type: Optional[str] = Field(default=None, max_length=100)
    event_datetime: Optional[datetime] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default="active", max_length=50)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

class Registration(SQLModel, table=True):
    __tablename__ = "registrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id")
    name: str = Field(max_length=100)
    phone: str = Field(max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    country_interest: Optional[str] = Field(default=None, max_length=100)
    education: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None)
    registration_date: Optional[datetime] = Field(default_factory=datetime.now)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
```

- [ ] **Step 2: 编写 connection.py 实现**

```python
# app/db/connection.py
import os
from sqlmodel import create_engine, Session

DATABASE_URL = (
    f"mysql+mysqlconnector://"
    f"{os.getenv('DATABASE_USER', 'root')}:{os.getenv('DATABASE_PASSWORD', '')}@"
    f"{os.getenv('DATABASE_HOST', 'localhost')}:{os.getenv('DATABASE_PORT', '3306')}/"
    f"{os.getenv('DATABASE_NAME', 'mt4a')}"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from app.db.models import Course, Event, Registration
    SQLModel.metadata.create_all(engine)
```

- [ ] **Step 3: 编写 db.py tool**

```python
# app/agent/tools/db.py
from app.db.connection import engine
from sqlmodel import Session
from app.db.models import Course, Event, Registration
import json

def db_query(operation: str, table: str, conditions: str = None, data: dict = None) -> str:
    """Query or modify database via natural language parameters."""
    try:
        with Session(engine) as session:
            if table == "courses":
                model = Course
            elif table == "events":
                model = Event
            elif table == "registrations":
                model = Registration
            else:
                return f"Error: Unknown table '{table}'"

            if operation.lower() == "select":
                results = session.select(model).all()
                return json.dumps([r.model_dump() for r in results], default=str, ensure_ascii=False)
            elif operation.lower() == "insert":
                obj = model(**data) if data else model()
                session.add(obj)
                session.commit()
                return f"Inserted: {obj.id}"
            elif operation.lower() == "update":
                # TODO: parse conditions and update
                return "Update operation not yet implemented"
            else:
                return f"Error: Unknown operation '{operation}'"
    except Exception as e:
        return f"Error: {e}"
```

- [ ] **Step 4: 更新 __init__.py 注册 db tool**

```python
# app/agent/tools/__init__.py
from .db import db_query

registry.register(
    "db_query",
    db_query,
    {"type": "object", "properties": {"operation": {"type": "string"}, "table": {"type": "string"}, "conditions": {"type": "string"}, "data": {"type": "object"}}, "required": ["operation", "table"]},
    "Query or modify database (courses, events, registrations)."
)
```

- [ ] **Step 5: 编写 db 测试**

```bash
pytest tests/db/ -v
```

- [ ] **Step 6: Commit**

```bash
git add app/db/ app/agent/tools/db.py tests/db/ && git commit -m "feat: add database layer with MySQL and SQLModel"
```

---

## Task 8: 创建前端静态页面

**Files:**
- Create: `app/api/static/index.html`
- Create: `app/api/static/style.css` (optional)
- Create: `app/api/static/app.js`

**Dependencies:** Task 7 完成

- [ ] **Step 1: 编写 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mt4a Agent</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        #chat { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        #input { width: 100%; padding: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; }
        .user { color: blue; }
        .assistant { color: green; }
    </style>
</head>
<body>
    <h1>mt4a Agent</h1>
    <div id="chat"></div>
    <input type="text" id="input" placeholder="Type your message..." />
    <button onclick="send()">Send</button>
    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 编写 app.js**

```javascript
const chatDiv = document.getElementById('chat');
const input = document.getElementById('input');

async function send() {
    const message = input.value;
    if (!message) return;
    input.value = '';

    // Display user message
    chatDiv.innerHTML += `<div class="message user"><strong>User:</strong> ${message}</div>`;

    // Send to /api/chat
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: [{role: 'user', content: message}]})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    chatDiv.innerHTML += `<div class="message assistant"><strong>Assistant:</strong> <span id="assistant-response"></span></div>`;
    const responseSpan = document.getElementById('assistant-response');

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.content) {
                        responseSpan.textContent += data.content;
                    }
                } catch (e) {}
            }
        }
    }
}

input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') send();
});
```

- [ ] **Step 3: 验证文件存在**

```bash
ls -la app/api/static/
```

- [ ] **Step 4: Commit**

```bash
git add app/api/static/ && git commit -m "feat: add frontend static files"
```

---

## Task 9: 集成 Agent Loop 到 API

**Files:**
- Modify: `app/api/routes/chat.py` (连接 agent_loop)
- Modify: `app/main.py` (启动时初始化)

**Dependencies:** Task 8 完成

- [ ] **Step 1: 修改 chat.py 集成 agent_loop**

```python
# app/api/routes/chat.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
from app.agent.core import agent_loop

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    async def event_stream():
        # Collect assistant response for streaming
        full_response = []

        # Run agent loop
        from app.agent.core import client, MODEL, registry, SYSTEM
        from anthropic import ALL_STOP_REASONS

        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=registry.list(),
            max_tokens=8000,
            stream=True
        )

        for event in response:
            if event.type == "content_block_delta":
                text = event.delta.text if hasattr(event, 'delta') else str(event)
                full_response.append(text)
                yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/api/test_chat.py -v
```

- [ ] **Step 3: Commit**

```bash
git add app/api/routes/chat.py && git commit -m "feat: integrate agent loop with SSE chat endpoint"
```

---

## Task 10: 清理和最终验证

**Files:**
- Delete: `agent/agent.py` (原单文件)
- Delete: `main.py` (已被 app/main.py 替代)
- Update: `.env.example` (补充所有环境变量)

- [ ] **Step 1: 删除旧文件**

```bash
rm agent/agent.py main.py
git add -A && git commit -m "refactor: remove old single-file agent, now using app/ structure"
```

- [ ] **Step 2: 更新 .env.example**

```bash
# Append new variables to .env.example
cat >> .env.example << 'EOF'

# Database (MySQL)
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=
DATABASE_NAME=mt4a

# DashScope Embedding
DASHSCOPE_API_KEY=
EOF
```

- [ ] **Step 3: 最终测试**

```bash
# Verify all imports work
python -c "from app.agent.tools import registry; print('Tools:', [t['name'] for t in registry.list()])"

# Verify FastAPI starts
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl http://localhost:8000/health
```

- [ ] **Step 4: Commit final state**

```bash
git add -A && git commit -m "feat: complete architecture refactor - multi-layer agent with FastAPI, RAG, and MySQL"
```

---

## 自检清单

- [ ] 所有 Task 完成
- [ ] 所有测试通过
- [ ] Spec 覆盖完整
- [ ] 无 placeholder (TBD/TODO)
- [ ] 类型一致性检查通过
- [ ] 提交历史清晰

---

**Plan complete.**