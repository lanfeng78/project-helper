# -*- coding: utf-8 -*-
from models import User


def test_user_table_exists(db_session):
    result = db_session.query(User).count()
    assert result == 0


def test_user_can_be_inserted(db_session):
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash="hashed_xxx",
    )
    db_session.add(user)
    db_session.commit()
    assert db_session.query(User).count() == 1
    fetched = db_session.query(User).filter_by(username="alice").first()
    assert fetched.email == "alice@example.com"
