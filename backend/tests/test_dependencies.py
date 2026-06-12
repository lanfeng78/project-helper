# -*- coding: utf-8 -*-
from models import User
from auth_utils import hash_password


def _create_user(db_session, email="alice@example.com", username="alice"):
    user = User(
        username=username,
        email=email,
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_register_endpoint_creates_user(client):
    res = client.post("/api/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["username"] == "alice"
    assert data["user"]["email"] == "alice@example.com"
    assert "id" in data["user"]
    assert data["access_token"]
    assert data["refresh_token"]


def test_register_rejects_short_password(client):
    res = client.post("/api/auth/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "short",
    })
    assert res.status_code == 422


def test_register_rejects_invalid_username(client):
    res = client.post("/api/auth/register", json={
        "username": "bo@b",
        "email": "bob@example.com",
        "password": "password123",
    })
    assert res.status_code == 422


def test_register_duplicate_email_returns_409(client, db_session):
    _create_user(db_session, email="alice@example.com")
    res = client.post("/api/auth/register", json={
        "username": "alice2",
        "email": "alice@example.com",
        "password": "password123",
    })
    assert res.status_code == 409
    assert "邮箱" in res.json()["detail"]


def test_register_duplicate_username_returns_409(client, db_session):
    _create_user(db_session, username="alice")
    res = client.post("/api/auth/register", json={
        "username": "alice",
        "email": "different@example.com",
        "password": "password123",
    })
    assert res.status_code == 409
    assert "用户名" in res.json()["detail"]


def test_login_with_valid_credentials(client, db_session):
    _create_user(db_session)
    res = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "password123",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["email"] == "alice@example.com"


def test_login_with_wrong_password_returns_401(client, db_session):
    _create_user(db_session)
    res = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "wrongpass",
    })
    assert res.status_code == 401
    assert "邮箱或密码" in res.json()["detail"]


def test_login_with_nonexistent_email_returns_401(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert res.status_code == 401
    assert "邮箱或密码" in res.json()["detail"]


def test_me_endpoint_returns_current_user(client, db_session):
    _create_user(db_session)
    login = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "password123",
    })
    token = login.json()["access_token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "alice@example.com"


def test_me_endpoint_without_token_returns_401(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_endpoint_with_invalid_token_returns_401(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


def test_refresh_endpoint_returns_new_access(client, db_session):
    _create_user(db_session)
    login = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "password123",
    })
    refresh_token = login.json()["refresh_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token


def test_refresh_with_access_token_returns_401(client, db_session):
    _create_user(db_session)
    login = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "password123",
    })
    access = login.json()["access_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": access})
    assert res.status_code == 401


def test_refresh_with_garbage_returns_401(client):
    res = client.post("/api/auth/refresh", json={"refresh_token": "garbage"})
    assert res.status_code == 401


def test_logout_returns_200(client, db_session):
    _create_user(db_session)
    login = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "password123",
    })
    token = login.json()["access_token"]
    res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
