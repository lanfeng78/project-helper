# -*- coding: utf-8 -*-
import json
import uuid
import asyncio
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from config import settings
from models import init_db, get_db, Project, User, QASession, QAMessage
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
    mode: Literal["simple", "detail"] = "detail"


class QARequest(BaseModel):
    project_id: str
    question: str
    conversation: list[dict] = []
    session_id: Optional[str] = None  # 若空则后端为本次提问新建一条会话


class QASessionCreateRequest(BaseModel):
    project_id: str
    title: Optional[str] = None


class QASessionRenameRequest(BaseModel):
    title: str


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
    """Start analysis of a GitHub repo. Returns immediately with project_id.

    Each user has their own Project row (id is user-scoped). The repo source
    cache on disk (`repos/{repo_hash}/`) is shared across users.

    Mode (simple|detail) is part of the project key, so simple and detail
    reports for the same repo coexist as two independent rows.
    """
    repo_hash = repo_id(req.repo_url)
    pid = f"u{current_user.id}_{repo_hash}_{req.mode}"

    existing = db.query(Project).filter(Project.id == pid).first()
    if existing and existing.status == "done":
        return {
            "project_id": pid,
            "status": "done",
            "cached": True,
            "report_json": json.loads(existing.report_json) if existing.report_json else {},
            "report_markdown": existing.report_markdown,
            "analysis_mode": existing.analysis_mode or req.mode,
        }

    if existing:
        existing.status = "pending"
        existing.progress = 0.0
        existing.progress_msg = "准备分析..."
        existing.error_msg = ""
        existing.analysis_mode = req.mode
    else:
        existing = Project(
            id=pid,
            repo_url=req.repo_url,
            repo_name=req.repo_url.rstrip("/").split("/")[-1],
            repo_hash=repo_hash,
            analysis_mode=req.mode,
            status="pending",
            user_id=current_user.id,
        )
        db.add(existing)
    db.commit()

    progress_store[pid] = {"progress": 0, "msg": "正在准备..."}

    thread = threading.Thread(
        target=_run_analysis,
        args=(pid, req.repo_url, repo_hash, req.mode),
        daemon=True,
    )
    thread.start()

    return {"project_id": pid, "status": "pending", "cached": False, "analysis_mode": req.mode}


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
        "analysis_mode": proj.analysis_mode or "detail",
        "model_used": proj.model_used or "",
        "report_json": json.loads(proj.report_json) if proj.report_json else {},
        "report_markdown": proj.report_markdown,
    }


@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a cached project. Repo source cache on disk is shared and not deleted here."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")
    db.delete(proj)
    db.commit()
    # 注意: repo source 缓存 (repos/{repo_hash}/) 是跨用户共享的，
    # 删除单个项目时不删除磁盘缓存——避免影响其他用户。
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
            "analysis_mode": p.analysis_mode or "detail",
            "model_used": p.model_used or "",
        }
        for p in projects
    ]


@app.post("/api/qa")
async def qa(
    req: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Streaming Q&A about a project's source code.

    若提供 session_id 则把 user/assistant 两端消息持久化到 qa_messages,
    否则后端会为本次提问新建一条 QASession(豆包"自动开新对话"行为)。
    流前先入库 user 消息;流式过程中累计 assistant 内容,流结束后入库 +
    bump session.updated_at;首条用户消息时用其前 40 字符回填 title。
    """
    proj = db.query(Project).filter(Project.id == req.project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")
    if proj.status != "done":
        raise HTTPException(400, "项目尚未分析完成")

    repo_path = Path(settings.repos_dir) / proj.repo_hash
    files = scan_codebase(repo_path) if repo_path.exists() else []
    if not files:
        raise HTTPException(
            409,
            "源码缓存已失效或为空，请回到首页删除该项目后重新分析。"
        )
    context = build_context_summary(files)

    # ── 解析或新建会话 ──
    session: Optional[QASession] = None
    if req.session_id:
        session = (
            db.query(QASession)
            .filter(QASession.id == req.session_id)
            .first()
        )
        if not session:
            raise HTTPException(404, "会话不存在")
        if session.user_id != current_user.id or session.project_id != req.project_id:
            raise HTTPException(403, "无权访问此会话")
    else:
        session = QASession(
            id=uuid.uuid4().hex,
            project_id=req.project_id,
            user_id=current_user.id,
            title=_make_session_title(req.question),
        )
        db.add(session)
        db.flush()  # 取 id 给前端

    # 若是首条消息(无任何 message),用本次提问回填 title
    has_msg = (
        db.query(QAMessage.id)
        .filter(QAMessage.session_id == session.id)
        .first()
        is not None
    )
    if not has_msg:
        session.title = _make_session_title(req.question)

    # 入库 user 消息
    db.add(QAMessage(session_id=session.id, role="user", content=req.question))
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    session_id = session.id

    # ── 优先使用数据库里的历史(防止前端发来的 conversation 不全)──
    history = (
        db.query(QAMessage)
        .filter(QAMessage.session_id == session_id)
        .order_by(QAMessage.id.asc())
        .all()
    )
    # 最后一条就是刚刚入库的 user 提问;answer_question 单独接 question 参数,
    # 所以 conversation 只取除最后一条之外的历史即可。
    conversation = [
        {"role": m.role, "content": m.content} for m in history[:-1]
    ]

    async def stream_qa():
        buf: list[str] = []
        try:
            async for token in answer_question(context, conversation, req.question):
                buf.append(token)
                yield token
        finally:
            # 不论正常/异常结束都把已生成内容存下来;异常情况下用户也能看到截断回复。
            content = "".join(buf).strip()
            if content:
                from models import SessionLocal
                _db = SessionLocal()
                try:
                    _db.add(QAMessage(
                        session_id=session_id,
                        role="assistant",
                        content=content,
                    ))
                    _sess = _db.query(QASession).filter(QASession.id == session_id).first()
                    if _sess:
                        _sess.updated_at = datetime.now(timezone.utc)
                    _db.commit()
                except Exception:
                    _db.rollback()
                finally:
                    _db.close()

    return StreamingResponse(
        stream_qa(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            # 把 session_id 透回给前端,前端拿到后写进 router query
            "X-Session-Id": session_id,
            "Access-Control-Expose-Headers": "X-Session-Id",
        }
    )


def _make_session_title(text: str, limit: int = 40) -> str:
    """把用户首句话压成一行短标题,超长截断 + 省略号。"""
    s = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if not s:
        return "新对话"
    return s if len(s) <= limit else s[:limit] + "…"


# ─────────────────────────── QA 会话管理 ───────────────────────────

@app.get("/api/qa/sessions")
def list_qa_sessions(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户在指定项目下的全部会话(按 updated_at 倒序)。"""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")

    sessions = (
        db.query(QASession)
        .filter(
            QASession.project_id == project_id,
            QASession.user_id == current_user.id,
        )
        .order_by(QASession.updated_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "title": s.title or "新对话",
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "updated_at": s.updated_at.isoformat() if s.updated_at else "",
        }
        for s in sessions
    ]


@app.post("/api/qa/sessions")
def create_qa_session(
    req: QASessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """显式新建一条空会话(前端"+ 新对话"按钮)。"""
    proj = db.query(Project).filter(Project.id == req.project_id).first()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.user_id != current_user.id:
        raise HTTPException(403, "无权访问此项目")

    sess = QASession(
        id=uuid.uuid4().hex,
        project_id=req.project_id,
        user_id=current_user.id,
        title=req.title or "新对话",
    )
    db.add(sess)
    db.commit()
    return {
        "id": sess.id,
        "title": sess.title,
        "created_at": sess.created_at.isoformat() if sess.created_at else "",
        "updated_at": sess.updated_at.isoformat() if sess.updated_at else "",
    }


@app.get("/api/qa/sessions/{session_id}/messages")
def get_qa_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """拿一条会话的全部消息(按发送顺序)。"""
    sess = db.query(QASession).filter(QASession.id == session_id).first()
    if not sess:
        raise HTTPException(404, "会话不存在")
    if sess.user_id != current_user.id:
        raise HTTPException(403, "无权访问此会话")

    msgs = (
        db.query(QAMessage)
        .filter(QAMessage.session_id == session_id)
        .order_by(QAMessage.id.asc())
        .all()
    )
    return {
        "session": {
            "id": sess.id,
            "title": sess.title or "新对话",
            "project_id": sess.project_id,
            "updated_at": sess.updated_at.isoformat() if sess.updated_at else "",
        },
        "messages": [
            {"role": m.role, "content": m.content}
            for m in msgs
        ],
    }


@app.patch("/api/qa/sessions/{session_id}")
def rename_qa_session(
    session_id: str,
    req: QASessionRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess = db.query(QASession).filter(QASession.id == session_id).first()
    if not sess:
        raise HTTPException(404, "会话不存在")
    if sess.user_id != current_user.id:
        raise HTTPException(403, "无权访问此会话")
    sess.title = (req.title or "").strip()[:120] or "新对话"
    db.commit()
    return {"id": sess.id, "title": sess.title}


@app.delete("/api/qa/sessions/{session_id}")
def delete_qa_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess = db.query(QASession).filter(QASession.id == session_id).first()
    if not sess:
        raise HTTPException(404, "会话不存在")
    if sess.user_id != current_user.id:
        raise HTTPException(403, "无权访问此会话")
    db.delete(sess)
    db.commit()
    return {"deleted": session_id}


def _run_analysis(pid: str, repo_url: str, repo_hash: str, mode: str = "detail"):
    """Run the full analysis pipeline in a background thread.

    pid: user-scoped Project.id (already includes mode suffix)
    repo_hash: shared cache key for repos/{repo_hash}/
    mode: "simple" | "detail" — controls model + prompt + context size
    """
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
            report = loop.run_until_complete(
                analyze_codebase(context, mode=mode, progress_cb=update)
            )
        finally:
            loop.close()

        markdown = build_markdown_report(report)

        # Resolve which actual model name was used (for the badge / debugging).
        if mode == "simple":
            model_name = settings.deepseek_model_simple or settings.deepseek_model
        else:
            model_name = settings.deepseek_model_detail or settings.deepseek_model

        proj = db.query(Project).filter(Project.id == pid).first()
        if proj:
            proj.status = "done"
            proj.progress = 100.0
            proj.progress_msg = "分析完成!"
            proj.report_json = json.dumps(report, ensure_ascii=False)
            proj.report_markdown = markdown
            proj.tech_stack = str(report.get("tech_stack", ""))
            proj.analysis_mode = mode
            proj.model_used = model_name
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
