# AGENTS.md — Project Helper

AI-powered GitHub repo analyzer. FastAPI backend + Vue 3 frontend. Recently added JWT auth and per-user project ownership.

## Project layout

- `backend/` — Python 3.12 FastAPI app, SQLite DB, repo cache, pytest suite.
- `frontend/` — Vite + Vue 3 + Pinia SPA.
- `docs/superpowers/` — design docs / implementation plans (not user docs).

## Commands

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

- `python main.py` also works and enables `--reload`.
- Tests: `cd backend && pytest tests/ -v`
- Single test: `pytest tests/test_project_ownership.py::test_analyze_requires_auth -v`

### Frontend

```bash
cd frontend
npm install
npm run dev        # port 3000, proxies /api to localhost:8000
npm run build
npm run preview
```

Start the backend first; the Vite dev server relies on its proxy.

## Required configuration

`backend/config.py` reads `backend/.env` via pydantic-settings. For any real run you need:

```bash
DEEPSEEK_API_KEY=sk-...
# optional but recommended in production:
JWT_SECRET=<32+ char secret>
```

Defaults live in `config.py`:

- model: `deepseek-v4-flash`
- base URL: `https://api.deepseek.com`
- DB: `backend/projects.db`
- repo cache: `backend/repos/`

Do not commit `.env`, DB files, or `backend/repos/` — they are already in `.gitignore`.

## Auth / ownership

- Almost every `/api/*` route now requires a Bearer access token. `/api/health` and `/api/auth/*` are public.
- SSE progress uses a `?token=` query param because `EventSource` cannot set custom headers.
- Access tokens live only in Pinia memory; refresh tokens are stored in `localStorage`.
- Project IDs are user-scoped: `u{user_id}_{repo_hash}`. The on-disk repo cache (`repos/{repo_hash}/`) is shared across users; deleting a project does not delete the disk cache.

## Architecture notes

- `main.py` lifespan calls `init_db()`, which creates tables. If the `users` table is newly added, it deletes legacy pre-auth project rows via raw SQL (no Alembic).
- Analysis runs in a background `threading.Thread`; the thread creates a fresh `asyncio` event loop to run the async LLM code.
- Source fetching order: GitHub REST API first; `git clone --depth 1` fallback if the API fails.
- LLM calls go through `langchain_openai.ChatOpenAI` using a DeepSeek-compatible base URL, not OpenAI.
- Limits: max 80 files via GitHub API, 200 KB per file, 5 MB total context; analyzer truncates context to ~60k chars; QA context to ~40k chars.
- SQLite runs in WAL mode, so expect `.db-shm` and `.db-wal` files.

## Style / tooling

- No lint, formatter, type-check, or pre-commit configuration is present. Follow existing file conventions.
- Python files use `# -*- coding: utf-8 -*-`; UI text is mostly Chinese.
- There are no frontend tests.

## Common gotchas

- The README quickstart is slightly stale: it omits auth and says the API key is preconfigured. You need `DEEPSEEK_API_KEY` in `backend/.env` and a registered user to use analyze/report/QA endpoints.
- `analyzer.py` imports from `langchain_openai`, not `langchain-deepseek`. Both packages are listed in `requirements.txt`.
- GitHub API calls are unauthenticated in this code, so public rate limits apply and private repos are unsupported.
- The SSE progress test that streams forever is intentionally skipped.
