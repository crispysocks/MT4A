import os
import mysql.connector
from sqlmodel import create_engine, Session, SQLModel

DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_PORT = os.getenv('DATABASE_PORT', '3306')
DATABASE_USER = os.getenv('DATABASE_USER', 'root')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'mt4a')

DATABASE_URL = (
    f"mysql+mysqlconnector://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/"
    f"{DATABASE_NAME}"
)

def ensure_database():
    conn = mysql.connector.connect(
        host=DATABASE_HOST,
        port=int(DATABASE_PORT),
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()

ensure_database()

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    ensure_database()
    from app.db.models import (
        Course, Event, Registration,
        User, Lead, LeadFollowUp, DailyReport, Complaint, Organization,
        StudentGrade, LeaveRequest, ExamSchedule, PsychologyProfile, PsychologyWarning,
        Notification,
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