# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from models import get_db, User
from auth_utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _serialize_user(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email}


def _issue_tokens(user: User) -> dict:
    return {
        "user": _serialize_user(user),
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
    }


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(409, "该邮箱已被注册")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(409, "该用户名已被使用")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user)


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "邮箱或密码错误")
    return _issue_tokens(user)


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    user_id = decode_token(req.refresh_token, expected_type="refresh")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "user not found")
    return {
        "user": _serialize_user(user),
        "access_token": create_access_token(user.id),
        "refresh_token": req.refresh_token,
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"ok": True}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"user": _serialize_user(current_user)}
