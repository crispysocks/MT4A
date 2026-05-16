# mt4a 项目架构审查报告

> 生成时间: 2026-05-16
> 项目路径: D:\Projects-dev\mt4a
> 用途: 供后续开发参考，快速理解系统全貌

---

## 一、项目概述与设计理念

### 1.1 核心创新点：单Agent + SOUL注入

用户视角看到多个不同的Agent（学生助手、企业助手、客服），但底层是**同一个 `agent_loop` 实例**，通过加载不同的 `SOUL.md` 动态切换认知、功能和服务方向。

```
souls/student/SOUL.md   → 学生Agent人格
souls/employee/SOUL.md  → 员工Agent人格
souls/guest/SOUL.md     → 客服Agent人格
```

SOUL.md 仅包含**系统提示词 + 工具白名单**，不包含框架层信息（知识库范围、数据库连接等），避免污染大模型认知。

### 1.2 技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web框架 + SSE流式 |
| SQLModel + MySQL | ORM + 数据库 |
| Anthropic SDK | LLM调用 |
| Chroma + DashScope | 向量存储 + 嵌入 |
| PyJWT + bcrypt | JWT鉴权 + 密码哈希 |
| uvicorn | ASGI服务器 |

---

## 二、整体数据流

```
用户输入 "查询成绩"
    ↓
POST /api/chat (chat.py:21-100)
    ↓ JWT解析 → soul_manager.load("student")
    ↓ 获取messages (新建或从磁盘恢复)
    ↓ messages.append({"role": "user", "content": "查询成绩"})
    ↓
agent_loop(messages, stream_callback) (core.py:163-319)
    ↓
client.messages.create(
    system=soul_manager.get_system_prompt()  ← "你是留学机构学生助手..."
    tools=registry.list(allowed_tools=["knowledge_search","db_query","TodoWrite","compress"])
    messages=messages
)
    ↓
LLM返回 tool_use: db_query
    ↓
registry.get_handler("db_query") → db_query(operation="select", table="student_grades", ...)
    ↓
结果写入messages: {"role": "user", "content": [{"type": "tool_result", ...}]}
    ↓
再次LLM调用（如果stop_reason=="tool_use"则继续循环）
    ↓
最终assistant text → SSE stream → 前端
    ↓
session_manager.save_session() → .conversations/{id}.json
```

---

## 三、系统提示词（System Prompt）

### 3.1 来源与优先级

| 来源 | 说明 | 优先级 |
|------|------|--------|
| `SoulManager.get_system_prompt()` | 来自SOUL.md的正文 | **实际使用** |
| `core.py` 的 `SYSTEM` 常量 | 硬编码的默认提示词 | **废弃未用** |

**重要**：`core.py:155-157` 定义了一个废弃的 `SYSTEM` 常量：

```python
SYSTEM = f"""You are a coding agent at {WORKDIR}. Use tools to solve tasks.
Use TodoWrite for short checklists. Use load_skill for specialized knowledge.
Skills: {SKILLS.descriptions()}"""
```

这个变量**从未被 `agent_loop` 使用**。所有 `client.messages.create()` 调用都改用了 `soul_manager.get_system_prompt()`。该常量应删除避免混淆。

### 3.2 SOUL.md 格式

```markdown
---
name: 学生智能助手
role: student
tools: [knowledge_search, db_query, TodoWrite, compress]
---

你是一个留学机构的学生智能助手。你的服务对象是留学生，你需要用亲切、友好的语气与他们沟通。

## 你的能力
- 查询留学政策（各国签证、院校申请要求）
- 查询课程和升学项目信息
...

## 注意事项
- 始终保持友善、耐心的态度
...
```

格式规则：
- Frontmatter (YAML) 解析 `---` 分隔符
- `tools:` 字段为列表格式：`[tool_a, tool_b]`
- 正文为 system prompt，直接传给 LLM

### 3.3 三个SOUL文件内容概览

| 文件 | 角色定位 | tools白名单 |
|------|---------|------------|
| `souls/student/SOUL.md` | 亲切友好的留学生助手 | knowledge_search, db_query, TodoWrite, compress |
| `souls/employee/SOUL.md` | 专业高效的企业内部助手 | knowledge_search, db_query, TodoWrite, compress |
| `souls/guest/SOUL.md` | 热情对外的客服咨询 | knowledge_search, TodoWrite, compress |

---

## 四、用户提示词（User Prompt）

用户发送的消息直接追加到 `messages` 列表：

```python
messages.append({"role": "user", "content": message})  # chat.py:60
```

工具执行结果也作为 `user` 消息追加：

```python
messages.append({"role": "user", "content": results})  # core.py:275
```

其中 `results` 格式为：
```python
[
  {"type": "tool_result", "tool_use_id": "tool_1", "content": "..."},
  {"type": "tool_result", "tool_use_id": "tool_2", "content": "..."},
]
```

---

## 五、工具系统（Tool Registry）

### 5.1 架构

```
app/agent/tools/__init__.py   ← 工具注册入口（模块加载时执行）
    ├── ENABLED_TOOLS         ← 白名单列表
    ├── _TOOL_DEFS            ← 所有工具定义 (name → handler, schema, description)
    └── registry.register()   ← 注册到全局 registry 实例

app/agent/tools/registry.py   ← ToolRegistry 类
    ├── _tools: dict[str, ToolDef]
    ├── list(allowed_tools)    ← 按白名单过滤
    ├── get_handler(name)      ← 获取handler
    ├── clear()                ← 清空（角色切换时）
    └── register_all()         ← 批量注册
```

### 5.2 工具注册时机

模块 `import` 时自动执行（`__init__.py:119-122`）：

```python
for _name in ENABLED_TOOLS:
    if _name in _TOOL_DEFS:
        _handler, _schema, _desc = _TOOL_DEFS[_name]
        registry.register(_name, _handler, _schema, _desc)
```

### 5.3 当前注册的工具（共6个）

| 工具名 | Handler | 功能 | schema |
|--------|---------|------|--------|
| `read_file` | `file.run_read` | 读文件（limit行数） | `{path, limit?}` |
| `knowledge_search` | `rag.knowledge_search` | RAG知识库检索 | `{query, top_k?}` |
| `db_query` | `db.db_query` | CRUD数据库（14表） | `{operation, table, conditions?, data?}` |
| `TodoWrite` | `_todo_write_handler` | 更新TODO列表 | `{items: [{content,status,activeForm}]}` |
| `load_skill` | `_load_skill_handler` | 加载SKILL.md | `{name}` |
| `compress` | `_compress_handler` | 触发上下文压缩 | `{}` |

`ENABLED_TOOLS` 定义于 `app/agent/tools/__init__.py:11-21`：

```python
ENABLED_TOOLS = [
    "read_file",
    "knowledge_search",
    "db_query",
    "TodoWrite",
    "load_skill",
    "compress",
]
```

注意：`bash`, `write_file`, `edit_file` 虽然在 `_TOOL_DEFS` 中定义，但不在 `ENABLED_TOOLS` 中，因此未注册。

### 5.4 工具白名单过滤机制

`registry.list(allowed_tools=None)` (`registry.py:20-27`)：

```python
def list(self, allowed_tools: list[str] = None) -> list[dict]:
    tools = self._tools.values()
    if allowed_tools is not None:
        tools = [t for t in tools if t.name in allowed_tools]
    return [{"name": t.name, "description": t.description, "input_schema": t.schema}
            for t in tools]
```

在 `agent_loop` 中的调用 (`core.py:181-182`)：

```python
tools=registry.list(allowed_tools=soul_manager.get_tools() or None)
```

`SoulManager.get_tools()` 从 SOUL.md 的 `tools:` 字段读取列表。

### 5.5 工具调用处理流程

```python
for block in content_blocks:
    if block["type"] == "tool_use":
        handler = registry.get_handler(block["name"])
        output = handler(**block["input"])
        results.append({"type": "tool_result", "tool_use_id": block["id"], "content": str(output)})
        if block["name"] == "TodoWrite":
            used_todo = True

messages.append({"role": "user", "content": results})
```

### 5.6 工具白名单与注册工具的交集验证缺失

**风险**：`soul_manager.get_tools()` 返回的列表中，如果包含未注册的工具名，`registry.list()` 会自动忽略（因为没有匹配的 ToolDef）。LLM会看到工具列表为空，导致无法调用任何工具。应该加校验：当 SOUL 加载时，验证白名单中的工具是否都已在 registry 中注册。

---

## 六、单轮会话循环（Single Turn）

每轮循环 = 1次LLM调用 + 0~N次工具调用：

```
messages [user msg]
    ↓
LLM → assistant (tool_use blocks OR text)
    ↓
if stop_reason != "tool_use":
    → 返回（单轮结束）
else:
    → 工具1 → tool_result
    → 工具2 → tool_result
    → messages [assistant, user(tool_results)]
    → 继续循环
```

`stop_reason` 来自 Anthropic API 响应：
- `"end_turn"` → 无工具调用，单轮结束
- `"tool_use"` → 有工具调用，继续循环

---

## 七、多轮对话管理（Multi-turn）

### 7.1 消息累积结构

```python
[
  {"role": "user", "content": "帮我查一下张三的成绩"},
  {"role": "assistant", "content": [{"type": "tool_use", "id": "tool_1", "name": "db_query", "input": {...}}]},
  {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tool_1", "content": "[{...}]"}]},
  {"role": "assistant", "content": [{"type": "text", "text": "张三的数学成绩是A..."}]},
]
```

`messages` 列表在内存中累积，每次 LLM 调用都传递完整历史。

### 7.2 上下文压缩

两种压缩策略，按 token 阈值触发：

**微压缩**（每轮检查，`core.py:117-128`）：
```python
def microcompact(messages: list):
    indices = [tool_result parts...]
    if len(indices) <= 3: return
    for part in indices[:-3]:
        if len(part["content"]) > 100:
            part["content"] = "[cleared]"
```
触发条件：超过3个 tool_result 时，保留最后3个，清空其余的。

**自动压缩**（>100K token，`core.py:131-146`）：
```python
def auto_compact(messages: list) -> list:
    # 保存完整历史到 .transcripts/transcript_{timestamp}.jsonl
    # 用LLM生成摘要，替换messages为 [{"role": "user", "content": "[Compressed...]"}]
```
触发条件：`estimate_tokens(messages) > 100_000`

### 7.3 会话持久化（SessionManager）

| 操作 | 说明 |
|------|------|
| `create_session()` | 生成UUID，创建空messages列表 |
| `get_session(id)` | 内存命中则返回；否则从 `.conversations/{id}.json` 读取 |
| `save_session(id)` | 每次交互结束后写入磁盘 |
| `list_sessions()` | 返回所有会话的元数据列表（按更新时间倒序） |

持久化格式（`.conversations/{id}.json`）：
```json
{
  "id": "uuid",
  "model": "qwen3.6-plus",
  "messages": [...],
  "created_at": "...",
  "updated_at": "..."
}
```

### 7.4 多SessionManager实例问题

**风险**：`app/api/routes/chat.py` 和 `app/api/routes/sessions.py` 分别创建了自己的 `SessionManager` 实例：

```python
# chat.py:18
session_manager = SessionManager(CONVERSATIONS_DIR)

# sessions.py:9
session_manager = SessionManager(CONVERSATIONS_DIR)
```

两者都指向同一个 `.conversations/` 目录，但内存不共享。可能导致：
- chat写入的会话，sessions读取不到最新状态（需等磁盘同步）
- 内存缓存失效，重复从磁盘加载

**建议**：共用同一个单例实例。

---

## 八、RAG知识库与KnowledgeRouter

### 8.1 知识库结构

```
knowledge/
├── raw/                      # 原始文档
│   ├── 公司信息/             # 企业信息.md, 常见问答对.md, 公司新人指南.md
│   ├── 公司业务/             # 中德精英人才共建计划.md, 新加坡国际本硕升学计划.md
│   └── 留学政策/             # 德国留学政策指南.md, 新加坡留学政策指南.md
└── processed/               # 已预处理分片
    ├── company/             # brand.md, campuses.md, faq.md, history.md
    ├── business/            # study_abroad.md, enhancement.md
    └── policy/             # germany.md, singapore.md
```

### 8.2 知识库分层与角色映射

| 层级 | 内容 | student | employee | guest |
|------|------|---------|----------|-------|
| `company/public` | 品牌、校区、对外FAQ | ✓ | ✓ | ✓ |
| `company/internal` | 新人指南、内部制度 | ✗ | ✓ | ✗ |
| `business` | 升学计划、项目 | ✓ | ✓ | ✓ |
| `policy` | 留学政策 | ✓ | ✓ | ✓ |

### 8.3 KnowledgeRouter 实现

```python
# app/rag/router.py

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
        allowed = self.get_allowed_bases()
        return {"source": {"$in": allowed}} if allowed else None

# 全局实例（未初始化！）
knowledge_router: Optional[KnowledgeRouter] = None
```

### 8.4 关键问题：KnowledgeRouter全局实例未初始化

`app/rag/router.py:27` 定义了 `knowledge_router = None`，但在 `app/agent/tools/rag.py:2` 导入：

```python
from app.rag.router import knowledge_router

def knowledge_search(query: str, top_k: int = 5) -> str:
    store = get_store()
    where_filter = knowledge_router.build_where_filter() if knowledge_router else None
    ...
```

由于 `knowledge_router` 始终为 `None`（从未被初始化），`build_where_filter()` 不生效，RAG 检索**没有按角色隔离**，所有知识库内容都会被返回。

**需要修复**：在 app 启动时初始化 `knowledge_router`：

```python
# app/api/main.py startup_event 中
from app.agent.soul import soul_manager
from app.rag.router import KnowledgeRouter, ROLE_KNOWLEDGE_BASES

router_mod = importlib.import_module('app.rag.router')
router_mod.knowledge_router = KnowledgeRouter(soul_manager, ROLE_KNOWLEDGE_BASES)
```

---

## 九、AuthManager与JWT鉴权

### 9.1 鉴权流程

```
用户登录 → POST /api/auth/login
    ↓
AuthManager.login(username, password)
    ↓
bcrypt验证密码 → 生成JWT token
    ↓
soul_manager.load(role)  ← 登录成功后加载对应SOUL
    ↓
返回 {token, role} 给前端
    ↓
前端存储localStorage，后续请求携带 Authorization: Bearer {token}
```

### 9.2 JWT payload结构

```python
{
    "user_id": 1,
    "username": "zhangsan",
    "role": "student",
    "exp": datetime + 24h
}
```

### 9.3 Chat路由中的SOUL注入逻辑

```python
# chat.py:31-48
token = None
auth_header = request.headers.get("Authorization", "")
if auth_header.startswith("Bearer "):
    token = auth_header[7:]

if token:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    role = payload.get("role", "guest")
    if not soul_manager.is_active() or soul_manager.current_role != role:
        soul_manager.load(role)
else:
    if not soul_manager.is_active():
        soul_manager.load("guest")
```

关键逻辑：
- 有token → 解码获取role → 加载对应SOUL（避免重复加载）
- 无token → 加载guest SOUL（客服免登录）
- SOUL跟随token中的role，**不与会话绑定**

### 9.4 AuthManager方法

| 方法 | 说明 |
|------|------|
| `register(username, password, role)` | 创建用户（bcrypt加密），返回User对象 |
| `login(username, password)` | 验证后返回 `(token, role)` |
| `verify(token)` | 解码JWT，返回payload dict |

---

## 十、数据库模型

### 10.1 模型总览

| 模型 | 表名 | 用途 |
|------|------|------|
| `Course` | courses | 课程项目 |
| `Event` | events | 活动/讲座 |
| `Registration` | registrations | 活动报名 |
| `User` | users | 用户认证（student/employee角色） |
| `Lead` | leads | 意向客户 |
| `LeadFollowUp` | lead_follow_ups | 客户跟进记录 |
| `DailyReport` | daily_reports | 员工日报 |
| `Complaint` | complaints | 投诉反馈 |
| `Organization` | organization | 组织架构 |
| `StudentGrade` | student_grades | 学生成绩 |
| `LeaveRequest` | leave_requests | 请假申请 |
| `ExamSchedule` | exam_schedule | 考务/DDL |
| `PsychologyProfile` | psychology_profiles | 心理健康画像 |
| `PsychologyWarning` | psychology_warnings | 心理预警 |

### 10.2 db_query工具支持的表

```python
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

---

## 十一、关键问题汇总

| # | 问题 | 严重程度 | 影响 |
|---|------|---------|------|
| 1 | `core.py` 的 `SYSTEM` 常量废弃未删除 | 低 | 混淆开发者，应删除 |
| 2 | `knowledge_router` 全局实例未初始化 | **高** | RAG隔离功能完全不工作，所有用户看到相同知识库 |
| 3 | SOUL工具白名单未验证交集 | 中 | 如果SOUL写了不存在的工具名，工具列表为空 |
| 4 | 多个SessionManager实例 | 中 | 会话状态可能不一致 |
| 5 | load_skill工具依赖旧SkillLoader | 低 | `skills/` 目录可能不存在，但工具仍注册；三个SOUL都没有包含load_skill所以不可见 |

---

## 十二、文件结构总览

```
D:\Projects-dev\mt4a\
├── app/
│   ├── api/
│   │   ├── main.py              # FastAPI入口，注册路由，CORS，启动事件
│   │   ├── routes/
│   │   │   ├── auth.py          # /api/auth/register, /login, /logout, /me
│   │   │   ├── chat.py          # /api/chat (SSE流式，SOUL注入入口)
│   │   │   └── sessions.py      # /api/sessions, /api/sessions/{id}
│   │   └── static/
│   │       ├── index.html       # 聊天页（深色侧边栏，主题色顶部栏）
│   │       ├── login.html       # 登录/注册页（Academic Atlas风格）
│   │       └── app.js           # 前端逻辑（鉴权，主题色，SSE处理）
│   ├── agent/
│   │   ├── core.py              # agent_loop（流式/同步），SYSTEM常量（废弃），TodoManager, SkillLoader
│   │   ├── soul.py              # SoulManager（加载/解析/卸载SOUL.md）
│   │   ├── auth.py              # AuthManager（JWT注册/登录/验证）
│   │   ├── session.py           # SessionManager（内存+磁盘持久化）
│   │   └── tools/
│   │       ├── __init__.py      # ENABLED_TOOLS, _TOOL_DEFS, registry.register()
│   │       ├── registry.py     # ToolRegistry（list/get_handler/clear/register_all）
│   │       ├── bash.py          # run_bash
│   │       ├── file.py          # run_read, run_write, run_edit
│   │       ├── rag.py           # knowledge_search（集成KnowledgeRouter）
│   │       └── db.py           # db_query（14表CRUD）
│   ├── db/
│   │   ├── models.py            # 14个SQLModel模型
│   │   └── connection.py         # MySQL连接，init_db_on_startup()
│   └── rag/
│       ├── embedder.py          # DashScope embedding
│       ├── store.py             # ChromaStore（query支持where过滤）
│       └── router.py            # KnowledgeRouter（未初始化全局实例）
├── souls/
│   ├── student/SOUL.md
│   ├── employee/SOUL.md
│   └── guest/SOUL.md
├── .conversations/              # 会话持久化（.json文件）
├── .transcripts/                # 压缩后的对话历史
├── tests/                       # 测试（auth, soul, knowledge_router等）
├── docs/superpowers/
│   ├── specs/                   # 设计文档
│   └── plans/                   # 实施计划
└── pyproject.toml               # uv依赖管理
```

---

## 十三、核心流程时序图

```
┌─────────┐      ┌──────────┐      ┌─────────┐      ┌───────────┐      ┌────────┐
│  用户   │      │  前端    │      │ chat.py │      │ SoulManager│      │LLM/工具│
└────┬────┘      └────┬────┘      └────┬────┘      └─────┬─────┘      └────┬───┘
     │ POST /api/chat │             │                 │                │
     │───────────────>│              │                 │                │
     │                │ Bearer token│                │                │
     │                │────────────>│ JWT decode      │                │
     │                │            │ get role        │                │
     │                │            │────────────────>│ load(role)     │
     │                │            │                 │ get_system_prompt
     │                │            │                 │<────────────────│
     │                │            │ get_messages(id) │                │
     │                │            │<────────────────│                │
     │                │            │ append user msg │                │
     │                │            │─────────────────>│             │
     │                │            │                 │ agent_loop()  │
     │                │            │                 │──LLM call─────>│
     │                │            │                 │<──tool_use─────│
     │                │            │                 │ get_handler() │
     │                │            │                 │<──────────────│
     │                │            │                 │ tool result    │
     │                │            │                 │──LLM call─────>│
     │                │            │                 │<──text────────│
     │                │            │<─────────────────│                │
     │                │            │ save_session()  │                │
     │ SSE stream     │<──────────│                │                │
     │                │            │                 │                │
```

---

## 十四、开发建议

1. **立即修复** `knowledge_router` 全局实例初始化问题，使 RAG 角色隔离生效
2. **删除** `core.py` 中废弃的 `SYSTEM` 常量
3. **验证** SOUL工具白名单与ENABLED_TOOLS的交集，在SoulManager.load()时加校验
4. **统一** SessionManager 为单例，避免跨模块状态不一致
5. **清理** 不再使用的 `load_skill` 工具（如果确定不需要）或补充 SKILL.md 文档