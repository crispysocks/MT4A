from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    type: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    recruitment_group: Optional[str] = Field(default=None, max_length=255)
    duration: Optional[str] = Field(default=None, max_length=100)
    fees: Optional[str] = Field(default=None)
    features: Optional[str] = Field(default=None)
    certification: Optional[str] = Field(default=None, max_length=255)
    allowance: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    type: Optional[str] = Field(default=None, max_length=100)
    event_datetime: Optional[datetime] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default="active", max_length=50)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())

class Registration(SQLModel, table=True):
    __tablename__ = "registrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id")
    name: str = Field(max_length=100)
    phone: str = Field(max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    country_interest: Optional[str] = Field(default=None, max_length=100)
    education: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None)
    registration_date: Optional[datetime] = Field(default_factory=datetime.now)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(max_length=20)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class Lead(SQLModel, table=True):
    __tablename__ = "leads"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    source: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default="new", max_length=50)
    assigned_to: Optional[int] = Field(default=None, foreign_key="users.id")
    notes: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"onupdate": lambda: datetime.now()})


class LeadFollowUp(SQLModel, table=True):
    __tablename__ = "lead_follow_ups"
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id")
    content: str = Field()
    follow_type: Optional[str] = Field(default=None, max_length=50)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class DailyReport(SQLModel, table=True):
    __tablename__ = "daily_reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    content: str = Field()
    summary: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None, max_length=100)
    submitted_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    category: Optional[str] = Field(default=None, max_length=100)
    content: str = Field()
    status: Optional[str] = Field(default="pending", max_length=50)
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id")
    resolution: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    resolved_at: Optional[datetime] = Field(default=None)


class Organization(SQLModel, table=True):
    __tablename__ = "organization"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    org_type: str = Field(max_length=50)
    parent_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    contact_info: Optional[str] = Field(default=None, max_length=255)


class StudentGrade(SQLModel, table=True):
    __tablename__ = "student_grades"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    subject: str = Field(max_length=100)
    grade: Optional[str] = Field(default=None, max_length=20)
    semester: Optional[str] = Field(default=None, max_length=50)
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    reason: str = Field()
    start_date: str = Field()
    end_date: str = Field()
    status: Optional[str] = Field(default="pending", max_length=50)
    approver_id: Optional[int] = Field(default=None, foreign_key="users.id")
    approved_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class ExamSchedule(SQLModel, table=True):
    __tablename__ = "exam_schedule"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    exam_type: Optional[str] = Field(default=None, max_length=100)
    subject: Optional[str] = Field(default=None, max_length=100)
    deadline: Optional[datetime] = Field(default=None)
    description: Optional[str] = Field(default=None)


class PsychologyProfile(SQLModel, table=True):
    __tablename__ = "psychology_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    emotion_tag: Optional[str] = Field(default=None, max_length=100)
    score: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class PsychologyWarning(SQLModel, table=True):
    __tablename__ = "psychology_warnings"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    trigger_reason: str = Field()
    risk_level: Optional[str] = Field(default="medium", max_length=50)
    status: Optional[str] = Field(default="active", max_length=50)
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    notification_type: str = Field(max_length=50)
    status: Optional[str] = Field(default="active", max_length=50)
    operation_type: str = Field(max_length=50)
    content_summary: str = Field()
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())