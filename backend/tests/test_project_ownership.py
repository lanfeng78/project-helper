# -*- coding: utf-8 -*-
from models import User, Project
from auth_utils import hash_password


def _create_user(db_session, email, username):
    user = User(
        username=username,
        email=email,
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email):
    res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_projects_requires_auth(client):
    res = client.get("/api/projects")
    assert res.status_code == 401


def test_list_projects_only_returns_own(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")
    db_session.add(Project(id="p_a", repo_url="https://github.com/x/a", repo_name="a", status="done", user_id=a.id))
    db_session.add(Project(id="p_b", repo_url="https://github.com/x/b", repo_name="b", status="done", user_id=b.id))
    db_session.commit()

    a_token = _login(client, "a@x.com")
    res = client.get("/api/projects", headers=_auth(a_token))
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert ids == ["p_a"]


def test_get_report_other_users_project_returns_403(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")
    db_session.add(Project(id="p_a", repo_url="https://github.com/x/a", repo_name="a",
                           status="done", user_id=a.id))
    db_session.commit()

    b_token = _login(client, "b@x.com")
    res = client.get("/api/report/p_a", headers=_auth(b_token))
    assert res.status_code == 403
    assert "无权" in res.json()["detail"]


def test_delete_other_users_project_returns_403(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")
    db_session.add(Project(id="p_a", repo_url="https://github.com/x/a", repo_name="a", user_id=a.id))
    db_session.commit()

    b_token = _login(client, "b@x.com")
    res = client.delete("/api/projects/p_a", headers=_auth(b_token))
    assert res.status_code == 403


def test_own_user_can_access_their_project(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    db_session.add(Project(id="p_a", repo_url="https://github.com/x/a", repo_name="a",
                           status="done", report_json='{"k":1}', user_id=a.id))
    db_session.commit()

    a_token = _login(client, "a@x.com")
    res = client.get("/api/report/p_a", headers=_auth(a_token))
    assert res.status_code == 200
    assert res.json()["report_json"] == {"k": 1}


def test_analyze_requires_auth(client):
    res = client.post("/api/analyze", json={"repo_url": "https://github.com/x/y"})
    assert res.status_code == 401


def test_analyze_cache_hit_does_not_leak_other_users_report(client, db_session, monkeypatch):
    """User A's cached report must not be returned to user B."""
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")

    # User A has a finished project for some repo
    repo_url = "https://github.com/facebook/react"
    repo_hash = "fakehash_react"
    db_session.add(Project(
        id=f"u{a.id}_{repo_hash}",
        repo_url=repo_url,
        repo_name="react",
        repo_hash=repo_hash,
        status="done",
        report_json='{"a_secret": "for A only"}',
        user_id=a.id,
    ))
    db_session.commit()

    # Stub repo_id so we get the predictable hash
    import main as main_mod
    monkeypatch.setattr(main_mod, "repo_id", lambda url: repo_hash)

    # User B calls /api/analyze on the same URL
    b_token = _login(client, "b@x.com")
    res = client.post("/api/analyze", json={"repo_url": repo_url}, headers=_auth(b_token))

    # Must NOT return user A's report. Either creates B's own project (200/202 with status pending)
    # or returns 200 with cached=False, and CRUCIALLY: project_id should be u{B.id}_{hash}, not u{A.id}_{hash}.
    assert res.status_code == 200
    body = res.json()
    assert body["project_id"] == f"u{b.id}_{repo_hash}"
    # User B should not see user A's report content
    if "report_json" in body:
        assert body["report_json"] != {"a_secret": "for A only"}


def test_qa_other_users_project_returns_403(client, db_session):
    a = _create_user(db_session, "a@x.com", "userA")
    b = _create_user(db_session, "b@x.com", "userB")
    db_session.add(Project(
        id=f"u{a.id}_xyz",
        repo_url="https://github.com/x/y",
        repo_name="y",
        repo_hash="xyz",
        status="done",
        user_id=a.id,
    ))
    db_session.commit()

    b_token = _login(client, "b@x.com")
    res = client.post("/api/qa",
        json={"project_id": f"u{a.id}_xyz", "question": "hi", "conversation": []},
        headers=_auth(b_token),
    )
    assert res.status_code == 403
