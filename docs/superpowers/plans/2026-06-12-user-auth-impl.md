# 用户注册登录模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Project Helper 增加 JWT 双 token 鉴权 + 用户系统，所有分析项目归属创建者。

**Architecture:** 后端新增 User 表与 Project.user_id 外键；新增 auth_utils（密码哈希+JWT）、dependencies（鉴权依赖）、auth（路由）三个模块；现有路由加 `current_user` 依赖。前端新增 Pinia auth store、`api/auth.js`、`authedFetch` 拦截器、路由守卫、Login/Register 页、NavBar 改用户信息。

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (后端)；PyJWT + passlib[bcrypt]（新增）；Vue 3 + Pinia + Vue Router（前端）；pytest + httpx（测试）。

**Spec:** `docs/superpowers/specs/2026-06-12-user-auth-design.md`

---

## 文件结构总览

**后端新建：**
- `backend/auth_utils.py` — 密码哈希、JWT 签发/验证
- `backend/dependencies.py` — `get_current_user`（Bearer 头 + SSE query 两种）
- `backend/auth.py` — 注册/登录/刷新/登出/me 五个路由
- `backend/tests/__init__.py`
- `backend/tests/conftest.py` — 测试夹具
- `backend/tests/test_user_model.py`
- `backend/tests/test_auth_utils.py`
- `backend/tests/test_dependencies.py`
- `backend/tests/test_project_ownership.py`
- `backend/tests/test_sse_auth.py`

**后端修改：**
- `backend/requirements.txt` — 新增 4 个依赖
- `backend/config.py` — 新增 jwt_secret 等
- `backend/models.py` — 新增 User 表；Project 加 user_id 外键
- `backend/main.py` — 挂载 auth 路由；现有路由加 current_user 依赖；清空旧项目

**前端新建：**
- `frontend/src/api/auth.js`
- `frontend/src/stores/auth.js`
- `frontend/src/views/LoginPage.vue`
- `frontend/src/views/RegisterPage.vue`

**前端修改：**
- `frontend/src/api/index.js` — `authedFetch` 拦截器
- `frontend/src/router/index.js` — 路由守卫 + 新增 login/register 路由
- `frontend/src/components/NavBar.vue` — 用户信息 + 登出按钮
- `frontend/src/views/HomePage.vue` — 未登录显示登录入口
- `frontend/src/main.js` — 启动时静默恢复会话

---

## Task 1: 更新后端依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 4 个新依赖**

在 `backend/requirements.txt` 末尾追加：

```
passlib[bcrypt]==1.7.4
PyJWT==2.10.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: 安装依赖**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && pip install -r requirements.txt
```
Expected: Successfully installed passlib-1.7.4 PyJWT-2.10.1 pytest-8.3.4 pytest-asyncio-0.25.0

- [ ] **Step 3: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/requirements.txt && git commit -m "chore: add auth dependencies (passlib, pyjwt, pytest)"
```

---

## Task 2: 添加 JWT 配置

**Files:**
- Modify: `backend/config.py`

- [ ] **Step 1: 修改 Settings 类**

将整个 `backend/config.py` 替换为：

```python
# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    deepseek_api_key: str = "sk-3e7ab7379d5443dfb4f374d0fbc7b114"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    db_path: str = str(Path(__file__).parent / "projects.db")
    repos_dir: str = str(Path(__file__).parent / "repos")
    max_file_size: int = 200 * 1024
    max_total_size: int = 5 * 1024 * 1024

    # Auth
    jwt_secret: str = "change-me-in-prod-please-use-32-chars-min"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
```

- [ ] **Step 2: 验证可导入**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -c "from config import settings; print(settings.jwt_secret[:10])"
```
Expected: `change-me-`

- [ ] **Step 3: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/config.py && git commit -m "feat(config): add JWT settings"
```

---

## Task 3: 添加 User 表与迁移逻辑（TDD）

**Files:**
- Modify: `backend/models.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_user_model.py`

- [ ] **Step 1: 写 conftest 测试夹具**

创建 `backend/tests/__init__.py`（空文件）和 `backend/tests/conftest.py`：

```python
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, get_db
from main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    yield TestingSessionLocal()
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 2: 写测试**

创建 `backend/tests/test_user_model.py`：

```python
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
```

- [ ] **Step 3: 运行测试，确认失败**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_user_model.py -v
```
Expected: FAIL（User 类不存在）

- [ ] **Step 4: 写 User 模型与迁移**

将 `backend/models.py` 替换为：

```python
# -*- coding: utf-8 -*-
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Float, Integer, ForeignKey, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from config import settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    repo_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    progress_msg = Column(String(512), default="")
    tech_stack = Column(Text, default="")
    report_json = Column(Text, default="")
    report_markdown = Column(Text, default="")
    error_msg = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User", backref="projects")


engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False, "timeout": 30}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def init_db():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    has_users = inspector.has_table("users")
    Base.metadata.create_all(bind=engine)
    if not has_users:
        with engine.begin() as conn:
            cols = [c["name"] for c in inspector.get_columns("projects")]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN user_id INTEGER"))
            conn.execute(text("DELETE FROM projects"))
            conn.execute(text("DELETE FROM sqlite_sequence WHERE name='projects'"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: 运行测试，确认通过**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_user_model.py -v
```
Expected: 2 passed

- [ ] **Step 6: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/models.py backend/tests/__init__.py backend/tests/conftest.py backend/tests/test_user_model.py && git commit -m "feat(models): add User table and project user_id foreign key"
```

---

## Task 4: 实现密码哈希与 JWT 工具（TDD）

**Files:**
- Create: `backend/auth_utils.py`
- Create: `backend/tests/test_auth_utils.py`

- [ ] **Step 1: 写测试**

创建 `backend/tests/test_auth_utils.py`：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_auth_utils.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'auth_utils'`

- [ ] **Step 3: 实现 auth_utils.py**

创建 `backend/auth_utils.py`：

```python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_ttl_min),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_ttl_days),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")
    if payload.get("type") != expected_type:
        raise HTTPException(401, "invalid token type")
    return int(payload["sub"])
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_auth_utils.py -v
```
Expected: 7 passed

- [ ] **Step 5: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/auth_utils.py backend/tests/test_auth_utils.py && git commit -m "feat(auth): add password hashing and JWT utilities"
```

---

## Task 5: 实现鉴权依赖 + auth 路由（TDD）

**Files:**
- Create: `backend/dependencies.py`
- Create: `backend/auth.py`
- Modify: `backend/main.py`（仅添加 include_router + 新 import）
- Create: `backend/tests/test_dependencies.py`

- [ ] **Step 1: 写测试**

创建 `backend/tests/test_dependencies.py`：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_dependencies.py -v 2>&1 | head -10
```
Expected: ImportError（auth 模块尚不存在）

- [ ] **Step 3: 实现 dependencies.py**

创建 `backend/dependencies.py`：

```python
# -*- coding: utf-8 -*-
from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from models import get_db, User
from auth_utils import decode_token


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
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
```

- [ ] **Step 4: 实现 auth.py**

创建 `backend/auth.py`：

```python
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
```

- [ ] **Step 5: 在 main.py 挂载 auth 路由**

打开 `backend/main.py`，将导入区从：

```python
from config import settings
from models import init_db, get_db, Project
from repo_manager import repo_id, clone_repo, scan_codebase, build_context_summary, fetch_via_api
from analyzer import analyze_codebase, build_markdown_report
from qa_engine import answer_question
```

改为：

```python
from config import settings
from models import init_db, get_db, Project, User
from repo_manager import repo_id, clone_repo, scan_codebase, build_context_summary, fetch_via_api
from analyzer import analyze_codebase, build_markdown_report
from qa_engine import answer_question
from auth import router as auth_router
from dependencies import get_current_user, get_current_user_sse
```

然后在 `app.add_middleware(...)` 之后追加：

```python
app.include_router(auth_router)
```

- [ ] **Step 6: 运行测试，确认通过**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_dependencies.py -v
```
Expected: 14 passed

- [ ] **Step 7: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/dependencies.py backend/auth.py backend/main.py backend/tests/test_dependencies.py && git commit -m "feat(auth): add register/login/refresh/logout/me routes and dependencies"
```

---

## Task 6: 给现有项目路由加鉴权与归属过滤（TDD）

**Files:**
- Modify: `backend/main.py`（完整替换）
- Create: `backend/tests/test_project_ownership.py`

- [ ] **Step 1: 写测试**

创建 `backend/tests/test_project_ownership.py`：

```python
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
    db_session.add(Project(id="p_a", repo_url="https://github.com/x/a", repo_name="a", user_id=a.id))
    db_session.add(Project(id="p_b", repo_url="https://github.com/x/b", repo_name="b", user_id=b.id))
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
```

- [ ] **Step 2: 运行测试，确认多数失败**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_project_ownership.py -v 2>&1 | tail -15
```
Expected: 多数测试 FAIL

- [ ] **Step 3: 完整替换 main.py**

将 `backend/main.py` 完整替换为：

```python
# -*- coding: utf-8 -*-
import json
import asyncio
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from config import settings
from models import init_db, get_db, Project, User
from repo_manager import repo_id, clone_repo, scan_codebase, build_context_summary, fetch_via_api
from analyzer import analyze_codebase, build_markdown_report
from qa_engine import answer_question
from auth import router as auth_router
from dependencies import get_current_user, get_current_user_sse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    Path(settings.repos_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Project Helper", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


class AnalyzeRequest(BaseModel):
    repo_url: str


class QARequest(BaseModel):
    project_id: str
    question: str
    conversation: list[dict] = []


progress_store: dict[str, dict] = {}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start analysis of a GitHub repo. Returns immediately with project_id."""
    pid = repo_id(req.repo_url)

    existing = db.query(Project).filter(Project.id == pid).first()
    if existing and existing.status == "done":
        return {
            "project_id": pid,
            "status": "done",
            "cached": True,
            "report_json": json.loads(existing.report_json) if existing.report_json else {},
            "report_markdown": existing.report_markdown,
        }

    if existing:
        existing.status = "pending"
        existing.progress = 0.0
        existing.progress_msg = "准备分析..."
        existing.error_msg = ""
        existing.user_id = current_user.id
    else:
        existing = Project(
            id=pid,
            repo_url=req.repo_url,
            repo_name=req.repo_url.rstrip("/").split("/")[-1],
            status="pending",
            user_id=current_user.id,
        )
        db.add(existing)
    db.commit()

    progress_store[pid] = {"progress": 0, "msg": "正在准备..."}

    thread = threading.Thread(
        target=_run_analysis,
        args=(pid, req.repo_url, current_user.id),
        daemon=True,
    )
    thread.start()

    return {"project_id": pid, "status": "pending", "cached": False}


@app.get("/api/progress/{project_id}")
async def progress(
    project_id: str,
    current_user: User = Depends(get_current_user_sse),
    db: Session = Depends(get_db),
):
    """SSE endpoint for real-time progress with keepalive pings."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")

    async def event_stream():
        last_progress = -1
        last_msg = ""
        silent_count = 0

        while True:
            data = progress_store.get(project_id, {"progress": 0, "msg": "等待中..."})
            pct = data.get("progress", 0)
            msg = data.get("msg", "")

            if pct != last_progress or msg != last_msg:
                last_progress = pct
                last_msg = msg
                silent_count = 0
                yield {
                    "event": "progress",
                    "data": json.dumps({"progress": pct, "msg": msg}, ensure_ascii=False)
                }
            else:
                silent_count += 1
                if silent_count >= 15:
                    silent_count = 0
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"progress": pct, "msg": msg}, ensure_ascii=False)
                    }

            if data.get("done"):
                yield {
                    "event": "done",
                    "data": json.dumps({"progress": 100, "msg": "分析完成!"}, ensure_ascii=False)
                }
                await asyncio.sleep(0.5)
                break

            if data.get("error"):
                yield {
                    "event": "error",
                    "data": json.dumps({"progress": pct, "msg": data.get("msg", "")}, ensure_ascii=False)
                }
                await asyncio.sleep(0.5)
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_stream())


@app.get("/api/report/{project_id}")
def get_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the analysis report for a project."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")
    if proj.status == "error":
        raise HTTPException(400, proj.error_msg or "分析失败")
    if proj.status != "done":
        return {"status": proj.status, "progress": proj.progress}

    return {
        "project_id": proj.id,
        "repo_url": proj.repo_url,
        "repo_name": proj.repo_name,
        "status": "done",
        "report_json": json.loads(proj.report_json) if proj.report_json else {},
        "report_markdown": proj.report_markdown,
    }


@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a cached project and its repo files."""
    import shutil
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")
    db.delete(proj)
    db.commit()
    repo_path = Path(settings.repos_dir) / project_id
    if repo_path.exists():
        shutil.rmtree(repo_path, ignore_errors=True)
    return {"deleted": project_id}


@app.get("/api/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List current user's cached/completed projects."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.status == "done")
        .order_by(Project.updated_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": p.id,
            "repo_url": p.repo_url,
            "repo_name": p.repo_name,
            "updated_at": p.updated_at.isoformat() if p.updated_at else "",
            "tech_stack": p.tech_stack[:200] if p.tech_stack else "",
        }
        for p in projects
    ]


@app.post("/api/qa")
async def qa(
    req: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Streaming Q&A about a project's source code."""
    proj = db.query(Project).filter(Project.id == req.project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")
    if proj.status != "done":
        raise HTTPException(400, "Project not analyzed yet")

    repo_path = Path(settings.repos_dir) / req.project_id
    if not repo_path.exists():
        raise HTTPException(404, "Repository files not found. Please re-analyze.")

    files = scan_codebase(repo_path)
    context = build_context_summary(files)

    async def stream_qa():
        async for token in answer_question(context, req.conversation, req.question):
            yield token

    return StreamingResponse(
        stream_qa(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


def _run_analysis(pid: str, repo_url: str, user_id: int):
    """Run the full analysis pipeline in a background thread."""
    from models import SessionLocal
    db = SessionLocal()
    try:
        def update(pct: float, msg: str):
            progress_store[pid] = {"progress": round(pct * 100, 1), "msg": msg}
            if pct >= 1.0 or pct <= 0.02 or int(pct * 100) % 25 == 0:
                proj = db.query(Project).filter(Project.id == pid).first()
                if proj:
                    proj.progress = round(pct * 100, 1)
                    proj.progress_msg = msg
                    proj.status = "analyzing"
                    db.commit()

        update(0.01, "通过 GitHub API 获取源码...")
        try:
            files, context = fetch_via_api(repo_url, progress_cb=update)
        except Exception as api_err:
            update(0.01, f"API 模式失败: {api_err}，尝试 git clone...")
            repo_path = clone_repo(repo_url, progress_cb=update)
            files = scan_codebase(repo_path, progress_cb=update)
            context = build_context_summary(files)

        update(0.72, "AI 正在分析项目结构...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report = loop.run_until_complete(analyze_codebase(context, progress_cb=update))
        finally:
            loop.close()

        markdown = build_markdown_report(report)

        proj = db.query(Project).filter(Project.id == pid).first()
        if proj:
            proj.status = "done"
            proj.progress = 100.0
            proj.progress_msg = "分析完成!"
            proj.report_json = json.dumps(report, ensure_ascii=False)
            proj.report_markdown = markdown
            proj.tech_stack = str(report.get("tech_stack", ""))
            proj.updated_at = datetime.now(timezone.utc)
            db.commit()

        progress_store[pid] = {"progress": 100.0, "msg": "分析完成!", "done": True}

    except Exception as e:
        error_text = str(e)
        proj = db.query(Project).filter(Project.id == pid).first()
        if proj:
            proj.status = "error"
            proj.error_msg = error_text
            db.commit()
        progress_store[pid] = {"progress": 0.0, "msg": error_text, "error": True}

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 4: 运行全部测试**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/ -v
```
Expected: 全部测试通过

- [ ] **Step 5: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/main.py backend/tests/test_project_ownership.py && git commit -m "feat(auth): add auth requirements and project ownership to existing routes"
```

---

## Task 7: SSE query token 鉴权测试

**Files:**
- Create: `backend/tests/test_sse_auth.py`

- [ ] **Step 1: 写测试**

创建 `backend/tests/test_sse_auth.py`：

```python
# -*- coding: utf-8 -*-
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
```

- [ ] **Step 2: 运行测试**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest tests/test_sse_auth.py -v
```
Expected: 3 passed

- [ ] **Step 3: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add backend/tests/test_sse_auth.py && git commit -m "test: add SSE auth tests"
```

---

## Task 8: 删除旧库验证 init_db 迁移

- [ ] **Step 1: 删除旧 DB 文件**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && rm -f projects.db projects.db-shm projects.db-wal
```

- [ ] **Step 2: 启动后端触发 init_db**

Run (前台, Ctrl+C 结束):
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Expected: 服务启动，控制台显示 `Application startup complete.`

- [ ] **Step 3: 验证注册可用 + 未鉴权被拒**

Run (新终端):
```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/register -H "Content-Type: application/json" -d '{"username":"alice","email":"alice@example.com","password":"password123"}'
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/projects
```
Expected: 第一个返回含 `access_token` 的 JSON；第二个返回 `401`

- [ ] **Step 4: 关闭后端（Ctrl+C）**

---

## Task 9: 前端 auth API 封装

**Files:**
- Create: `frontend/src/api/auth.js`

- [ ] **Step 1: 创建 auth.js**

创建 `frontend/src/api/auth.js`：

```javascript
const BASE = '/api/auth'

async function handleAuthResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function register(username, email, password) {
  const res = await fetch(`${BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  return handleAuthResponse(res)
}

export async function login(email, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  return handleAuthResponse(res)
}

export async function refresh(refreshToken) {
  const res = await fetch(`${BASE}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  })
  return handleAuthResponse(res)
}

export async function logout() {
  try {
    await fetch(`${BASE}/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
  } catch {
    // 忽略网络错误
  }
}

export async function fetchMe(accessToken) {
  const res = await fetch(`${BASE}/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  })
  if (!res.ok) throw new Error('Not authenticated')
  return res.json()
}
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/api/auth.js && git commit -m "feat(frontend): add auth API client"
```

---

## Task 10: 前端 Pinia auth store

**Files:**
- Create: `frontend/src/stores/auth.js`

- [ ] **Step 1: 创建 auth store**

创建 `frontend/src/stores/auth.js`：

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref('')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  function setTokens({ access_token, refresh_token }) {
    accessToken.value = access_token
    refreshToken.value = refresh_token
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token)
    }
  }

  function clear() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('refresh_token')
  }

  async function login(email, password) {
    const data = await authApi.login(email, password)
    setTokens(data)
    user.value = data.user
  }

  async function registerUser(username, email, password) {
    const data = await authApi.register(username, email, password)
    setTokens(data)
    user.value = data.user
  }

  async function tryRefresh() {
    if (!refreshToken.value) return false
    try {
      const data = await authApi.refresh(refreshToken.value)
      setTokens(data)
      return true
    } catch {
      clear()
      return false
    }
  }

  async function tryRestoreSession() {
    if (!refreshToken.value) return false
    try {
      const data = await authApi.refresh(refreshToken.value)
      setTokens(data)
      const me = await authApi.fetchMe(data.access_token)
      user.value = me.user
      return true
    } catch {
      clear()
      return false
    }
  }

  async function logout() {
    try { await authApi.logout() } catch {}
    clear()
  }

  return {
    user, accessToken, refreshToken,
    login, registerUser, logout,
    tryRestoreSession, tryRefresh, clear
  }
})
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/stores/auth.js && git commit -m "feat(frontend): add Pinia auth store with token persistence"
```

---

## Task 11: 前端 authedFetch 拦截器

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 替换 api/index.js**

将 `frontend/src/api/index.js` 完整替换为：

```javascript
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const BASE = '/api'

export async function authedFetch(url, options = {}) {
  const auth = useAuthStore()
  const headers = { ...(options.headers || {}) }

  if (auth.accessToken) {
    headers['Authorization'] = `Bearer ${auth.accessToken}`
  }

  let res = await fetch(url, { ...options, headers })

  if (res.status === 401 && auth.refreshToken) {
    const ok = await auth.tryRefresh()
    if (ok) {
      headers['Authorization'] = `Bearer ${auth.accessToken}`
      res = await fetch(url, { ...options, headers })
    } else {
      router.push('/login')
      throw new Error('会话已过期，请重新登录')
    }
  }

  return res
}

export async function analyzeRepo(repoUrl) {
  const res = await authedFetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export function subscribeProgress(projectId, onProgress, onDone, onError) {
  const auth = useAuthStore()
  const url = `${BASE}/progress/${projectId}?token=${encodeURIComponent(auth.accessToken)}`
  let reconnectAttempts = 0
  const MAX_RECONNECT = 3
  let es = null

  function connect() {
    es = new EventSource(url)

    es.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data)
        onProgress(data)
      } catch {}
    })

    es.addEventListener('keepalive', () => {
      reconnectAttempts = 0
    })

    es.addEventListener('done', (e) => {
      es.close()
      try {
        const data = JSON.parse(e.data)
        onDone(data)
      } catch {
        onDone({})
      }
    })

    es.addEventListener('error', (e) => {
      es.close()
      try {
        if (e.data) {
          const data = JSON.parse(e.data)
          onError(data)
          return
        }
      } catch {}

      reconnectAttempts++
      if (reconnectAttempts <= MAX_RECONNECT) {
        setTimeout(connect, 2000)
        onProgress({ progress: 0, msg: `连接断开，正在重试 (${reconnectAttempts}/${MAX_RECONNECT})...` })
      } else {
        onError({ msg: '连接超时。分析可能仍在后台进行，请稍后刷新页面查看结果。' })
      }
    })

    es.onerror = () => {}
  }

  connect()
  return {
    close: () => { if (es) es.close() }
  }
}

export async function getReport(projectId) {
  const res = await authedFetch(`${BASE}/report/${projectId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Report not found' }))
    throw new Error(err.detail || 'Report not found')
  }
  return res.json()
}

export async function listProjects() {
  const res = await authedFetch(`${BASE}/projects`)
  return res.json()
}

export async function streamQA(projectId, question, conversation, onToken, onDone, onError) {
  const auth = useAuthStore()
  try {
    const res = await fetch(`${BASE}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.accessToken}`
      },
      body: JSON.stringify({ project_id: projectId, question, conversation })
    })
    if (!res.ok) {
      if (res.status === 401) {
        const ok = await auth.tryRefresh()
        if (ok) return streamQA(projectId, question, conversation, onToken, onDone, onError)
      }
      throw new Error('QA failed')
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onToken(decoder.decode(value, { stream: true }))
    }
    onDone()
  } catch (e) {
    onError(e.message)
  }
}

export async function deleteProject(projectId) {
  const res = await authedFetch(`${BASE}/projects/${projectId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
  return res.json()
}
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/api/index.js && git commit -m "feat(frontend): add authedFetch with auto refresh and SSE token query"
```

---

## Task 12: 前端路由守卫 + login/register 路由

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: 替换 router**

将 `frontend/src/router/index.js` 完整替换为：

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginPage.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterPage.vue') },
  { path: '/analyze/:id', name: 'Analyze', component: () => import('@/views/AnalyzePage.vue') },
  { path: '/report/:id', name: 'Report', component: () => import('@/views/ReportPage.vue') },
  { path: '/qa/:id', name: 'QA', component: () => import('@/views/QAPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const PUBLIC_ROUTES = new Set(['Home', 'Login', 'Register'])

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && auth.refreshToken) {
    await auth.tryRestoreSession()
  }

  if (!PUBLIC_ROUTES.has(to.name) && !auth.user) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (auth.user && (to.name === 'Login' || to.name === 'Register')) {
    return { name: 'Home' }
  }
})

export default router
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/router/index.js && git commit -m "feat(frontend): add auth route guard and login/register routes"
```

---

## Task 13: LoginPage 组件

**Files:**
- Create: `frontend/src/views/LoginPage.vue`

- [ ] **Step 1: 创建 LoginPage.vue**

创建 `frontend/src/views/LoginPage.vue`：

```vue
<template>
  <div class="auth-page">
    <div class="auth-card glass-card">
      <h1 class="auth-title">登录</h1>
      <p class="auth-sub">欢迎回来，继续你的项目探索</p>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="input-field"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="input-field"
            placeholder="至少 8 位"
            required
            autocomplete="current-password"
            minlength="8"
          />
        </div>

        <Transition name="fade">
          <p v-if="error" class="error-msg">{{ error }}</p>
        </Transition>

        <button type="submit" class="btn btn-primary auth-submit" :disabled="loading">
          <span v-if="!loading">登录</span>
          <span v-else class="spinner"></span>
        </button>
      </form>

      <p class="auth-switch">
        还没账号？<router-link :to="{ name: 'Register' }">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
  padding: var(--space-6);
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: var(--space-10);
}
.auth-title {
  font-size: 2rem;
  margin-bottom: var(--space-2);
  text-align: center;
}
.auth-sub {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: var(--space-8);
  font-size: 0.9rem;
}
.auth-form { display: flex; flex-direction: column; gap: var(--space-5); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); }
.form-group label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
.auth-submit { margin-top: var(--space-2); width: 100%; }
.error-msg {
  color: var(--neon-coral);
  font-size: 0.85rem;
  text-align: center;
  padding: var(--space-3);
  background: rgba(255, 82, 82, 0.08);
  border: 1px solid rgba(255, 82, 82, 0.2);
  border-radius: var(--radius-sm);
}
.auth-switch {
  text-align: center;
  margin-top: var(--space-6);
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/views/LoginPage.vue && git commit -m "feat(frontend): add LoginPage"
```

---

## Task 14: RegisterPage 组件

**Files:**
- Create: `frontend/src/views/RegisterPage.vue`

- [ ] **Step 1: 创建 RegisterPage.vue**

创建 `frontend/src/views/RegisterPage.vue`：

```vue
<template>
  <div class="auth-page">
    <div class="auth-card glass-card">
      <h1 class="auth-title">注册</h1>
      <p class="auth-sub">创建账号，开启你的开源之旅</p>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="input-field"
            placeholder="3-32 位字母数字下划线"
            required
            autocomplete="username"
            pattern="^[a-zA-Z0-9_]{3,32}$"
            :class="{ 'input-error': fieldError.username }"
          />
          <span v-if="fieldError.username" class="field-error">{{ fieldError.username }}</span>
        </div>

        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="input-field"
            placeholder="you@example.com"
            required
            autocomplete="email"
            :class="{ 'input-error': fieldError.email }"
          />
          <span v-if="fieldError.email" class="field-error">{{ fieldError.email }}</span>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="input-field"
            placeholder="至少 8 位"
            required
            autocomplete="new-password"
            minlength="8"
            :class="{ 'input-error': fieldError.password }"
          />
          <span v-if="fieldError.password" class="field-error">{{ fieldError.password }}</span>
        </div>

        <Transition name="fade">
          <p v-if="generalError" class="error-msg">{{ generalError }}</p>
        </Transition>

        <button type="submit" class="btn btn-primary auth-submit" :disabled="loading">
          <span v-if="!loading">创建账号</span>
          <span v-else class="spinner"></span>
        </button>
      </form>

      <p class="auth-switch">
        已有账号？<router-link :to="{ name: 'Login' }">直接登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', email: '', password: '' })
const fieldError = reactive({ username: '', email: '', password: '' })
const generalError = ref('')
const loading = ref(false)

function validate() {
  fieldError.username = ''
  fieldError.email = ''
  fieldError.password = ''

  if (!/^[a-zA-Z0-9_]{3,32}$/.test(form.username)) {
    fieldError.username = '用户名必须为 3-32 位字母、数字或下划线'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    fieldError.email = '邮箱格式不正确'
  }
  if (form.password.length < 8) {
    fieldError.password = '密码至少 8 位'
  }

  return !fieldError.username && !fieldError.email && !fieldError.password
}

async function handleSubmit() {
  generalError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    await auth.registerUser(form.username, form.email, form.password)
    router.push('/')
  } catch (e) {
    generalError.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
  padding: var(--space-6);
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: var(--space-10);
}
.auth-title {
  font-size: 2rem;
  margin-bottom: var(--space-2);
  text-align: center;
}
.auth-sub {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: var(--space-8);
  font-size: 0.9rem;
}
.auth-form { display: flex; flex-direction: column; gap: var(--space-5); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); }
.form-group label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
.auth-submit { margin-top: var(--space-2); width: 100%; }
.input-error { border-color: var(--neon-coral) !important; }
.field-error { font-size: 0.78rem; color: var(--neon-coral); }
.error-msg {
  color: var(--neon-coral);
  font-size: 0.85rem;
  text-align: center;
  padding: var(--space-3);
  background: rgba(255, 82, 82, 0.08);
  border: 1px solid rgba(255, 82, 82, 0.2);
  border-radius: var(--radius-sm);
}
.auth-switch {
  text-align: center;
  margin-top: var(--space-6);
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/views/RegisterPage.vue && git commit -m "feat(frontend): add RegisterPage"
```

---

## Task 15: NavBar 加用户信息 + 登出

**Files:**
- Modify: `frontend/src/components/NavBar.vue`

- [ ] **Step 1: 替换 NavBar.vue**

将 `frontend/src/components/NavBar.vue` 完整替换为：

```vue
<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="logo">
        <div class="logo-mark">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.3"/>
            <rect x="14" y="3" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.6"/>
            <rect x="3" y="14" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.8"/>
            <rect x="14" y="14" width="7" height="7" rx="1.5" fill="currentColor"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">Project Helper</span>
          <span class="logo-sub">AI-Powered Code Analyzer</span>
        </div>
      </router-link>
      <div class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          Home
        </router-link>
        <a href="https://github.com" target="_blank" class="nav-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
          GitHub
        </a>

        <template v-if="auth.user">
          <div class="user-chip">
            <span class="user-avatar">{{ auth.user.username.charAt(0).toUpperCase() }}</span>
            <span class="user-name">{{ auth.user.username }}</span>
          </div>
          <button class="nav-link nav-link-btn" @click="handleLogout">登出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link" exact-active-class="active">登录</router-link>
          <router-link to="/register" class="nav-link nav-link-cta" exact-active-class="active">注册</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(6, 11, 26, 0.8);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--border-subtle);
}

.nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--space-6);
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo { display: flex; align-items: center; gap: 12px; text-decoration: none; }
.logo-mark { color: var(--neon-cyan); }
.logo-text { display: flex; flex-direction: column; }
.logo-name { font-size: 1rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.logo-sub { font-size: 0.65rem; color: var(--text-muted); font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; }

.nav-links { display: flex; align-items: center; gap: var(--space-2); }

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--duration-fast);
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
}
.nav-link:hover { color: var(--text-primary); background: rgba(255,255,255,0.04); }
.nav-link.active { color: var(--neon-cyan); background: var(--neon-cyan-10); }
.nav-link-cta {
  background: var(--gradient-btn);
  color: #fff !important;
  font-weight: 600;
}
.nav-link-cta:hover { box-shadow: 0 0 16px rgba(0, 229, 255, 0.3); }
.nav-link-btn { color: var(--text-secondary); }
.nav-link-btn:hover { color: var(--neon-coral); }

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px 4px 4px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  margin-left: var(--space-2);
}
.user-avatar {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--gradient-btn);
  color: #fff;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.85rem;
}
.user-name {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .nav-inner { padding: 0 var(--space-4); }
  .logo-sub { display: none; }
  .user-name { display: none; }
}
</style>
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/components/NavBar.vue && git commit -m "feat(frontend): add user info and logout to NavBar"
```

---

## Task 16: HomePage 未登录态显示登录入口

**Files:**
- Modify: `frontend/src/views/HomePage.vue`

- [ ] **Step 1: 在 template 顶部加 banner**

读取 `frontend/src/views/HomePage.vue` 找到 `<section class="hero">`，在它**之前**插入：

```vue
<Transition name="fade">
  <div v-if="!auth.user" class="login-banner glass-card">
    <div class="login-banner-icon">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
    <div class="login-banner-text">
      <h3>登录以保存你的项目</h3>
      <p>每个分析的项目都会归你所有，随时回看</p>
    </div>
    <div class="login-banner-actions">
      <router-link :to="{ name: 'Login' }" class="btn btn-secondary">登录</router-link>
      <router-link :to="{ name: 'Register' }" class="btn btn-primary">注册</router-link>
    </div>
  </div>
</Transition>
```

- [ ] **Step 2: 替换 `<script setup>` 块**

将整个 `<script setup>` 替换为：

```javascript
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { analyzeRepo } from '@/api'

const appStore = useAppStore()
const auth = useAuthStore()
const router = useRouter()

const repoUrl = ref('')
const loading = ref(false)
const error = ref('')

async function startAnalysis() {
  if (!auth.user) {
    router.push({ name: 'Login', query: { redirect: '/' } })
    return
  }
  if (!repoUrl.value.trim()) {
    error.value = '请输入 GitHub 仓库地址'
    return
  }
  error.value = ''
  loading.value = true
  try {
    const result = await analyzeRepo(repoUrl.value.trim())
    appStore.setProject(result.project_id)
    router.push(`/analyze/${result.project_id}`)
  } catch (e) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 3: 在 `<style scoped>` 末尾追加 banner 样式**

在 `</style>` 之前追加：

```css
.login-banner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  margin-bottom: var(--space-8);
  border: 1px solid var(--neon-cyan-25);
}
.login-banner-icon {
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  background: var(--neon-cyan-10);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}
.login-banner-text { flex: 1; }
.login-banner-text h3 { font-size: 1rem; margin-bottom: 4px; }
.login-banner-text p { color: var(--text-secondary); font-size: 0.85rem; }
.login-banner-actions { display: flex; gap: var(--space-2); }
```

- [ ] **Step 4: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/views/HomePage.vue && git commit -m "feat(frontend): show login banner on HomePage for unauthenticated users"
```

---

## Task 17: 启动时静默恢复会话

**Files:**
- Modify: `frontend/src/main.js`

- [ ] **Step 1: 替换 main.js**

将 `frontend/src/main.js` 完整替换为：

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const auth = useAuthStore()
auth.tryRestoreSession().finally(() => {
  app.mount('#app')
})
```

- [ ] **Step 2: 提交**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git add frontend/src/main.js && git commit -m "feat(frontend): restore session on app startup"
```

---

## Task 18: 端到端浏览器验证

- [ ] **Step 1: 启动后端（后台）**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: 启动前端（后台）**

Run (新终端):
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/frontend" && npx vite --host 127.0.0.1 --port 3000
```

- [ ] **Step 3: 浏览器手工验证（按顺序检查）**

在浏览器打开 `http://127.0.0.1:3000`：

1. 首页 → 看到「登录以保存你的项目」banner
2. 点击 NavBar「注册」→ 填写 username/email/password（≥8位）→ 提交 → 跳回首页，NavBar 显示用户名
3. 点击「登出」→ 跳到 /login，banner 重现
4. 点「登录」→ 输邮箱密码 → 跳回首页
5. 输入合法 GitHub URL 提交 → 跳到 /analyze/xxx，跑通分析
6. 关浏览器重开 → 仍能进入首页（refreshToken 持久化恢复）
7. 控制台执行 `localStorage.removeItem('refresh_token')` 后刷新 → 跳到 /login

- [ ] **Step 4: 跨用户隔离验证**

1. 无痕模式注册第二个用户
2. 用户 A 提交一个 repo，等分析完成
3. 切到用户 B → 看不到 A 的项目列表
4. 用户 B 直接访问 `/report/<A 的项目ID>` → 应被后端 403 / 前端跳走

- [ ] **Step 5: 关闭两个服务（Ctrl+C）**

---

## Task 19: 全测 + 构建 + 推送

- [ ] **Step 1: 跑后端全测**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/backend" && python -m pytest -v
```
Expected: 全部通过

- [ ] **Step 2: 跑前端构建验证语法**

Run:
```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper/frontend" && npx vite build
```
Expected: 构建成功

- [ ] **Step 3: 推送到远程**

```bash
cd "D:/JavaRoad/vibe coding/Codex/project-helper" && git push origin master
```

---

## 自检：Spec 覆盖

| Spec 章节 | 对应任务 |
|----------|---------|
| 2.1 文件变更 | Task 1-17（所有新建/修改文件均覆盖）|
| 3.1 User 表 + Project.user_id | Task 3 |
| 3.2 迁移策略 | Task 3（init_db）+ Task 8（验证）|
| 3.3 JWT 配置 | Task 2 |
| 3.4 鉴权工具 | Task 4 |
| 3.5 依赖（get_current_user + sse 变体）| Task 5 |
| 3.6 auth 五个路由 | Task 5（含测试 14 用例）|
| 3.7 现有路由加鉴权 + 归属过滤 | Task 6（含 6 用例）|
| 3.8 CORS | Task 6 保留 `allow_origins=["*"]` |
| 4.1 前端 api/auth.js | Task 9 |
| 4.2 authedFetch | Task 11 |
| 4.3 Pinia store | Task 10 |
| 4.4 路由守卫 | Task 12 |
| 4.5 Login/Register UI | Task 13/14 |
| NavBar 用户信息 | Task 15 |
| HomePage banner | Task 16 |
| 4.5 启动恢复 | Task 17 |
| 5 错误码 | 测试覆盖（401/403/404/409/422）|
| 6 数据流 | Task 18 E2E 验证 |
| 7 测试 | Task 1-7 测试 + Task 18/19 收尾 |
| 8 依赖 | Task 1 |

