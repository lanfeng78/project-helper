# -*- coding: utf-8 -*-
import datetime as _dt
import jwt
from auth_utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from config import settings


def test_hash_and_verify_password():
    hashed = hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert verify_password("mypassword123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token(user_id=42)
    user_id = decode_token(token, expected_type="access")
    assert user_id == 42


def test_create_and_decode_refresh_token():
    token = create_refresh_token(user_id=7)
    user_id = decode_token(token, expected_type="refresh")
    assert user_id == 7


def test_access_token_cannot_be_used_as_refresh():
    token = create_access_token(user_id=1)
    try:
        decode_token(token, expected_type="refresh")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "invalid token type" in e.detail


def test_refresh_token_cannot_be_used_as_access():
    token = create_refresh_token(user_id=1)
    try:
        decode_token(token, expected_type="access")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "invalid token type" in e.detail


def test_expired_token_rejected():
    payload = {
        "sub": "1",
        "type": "access",
        "exp": _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(seconds=10),
        "iat": _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(seconds=20),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    try:
        decode_token(token, expected_type="access")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "expired" in e.detail


def test_invalid_signature_rejected():
    token = jwt.encode(
        {"sub": "1", "type": "access", "exp": 9999999999},
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )
    try:
        decode_token(token, expected_type="access")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "invalid" in e.detail


def test_token_with_missing_sub_returns_401():
    """token 缺少 sub 字段应被拒绝（不抛 500）。"""
    import datetime as _dt
    payload = {
        "type": "access",
        "exp": _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=5),
        "iat": _dt.datetime.now(_dt.timezone.utc),
        # no "sub" field
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    try:
        decode_token(token, expected_type="access")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "invalid" in e.detail


def test_token_with_non_numeric_sub_returns_401():
    """sub 不是数字应被拒绝。"""
    import datetime as _dt
    payload = {
        "sub": "not-a-number",
        "type": "access",
        "exp": _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=5),
        "iat": _dt.datetime.now(_dt.timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    try:
        decode_token(token, expected_type="access")
        assert False, "expected HTTPException"
    except Exception as e:
        assert e.status_code == 401
        assert "invalid" in e.detail
