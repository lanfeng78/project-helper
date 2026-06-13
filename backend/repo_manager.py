# -*- coding: utf-8 -*-
"""
Repository access layer. Primary: GitHub REST API. Fallback: git clone.
"""
import os
import re
import hashlib
import shutil
import subprocess
import socket
from pathlib import Path
from config import settings
from github_api import (
    parse_github_url, repo_id, fetch_repo_info, fetch_file_tree,
    fetch_file_contents, build_context_from_api,
)

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".vue", ".svelte",
    ".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".xml", ".html", ".css",
    ".scss", ".less", ".sh", ".bash", ".ps1", ".sql", ".graphql", ".proto",
    ".cfg", ".ini", ".dockerfile", "makefile", ".gradle", ".cmake", ".m", ".mm",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".nuxt",
             "target", "bin", "obj", ".idea", ".vscode", ".DS_Store", ".gradle"}

# ============================================================
#  PRIMARY: GitHub REST API (no clone needed)
# ============================================================

def fetch_via_api(url: str, progress_cb=None) -> tuple:
    """
    Fetch repository contents via GitHub REST API (sync).
    Returns (files, context_text). No git required.

    Side effect: persists fetched files to ``<repos_dir>/<repo_hash>/`` so the
    QA endpoint (which re-scans that directory) can find real content. Without
    this, the API path leaves the directory empty and QA reports "files are empty".
    """
    owner, repo = parse_github_url(url)

    if progress_cb:
        progress_cb(0.05, "获取仓库信息...")

    repo_info = fetch_repo_info(owner, repo)

    if progress_cb:
        progress_cb(0.10, "获取目录结构...")

    file_tree = fetch_file_tree(owner, repo)

    if progress_cb:
        progress_cb(0.15, f"发现 {len(file_tree)} 个相关文件，开始读取...")

    files = fetch_file_contents(owner, repo, file_tree, progress_cb=progress_cb)

    context = build_context_from_api(files, repo_info)

    # Persist to disk so QA (which scan_codebase's the dir) sees real content.
    _persist_files_to_disk(url, files)

    if progress_cb:
        progress_cb(0.70, f"API 读取完成，共 {len(files)} 个文件")

    return files, context


def _persist_files_to_disk(url: str, files: list[dict]) -> None:
    """Write each fetched file under ``<repos_dir>/<repo_hash>/<rel_path>``.

    Skips placeholder content (e.g. "[文件过大: ...]") and any path that would
    escape the repo root. Idempotent: clears the destination first so re-analysis
    doesn't leak files from a prior run.
    """
    pid = repo_id(url)
    dest = Path(settings.repos_dir) / pid
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    for f in files:
        rel = (f.get("path") or "").lstrip("/").replace("\\", "/")
        if not rel or ".." in rel.split("/"):
            continue
        content = f.get("content", "")
        if not isinstance(content, str) or content.startswith("[文件过大:"):
            continue
        target = dest / rel
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", errors="replace")
        except OSError:
            # Best-effort: skip individual files that fail (long path, illegal chars).
            continue

# ============================================================
#  FALLBACK: git clone (when API fails or user prefers)
# ============================================================

def _check_github_reachable() -> bool:
    try:
        s = socket.create_connection(("github.com", 443), timeout=3)
        s.close()
        return True
    except Exception:
        return False

def _kill_proc(proc):
    try:
        proc.kill()
        proc.wait(timeout=5)
    except Exception:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                         capture_output=True, timeout=5)
        except Exception:
            pass

def _parse_git_progress(line: str) -> tuple:
    m = re.search(r'(\w+).*?(\d+)%', line)
    if m:
        return m.group(1), float(m.group(2))
    return None, 0

def clone_repo(url: str, progress_cb=None) -> Path:
    """Clone a GitHub repo using subprocess. Fallback mode."""
    pid = repo_id(url)
    dest = Path(settings.repos_dir) / pid

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    if "github.com" in url and not _check_github_reachable():
        raise RuntimeError("无法连接 GitHub。请检查网络。")

    if progress_cb:
        progress_cb(0.02, "验证仓库地址...")

    # Validate with ls-remote
    try:
        proc = subprocess.Popen(
            ["git", "ls-remote", "--exit-code", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        )
        try:
            _, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            _kill_proc(proc)
            raise RuntimeError("连接 GitHub 超时，已自动切换为 API 模式")
        if proc.returncode != 0:
            raise RuntimeError(f"仓库验证失败: {stderr.strip()}")
    except FileNotFoundError:
        raise RuntimeError("系统未安装 Git")

    if progress_cb:
        progress_cb(0.05, "开始克隆仓库...")

    try:
        proc = subprocess.Popen(
            ["git", "clone", "--depth", "1", "--progress", url, str(dest)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        )
        output_lines = []
        got_progress = False

        import threading
        def read_stderr():
            nonlocal got_progress
            for line in proc.stderr:
                line = line.strip()
                if line:
                    output_lines.append(line)
                    phase, pct = _parse_git_progress(line)
                    if phase:
                        got_progress = True
                        pb = 0.05 + (pct / 100.0) * 0.45
                        if progress_cb:
                            progress_cb(pb, f"克隆中... {pct:.0f}%")
                    elif not got_progress and progress_cb:
                        progress_cb(0.06, f"克隆中... {line[:60]}")

        reader = threading.Thread(target=read_stderr, daemon=True)
        reader.start()
        try:
            proc.wait(timeout=120)
            reader.join(timeout=5)
        except subprocess.TimeoutExpired:
            _kill_proc(proc)
            raise RuntimeError("克隆超时 (120秒)，已自动切换为 API 模式")

        if proc.returncode != 0:
            raise RuntimeError(f"克隆失败: {chr(10).join(output_lines[-5:]) or '未知错误'}")
    except FileNotFoundError:
        raise RuntimeError("系统未安装 Git")

    if progress_cb:
        progress_cb(0.50, "克隆完成，开始扫描文件...")

    # Remove .git
    git_dir = dest / ".git"
    if git_dir.exists():
        def _on_rm_error(func, path, exc_info):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(git_dir, onerror=_on_rm_error)

    return dest

def scan_codebase(root: Path, progress_cb=None) -> list[dict]:
    """Scan a local directory for code files."""
    files = []
    total = 0
    for p in root.rglob("*"):
        if p.is_file() and not any(s in p.parts for s in SKIP_DIRS):
            total += 1

    scanned = 0
    for p in root.rglob("*"):
        if p.is_file() and not any(s in p.parts for s in SKIP_DIRS):
            scanned += 1
            suffix = p.suffix.lower()
            name = p.name.lower()
            if suffix in CODE_EXTENSIONS or name in CODE_EXTENSIONS:
                try:
                    size = p.stat().st_size
                    if size > settings.max_file_size:
                        content = f"[文件过大: {size} bytes]"
                    else:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                    rel = str(p.relative_to(root)).replace("\\", "/")
                    files.append({"path": rel, "size": size, "content": content, "ext": suffix})
                except Exception:
                    pass
            if progress_cb and total:
                pct = 0.50 + (scanned / total) * 0.2
                progress_cb(pct, f"扫描文件... {scanned}/{total}")

    if progress_cb:
        progress_cb(0.70, f"扫描完成，共 {len(files)} 个相关文件")
    return files

def build_context_summary(files: list[dict]) -> str:
    """Build context from locally scanned files."""
    lines = []
    total_size = 0

    dirs = {}
    for f in files:
        parts = f["path"].split("/")
        for i in range(len(parts) - 1):
            d = "/".join(parts[:i+1])
            dirs[d] = dirs.get(d, 0) + 1

    lines.append("## Directory Structure")
    for d, count in sorted(dirs.items()):
        indent = "  " * (d.count("/"))
        name = d.split("/")[-1]
        lines.append(f"{indent}- {name}/ ({count} files)")

    lines.append("\n## File List")
    for f in files:
        lines.append(f"- {f['path']} ({f['size']} bytes)")

    lines.append("\n## File Contents")
    for f in sorted(files, key=lambda x: x.get("size", 0), reverse=True):
        if total_size + f.get("size", 0) > settings.max_total_size:
            lines.append(f"\n### {f['path']}\n(截断 - 达到大小限制)")
            break
        total_size += f.get("size", 0)
        lines.append(f"\n### {f['path']}")
        lines.append(f["content"])

    return "\n".join(lines)
