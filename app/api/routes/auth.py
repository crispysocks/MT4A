from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from app.db.connection import get_session
from app.db.models import User
from app.agent.auth import AuthManager
from app.agent.soul import SoulManager

router = APIRouter()

soul_manager = SoulManager()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/register")
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    if req.role not in ("student", "employee"):
        raise HTTPException(400, "role must be 'student' or 'employee'")
    if len(req.username) < 2:
        raise HTTPException(400, "username too short")
    if len(req.password) < 4:
        raise HTTPException(400, "password too short")
    try:
        auth = AuthManager(session)
        user = auth.register(req.username, req.password, req.role)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.post("/auth/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    try:
        auth = AuthManager(session)
        token, role = auth.login(req.username, req.password)
        soul_manager.load(role)
        return {"token": token, "role": role}
    except ValueError as e:
        raise HTTPException(401, str(e))


@router.post("/auth/logout")
def logout():
    soul_manager.unload()
    return {"status": "logged_out"}


@router.get("/auth/me")
def me():
    if not soul_manager.is_active():
        return {"role": "guest"}
    return {"role": soul_manager.current_role}


@router.get("/employees")
def list_employees(session: Session = Depends(get_session)):
    employees = session.exec(
        select(User).where(User.role == "employee")
    ).all()
    return {
        "employees": [
            {"id": e.id, "username": e.username}
            for e in employees
        ]
    }
