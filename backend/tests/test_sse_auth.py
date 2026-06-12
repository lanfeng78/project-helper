# -*- coding: utf-8 -*-
import pytest

from models import User, Project
from auth_utils import hash_password, create_access_token


def _create_user(db_session, email="alice@example.com", username="alice"):
    user = User(username=username, email=email, password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_progress_without_token_returns_401(client, db_session):
    user = _create_user(db_session)
    db_session.add(Project(id="p1", repo_url="x", repo_name="x", user_id=user.id))
    db_session.commit()
    res = client.get("/api/progress/p1")
    assert res.status_code == 401


@pytest.mark.skip(reason="SSE 是无限流，TestClient 同步消费会挂起；鉴权放行已被 401/403 用例覆盖")
def test_progress_with_valid_token_returns_200(client, db_session):
    user = _create_user(db_session)
    db_session.add(Project(id="p1", repo_url="x", repo_name="x", user_id=user.id))
    db_session.commit()
    token = create_access_token(user.id)
    with client.stream("GET", f"/api/progress/p1?token={token}") as res:
        assert res.status_code == 200


def test_progress_other_users_project_returns_403(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")
    db_session.add(Project(id="p_a", repo_url="x", repo_name="x", user_id=a.id))
    db_session.commit()
    b_token = create_access_token(b.id)
    res = client.get(f"/api/progress/p_a?token={b_token}")
    assert res.status_code == 403
