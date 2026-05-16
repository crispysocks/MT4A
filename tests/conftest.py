import pytest
from sqlmodel import Session, SQLModel, create_engine
from app.db.models import User


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine, tables=[User.__table__])
    with Session(engine) as session:
        yield session
