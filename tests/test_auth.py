import pytest
import jwt
from datetime import datetime, timezone
from app.agent.auth import AuthManager, hash_password, verify_password


def test_hash_and_verify_password():
    password = "test1234"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_register_user(db_session):
    mgr = AuthManager(db_session)
    user = mgr.register("zhangsan", "pass1234", "student")
    assert user.username == "zhangsan"
    assert user.role == "student"
    assert user.password_hash != "pass1234"


def test_register_duplicate_username(db_session):
    mgr = AuthManager(db_session)
    mgr.register("lisi", "pass1", "student")
    with pytest.raises(ValueError, match="already exists"):
        mgr.register("lisi", "pass2", "employee")


def test_login_success(db_session):
    mgr = AuthManager(db_session)
    mgr.register("wangwu", "mypass", "employee")
    token, role = mgr.login("wangwu", "mypass")
    assert role == "employee"
    assert isinstance(token, str)


def test_login_wrong_password(db_session):
    mgr = AuthManager(db_session)
    mgr.register("testuser", "correct", "student")
    with pytest.raises(ValueError, match="Invalid"):
        mgr.login("testuser", "wrong")


def test_verify_token(db_session):
    mgr = AuthManager(db_session)
    user = mgr.register("tokenuser", "pass", "student")
    token, _ = mgr.login("tokenuser", "pass")
    payload = mgr.verify(token)
    assert payload["user_id"] == user.id
    assert payload["role"] == "student"
    assert payload["username"] == "tokenuser"


def test_verify_invalid_token(db_session):
    mgr = AuthManager(db_session)
    with pytest.raises(jwt.PyJWTError):
        mgr.verify("invalid.token.here")
