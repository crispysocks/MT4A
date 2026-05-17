import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, SQLModel

load_dotenv()

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
    from app.db.models import (
        Course, Event, Registration,
        User, Lead, LeadFollowUp, DailyReport, Complaint, Organization,
        StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
    )
    SQLModel.metadata.create_all(engine)
    from app.db.seed_data import seed_all
    seed_all()


def init_db_on_startup():
    """Startup-time DB init with error handling"""
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] Database init skipped: {e}")