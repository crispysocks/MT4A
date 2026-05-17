# dbman: NL2SQL 统一数据库工具设计

> 日期: 2026-05-17
> 状态: 待评审
> 作者: AI Assistant

---

## 1. 概述

替换现有的 `db_query` 工具，重构为统一的 `dbman` 工具。新工具接收自然语言参数，内部通过 LLM 生成 SQL，经安全校验后执行。支持 SELECT/INSERT/UPDATE/DELETE 全操作类型，按角色控制可访问的表范围。

**项目需求来源：**
- 企业智能助手 → NL2SQL实现：针对数据表开发自然语言转SQL功能，支持员工通过口语直接调取数据库信息
- 客服Agent → 活动与讲座报名：支持客户查询活动并完成预约报名
- 学生智能助手 → 行政服务/学业考务/投诉反馈等

## 2. 架构

```
用户自然语言
    │
    ▼
┌─────────────────────────────────┐
│         agent_loop              │
│  - 解析用户意图                  │
│  - 调用 dbman(nl="...")         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│         NL2SQL Engine           │
│                                 │
│  调用LLM，system prompt包含：   │
│  - 动态提取的表schema           │
│  - 当前角色可访问的表列表       │
│  - SQL生成规则（souls/nl2sql/  │
│    SOUL.md）                    │
│                                 │
│  输出：完整SQL语句              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│         SQL Validator           │
│  - 拦截DROP/ALTER/TRUNCATE等    │
│  - DELETE/UPDATE必须有WHERE     │
│  - 限制SELECT返回行数(默认100)  │
│  - 按角色过滤可操作的表         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│         SQL Executor            │
│  - 执行SQL，返回JSON结果        │
│  - 写操作返回影响行数           │
│  - 错误捕获与友好提示           │
└─────────────────────────────────┘
```

## 3. 模块设计

### 3.1 NL2SQL Engine (`app/agent/tools/nl2sql.py`)

**职责：** 将自然语言转换为 SQL

**设计模式：** 参考 SoulManager，使用 YAML frontmatter + body 的模板方式，而非硬编码 prompt。

```python
class NL2SQLEngine:
    def __init__(self, llm_client, schema_context: str, soul_template: str):
        self.llm = llm_client  # 复用项目 anthropic 客户端配置
        self.schema_context = schema_context  # 启动时动态生成
        self.soul_template = soul_template     # 从 souls/nl2sql/SOUL.md 加载

    def generate_sql(self, natural_query: str, role: str) -> str:
        """生成SQL，返回纯SQL字符串（不含markdown标记）"""
        # 1. 组装system prompt: soul_template + schema_context + role_allowed_tables
        # 2. 调用LLM
        # 3. 提取SQL（去除```sql```标记）
        # 4. 返回
```

**Schema 提取：** 启动时遍历 `SQLModel.metadata.tables`，自动生成每张表的列定义文本，不硬编码。

输出格式示例：
```
Table: leads
Columns: id (INTEGER PK), name (VARCHAR), phone (VARCHAR), email (VARCHAR),
         source (VARCHAR), status (VARCHAR), assigned_to (INTEGER FK→users.id),
         notes (TEXT), created_at (DATETIME), updated_at (DATETIME)
```

### 3.2 SQL Validator + Executor (`app/agent/tools/sql_validator.py`)

**SQLValidator：**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    sql: str          # 校验通过时为修正后的SQL，失败时为原始SQL
    error: str = ""   # 校验失败时的错误信息

class SQLValidator:
    DANGEROUS_KEYWORDS = ["DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]

    def __init__(self, allowed_tables: list[str], max_rows: int = 100):
        self.allowed_tables = set(t.lower() for t in allowed_tables)
        self.max_rows = max_rows

    def validate(self, sql: str) -> ValidationResult:
        """校验SQL安全性"""
        # 1. 检查危险关键字 → 失败返回 ValidationResult(False, sql, "拒绝原因")
        # 2. 检查表是否在 allowed_tables 中
        # 3. DELETE/UPDATE 必须包含 WHERE
        # 4. SELECT 无 LIMIT 时自动追加 LIMIT {max_rows} → 成功返回 ValidationResult(True, modified_sql)
```

**SQLExecutor：**
```python
class SQLExecutor:
    def __init__(self, engine):
        self.engine = engine  # SQLAlchemy engine（复用现有连接）

    def execute(self, sql: str) -> dict:
        """执行SQL并返回结构化结果"""
        # SELECT → {"rows": [...], "count": N}
        # INSERT/UPDATE/DELETE → {"affected_rows": N}
        # 异常 → {"error": "友好错误信息"}
```

### 3.3 统一工具入口 (`app/agent/tools/dbman.py`)

```python
@tool("dbman", schema={"nl": {"type": "string", "description": "用自然语言描述你想查询或操作的数据"}}, description="数据库操作工具，支持自然语言查询和修改")
def dbman(nl: str) -> str:
    """
    1. 获取当前角色（从 soul_manager）
    2. 查询角色可访问的表列表
    3. NL2SQLEngine.generate_sql(nl, role) → SQL
    4. SQLValidator.validate(SQL) → 校验 + 可能的SQL修正
    5. SQLExecutor.execute(SQL) → 结果
    6. 格式化为自然语言返回
    """
```

## 4. 角色表权限配置

### 4.1 配置文件 (`souls/nl2sql/tables.yaml`)

```yaml
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

### 4.2 权限说明

| 角色 | 可访问表数 | 说明 |
|------|-----------|------|
| employee | 14张（全部） | 企业内部管理，全量读写 |
| student | 10张 | 学生自助，可查改自身相关数据 |
| guest | 4张 | 客服对外，课程/活动查询与报名 |

## 5. SQL 生成模板 (`souls/nl2sql/SOUL.md`)

采用与角色 SOUL.md 相同的 YAML frontmatter + body 格式：

```yaml
---
name: nl2sql
role: sql_generator
---
```

Body 部分定义 SQL 生成规则：
- 使用 MySQL 语法
- 涉及多表时使用 JOIN
- 时间查询使用合理范围（最近7天/30天）
- 只输出 SQL，不附加解释
- 中文列名/值使用原始数据

## 6. 工具配置更新 (`souls/tool_config.yaml`)

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
```

所有三个角色均开放 `dbman` 工具（替代原 `db_query`）。

## 7. 错误处理

| 场景 | 处理方式 |
|------|---------|
| LLM 生成的 SQL 语法错误 | 捕获异常，返回"未能理解查询，请换种说法" |
| SQL 校验失败（危险操作/无权限） | 返回明确拒绝信息："无法执行该操作" |
| 查询结果为空 | 返回"未找到相关数据" |
| 查询超时（>10s） | 中断执行，返回"查询超时，请缩小范围" |
| LLM 未返回有效 SQL | 将错误信息追加到对话历史，重试1次LLM调用；仍失败则返回友好提示 |

## 8. 数据库 Schema（14张表）

| 表名 | 关键字段 | 外键 |
|------|---------|------|
| courses | id, name, type, country, fees, description | - |
| events | id, name, type, event_datetime, location, status | - |
| registrations | id, event_id, name, phone, email, country_interest | events.id |
| users | id, username, role | - |
| leads | id, name, phone, email, source, status, assigned_to | users.id |
| lead_follow_ups | id, lead_id, content, follow_type, created_by | leads.id, users.id |
| daily_reports | id, user_id, content, summary, department | users.id |
| complaints | id, student_id, category, content, status, handler_id, resolution | users.id |
| organization | id, name, org_type, parent_id, contact_info | organization.id |
| student_grades | id, student_id, subject, grade, semester | users.id |
| leave_requests | id, student_id, reason, start_date, end_date, status, approver_id | users.id |
| exam_schedule | id, student_id, exam_type, subject, deadline | users.id |
| psychology_profiles | id, student_id, emotion_tag, score, notes | users.id |
| psychology_warnings | id, student_id, trigger_reason, risk_level, status, handler_id | users.id |

## 9. 测试策略

### 9.1 NL2SQL 引擎测试 (`tests/test_nl2sql.py`)

| 测试项 | 说明 |
|--------|------|
| `test_generate_select` | 简单单表查询 |
| `test_generate_join` | 跨表 JOIN 查询 |
| `test_generate_aggregate` | GROUP BY / COUNT 等聚合查询 |
| `test_generate_insert` | INSERT 语句生成 |
| `test_generate_update` | UPDATE 语句生成 |
| `test_schema_extraction` | 验证 schema 从模型正确提取 |

### 9.2 SQL 校验测试 (`tests/test_sql_validator.py`)

| 测试项 | 说明 |
|--------|------|
| `test_dangerous_sql_blocked` | DROP/ALTER 等被拦截 |
| `test_delete_without_where_blocked` | 无 WHERE 的 DELETE 被拦截 |
| `test_unauthorized_table_blocked` | 访问未授权表被拦截 |
| `test_select_auto_limit` | SELECT 自动追加 LIMIT |
| `test_valid_select_passes` | 合法 SELECT 通过 |

### 9.3 集成测试 (`tests/test_dbman.py`)

| 测试项 | 说明 |
|--------|------|
| `test_select_returns_json` | 查询返回 JSON 格式结果 |
| `test_insert_returns_rows` | 插入返回影响行数 |
| `test_update_with_where` | 带条件的更新 |
| `test_role_table_filter` | guest 只能访问4张表 |
| `test_natural_language_query` | 端到端：自然语言→结果 |

## 10. 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/agent/tools/nl2sql.py` | 新增 | NL2SQL 引擎 |
| `app/agent/tools/sql_validator.py` | 新增 | SQL 校验 + 执行器 |
| `app/agent/tools/dbman.py` | 新增 | 统一工具入口 |
| `app/agent/tools/__init__.py` | 修改 | 注册 dbman，移除 db_query |
| `souls/nl2sql/SOUL.md` | 新增 | SQL 生成规则模板 |
| `souls/nl2sql/tables.yaml` | 新增 | 角色表权限配置 |
| `souls/tool_config.yaml` | 修改 | db_query → dbman，guest 新增 dbman |
| `souls/student/SOUL.md` | 修改 | 工具描述更新 |
| `souls/employee/SOUL.md` | 修改 | 工具描述更新 |
| `souls/guest/SOUL.md` | 修改 | 工具描述更新 |
| `app/agent/tools/db.py` | 删除 | 旧工具移除 |
| `tests/test_nl2sql.py` | 新增 | NL2SQL 引擎测试 |
| `tests/test_sql_validator.py` | 新增 | SQL 校验测试 |
| `tests/test_dbman.py` | 新增 | 集成测试 |

## 11. 迁移步骤

1. 创建 `souls/nl2sql/` 目录，编写 SOUL.md 和 tables.yaml
2. 实现 `nl2sql.py`、`sql_validator.py`、`dbman.py`
3. 更新 `__init__.py` 注册新工具，移除旧 `db_query`
4. 更新 `tool_config.yaml` 和各角色 SOUL.md
5. 删除旧 `db.py`
6. 编写测试并验证
7. 运行全量测试确保无回归
