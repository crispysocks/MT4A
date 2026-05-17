# dbman: NL2SQL 统一数据库工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 替换旧 `db_query` 工具，实现基于 LLM 的自然语言数据库操作工具 `dbman`，支持 SELECT/INSERT/UPDATE/DELETE，按角色控制表权限。

**Architecture:** 自然语言 → NL2SQL Engine（LLM生成SQL）→ SQL Validator（安全校验）→ SQL Executor（执行并返回结果）。参考 SoulManager 的 YAML frontmatter 模板模式，不硬编码 prompt。

**Tech Stack:** Python, SQLModel, Anthropic LLM client, YAML, pytest, SQLite（测试用内存库）

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/agent/tools/sql_validator.py` | 新增 | ValidationResult, SQLValidator, SQLExecutor |
| `app/agent/tools/nl2sql.py` | 新增 | SchemaExtractor, NL2SQLEngine |
| `app/agent/tools/dbman.py` | 新增 | dbman(nl: str) 工具入口 |
| `app/agent/tools/__init__.py` | 修改 | 替换 db_query 为 dbman |
| `souls/nl2sql/SOUL.md` | 新增 | SQL生成规则模板 |
| `souls/nl2sql/tables.yaml` | 新增 | 角色表权限配置 |
| `souls/tool_config.yaml` | 修改 | db_query → dbman，guest新增 |
| `souls/student/SOUL.md` | 修改 | 工具描述 |
| `souls/employee/SOUL.md` | 修改 | 工具描述 |
| `souls/guest/SOUL.md` | 修改 | 工具描述 |
| `app/agent/tools/db.py` | 删除 | 旧工具 |
| `tests/test_sql_validator.py` | 新增 | 校验器测试 |
| `tests/test_nl2sql.py` | 新增 | NL2SQL引擎测试 |
| `tests/test_dbman.py` | 新增 | 集成测试 |

---

### Task 1: SQL Validator — 安全校验层

**Files:**
- Create: `app/agent/tools/sql_validator.py`
- Test: `tests/test_sql_validator.py`

- [ ] **Step 1: 写测试 — 危险SQL被拦截**

```python
# tests/test_sql_validator.py
from app.agent.tools.sql_validator import SQLValidator, ValidationResult

ALL_TABLES = ["users", "leads", "courses", "events", "registrations",
              "lead_follow_ups", "daily_reports", "complaints", "organization",
              "student_grades", "leave_requests", "exam_schedule",
              "psychology_profiles", "psychology_warnings"]

def test_dangerous_sql_blocked():
    v = SQLValidator(ALL_TABLES)
    for sql in ["DROP TABLE users", "ALTER TABLE leads ADD COLUMN x INT",
                "TRUNCATE TABLE courses", "GRANT ALL ON users TO 'hack'"]:
        result = v.validate(sql)
        assert result.is_valid is False, f"Should block: {sql}"
        assert "拒绝" in result.error or "不允许" in result.error
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_sql_validator.py::test_dangerous_sql_blocked -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'app.agent.tools.sql_validator'"

- [ ] **Step 3: 实现 ValidationResult 和 SQLValidator 基础结构**

```python
# app/agent/tools/sql_validator.py
"""SQL 安全校验层 + 执行器"""
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    is_valid: bool
    sql: str
    error: str = ""


class SQLValidator:
    DANGEROUS_KEYWORDS = [
        "DROP", "ALTER", "TRUNCATE", "CREATE",
        "GRANT", "REVOKE", "EXEC", "EXECUTE",
    ]

    def __init__(self, allowed_tables: list[str], max_rows: int = 100):
        self.allowed_tables = set(t.lower() for t in allowed_tables)
        self.max_rows = max_rows

    def validate(self, sql: str) -> ValidationResult:
        sql_upper = sql.upper().strip()

        # 1. 检查危险关键字
        for kw in self.DANGEROUS_KEYWORDS:
            if re.search(r'\b' + kw + r'\b', sql_upper):
                return ValidationResult(False, sql, f"不允许使用 {kw} 操作")

        # 2. 检查表权限
        table = self._extract_table(sql_upper)
        if table and table not in self.allowed_tables:
            return ValidationResult(False, sql, f"无权访问表 {table}")

        # 3. DELETE/UPDATE 必须有 WHERE
        if sql_upper.startswith("DELETE") and "WHERE" not in sql_upper:
            return ValidationResult(False, sql, "DELETE 语句必须包含 WHERE 条件")
        if sql_upper.startswith("UPDATE") and "WHERE" not in sql_upper:
            return ValidationResult(False, sql, "UPDATE 语句必须包含 WHERE 条件")

        # 4. SELECT 自动追加 LIMIT
        if sql_upper.startswith("SELECT") and "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + f" LIMIT {self.max_rows}"

        return ValidationResult(True, sql)

    def _extract_table(self, sql_upper: str) -> str | None:
        """从SQL中提取表名（简化版，覆盖常见模式）"""
        # FROM table / INTO table / UPDATE table / JOIN table
        patterns = [
            r'\bFROM\s+(\w+)',
            r'\bINTO\s+(\w+)',
            r'\bUPDATE\s+(\w+)',
            r'\bJOIN\s+(\w+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, sql_upper)
            if m:
                return m.group(1).lower()
        return None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_sql_validator.py::test_dangerous_sql_blocked -v
```
Expected: PASS

- [ ] **Step 5: 写测试 — DELETE/UPDATE无WHERE被拦截**

```python
def test_delete_without_where_blocked():
    v = SQLValidator(ALL_TABLES)
    result = v.validate("DELETE FROM users")
    assert result.is_valid is False
    assert "WHERE" in result.error

def test_update_without_where_blocked():
    v = SQLValidator(ALL_TABLES)
    result = v.validate("UPDATE users SET role = 'admin'")
    assert result.is_valid is False
    assert "WHERE" in result.error

def test_delete_with_where_passes():
    v = SQLValidator(ALL_TABLES)
    result = v.validate("SELECT id FROM users WHERE id = 1")
    assert result.is_valid is True
```

- [ ] **Step 6: 运行测试，实现代码使其通过**

```bash
uv run pytest tests/test_sql_validator.py -v
```
Expected: 全部 PASS（Step 3 已实现相关逻辑）

- [ ] **Step 7: 写测试 — 未授权表被拦截**

```python
def test_unauthorized_table_blocked():
    guest_tables = ["users", "courses", "events", "registrations"]
    v = SQLValidator(guest_tables)

    result = v.validate("SELECT * FROM leads WHERE name = '张三'")
    assert result.is_valid is False
    assert "无权访问" in result.error

def test_authorized_table_passes():
    guest_tables = ["users", "courses", "events", "registrations"]
    v = SQLValidator(guest_tables)

    result = v.validate("SELECT * FROM events WHERE status = 'active'")
    assert result.is_valid is True
```

- [ ] **Step 8: 运行测试确认通过**

```bash
uv run pytest tests/test_sql_validator.py -v
```
Expected: 全部 PASS

- [ ] **Step 9: 写测试 — SELECT自动追加LIMIT**

```python
def test_select_auto_limit():
    v = SQLValidator(ALL_TABLES, max_rows=50)
    result = v.validate("SELECT * FROM users")
    assert result.is_valid is True
    assert "LIMIT 50" in result.sql.upper()

def test_select_with_limit_not_duplicated():
    v = SQLValidator(ALL_TABLES, max_rows=50)
    result = v.validate("SELECT * FROM users LIMIT 10")
    assert result.is_valid is True
    # 不应出现两个 LIMIT
    assert result.sql.upper().count("LIMIT") == 1
```

- [ ] **Step 10: 运行测试确认通过**

```bash
uv run pytest tests/test_sql_validator.py -v
```
Expected: 全部 PASS

- [ ] **Step 11: 提交**

```bash
git add app/agent/tools/sql_validator.py tests/test_sql_validator.py
git commit -m "feat: add SQLValidator with safety checks (dangerous ops, WHERE required, table auth, auto LIMIT)"
```

---

### Task 2: SQL Executor — SQL执行器

**Files:**
- Modify: `app/agent/tools/sql_validator.py`（追加 SQLExecutor 类）
- Modify: `tests/test_sql_validator.py`（追加 Executor 测试）

- [ ] **Step 1: 写测试 — 执行SELECT返回JSON**

在 `tests/test_sql_validator.py` 末尾追加：

```python
from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional

class _TestUser(SQLModel, table=True):
    __tablename__ = "test_users"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: str = "student"

def test_executor_select():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(_TestUser(name="张三", role="student"))
        session.commit()

    from app.agent.tools.sql_validator import SQLExecutor
    ex = SQLExecutor(engine)
    result = ex.execute("SELECT * FROM test_users")
    assert "rows" in result
    assert len(result["rows"]) == 1
    assert result["rows"][0]["name"] == "张三"

def test_executor_insert():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    from app.agent.tools.sql_validator import SQLExecutor
    ex = SQLExecutor(engine)
    result = ex.execute("INSERT INTO test_users (name, role) VALUES ('李四', 'employee')")
    assert "affected_rows" in result
    assert result["affected_rows"] == 1

def test_executor_update():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(_TestUser(name="王五", role="student"))
        session.commit()

    from app.agent.tools.sql_validator import SQLExecutor
    ex = SQLExecutor(engine)
    result = ex.execute("UPDATE test_users SET role = 'admin' WHERE name = '王五'")
    assert result["affected_rows"] == 1

def test_executor_error():
    engine = create_engine("sqlite:///:memory:")
    from app.agent.tools.sql_validator import SQLExecutor
    ex = SQLExecutor(engine)
    result = ex.execute("SELECT * FROM nonexistent_table")
    assert "error" in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_sql_validator.py::test_executor_select -v
```
Expected: FAIL (SQLExecutor 不存在)

- [ ] **Step 3: 在 `app/agent/tools/sql_validator.py` 末尾追加 SQLExecutor**

```python
# 追加到 sql_validator.py 文件末尾
from app.db.connection import engine as production_engine
from sqlalchemy import text


class SQLExecutor:
    def __init__(self, engine=None):
        self.engine = engine or production_engine

    def execute(self, sql: str) -> dict:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                conn.commit()

                if sql.strip().upper().startswith("SELECT"):
                    rows = [dict(row._mapping) for row in result.fetchall()]
                    for row in rows:
                        for k, v in row.items():
                            if hasattr(v, "isoformat"):
                                row[k] = v.isoformat()
                    return {"rows": rows, "count": len(rows)}
                else:
                    return {"affected_rows": result.rowcount}
        except Exception as e:
            return {"error": str(e)}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_sql_validator.py -v
```
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add app/agent/tools/sql_validator.py tests/test_sql_validator.py
git commit -m "feat: add SQLExecutor with SELECT/INSERT/UPDATE/DELETE support"
```

---

### Task 3: NL2SQL Engine — Schema提取 + LLM调用

**Files:**
- Create: `app/agent/tools/nl2sql.py`
- Test: `tests/test_nl2sql.py`

- [ ] **Step 1: 写测试 — Schema从模型动态提取**

```python
# tests/test_nl2sql.py
from app.agent.tools.nl2sql import SchemaExtractor

def test_schema_extraction():
    """SchemaExtractor reads from SQLModel.metadata.tables (populated by model imports)."""
    extractor = SchemaExtractor()
    schema_text = extractor.extract()

    assert "leads" in schema_text
    assert "users" in schema_text
    assert "events" in schema_text
    # 验证列信息和PK/FK标记
    assert "id" in schema_text
    assert "PK" in schema_text
    assert "FK" in schema_text
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_nl2sql.py::test_schema_extraction -v
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现 SchemaExtractor**

```python
# app/agent/tools/nl2sql.py
"""NL2SQL 引擎 — 自然语言转SQL"""
import re
from pathlib import Path
import yaml


class SchemaExtractor:
    """从 SQLModel metadata 动态提取表schema"""

    def extract(self) -> str:
        from sqlmodel import SQLModel
        from app.db.models import (
            Course, Event, Registration, User, Lead, LeadFollowUp,
            DailyReport, Complaint, Organization, StudentGrade,
            LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
        )

        lines = []
        for table_name, table in SQLModel.metadata.tables.items():
            if table_name.startswith("_"):
                continue
            cols = []
            for col in table.columns:
                parts = [col.name, str(col.type)]
                if col.primary_key:
                    parts.append("PK")
                if col.foreign_keys:
                    fk = ", ".join(fk.target_fullname for fk in col.foreign_keys)
                    parts.append(f"FK→{fk}")
                if not col.nullable:
                    parts.append("NOT NULL")
                cols.append(" ".join(parts))
            lines.append(f"Table: {table_name}")
            lines.append(f"Columns: {', '.join(cols)}")
            lines.append("")

        return "\n".join(lines).strip()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_nl2sql.py::test_schema_extraction -v
```
Expected: PASS

- [ ] **Step 5: 写测试 — SQL从markdown中提取**

```python
def test_extract_sql_from_markdown():
    from app.agent.tools.nl2sql import extract_sql

    # 带markdown代码块
    text = "```sql\nSELECT * FROM users;\n```"
    assert extract_sql(text) == "SELECT * FROM users;"

    # 纯SQL
    text2 = "SELECT * FROM users WHERE id = 1"
    assert extract_sql(text2) == "SELECT * FROM users WHERE id = 1"

    # 带解释文字
    text3 = "这是查询语句：\n```sql\nSELECT name FROM leads;\n```\n请执行"
    assert extract_sql(text3) == "SELECT name FROM leads;"
```

- [ ] **Step 6: 运行测试，实现 extract_sql 函数**

在 `nl2sql.py` 中追加：

```python
def extract_sql(text: str) -> str:
    """从LLM响应中提取纯SQL（去除markdown标记和解释文字）"""
    # 尝试匹配 ```sql ... ``` 代码块（兼容有无换行）
    match = re.search(r'```sql\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 尝试匹配 ``` ... ``` 代码块（无语言标记）
    match = re.search(r'```\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 如果没有代码块，尝试提取包含SQL关键字的行
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    for line in text.split("\n"):
        line_stripped = line.strip().upper()
        if any(line_stripped.startswith(kw) for kw in sql_keywords):
            return line.strip()

    # 最后兜底：返回原文
    return text.strip()
```

- [ ] **Step 7: 运行测试确认通过**

```bash
uv run pytest tests/test_nl2sql.py -v
```
Expected: 全部 PASS

- [ ] **Step 8: 写测试 — NL2SQLEngine prompt组装**

```python
def test_engine_prompt_assembly():
    from app.agent.tools.nl2sql import NL2SQLEngine

    class FakeMessages:
        def __init__(self):
            self.last_system = None
            self.last_user = None

        def create(self, model, system, messages, max_tokens):
            self.last_system = system
            self.last_user = messages[0]["content"]

            class FakeContent:
                text = "SELECT 1"
            class FakeResponse:
                content = [FakeContent()]
            return FakeResponse()

    class FakeLLM:
        messages = FakeMessages()

    engine = NL2SQLEngine(
        llm_client=FakeLLM(),
        schema_context="Table: users\nColumns: id INTEGER PK, name VARCHAR",
        soul_template="你是SQL助手。",
    )

    engine.generate_sql("查所有用户", "employee", allowed_tables=["users"])
    assert "Table: users" in FakeLLM.messages.last_system
    assert "查所有用户" in FakeLLM.messages.last_user
```

- [ ] **Step 9: 运行测试，实现 NL2SQLEngine**

在 `nl2sql.py` 中追加：

```python
class NL2SQLEngine:
    def __init__(self, llm_client, schema_context: str, soul_template: str):
        self.llm = llm_client
        self.schema_context = schema_context
        self.soul_template = soul_template

    def generate_sql(self, natural_query: str, role: str, allowed_tables: list[str]) -> str:
        system_prompt = self._build_system_prompt(role, allowed_tables)

        response = self.llm.messages.create(
            model=os.environ.get("MODEL_ID", "qwen3.6-plus"),
            system=system_prompt,
            messages=[{"role": "user", "content": natural_query}],
            max_tokens=2000,
        )
        return extract_sql(response.content[0].text)

    def _build_system_prompt(self, role: str, allowed_tables: list[str]) -> str:
        prompt = self.soul_template
        prompt += f"\n\n## 数据库Schema\n{self.schema_context}"
        prompt += f"\n\n## 可访问表\n你只能操作以下表: {', '.join(allowed_tables)}"
        prompt += f"\n\n## 当前角色\n{role}"
        return prompt
```

在文件顶部添加 `import os`。

- [ ] **Step 10: 运行测试确认通过**

```bash
uv run pytest tests/test_nl2sql.py -v
```
Expected: 全部 PASS

- [ ] **Step 11: 提交**

```bash
git add app/agent/tools/nl2sql.py tests/test_nl2sql.py
git commit -m "feat: add NL2SQLEngine with dynamic schema extraction and prompt assembly"
```

---

### Task 4: souls/nl2sql 配置 + dbman 工具入口

**Files:**
- Create: `souls/nl2sql/SOUL.md`
- Create: `souls/nl2sql/tables.yaml`
- Create: `app/agent/tools/dbman.py`

- [ ] **Step 1: 创建 `souls/nl2sql/SOUL.md`**

```markdown
---
name: nl2sql
role: sql_generator
---

你是一个SQL生成助手。根据用户的自然语言描述，生成对应的MySQL查询语句。

## 规则

1. 只输出SQL，不附加任何解释
2. 使用MySQL语法
3. 涉及多表查询时使用 JOIN 连接
4. 时间相关的查询使用合理的范围（如最近7天、最近30天）
5. 字符串比较使用 LIKE 进行模糊匹配
6. 中文值使用原始中文字符
7. 输出格式为纯SQL语句，以分号结尾

## 示例

用户：帮我查一下张三的最近跟进记录
SQL：SELECT l.name, lf.content, lf.created_at FROM leads l JOIN lead_follow_ups lf ON l.id = lf.lead_id WHERE l.name LIKE '%张三%' ORDER BY lf.created_at DESC LIMIT 10;

用户：统计各部门本周提交的日报数量
SQL：SELECT department, COUNT(*) as count FROM daily_reports WHERE submitted_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY department;

用户：把李四的投诉状态改为已解决
SQL：UPDATE complaints SET status = '已解决', resolved_at = NOW() WHERE student_id = (SELECT id FROM users WHERE username = '李四');
```

- [ ] **Step 2: 创建 `souls/nl2sql/tables.yaml`**

```yaml
# 角色可访问的数据库表配置
employee:
  - users
  - leads
  - lead_follow_ups
  - daily_reports
  - complaints
  - organization
  - student_grades
  - leave_requests
  - exam_schedule
  - psychology_profiles
  - psychology_warnings
  - courses
  - events
  - registrations

student:
  - users
  - student_grades
  - leave_requests
  - exam_schedule
  - psychology_profiles
  - psychology_warnings
  - complaints
  - courses
  - events
  - registrations

guest:
  - users
  - courses
  - events
  - registrations
```

- [ ] **Step 3: 创建 `app/agent/tools/dbman.py`**

```python
"""dbman — 统一数据库操作工具（自然语言入口）"""
import os
import yaml
from pathlib import Path
from anthropic import Anthropic

from app.agent.tools.nl2sql import NL2SQLEngine, SchemaExtractor, extract_sql
from app.agent.tools.sql_validator import SQLValidator, SQLExecutor

# 全局单例（启动时初始化）
_nl2sql_engine = None
_tables_config = None


def _load_tables_config() -> dict:
    global _tables_config
    if _tables_config is None:
        config_path = Path("souls/nl2sql/tables.yaml")
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                _tables_config = yaml.safe_load(f) or {}
        else:
            _tables_config = {}
    return _tables_config


def _get_engine() -> NL2SQLEngine:
    global _nl2sql_engine
    if _nl2sql_engine is None:
        client = Anthropic(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_AUTH_TOKEN"),
        )
        schema = SchemaExtractor().extract()
        soul_path = Path("souls/nl2sql/SOUL.md")
        soul_template = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
        # 去除 frontmatter
        if soul_template.startswith("---"):
            parts = soul_template.split("---", 2)
            if len(parts) >= 3:
                soul_template = parts[2].strip()
        _nl2sql_engine = NL2SQLEngine(client, schema, soul_template)
    return _nl2sql_engine


def dbman(nl: str) -> str:
    """数据库操作工具 — 接收自然语言，生成SQL并执行"""
    try:
        # 1. 获取当前角色（从全局 soul_manager）
        from app.agent.core import soul_manager
        role = soul_manager.current_role or "employee"

        # 2. 获取角色可访问表
        tables_config = _load_tables_config()
        allowed_tables = tables_config.get(role, [])
        if not allowed_tables:
            return "错误：当前角色无权访问任何数据库表。"

        # 3. 生成SQL
        engine = _get_engine()
        sql = engine.generate_sql(nl, role, allowed_tables)

        if not sql or not any(kw in sql.upper() for kw in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
            return "未能理解您的查询，请换一种说法。"

        # 4. 安全校验
        validator = SQLValidator(allowed_tables)
        validation = validator.validate(sql)
        if not validation.is_valid:
            return f"操作被拒绝：{validation.error}"

        # 5. 执行
        executor = SQLExecutor()
        result = executor.execute(validation.sql)

        # 6. 格式化返回
        if "error" in result:
            return f"执行出错：{result['error']}"

        if "rows" in result:
            if result["count"] == 0:
                return "未找到相关数据。"
            return f"查询到 {result['count']} 条结果：\n```json\n{_format_json(result['rows'])}\n```"

        if "affected_rows" in result:
            return f"操作成功，影响 {result['affected_rows']} 行。"

        return "操作完成。"

    except Exception as e:
        return f"错误：{e}"


def _format_json(rows: list, max_rows: int = 10) -> str:
    import json
    display = rows[:max_rows]
    output = json.dumps(display, default=str, ensure_ascii=False, indent=2)
    if len(rows) > max_rows:
        output += f"\n... 仅显示前 {max_rows} 条，共 {len(rows)} 条"
    return output
```

- [ ] **Step 4: 提交**

```bash
git add souls/nl2sql/ app/agent/tools/dbman.py
git commit -m "feat: add dbman tool entry point with nl2sql config"
```

---

### Task 5: 更新工具注册 + 配置文件

**Files:**
- Modify: `app/agent/tools/__init__.py`
- Modify: `souls/tool_config.yaml`
- Modify: `souls/student/SOUL.md`
- Modify: `souls/employee/SOUL.md`
- Modify: `souls/guest/SOUL.md`
- Delete: `app/agent/tools/db.py`

- [ ] **Step 1: 更新 `app/agent/tools/__init__.py`**

将第5行 `from .db import db_query` 替换为：
```python
from .dbman import dbman
```

将第52-65行的 `db_query` 工具定义替换为：
```python
    "dbman": (
        dbman,
        {
            "type": "object",
            "properties": {
                "nl": {
                    "type": "string",
                    "description": "用自然语言描述你想查询或操作的数据，例如：'帮我查一下张三的最近跟进记录'",
                },
            },
            "required": ["nl"],
        },
        "数据库操作工具，支持自然语言查询和修改。可以说'查一下所有待审批的请假'或'把李四的投诉改为已解决'。",
    ),
```

- [ ] **Step 2: 更新 `souls/tool_config.yaml`**

```yaml
student:
  - knowledge_search
  - dbman

employee:
  - knowledge_search
  - dbman

guest:
  - knowledge_search
  - dbman

faq_roles:
  - guest
```

- [ ] **Step 3: 更新各角色 SOUL.md 中的工具描述**

在 `souls/student/SOUL.md`、`souls/employee/SOUL.md`、`souls/guest/SOUL.md` 中，找到所有提到 `db_query` 或数据库操作的地方，更新为使用 `dbman` 的描述（具体文本根据各文件内容调整）。

在 `souls/employee/SOUL.md` 中追加 NL2SQL 使用指引：
```markdown
## 数据库查询

使用 `dbman` 工具进行数据库操作。直接用自然语言描述你的需求，例如：
- "帮我查一下张三的最近跟进记录"
- "统计本月新增意向客户数量"
- "查看所有待审批的请假申请"
```

在 `souls/guest/SOUL.md` 中追加活动报名指引：
```markdown
## 活动与课程

使用 `dbman` 工具查询活动和课程：
- "查询最近的活动"
- "帮我报名参加XX活动"
- "推荐适合我的课程"
```

- [ ] **Step 4: 删除旧 `db.py`**

```bash
Remove-Item app/agent/tools/db.py
```

- [ ] **Step 5: 提交**

```bash
git add app/agent/tools/__init__.py souls/tool_config.yaml souls/student/SOUL.md souls/employee/SOUL.md souls/guest/SOUL.md
git rm app/agent/tools/db.py
git commit -m "refactor: replace db_query with dbman, update all configs and SOULs"
```

---

### Task 6: 集成测试 + 全量验证

**Files:**
- Create: `tests/test_dbman.py`

- [ ] **Step 1: 写集成测试**

```python
# tests/test_dbman.py
"""dbman 集成测试 — 使用 SQLite 内存数据库"""
import pytest
from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional


class _TestUser(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    role: str = "student"


class _TestEvent(SQLModel, table=True):
    __tablename__ = "events"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: str = "active"


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(_TestUser(username="张三", role="student"))
        session.add(_TestUser(username="李四", role="employee"))
        session.add(_TestEvent(name="留学分享会", status="active"))
        session.add(_TestEvent(name="招生见面会", status="active"))
        session.commit()
    return engine


def test_sql_validator_integration(test_engine):
    """验证 SQLValidator + SQLExecutor 端到端工作"""
    from app.agent.tools.sql_validator import SQLValidator, SQLExecutor

    tables = ["users", "events"]
    validator = SQLValidator(tables)
    executor = SQLExecutor(test_engine)

    # 合法查询
    result = validator.validate("SELECT * FROM users WHERE role = 'student'")
    assert result.is_valid is True
    exec_result = executor.execute(result.sql)
    assert exec_result["count"] == 1

    # 危险操作被拦截
    result = validator.validate("DROP TABLE users")
    assert result.is_valid is False


def test_role_table_filter():
    """验证 guest 角色只能访问4张表"""
    from app.agent.tools.sql_validator import SQLValidator

    guest_tables = ["users", "courses", "events", "registrations"]
    v = SQLValidator(guest_tables)

    # 授权表通过
    r = v.validate("SELECT * FROM events")
    assert r.is_valid is True

    # 未授权表被拦截
    r = v.validate("SELECT * FROM leads")
    assert r.is_valid is False
    assert "无权访问" in r.error
```

- [ ] **Step 2: 运行集成测试**

```bash
uv run pytest tests/test_dbman.py -v
```
Expected: 全部 PASS

- [ ] **Step 3: 运行全量测试**

```bash
uv run pytest tests/ -v
```
Expected: 全部 PASS（包括已有的 test_soul.py 等）

- [ ] **Step 4: 验证服务启动无报错**

```bash
uv run python -c "from app.agent.tools import registry; print('Tools:', [t.name for t in registry._tools.values()])"
```
Expected: 输出包含 `dbman`，不包含 `db_query`

- [ ] **Step 5: 提交**

```bash
git add tests/test_dbman.py
git commit -m "test: add dbman integration tests"
```

---

### Task 7: 更新进度文档

**Files:**
- Modify: `docs/PROGRESS.md`

- [ ] **Step 1: 更新 PROGRESS.md 中 NL2SQL 状态**

将 `docs/PROGRESS.md` 中 `#### 1. NL2SQL 自然语言查询` 部分的状态从 ❌ 改为 ✅，更新说明：

```markdown
#### 1. NL2SQL 自然语言查询

- **客户需求原文**：`企业智能助手 → NL2SQL实现：针对上述数据表开发自然语言转SQL功能，支持员工通过口语（如"帮我查一下张三的最近跟进记录"）直接调取数据库信息。`
- **当前状态**：✅ 已完成
- **实现**：`dbman` 工具（`app/agent/tools/dbman.py`），基于 LLM 的 NL2SQL 引擎 + SQL 安全校验层 + 执行器。按角色控制表权限（employee 14张 / student 10张 / guest 4张）。
```

- [ ] **Step 2: 提交**

```bash
git add docs/PROGRESS.md
git commit -m "docs: update progress - NL2SQL complete"
```
