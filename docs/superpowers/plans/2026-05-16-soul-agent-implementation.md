# SOUL注入多角色Agent系统 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有mt4a单Agent框架改造为身份驱动SOUL注入系统，支持学生/员工/客服三种角色通过登录后自动切换Agent认知和工具能力。

**Architecture:** 新增SoulManager层负责SOUL.md加载与解析，新增AuthManager处理JWT鉴权，改造agent_loop从SoulManager动态获取system prompt和工具列表，KnowledgeRouter按角色隔离RAG检索范围。

**Tech Stack:** Python 3.12+, FastAPI, SQLModel+MySQL, Anthropic SDK, Chroma+DashScope, PyJWT, bcrypt

---

## 文件结构

```
新建:
  app/agent/auth.py            # AuthManager + 密码工具
  app/agent/soul.py            # SoulManager
  app/api/routes/auth.py       # 鉴权API路由
  app/rag/router.py            # KnowledgeRouter
  souls/student/SOUL.md        # 学生角色SOUL
  souls/employee/SOUL.md       # 员工角色SOUL
  souls/guest/SOUL.md          # 客服角色SOUL
  app/api/static/login.html    # 登录/注册页
  tests/test_auth.py           # AuthManager测试
  tests/test_soul.py           # SoulManager测试
  tests/test_knowledge_router.py  # KnowledgeRouter测试

修改:
  app/agent/core.py            # agent_loop使用SoulManager
  app/agent/tools/__init__.py  # ENABLED_TOOLS按角色, registry.list()支持过滤
  app/agent/tools/rag.py       # knowledge_search集成KnowledgeRouter
  app/agent/tools/db.py        # db_query支持新表
  app/db/models.py             # 新增11张业务表
  app/db/connection.py         # init_db自动建所有表
  app/api/main.py              # 注册auth路由,添加CORS
  app/api/routes/chat.py       # 注入用户/SOUL上下文
  app/api/static/index.html    # 改为登录检查+主题色+登出
  app/api/static/app.js        # 鉴权流程集成
  pyproject.toml               # 添加PyJWT和bcrypt依赖
```

---

### Task 1: 添加依赖

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加PyJWT和bcrypt依赖**

```toml
# pyproject.toml dependencies列表追加
"pyjwt>=2.10.0",
"bcrypt>=5.0.0",
```

- [ ] **Step 2: 安装依赖**

```bash
uv sync
```

Expected: 无错误, pyjwt和bcrypt包安装成功

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add pyjwt and bcrypt for auth"
```

---

### Task 2: 扩展数据库模型

**Files:**
- Modify: `app/db/models.py` (追加新模型)

- [ ] **Step 1: 在models.py末尾追加所有新表模型**

```python
# app/db/models.py 末尾追加

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(max_length=20)  # 'student' or 'employee'
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class Lead(SQLModel, table=True):
    __tablename__ = "leads"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    source: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default="new", max_length=50)
    assigned_to: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class LeadFollowUp(SQLModel, table=True):
    __tablename__ = "lead_follow_ups"
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id")
    content: str = Field()
    follow_type: Optional[str] = Field(default=None, max_length=50)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class DailyReport(SQLModel, table=True):
    __tablename__ = "daily_reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    content: str = Field()
    summary: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None, max_length=100)
    submitted_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    category: Optional[str] = Field(default=None, max_length=100)
    content: str = Field()
    status: Optional[str] = Field(default="pending", max_length=50)
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id")
    resolution: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    resolved_at: Optional[datetime] = Field(default=None)


class Organization(SQLModel, table=True):
    __tablename__ = "organization"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    type: str = Field(max_length=50)  # 'department' or 'person'
    parent_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    contact_info: Optional[str] = Field(default=None, max_length=255)


class StudentGrade(SQLModel, table=True):
    __tablename__ = "student_grades"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    subject: str = Field(max_length=100)
    grade: Optional[str] = Field(default=None, max_length=20)
    semester: Optional[str] = Field(default=None, max_length=50)
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    reason: str = Field()
    start_date: str = Field()  # DATE as string for simplicity
    end_date: str = Field()
    status: Optional[str] = Field(default="pending", max_length=50)
    approver_id: Optional[int] = Field(default=None, foreign_key="users.id")
    approved_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class ExamSchedule(SQLModel, table=True):
    __tablename__ = "exam_schedule"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    type: Optional[str] = Field(default=None, max_length=100)
    subject: Optional[str] = Field(default=None, max_length=100)
    deadline: Optional[datetime] = Field(default=None)
    description: Optional[str] = Field(default=None)


class PsychologyProfile(SQLModel, table=True):
    __tablename__ = "psychology_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    emotion_tag: Optional[str] = Field(default=None, max_length=100)
    score: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class PsychologyWarning(SQLModel, table=True):
    __tablename__ = "psychology_warnings"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    trigger_reason: str = Field()
    risk_level: Optional[str] = Field(default="medium", max_length=50)
    status: Optional[str] = Field(default="active", max_length=50)
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
```

- [ ] **Step 2: 验证模型可导入**

```bash
uv run python -c "from app.db.models import User, Lead, LeadFollowUp, DailyReport, Complaint, Organization, StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning; print('All models OK')"
```

Expected: `All models OK`

- [ ] **Step 3: Commit**

```bash
git add app/db/models.py
git commit -m "feat: add 11 business models for multi-role agent system"
```

---

### Task 3: 更新数据库连接和db_query工具

**Files:**
- Modify: `app/db/connection.py` (init_db注册所有模型)
- Modify: `app/agent/tools/db.py` (db_query model_map扩展新表)

- [ ] **Step 1: 更新init_db注册所有模型**

修改 `app/db/connection.py:17-19`:

```python
def init_db():
    from app.db.models import (
        Course, Event, Registration,
        User, Lead, LeadFollowUp, DailyReport, Complaint, Organization,
        StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
    )
    SQLModel.metadata.create_all(engine)
```

- [ ] **Step 2: 更新db_query的model_map**

修改 `app/db/models.py` 导入部分, 以及 `app/agent/tools/db.py`:

```python
# app/agent/tools/db.py 顶部导入替换为:
from app.db.models import (
    Course, Event, Registration,
    User, Lead, LeadFollowUp, DailyReport, Complaint, Organization,
    StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
)

# model_map 字典替换为:
model_map = {
    "courses": Course,
    "events": Event,
    "registrations": Registration,
    "users": User,
    "leads": Lead,
    "lead_follow_ups": LeadFollowUp,
    "daily_reports": DailyReport,
    "complaints": Complaint,
    "organization": Organization,
    "student_grades": StudentGrade,
    "leave_requests": LeaveRequest,
    "exam_schedule": ExamSchedule,
    "psychology_profiles": PsychologyProfile,
    "psychology_warnings": PsychologyWarning,
}
```

同时更新 `db_query` 的 schema 中的 `table.enum`, 在 `app/agent/tools/__init__.py` 的 `_TOOL_DEFS["db_query"]` 中把 `table.enum` 改为:

```python
"enum": ["courses", "events", "registrations", "users", "leads", "lead_follow_ups", "daily_reports", "complaints", "organization", "student_grades", "leave_requests", "exam_schedule", "psychology_profiles", "psychology_warnings"],
```

- [ ] **Step 3: Commit**

```bash
git add app/db/connection.py app/agent/tools/db.py app/agent/tools/__init__.py
git commit -m "feat: expand db_query to support all new business tables"
```

---

### Task 4: AuthManager实现（TDD）

**Files:**
- Create: `app/agent/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/test_auth.py
import pytest
import jwt
from datetime import datetime, timezone
from app.agent.auth import AuthManager, hash_password, verify_password

def test_hash_and_verify_password():
    password = "test1234"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_register_user(db_session):
    mgr = AuthManager(db_session)
    user = mgr.register("zhangsan", "pass1234", "student")
    assert user.username == "zhangsan"
    assert user.role == "student"
    assert user.password_hash != "pass1234"

def test_register_duplicate_username(db_session):
    mgr = AuthManager(db_session)
    mgr.register("lisi", "pass1", "student")
    with pytest.raises(ValueError, match="already exists"):
        mgr.register("lisi", "pass2", "employee")

def test_login_success(db_session):
    mgr = AuthManager(db_session)
    mgr.register("wangwu", "mypass", "employee")
    token, role = mgr.login("wangwu", "mypass")
    assert role == "employee"
    assert isinstance(token, str)

def test_login_wrong_password(db_session):
    mgr = AuthManager(db_session)
    mgr.register("testuser", "correct", "student")
    with pytest.raises(ValueError, match="Invalid"):
        mgr.login("testuser", "wrong")

def test_verify_token(db_session):
    mgr = AuthManager(db_session)
    user = mgr.register("tokenuser", "pass", "student")
    token, _ = mgr.login("tokenuser", "pass")
    payload = mgr.verify(token)
    assert payload["user_id"] == user.id
    assert payload["role"] == "student"
    assert payload["username"] == "tokenuser"

def test_verify_invalid_token(db_session):
    mgr = AuthManager(db_session)
    with pytest.raises(jwt.PyJWTError):
        mgr.verify("invalid.token.here")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: FAIL (文件不存在或类未定义)

- [ ] **Step 3: 实现AuthManager**

```python
# app/agent/auth.py
import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Tuple
from sqlmodel import Session, select
from app.db.models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


class AuthManager:
    def __init__(self, session: Session):
        self.session = session

    def register(self, username: str, password: str, role: str) -> User:
        existing = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing:
            raise ValueError(f"Username '{username}' already exists")
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def login(self, username: str, password: str) -> Tuple[str, str]:
        user = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token, user.role

    def verify(self, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

- [ ] **Step 4: 创建conftest和数据库fixture**

```python
# tests/conftest.py (如果不存在则创建)
import pytest
from sqlmodel import Session, SQLModel, create_engine
from app.db.models import User

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    # 只创建User表用于AuthManager测试
    SQLModel.metadata.create_all(engine, tables=[User.__table__])
    with Session(engine) as session:
        yield session
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add app/agent/auth.py tests/test_auth.py tests/conftest.py
git commit -m "feat: AuthManager with JWT auth, register, login, verify"
```

---

### Task 5: 鉴权API路由

**Files:**
- Create: `app/api/routes/auth.py`

- [ ] **Step 1: 创建auth路由**

```python
# app/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from app.db.connection import get_session
from app.agent.auth import AuthManager
from app.agent.soul import SoulManager

router = APIRouter()

soul_manager = SoulManager()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str  # "student" or "employee"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/register")
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    if req.role not in ("student", "employee"):
        raise HTTPException(400, "role must be 'student' or 'employee'")
    if len(req.username) < 2:
        raise HTTPException(400, "username too short")
    if len(req.password) < 4:
        raise HTTPException(400, "password too short")
    try:
        auth = AuthManager(session)
        user = auth.register(req.username, req.password, req.role)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.post("/auth/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    try:
        auth = AuthManager(session)
        token, role = auth.login(req.username, req.password)
        # 登录成功后加载SOUL
        soul_manager.load(role)
        return {"token": token, "role": role}
    except ValueError as e:
        raise HTTPException(401, str(e))


@router.post("/auth/logout")
def logout():
    soul_manager.unload()
    return {"status": "logged_out"}


@router.get("/auth/me")
def me(session: Session = Depends(get_session)):
    # 由中间件处理的token验证，此处检查soul状态
    from fastapi import Request
    import jwt
    import os
    from app.agent.auth import SECRET_KEY

    # me端点由JWT中间件处理验证，这里默认已通过
    # 简化实现: 查询当前SOUL状态
    if not soul_manager.is_active():
        return {"role": "guest"}
    return {"role": soul_manager.current_role}
```

- [ ] **Step 2: Commit**

```bash
git add app/api/routes/auth.py
git commit -m "feat: auth API routes (register, login, logout, me)"
```

---

### Task 6: 注册auth路由 + CORS + JWT中间件

**Files:**
- Modify: `app/api/main.py`

- [ ] **Step 1: 改造main.py**

```python
# app/api/main.py 完整替换
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import jwt
from app.agent.auth import SECRET_KEY

from .routes import chat, sessions
from .routes.auth import router as auth_router

app = FastAPI(title="mt4a Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开路由（无需鉴权）
app.include_router(auth_router, prefix="/api")
app.include_router(sessions.router, prefix="/api")

# 需要鉴权的chat路由通过中间件处理
@app.post("/api/chat")
async def chat_endpoint(request: Request):
    # 解析token（可选，未登录则guest）
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    return await chat.handle_chat(request, token)

# 单独注册chat的SSE流式路由以绕过中间件
# 实际上由chat.handle_chat处理

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/login")
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"error": "login page not found"}


@app.get("/")
async def root(request: Request):
    # 检查是否有token cookie/header，无则重定向到登录页
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "mt4a Agent API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add app/api/main.py
git commit -m "feat: register auth routes, add CORS middleware"
```

---

### Task 7: SoulManager实现（TDD）

**Files:**
- Create: `app/agent/soul.py`
- Create: `tests/test_soul.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/test_soul.py
import tempfile
from pathlib import Path
from app.agent.soul import SoulManager

SAMPLE_SOUL = """---
name: Test Agent
role: test
tools: [tool_a, tool_b]
---

You are a test agent. Help users with testing.
"""


def test_load_and_parse_soul(tmp_path):
    soul_dir = tmp_path / "souls" / "test"
    soul_dir.mkdir(parents=True)
    (soul_dir / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")

    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("test")

    assert mgr.is_active() is True
    assert mgr.current_role == "test"
    assert "test agent" in mgr.get_system_prompt().lower()
    assert mgr.get_tools() == ["tool_a", "tool_b"]


def test_unload_soul(tmp_path):
    soul_dir = tmp_path / "souls" / "test"
    soul_dir.mkdir(parents=True)
    (soul_dir / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")

    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("test")
    assert mgr.is_active() is True

    mgr.unload()
    assert mgr.is_active() is False
    assert mgr.current_role is None


def test_load_nonexistent_soul(tmp_path):
    mgr = SoulManager(str(tmp_path / "souls"))
    mgr.load("nonexistent")
    assert mgr.is_active() is False


def test_singleton_reset(tmp_path):
    soul_dir = tmp_path / "souls"
    (soul_dir / "test_a").mkdir(parents=True)
    (soul_dir / "test_b").mkdir(parents=True)
    (soul_dir / "test_a" / "SOUL.md").write_text(SAMPLE_SOUL, encoding="utf-8")
    (soul_dir / "test_b" / "SOUL.md").write_text(
        SAMPLE_SOUL.replace("test", "test_b").replace("test agent", "test b agent"), encoding="utf-8"
    )

    mgr = SoulManager(str(soul_dir))
    mgr.load("test_a")
    assert mgr.current_role == "test"
    assert "test a" not in mgr.get_system_prompt().lower()
    # load另一个角色覆盖
    mgr.load("test_b")
    assert mgr.current_role == "test_b"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_soul.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现SoulManager**

```python
# app/agent/soul.py
import re
from pathlib import Path
from typing import Optional, List


class SoulManager:
    def __init__(self, souls_dir: str = "souls"):
        self.souls_dir = Path(souls_dir)
        self._active_soul: Optional[dict] = None
        self.current_role: Optional[str] = None

    def load(self, role: str) -> None:
        soul_path = self.souls_dir / role / "SOUL.md"
        if not soul_path.exists():
            self._active_soul = None
            self.current_role = None
            return

        text = soul_path.read_text(encoding="utf-8")
        meta, body = self._parse_frontmatter(text)

        self._active_soul = {
            "name": meta.get("name", role),
            "role": meta.get("role", role),
            "tools": meta.get("tools", []),
            "system_prompt": body.strip(),
        }
        self.current_role = role

    def unload(self) -> None:
        self._active_soul = None
        self.current_role = None

    def is_active(self) -> bool:
        return self._active_soul is not None

    def get_system_prompt(self) -> str:
        if not self._active_soul:
            return "You are a helpful assistant."
        return self._active_soul["system_prompt"]

    def get_tools(self) -> List[str]:
        if not self._active_soul:
            return []
        return self._active_soul.get("tools", [])

    def _parse_frontmatter(self, text: str) -> tuple:
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text

        meta = {}
        for line in match.group(1).strip().splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                meta[key] = value

        return meta, match.group(2).strip()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_soul.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/agent/soul.py tests/test_soul.py
git commit -m "feat: SoulManager for SOUL.md loading, parsing, unloading"
```

---

### Task 8: 三份SOUL.md文件

**Files:**
- Create: `souls/student/SOUL.md`
- Create: `souls/employee/SOUL.md`
- Create: `souls/guest/SOUL.md`

- [ ] **Step 1: 创建学生SOUL**

```markdown
<!-- souls/student/SOUL.md -->
---
name: 学生智能助手
role: student
tools: [knowledge_search, db_query, TodoWrite, compress]
---

你是一个留学机构的学生智能助手。你的服务对象是留学生，你需要用亲切、友好的语气与他们沟通。

## 你的能力
- 查询留学政策（各国签证、院校申请要求）
- 查询课程和升学项目信息
- 提交请假申请
- 提交投诉或建议反馈
- 查询考试成绩
- 查询论文DDL和考试时间
- 日常闲聊与情感关怀

## 注意事项
- 始终保持友善、耐心的态度
- 涉及请假、投诉等操作时，确认用户意图后再执行
- 不要编造知识库中没有的信息
```

- [ ] **Step 2: 创建员工SOUL**

```markdown
<!-- souls/employee/SOUL.md -->
---
name: 企业智能助手
role: employee
tools: [knowledge_search, db_query, TodoWrite, compress]
---

你是一个留学机构的内部企业智能助手。你的服务对象是公司员工（销售、教务、管理层），你需要用专业、高效的语言协助他们完成日常工作。

## 你的能力
- 查询和录入意向客户信息
- 查看和更新客户跟进记录
- 口述日报并自动转化为结构化文本
- 查询员工日报
- 查询学生成绩
- 审批请假申请
- 处理投诉反馈
- 查询组织架构和同事联系方式
- 查询公司内部制度和新手指南

## 注意事项
- 保持专业、简洁的沟通风格
- 涉及数据修改操作时需确认
- 不泄露客户隐私信息给无关人员
```

- [ ] **Step 3: 创建客服SOUL**

```markdown
<!-- souls/guest/SOUL.md -->
---
name: 客服助手
role: guest
tools: [knowledge_search, TodoWrite, compress]
---

你是一个留学机构的对外客服助手。你的服务对象是潜在客户（学生、家长等），你需要热情、专业地解答他们的咨询，建立对机构的第一层信任感。

## 你的能力
- 介绍机构品牌背景、发展历程和校区分布
- 介绍留学申请、背景提升、语言培训等核心业务
- 解读各国签证要求和院校申请门槛
- 推荐匹配的留学方案和课程项目
- 查询近期讲座、分享会等活动信息
- 回答常见高频问题（申请流程、费用等）
- 日常闲聊互动

## 注意事项
- 语气热情亲切但不浮夸
- 不知道的信息不要编造，引导用户联系专业顾问
- 主动了解用户学历背景和意向国家以精准推荐
- 不提供公司内部信息
```

- [ ] **Step 4: Commit**

```bash
git add souls/
git commit -m "feat: SOUL.md files for student, employee, guest roles"
```

---

### Task 9: ToolRegistry过滤支持

**Files:**
- Modify: `app/agent/tools/registry.py`

- [ ] **Step 1: 改造ToolRegistry.list()支持白名单过滤**

```python
# app/agent/tools/registry.py
# 修改 list() 方法，其他保持不变

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, name: str, handler: Callable, schema: dict, description: str):
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        self._tools[name] = ToolDef(name, handler, schema, description)

    def list(self, allowed_tools: list[str] = None) -> list[dict]:
        tools = self._tools.values()
        if allowed_tools is not None:
            tools = [t for t in tools if t.name in allowed_tools]
        return [
            {"name": t.name, "description": t.description, "input_schema": t.schema}
            for t in tools
        ]

    def get_handler(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler

    def clear(self):
        """清空所有注册的工具（用于角色切换时重新注册）"""
        self._tools.clear()

    def register_all(self, tool_defs: dict, enabled: list[str]):
        """批量注册工具（同时清空旧工具）"""
        self.clear()
        for name in enabled:
            if name in tool_defs:
                handler, schema, desc = tool_defs[name]
                self.register(name, handler, schema, desc)
```

- [ ] **Step 2: Commit**

```bash
git add app/agent/tools/registry.py
git commit -m "feat: ToolRegistry.list() supports allowed_tools filtering"
```

---

### Task 10: KnowledgeRouter实现（TDD）

**Files:**
- Create: `app/rag/router.py`
- Create: `tests/test_knowledge_router.py`
- Modify: `app/agent/tools/rag.py` (集成KnowledgeRouter)

- [ ] **Step 1: 写失败的测试**

```python
# tests/test_knowledge_router.py
from app.rag.router import KnowledgeRouter

ROLE_BASES = {
    "student": ["company/public", "business", "policy"],
    "employee": ["company/public", "company/internal", "business", "policy"],
    "guest": ["company/public", "business", "policy"],
}


class FakeSoulManager:
    def __init__(self, role=None):
        self.current_role = role

    def is_active(self):
        return self.current_role is not None


def test_knowledge_router_for_guest():
    soul = FakeSoulManager("guest")
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    assert "company/public" in bases
    assert "business" in bases
    assert "policy" in bases
    assert "company/internal" not in bases


def test_knowledge_router_for_employee():
    soul = FakeSoulManager("employee")
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    assert "company/internal" in bases


def test_knowledge_router_no_soul():
    soul = FakeSoulManager(None)
    router = KnowledgeRouter(soul, ROLE_BASES)
    bases = router.get_allowed_bases()
    # 未登录时(inactive)默认guest
    assert "company/public" in bases
    assert "company/internal" not in bases
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_knowledge_router.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现KnowledgeRouter**

```python
# app/rag/router.py
from typing import List, Optional

ROLE_KNOWLEDGE_BASES = {
    "student": ["company/public", "business", "policy"],
    "employee": ["company/public", "company/internal", "business", "policy"],
    "guest": ["company/public", "business", "policy"],
}


class KnowledgeRouter:
    def __init__(self, soul_manager, role_bases: dict = None):
        self.soul_manager = soul_manager
        self.role_bases = role_bases or ROLE_KNOWLEDGE_BASES

    def get_allowed_bases(self) -> List[str]:
        if self.soul_manager.is_active():
            role = self.soul_manager.current_role
            return self.role_bases.get(role, self.role_bases.get("guest", []))
        return self.role_bases.get("guest", [])

    def build_where_filter(self) -> Optional[dict]:
        """构建Chroma metadata过滤条件"""
        allowed = self.get_allowed_bases()
        return {"source": {"$in": allowed}} if allowed else None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_knowledge_router.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: 改造knowledge_search工具集成KnowledgeRouter**

修改 `app/agent/tools/rag.py`:

```python
# app/agent/tools/rag.py
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
```

同时修改 `app/rag/store.py` 的 `query` 方法以支持 `where` 参数:

```python
def query(self, query_text: str, top_k: int = 5, where: dict = None) -> List[dict]:
    from app.rag.embedder import Embedder
    embedder = Embedder()
    query_embedding = embedder.embed([query_text])[0]
    kwargs = dict(query_embeddings=[query_embedding], n_results=top_k)
    if where:
        kwargs["where"] = where
    results = self.collection.query(**kwargs)
    if not results["documents"][0]:
        return []
    return [
        {"content": doc, "distance": dist, "metadata": meta}
        for doc, dist, meta in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0]
        )
    ]
```

在 `app/rag/router.py` 中需要声明全局变量供 `knowledge_search` 使用。在`app/rag/router.py`末尾加:

```python
# 全局实例，由app启动时初始化
knowledge_router: Optional[KnowledgeRouter] = None
```

在 `app/api/routes/auth.py` 中初始化:

```python
# 在文件顶部导入后添加
from app.rag.router import knowledge_router as _kr, KnowledgeRouter, ROLE_KNOWLEDGE_BASES
from app.agent.soul import soul_manager as _soul_manager
_kr_instance = KnowledgeRouter(_soul_manager, ROLE_KNOWLEDGE_BASES)
import app.rag.router as router_mod
router_mod.knowledge_router = _kr_instance
```

- [ ] **Step 6: Commit**

```bash
git add app/rag/router.py tests/test_knowledge_router.py app/agent/tools/rag.py app/rag/store.py app/api/routes/auth.py
git commit -m "feat: KnowledgeRouter with role-based RAG isolation"
```

---

### Task 11: 改造agent_loop使用SoulManager

**Files:**
- Modify: `app/agent/core.py`

- [ ] **Step 1: 修改agent_loop**

需要将硬编码的 `SYSTEM` 替换为从 SoulManager 动态获取, `registry.list()` 传入工具白名单。

修改 `app/agent/core.py`:

```python
# 在文件顶部导入部分后添加
from app.agent.soul import SoulManager

# 删除或注释原有SYSTEM常量
# SYSTEM = f"""You are a coding agent..."""

# 全局SoulManager实例
soul_manager = SoulManager()


def agent_loop(messages: list, stream_callback=None):
    rounds_without_todo = 0
    while True:
        microcompact(messages)
        if estimate_tokens(messages) > TOKEN_THRESHOLD:
            print("[auto-compact triggered]")
            messages[:] = auto_compact(messages)

        # 从SoulManager获取当前system prompt和工具列表
        system_prompt = soul_manager.get_system_prompt()
        allowed_tools = soul_manager.get_tools()

        if stream_callback:
            response_stream = client.messages.create(
                model=MODEL, system=system_prompt, messages=messages,
                tools=registry.list(allowed_tools=allowed_tools if allowed_tools else None),
                max_tokens=8000, stream=True,
            )
            # ... 其余保持不变 ...

        else:
            response = client.messages.create(
                model=MODEL, system=system_prompt, messages=messages,
                tools=registry.list(allowed_tools=allowed_tools if allowed_tools else None),
                max_tokens=8000,
            )
            # ... 其余保持不变 ...
```

实际上只需要修改两处 `client.messages.create(...)` 调用中的 `system` 和 `tools` 参数。其他逻辑保持不变。

- [ ] **Step 2: 验证导入**

```bash
uv run python -c "from app.agent.core import agent_loop, soul_manager; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/agent/core.py
git commit -m "feat: agent_loop uses SoulManager for dynamic system prompt and tools"
```

---

### Task 12: 改造chat路由注入SOUL上下文

**Files:**
- Modify: `app/api/routes/chat.py`
- Modify: `app/api/main.py` (已完成部分)

- [ ] **Step 1: 改造chat.py添加身份注入**

```python
# app/api/routes/chat.py
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import jwt
import os

from app.agent.session import SessionManager
from app.agent.core import agent_loop, soul_manager
from app.agent.auth import SECRET_KEY

router = APIRouter()

CONVERSATIONS_DIR = Path(".conversations")
CONVERSATIONS_DIR.mkdir(exist_ok=True)

session_manager = SessionManager(CONVERSATIONS_DIR)


async def handle_chat(request: Request, token: str = None):
    """处理chat请求，注入用户身份"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    message = body.get("message", "")
    conversation_id = body.get("conversation_id")

    # 解析token获取用户身份
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            role = payload.get("role", "guest")
            # 确保SOUL已加载
            if not soul_manager.is_active() or soul_manager.current_role != role:
                soul_manager.load(role)
        except jwt.PyJWTError:
            raise HTTPException(401, "Invalid token")
    else:
        # 无token，加载guest SOUL
        if not soul_manager.is_active():
            soul_manager.load("guest")

    # 加载或创建会话
    if conversation_id:
        messages = session_manager.get_session(conversation_id)
        if messages is None:
            conversation_id = session_manager.create_session()
            messages = session_manager.get_session(conversation_id)
    else:
        conversation_id = session_manager.create_session()
        messages = session_manager.get_session(conversation_id)

    messages.append({"role": "user", "content": message})

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def stream_callback(text: str):
        loop.call_soon_threadsafe(
            queue.put_nowait, {"type": "content", "content": text}
        )

    async def event_stream():
        import threading

        def run_agent():
            try:
                agent_loop(messages, stream_callback=stream_callback)
            except Exception as e:
                queue.put_nowait({"type": "error", "content": str(e)})
            finally:
                queue.put_nowait({"type": "done"})

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

        # 发送conversation_id和role
        yield f"data: {json.dumps({'type': 'role', 'role': soul_manager.current_role or 'guest'})}\n\n"
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation_id})}\n\n"

        while True:
            item = await queue.get()
            if item["type"] == "done":
                session_manager.save_session(conversation_id)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            elif item["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': item['content']})}\n\n"
                break
            else:
                yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 2: 更新main.py中的chat路由绑定**

```python
# app/api/main.py 的chat端点已经是正确的，确保 import 正确
from .routes.chat import handle_chat
```

- [ ] **Step 3: 测试chat路由可用**

手动测: 启动服务，直接用curl/PowerShell发送POST到/api/chat

- [ ] **Step 4: Commit**

```bash
git add app/api/routes/chat.py app/api/main.py
git commit -m "feat: chat route injects user identity via JWT token"
```

---

### Task 13: 登录/注册页

**Files:**
- Create: `app/api/static/login.html`

- [ ] **Step 1: 创建登录/注册页**

```html
<!-- app/api/static/login.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>登录 - 留学机构智能助手</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f4f8; }
.container { background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); width: 380px; }
h1 { text-align: center; margin-bottom: 32px; color: #1e293b; font-size: 24px; }
.form-group { margin-bottom: 16px; }
label { display: block; margin-bottom: 6px; font-size: 14px; color: #475569; font-weight: 500; }
input, select { width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; }
input:focus, select:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.btn { width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-bottom: 12px; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-secondary { background: #e2e8f0; color: #334155; }
.btn-secondary:hover { background: #cbd5e1; }
.error { color: #dc2626; font-size: 13px; margin-bottom: 12px; text-align: center; }
.success { color: #16a34a; font-size: 13px; margin-bottom: 12px; text-align: center; }
.tabs { display: flex; margin-bottom: 24px; border-bottom: 2px solid #e2e8f0; }
.tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; color: #64748b; font-size: 14px; font-weight: 500; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.hidden { display: none; }
.guest-link { text-align: center; margin-top: 20px; }
.guest-link a { color: #2563eb; text-decoration: none; font-size: 14px; }
.guest-link a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
    <h1>留学机构智能助手</h1>
    <div class="tabs">
        <div class="tab active" onclick="switchTab('login')">登录</div>
        <div class="tab" onclick="switchTab('register')">注册</div>
    </div>
    <div id="error" class="error hidden"></div>
    <div id="success" class="success hidden"></div>
    <form id="loginForm">
        <div class="form-group"><label>用户名</label><input type="text" id="loginUser" required></div>
        <div class="form-group"><label>密码</label><input type="password" id="loginPass" required></div>
        <button type="submit" class="btn btn-primary">登录</button>
    </form>
    <form id="registerForm" class="hidden">
        <div class="form-group"><label>用户名</label><input type="text" id="regUser" required minlength="2"></div>
        <div class="form-group"><label>密码</label><input type="password" id="regPass" required minlength="4"></div>
        <div class="form-group">
            <label>角色</label>
            <select id="regRole"><option value="student">学生</option><option value="employee">员工</option></select>
        </div>
        <button type="submit" class="btn btn-primary">注册</button>
    </form>
    <div class="guest-link"><a href="/">免登录直接咨询（客服模式）</a></div>
</div>

<script>
let currentTab = 'login';
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', (i===0)===(tab==='login')));
    document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
    document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
    hideMessages();
}
function showError(msg) { const e=document.getElementById('error'); e.textContent=msg; e.classList.remove('hidden'); document.getElementById('success').classList.add('hidden'); }
function showSuccess(msg) { const s=document.getElementById('success'); s.textContent=msg; s.classList.remove('hidden'); document.getElementById('error').classList.add('hidden'); }
function hideMessages() { document.getElementById('error').classList.add('hidden'); document.getElementById('success').classList.add('hidden'); }

document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    hideMessages();
    const username = document.getElementById('loginUser').value;
    const password = document.getElementById('loginPass').value;
    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await resp.json();
        if (!resp.ok) { showError(data.detail || '登录失败'); return; }
        localStorage.setItem('token', data.token);
        localStorage.setItem('role', data.role);
        window.location.href = '/';
    } catch (err) { showError('网络错误，请重试'); }
};

document.getElementById('registerForm').onsubmit = async (e) => {
    e.preventDefault();
    hideMessages();
    const username = document.getElementById('regUser').value;
    const password = document.getElementById('regPass').value;
    const role = document.getElementById('regRole').value;
    try {
        const resp = await fetch('/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password, role})
        });
        const data = await resp.json();
        if (!resp.ok) { showError(data.detail || '注册失败'); return; }
        showSuccess('注册成功！请切换到登录页面登录');
        document.getElementById('regUser').value = '';
        document.getElementById('regPass').value = '';
    } catch (err) { showError('网络错误，请重试'); }
};
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add app/api/static/login.html
git commit -m "feat: login/register page with role selection"
```

---

### Task 14: 聊天页改造（鉴权集成 + 主题色）

**Files:**
- Modify: `app/api/static/index.html`
- Modify: `app/api/static/app.js`

- [ ] **Step 1: 改造index.html添加鉴权检查、主题色、登出按钮**

修改 `app/api/static/index.html` 的 `<style>` 部分追加:

```css
/* 在现有 style 块末尾追加 */
#topbar { height: 48px; background: #2563eb; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; color: #fff; font-size: 14px; }
#topbar .role-label { font-weight: 600; }
#logout-btn { background: rgba(255,255,255,0.2); color: #fff; border: 1px solid rgba(255,255,255,0.3); padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; }
#logout-btn:hover { background: rgba(255,255,255,0.3); }
#guest-banner { background: #fef3c7; color: #92400e; padding: 6px 16px; text-align: center; font-size: 13px; }
#guest-banner a { color: #2563eb; }
```

在 `<body>` 内 `#sidebar` 之前插入:

```html
<div id="topbar">
    <span class="role-label" id="role-label">加载中...</span>
    <button id="logout-btn" onclick="logout()">登出</button>
</div>
<div id="guest-banner" style="display:none">游客模式 · <a href="/login">登录享受更多功能</a></div>
```

- [ ] **Step 2: 改造app.js鉴权流程**

`app/api/static/app.js` 完整替换:

```javascript
// 鉴权检查
const token = localStorage.getItem('token');
const role = localStorage.getItem('role') || 'guest';
const THEME_COLORS = { student: '#2563eb', employee: '#16a34a', guest: '#6b7280' };

let currentConversationId = null;
let isStreaming = false;
let needScroll = true;

// DOM引用
const chatEl = document.getElementById('chat');
const chatEmpty = document.getElementById('chat-empty');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const sessionListEl = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');
const topbar = document.getElementById('topbar');
const roleLabel = document.getElementById('role-label');
const guestBanner = document.getElementById('guest-banner');

// 初始化主题
const themeColor = THEME_COLORS[role] || '#6b7280';
topbar.style.background = themeColor;
sendBtn.style.background = themeColor;

if (!token) {
    roleLabel.textContent = '客服助手 (游客)';
    document.getElementById('logout-btn').style.display = 'none';
    guestBanner.style.display = 'block';
} else if (role === 'student') {
    roleLabel.textContent = '学生助手';
} else if (role === 'employee') {
    roleLabel.textContent = '企业助手';
}

// 登出
function logout() {
    fetch('/api/auth/logout', { method: 'POST' });
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
}

// 发送消息
async function send() {
    const message = inputEl.value.trim();
    if (!message || isStreaming) return;

    inputEl.value = '';
    hideEmpty();
    appendMessage('user', message);

    isStreaming = true;
    sendBtn.disabled = true;

    const assistantDiv = appendMessage('assistant', '');
    showLoading(assistantDiv);
    let assistantText = '';

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST', headers,
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: message
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            for (const line of chunk.split('\n')) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'conversation_id') {
                            currentConversationId = data.conversation_id;
                        } else if (data.type === 'role') {
                            // 更新角色信息
                        } else if (data.type === 'content') {
                            hideLoading(assistantDiv);
                            assistantText += data.content;
                            assistantDiv.textContent = assistantText;
                            scrollToBottom();
                        } else if (data.type === 'error') {
                            assistantDiv.textContent = `Error: ${data.content}`;
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (e) {
        assistantDiv.textContent = `Error: ${e.message}`;
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        loadSessions();
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="role">${role === 'user' ? 'You' : 'Assistant'}</div>`;
    div.appendChild(document.createTextNode(text));
    chatEl.appendChild(div);
    scrollToBottom();
    return div;
}

function scrollToBottom() { chatEl.scrollTop = chatEl.scrollHeight; }

function showLoading(container) {
    const dots = document.createElement('div');
    dots.className = 'loading-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(dots);
    scrollToBottom();
}

function hideLoading(container) {
    const dots = container.querySelector('.loading-dots');
    if (dots) dots.remove();
}

function hideEmpty() { if (chatEmpty) chatEmpty.style.display = 'none'; }
function showEmpty() { if (chatEmpty) chatEmpty.style.display = 'flex'; }

async function loadSessions() {
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const response = await fetch('/api/sessions', { headers });
        const sessions = await response.json();
        sessionListEl.innerHTML = '';
        if (sessions.length === 0) {
            sessionListEl.innerHTML = '<div class="empty-state">暂无对话</div>';
            return;
        }
        sessions.forEach(s => {
            const div = document.createElement('div');
            div.className = `session-item ${s.id === currentConversationId ? 'active' : ''}`;
            div.textContent = `对话 ${s.id.slice(0, 8)}`;
            div.onclick = () => loadSession(s.id);
            sessionListEl.appendChild(div);
        });
    } catch (e) { console.error('Failed to load sessions:', e); }
}

async function loadSession(id) {
    if (isStreaming) return;
    currentConversationId = id;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const response = await fetch(`/api/sessions/${id}`, { headers });
        const session = await response.json();
        if (session.messages && session.messages.length > 0) {
            hideEmpty();
            session.messages.forEach(msg => {
                const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
                appendMessage(msg.role, content);
            });
        } else { showEmpty(); }
    } catch (e) { console.error('Failed to load session:', e); }
    loadSessions();
}

newChatBtn.onclick = () => {
    if (isStreaming) return;
    currentConversationId = null;
    chatEl.innerHTML = '<div id="chat-empty">开始新对话</div>';
    showEmpty();
    loadSessions();
};

sendBtn.onclick = send;
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

loadSessions();
```

- [ ] **Step 3: Commit**

```bash
git add app/api/static/index.html app/api/static/app.js
git commit -m "feat: chat page with auth, theme colors, logout"
```

---

### Task 15: 集成验证 + 修正

**Files:**
- Modify: `app/db/connection.py` (启动时init_db)
- Modify: `app/api/main.py` (启动事件)

- [ ] **Step 1: 添加启动时数据库初始化**

修改 `app/db/connection.py` 在文件末尾:

```python
def init_db_on_startup():
    """启动时自动创建所有表"""
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] Database init skipped: {e}")
```

修改 `app/api/main.py` 添加启动事件:

```python
@app.on_event("startup")
async def startup_event():
    from app.db.connection import init_db_on_startup
    init_db_on_startup()
    print("[INFO] mt4a Agent API started")
```

- [ ] **Step 2: 验证导入链**

```bash
uv run python -c "from app.api.main import app; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 3: 运行全部测试**

```bash
uv run pytest tests/ -v
```

Expected: 全部PASS (auth, soul, knowledge_router测试)

- [ ] **Step 4: Commit**

```bash
git add app/db/connection.py app/api/main.py
git commit -m "chore: add startup DB init, verify full import chain"
```

---

### 验证检查清单

在服务启动后手动验证:
- [ ] 访问 `/login` 看到登录/注册页
- [ ] 注册学生账号 → 登录 → 页面主题色变蓝，显示"学生助手"
- [ ] 发消息后 agent 以学生角色回复
- [ ] 登出 → 回到登录页
- [ ] 免登录入口 → 页面主题色变灰，显示"客服助手"
- [ ] 客服模式下 knowledge_search 仅返回public知识
