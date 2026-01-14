from uuid import UUID

from sqlmodel import select

from main import app
from modules.user.user_model import User
from shared.dependencies import get_current_user


def test_register_user(client, session):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data

    user_in_db = session.exec(
        select(User).where(User.email == "test@example.com")
    ).first()
    assert user_in_db is not None


def test_login_user(client):
    """測試使用者登入 (Login)"""
    client.post(
        "/users/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "mypassword",
        },
    )

    login_payload = {
        "email": "login@example.com",
        "password": "mypassword",
        "remember": False,
    }
    response = client.post("/users/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_me_protected(client):
    reg_resp = client.post(
        "/users/register",
        json={"username": "me_user", "email": "me@example.com", "password": "pw"},
    )
    real_user_id = reg_resp.json()["user_id"]

    async def mock_get_current_user():
        return {
            "user_id": UUID(real_user_id),
            "email": "me@example.com",
        }

    app.dependency_overrides[get_current_user] = mock_get_current_user

    response = client.get("/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "me_user"

    del app.dependency_overrides[get_current_user]


def test_change_password(client):
    """測試修改密碼 (Update)"""
    client.post(
        "/users/register",
        json={
            "username": "pwd_user",
            "email": "pwd@example.com",
            "password": "old_password",
        },
    )

    async def mock_user_context():
        return {"user_id": "...", "email": "pwd@example.com"}

    app.dependency_overrides[get_current_user] = mock_user_context

    payload = {"old_password": "old_password", "new_password": "new_secure_password"}
    response = client.post("/users/change-password", json=payload)

    assert response.status_code == 200

    del app.dependency_overrides[get_current_user]

    login_resp = client.post(
        "/users/login",
        json={
            "email": "pwd@example.com",
            "password": "new_secure_password",
            "remember": False,
        },
    )
    assert login_resp.status_code == 200
