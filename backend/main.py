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
    """Start analysis of a GitHub repo. Returns immediately with project_id.

    Each user has their own Project row (id is user-scoped). The repo source
    cache on disk (`repos/{repo_hash}/`) is shared across users.
    """
    repo_hash = repo_id(req.repo_url)
    pid = f"u{current_user.id}_{repo_hash}"

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
    else:
        existing = Project(
            id=pid,
            repo_url=req.repo_url,
            repo_name=req.repo_url.rstrip("/").split("/")[-1],
            repo_hash=repo_hash,
            status="pending",
            user_id=current_user.id,
        )
        db.add(existing)
    db.commit()

    progress_store[pid] = {"progress": 0, "msg": "正在准备..."}

    thread = threading.Thread(
        target=_run_analysis,
        args=(pid, req.repo_url, repo_hash),
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
        raise HTTPException(400, "项目尚未分析完成")

    repo_path = Path(settings.repos_dir) / proj.repo_hash
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


def _run_analysis(pid: str, repo_url: str, repo_hash: str):
    """Run the full analysis pipeline in a background thread.

    pid: user-scoped Project.id
    repo_hash: shared cache key for repos/{repo_hash}/
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
