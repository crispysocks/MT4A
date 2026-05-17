import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from app.db.models import Notification, User
from datetime import datetime


@pytest.fixture(scope="function")
def engine():
    """Create SQLite in-memory engine with User and Notification tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine, tables=[User.__table__, Notification.__table__])
    return engine


@pytest.fixture(scope="function")
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def test_user(session):
    user = User(username="test_student", password_hash="hash", role="student")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestNotificationModel:
    def test_create_notification(self, session, test_user):
        """Test creating a notification record."""
        notification = Notification(
            user_id=test_user.id,
            notification_type="leave_request",
            status="active",
            operation_type="approve",
            content_summary="请假5月17日-18日"
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)

        assert notification.id is not None
        assert notification.user_id == test_user.id
        assert notification.notification_type == "leave_request"
        assert notification.status == "active"
        assert notification.operation_type == "approve"
        assert notification.content_summary == "请假5月17日-18日"
        assert notification.created_at is not None

    def test_dismiss_notification(self, session, test_user):
        """Test marking a notification as dismissed."""
        notification = Notification(
            user_id=test_user.id,
            notification_type="exam_reminder",
            status="active",
            operation_type="confirm",
            content_summary="考试提醒：数学5月20日"
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)

        notification.status = "dismissed"
        session.commit()

        fetched = session.get(Notification, notification.id)
        assert fetched.status == "dismissed"

    def test_query_active_notifications(self, session, test_user):
        """Test querying only active notifications for a user."""
        active = Notification(
            user_id=test_user.id,
            notification_type="complaint_result",
            status="active",
            operation_type="read",
            content_summary="投诉已处理"
        )
        dismissed = Notification(
            user_id=test_user.id,
            notification_type="leave_result",
            status="dismissed",
            operation_type="read",
            content_summary="请假已通过"
        )
        session.add_all([active, dismissed])
        session.commit()

        active_notifications = session.exec(
            select(Notification).where(
                Notification.user_id == test_user.id,
                Notification.status == "active"
            )
        ).all()

        assert len(active_notifications) == 1
        assert active_notifications[0].notification_type == "complaint_result"

    def test_notification_type_values(self, session, test_user):
        """Test all notification type values can be stored."""
        types = [
            "leave_request", "leave_result",
            "complaint", "complaint_result",
            "exam_reminder", "psychology_warning",
            "progress_update", "todo_reminder"
        ]
        for t in types:
            n = Notification(
                user_id=test_user.id,
                notification_type=t,
                status="active",
                operation_type="read",
                content_summary=f"Test: {t}"
            )
            session.add(n)
        session.commit()

        results = session.exec(
            select(Notification).where(Notification.user_id == test_user.id)
        ).all()
        assert len(results) == len(types)

    def test_default_status_is_active(self, session, test_user):
        """Test that new notifications default to active status."""
        notification = Notification(
            user_id=test_user.id,
            notification_type="progress_update",
            operation_type="read",
            content_summary="签证进度已更新"
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)

        assert notification.status == "active"
