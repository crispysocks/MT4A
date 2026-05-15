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