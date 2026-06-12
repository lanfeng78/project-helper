# -*- coding: utf-8 -*-
from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from models import get_db, User
from auth_utils import decode_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing or invalid Authorization header")
    token = authorization[7:]
    user_id = decode_token(token, expected_type="access")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "user not found")
    return user


def get_current_user_sse(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(token, expected_type="access")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "user not found")
    return user
