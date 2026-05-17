from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.db.connection import Session, engine
from app.db.models import Notification
import jwt
from app.agent.auth import SECRET_KEY

router = APIRouter()


class ActionRequest(BaseModel):
    operation_type: str = "read"


@router.get("/notifications")
async def get_notifications(request: Request, status: str = "active"):
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

    with Session(engine) as session:
        notifications = session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == status
        ).order_by(Notification.created_at.desc()).all()

        return {
            "notifications": [
                {
                    "id": n.id,
                    "notification_type": n.notification_type,
                    "operation_type": n.operation_type,
                    "content_summary": n.content_summary,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                }
                for n in notifications
            ]
        }


@router.post("/notifications/{notification_id}/action")
async def execute_action(notification_id: int, body: ActionRequest, request: Request):
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

    with Session(engine) as session:
        notification = session.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            raise HTTPException(404, "Notification not found")

        notification.status = "dismissed"
        session.commit()

        return {"success": True}
