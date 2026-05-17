from sqlmodel import SQLModel

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