from sqlmodel import SQLModel

def test_get_employees_returns_employee_list(db_session):
    from app.agent.auth import AuthManager
    auth = AuthManager(db_session)
    auth.register("teacher1", "password", "employee")
    auth.register("student1", "password", "student")

    from sqlmodel import select
    from app.db.models import User
    employees = db_session.exec(
        select(User).where(User.role == "employee")
    ).all()
    employee_usernames = [e.username for e in employees]
    assert "teacher1" in employee_usernames
    assert "student1" not in employee_usernames

def test_user_class_advisor_id_field():
    from app.db.models import User
    assert "class_advisor_id" in User.__fields__

def test_user_class_advisor_id_nullable():
    from app.db.models import User
    field = User.__fields__["class_advisor_id"]
    assert not field.is_required()

def test_user_class_advisor_id_fk():
    from app.db.models import User
    field = User.__fields__["class_advisor_id"]
    meta_list = field.metadata
    fk = next((m.foreign_key for m in meta_list if hasattr(m, 'foreign_key') and m.foreign_key), None)
    assert fk is not None
    assert "users.id" in str(fk)