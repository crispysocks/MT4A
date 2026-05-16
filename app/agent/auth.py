import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Tuple
from sqlmodel import Session, select
from app.db.models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


class AuthManager:
    def __init__(self, session: Session):
        self.session = session

    def register(self, username: str, password: str, role: str) -> User:
        existing = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing:
            raise ValueError(f"Username '{username}' already exists")
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def login(self, username: str, password: str) -> Tuple[str, str]:
        user = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token, user.role

    def verify(self, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
