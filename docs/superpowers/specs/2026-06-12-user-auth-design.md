# 用户注册登录模块 — 设计文档

**日期**：2026-06-12
**项目**：Project Helper（FastAPI + Vue 3 + SQLite + DeepSeek）
**目标**：为 Project Helper 增加完整的注册/登录模块，所有分析项目归属创建者，全站 API 默认需鉴权。

---

## 1. 范围

### 1.1 本期要做

- 用户注册、登录、登出、刷新 token、获取当前用户信息
- JWT 双 token（access 15min + refresh 7d）鉴权
- 项目归属用户：用户仅能看/管自己创建的项目
- 全站 API 需鉴权（仅首页/登录/注册页公开）
- 数据库迁移：清空旧项目，加 User 表与 Project.user_id 外键
- 后端测试：注册/登录/刷新/鉴权/越权访问 5 类用例

### 1.2 本期不做（YAGNI）

- 邮箱验证、找回密码、改密码
- 第三方登录（GitHub OAuth 等）
- 角色权限（管理员/普通用户）
- 头像、个人资料编辑
- 速率限制
- Alembic 迁移（手写 SQL 清空 + `create_all` 即可）
- 前端 E2E 测试

---

## 2. 架构

### 2.1 文件变更总览

**后端（`backend/`）**：

| 文件 | 变更 |
|------|------|
| `models.py` | 新增 `User` 表；`Project` 加 `user_id` 外键 + `owner` 关系 |
| `config.py` | 新增 `jwt_secret` 字段（`.env` 注入优先） |
| `auth_utils.py`（新） | 密码哈希、JWT 签发与验证 |
| `dependencies.py`（新） | `get_current_user` 依赖（含 Bearer 头与 SSE query 两种变体） |
| `auth.py`（新） | 注册/登录/刷新/登出/me 五个路由 |
| `main.py` | 挂载 auth 路由；现有 `/api/*` 加 `current_user` 依赖；`list_projects`/`delete_project` 加归属过滤 |
| `requirements.txt` | 新增 `passlib[bcrypt]`、`python-jose` 或 `pyjwt`（二选一，本设计选 `pyjwt`） |

**前端（`frontend/src/`）**：

| 文件 | 变更 |
|------|------|
| `api/auth.js`（新） | 注册/登录/刷新/登出/me 五个 HTTP 封装 |
| `stores/auth.js`（新） | Pinia 状态：user、accessToken、refreshToken 及动作 |
| `api/index.js` | 新增 `authedFetch` 包装（含 401 自动刷新重试）；现有 API 改用 `authedFetch`；SSE 改用 query param 传 token |
| `router/index.js` | 全局 `beforeEach` 守卫；新增 `/login`、`/register` 路由 |
| `views/LoginPage.vue`（新） | 登录页 |
| `views/RegisterPage.vue`（新） | 注册页 |
| `views/HomePage.vue` | 顶栏加用户信息+登出；未登录显示登录/注册入口 |
| `main.js` | 启动时调 `authStore.tryRestoreSession()` 静默恢复会话 |

---

## 3. 后端详细设计

### 3.1 数据模型（`models.py`）

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Project(Base):
    # ... 现有字段保持不变 ...
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    owner = relationship("User", backref="projects")
```

### 3.2 迁移策略

不引入 Alembic。`init_db()` 启动时执行：

1. `Base.metadata.create_all(bind=engine)` — 新表会建，旧表保留
2. 检测 `users` 表是否刚创建（即旧库中不存在）→ 若是，执行 `DELETE FROM projects` 清空旧数据
3. 旧库的 `Project` 表不包含 `user_id` 列，create_all 不会加列 —— **需要主动 `ALTER TABLE projects ADD COLUMN user_id INTEGER`** 然后再 `UPDATE projects SET user_id = 1` 占位、再 `DELETE FROM projects` 清空（让 user_id 1 没有任何项目但表结构对齐）。

最终落地步骤（在 `init_db` 内顺序执行）：

```python
def init_db():
    inspector = inspect(engine)
    has_users = inspector.has_table("users")
    Base.metadata.create_all(bind=engine)
    if not has_users:
        # 首次引入用户系统：清空旧项目，对齐 schema
        with engine.begin() as conn:
            cols = [c["name"] for c in inspector.get_columns("projects")]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN user_id INTEGER"))
            conn.execute(text("DELETE FROM projects"))
            conn.execute(text("DELETE FROM sqlite_sequence WHERE name='projects'"))
```

### 3.3 配置（`config.py`）

```python
class Settings(BaseSettings):
    # ... 现有字段 ...
    jwt_secret: str = "change-me-in-prod-please-use-32-chars-min"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 7
```

生产通过 `.env` 文件注入 `JWT_SECRET`。

### 3.4 鉴权工具（`auth_utils.py`）

```python
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...

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
    """解码 → 验签 → 校验 type → 校验 exp。任一失败抛 HTTPException(401)。返回 user_id。"""
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

### 3.5 依赖（`dependencies.py`）

```python
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """从 Bearer 头取 access token，验签后返回 User 对象。"""
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
    """SSE 专用：从 query param 取 token（EventSource 不支持自定义头）。"""
    user_id = decode_token(token, expected_type="access")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "user not found")
    return user
```

### 3.6 路由（`auth.py`）

| 方法 | 路径 | 请求体 | 返回 | 成功状态码 |
|------|------|--------|------|-----------|
| POST | `/api/auth/register` | `{username, email, password}` | `{user, access_token, refresh_token}` | 201 |
| POST | `/api/auth/login` | `{email, password}` | `{user, access_token, refresh_token}` | 200 |
| POST | `/api/auth/refresh` | `{refresh_token}` | `{access_token, refresh_token}` | 200 |
| POST | `/api/auth/logout` | (无) | `{ok: true}` | 200 |
| GET | `/api/auth/me` | (无, 需鉴权) | `{user}` | 200 |

#### 校验规则（Pydantic）

```python
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str
```

#### 注册流程

1. 检查 username 唯一性 → 重复返 409 `{detail: "该用户名已被使用"}`
2. 检查 email 唯一性 → 重复返 409 `{detail: "该邮箱已被注册"}`
3. `hash_password(password)` → 插 User 行
4. 签发 access + refresh → 返回

#### 登录流程

1. SELECT user by email → 不存在返 401 `{detail: "邮箱或密码错误"}`（不区分）
2. `verify_password` → 失败返同上 401
3. 签发 access + refresh → 返回

#### 刷新流程

1. `decode_token(refresh_token, "refresh")` → 失败 401
2. 签发新 access + 新 refresh（**轮换**——refresh token 一次性，旧 refresh 不能再用）
3. 返回

#### 登出流程

JWT 无状态，客户端丢弃 token 即可。后端路由保留仅为预留未来吊销位。

### 3.7 现有路由加鉴权（`main.py`）

| 路由 | 依赖变更 | 业务逻辑变更 |
|------|---------|-------------|
| `POST /api/analyze` | 加 `current_user` | 创建 Project 时写入 `user_id=current_user.id` |
| `GET /api/progress/{id}` | 改用 `get_current_user_sse`，并检查 `proj.user_id == current_user.id` | 越权 403 |
| `GET /api/report/{id}` | 加 `current_user` | 越权 403 |
| `DELETE /api/projects/{id}` | 加 `current_user` | 越权 403 |
| `GET /api/projects` | 加 `current_user` | 过滤 `Project.user_id == current_user.id` |
| `POST /api/qa` | 加 `current_user` | 越权 403 |
| `GET /api/health` | 不变 | 探活仍公开 |

### 3.8 CORS

保持 `allow_origins=["*"]`（用 Bearer 头而非 cookie，无需配 `allow_credentials`）。

---

## 4. 前端详细设计

### 4.1 API 封装（`api/auth.js`）

```js
const BASE = '/api/auth'

export async function register(username, email, password) {
  const res = await fetch(`${BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  return handleAuthResponse(res)  // { user, access_token, refresh_token }
}

export async function login(email, password) { ... }
export async function refresh(refreshToken) { ... }
export async function logout() {
  // POST /api/auth/logout，错误也忽略（清本地为主）
}
export async function fetchMe(accessToken) {
  // GET /api/auth/me
}
```

### 4.2 通用 fetch 拦截（`api/index.js`）

```js
export async function authedFetch(url, options = {}) {
  const auth = useAuthStore()
  const doFetch = (token) => fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    }
  })

  let res = await doFetch(auth.accessToken)
  if (res.status === 401) {
    // 尝试刷新
    const ok = await auth.tryRefresh()
    if (ok) res = await doFetch(auth.accessToken)
    else {
      auth.clear()
      router.push('/login')
      throw new Error('会话已过期')
    }
  }
  return res
}
```

SSE 改造：`subscribeProgress(projectId, ...)` 内部把 `token` 拼到 URL `?token=xxx`。

### 4.3 Pinia Store（`stores/auth.js`）

```js
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
    localStorage.setItem('refresh_token', refresh_token)
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

  async function register(username, email, password) {
    const data = await authApi.register(username, email, password)
    setTokens(data)
    user.value = data.user
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

  async function logout() {
    try { await authApi.logout() } catch {}
    clear()
  }

  return { user, accessToken, refreshToken, login, register, logout, tryRestoreSession, tryRefresh, clear }
})
```

**Token 存储**：
- `accessToken` 仅存 Pinia 内存（刷新即丢）
- `refreshToken` 存 `localStorage`（7 天有效，XSS 风险可接受——本项目为个人工具）

### 4.4 路由守卫（`router/index.js`）

```js
const PUBLIC_ROUTES = new Set(['Home', 'Login', 'Register'])

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 静默恢复会话
  if (!auth.user && auth.refreshToken) {
    await auth.tryRestoreSession()
  }

  // 受保护路由 + 未登录 → 跳登录
  if (!PUBLIC_ROUTES.has(to.name) && !auth.user) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  // 已登录访问登录/注册 → 跳首页
  if (auth.user && (to.name === 'Login' || to.name === 'Register')) {
    return { name: 'Home' }
  }
})
```

### 4.5 UI 页面

- **LoginPage** 居中玻璃卡片，邮箱+密码，提交按钮，底部「还没账号？去注册」链接
- **RegisterPage** 同上，加 username 字段
- 表单前端实时校验（必填、长度、邮箱格式、username 字符），后端再校验一次
- API 错误用 toast 或内联红色文字
- 沿用现有 cyber-neon 暗色主题风格（`#030712` 背景 + `#00e5ff` 青 + `#e040fb` 紫）
- HomePage 顶栏右侧：未登录显示「登录 / 注册」按钮；已登录显示 `username` + 「登出」按钮

---

## 5. 错误处理

### 5.1 后端错误码

| 场景 | HTTP | 响应体 `detail` |
|------|------|----------------|
| 字段格式错（短密码/非法 username 等） | 422 | Pydantic 自动 |
| email 重复 | 409 | `该邮箱已被注册` |
| username 重复 | 409 | `该用户名已被使用` |
| 登录邮箱不存在 | 401 | `邮箱或密码错误`（同密码错） |
| 登录密码错 | 401 | `邮箱或密码错误` |
| access token 过期 | 401 | `token expired` |
| access token 无效 | 401 | `invalid token` |
| access 当 refresh 用 | 401 | `invalid token type` |
| refresh token 过期/无效 | 401 | `refresh token expired` / `invalid token` |
| 越权访问他人项目 | 403 | `无权访问此项目` |
| 项目不存在 | 404 | `项目不存在` |

**安全要点**：登录时邮箱不存在与密码错返回相同消息，避免邮箱枚举。

### 5.2 前端错误处理

- `/auth/refresh` 返回 401 → 清 token + 跳 `/login` + toast「会话已过期，请重新登录」
- 422 → 字段下方红色提示
- 409 → toast「该邮箱已注册，可直接登录」 / 「该用户名已被使用」
- 5xx → toast「服务异常，请稍后重试」
- 网络错 → toast「网络连接失败」

---

## 6. 数据流

### 6.1 注册
```
RegisterPage submit
  → authApi.register
  → POST /api/auth/register
  → hash → INSERT user → 签发 access+refresh
  → 前端: setTokens + setUser → router.push('/')
```

### 6.2 登录
```
LoginPage submit
  → authApi.login
  → POST /api/auth/login
  → SELECT user → verify → 签发 token
  → 前端: 同上
```

### 6.3 访问受保护页
```
用户访问 /report/abc
  → router.beforeEach:
      若有 refreshToken → tryRestoreSession（调 /refresh + /me）
      成功 → 放行；失败 → 清 token → 跳 /login
  → 页面挂载 → authedFetch('/api/report/abc') 带 Bearer
  → 后端 get_current_user → 查 Project → 检查 user_id 匹配 → 返回
```

### 6.4 Token 自动刷新
```
authedFetch 收到 401
  → tryRefresh() → POST /auth/refresh
  → 成功: setTokens(new) → 重试原请求一次
  → 失败: clear() + router.push('/login')
```

### 6.5 登出
```
点击登出
  → authStore.logout()
  → POST /api/auth/logout (后端无状态，仅占位)
  → clear() (清内存 + localStorage)
  → router.push('/login')
```

---

## 7. 测试

### 7.1 后端（`pytest` + `httpx.AsyncClient`，最小集）

新建 `backend/tests/`：

- `test_register.py`：
  - 成功注册 → 201，返回 user + 双 token
  - username 重复 → 409
  - email 重复 → 409
  - 密码 < 8 字符 → 422
  - username 含 `@` 等非法字符 → 422
- `test_login.py`：
  - 成功登录 → 200
  - 邮箱不存在 → 401（消息同密码错）
  - 密码错 → 401
- `test_refresh.py`：
  - 有效 refresh → 200，新 access + 新 refresh
  - 旧 refresh 不能再用（轮换）→ 401
  - 过期 refresh → 401
  - access token 当 refresh 用 → 401
- `test_auth_required.py`：
  - 无 token 访问 `/api/projects` → 401
  - 过期 access → 401
  - 错误签名 token → 401
  - 有效 token → 200
- `test_project_ownership.py`：
  - 用户 A 创建项目 → 写入 user_id=A
  - 用户 B 调 `/api/report/{pid_A}` → 403
  - 用户 B 调 `DELETE /api/projects/{pid_A}` → 403
  - 用户 A 调 `/api/projects` → 仅看到自己的
- `test_sse_auth.py`：
  - SSE 不带 token → 401
  - SSE 带有效 token → 200

### 7.2 前端

本期不做 E2E。

---

## 8. 依赖

**`backend/requirements.txt` 新增**：
```
passlib[bcrypt]==1.7.4
PyJWT==2.10.1
pytest==8.3.4
pytest-asyncio==0.25.0
httpx==0.28.1
```

**前端**：无新依赖。

---

## 9. 后续演进（不在本期范围）

- 邮箱验证 + 找回密码
- GitHub OAuth 登录
- 用户设置页（改密码、删账号）
- 速率限制（登录/注册端点防爆破）
- 角色权限
- Alembic 替换手动迁移
- 前端 Playwright E2E
