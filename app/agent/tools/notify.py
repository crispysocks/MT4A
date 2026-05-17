"""notify — 通知写入工具"""
from app.db.connection import Session, engine
from app.db.models import Notification

def notify(
    notification_type: str,
    user_id: int,
    operation_type: str,
    content_summary: str
) -> str:
    """写入通知记录"""
    try:
        with Session(engine) as session:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                status="active",
                operation_type=operation_type,
                content_summary=content_summary
            )
            session.add(notification)
            session.commit()
        return f"通知已写入：{content_summary}"
    except Exception as e:
        return f"通知写入失败：{e}"
