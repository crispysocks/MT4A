import os
from sqlmodel import create_engine, Session, SQLModel

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