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


def test_select_auto_limit():
    v = SQLValidator(ALL_TABLES, max_rows=50)
    result = v.validate("SELECT * FROM users")
    assert result.is_valid is True
    assert "LIMIT 50" in result.sql.upper()


def test_select_with_limit_not_duplicated():
    v = SQLValidator(ALL_TABLES, max_rows=50)
    result = v.validate("SELECT * FROM users LIMIT 10")
    assert result.is_valid is True
    assert result.sql.upper().count("LIMIT") == 1


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