# -*- coding: utf-8 -*-
"""GitHub REST API client using requests library."""
import hashlib
from urllib.parse import urlparse
import requests

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".vue", ".svelte",
    ".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".xml", ".html", ".css",
    ".scss", ".less", ".sh", ".bash", ".ps1", ".sql", ".graphql", ".proto",
    ".cfg", ".ini", ".dockerfile", "makefile", ".gradle", ".cmake", ".m", ".mm",
}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".tox",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".nuxt",
             "target", "bin", "obj", ".idea", ".vscode", ".DS_Store", ".gradle",
             "test", "tests", "__tests__", "spec", "fixtures", "examples"}

MAX_FILES_TO_FETCH = 80
MAX_FILE_SIZE = 200 * 1024
MAX_TOTAL_SIZE = 5 * 1024 * 1024

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "project-helper"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def parse_github_url(url: str) -> tuple:
    parsed = urlparse(url.strip().rstrip("/"))
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    raise ValueError(f"Invalid GitHub URL: {url}")

def repo_id(url: str) -> str:
    return hashlib.md5(url.strip().lower().encode()).hexdigest()

def _get(url):
    resp = SESSION.get(url, timeout=10)
    if resp.status_code == 404:
        raise RuntimeError("仓库不存在")
    if resp.status_code == 403:
        raise RuntimeError("GitHub API 速率限制，请稍后重试")
    resp.raise_for_status()
    return resp.json()

def fetch_repo_info(owner: str, repo: str) -> dict:
    data = _get(f"https://api.github.com/repos/{owner}/{repo}")
    return {
        "name": data.get("full_name", f"{owner}/{repo}"),
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "stars": data.get("stargazers_count", 0),
        "topics": data.get("topics", []),
        "default_branch": data.get("default_branch", "main"),
    }

def fetch_file_tree(owner: str, repo: str) -> list[dict]:
    repo_data = _get(f"https://api.github.com/repos/{owner}/{repo}")
    default_branch = repo_data.get("default_branch", "main")

    ref_data = _get(f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{default_branch}")
    head_sha = ref_data["object"]["sha"]

    tree_data = _get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{head_sha}?recursive=1")

    files = []
    for item in tree_data.get("tree", []):
        if item["type"] == "blob":
            path = item["path"]
            name = path.split("/")[-1].lower()
            suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""
            parts = path.split("/")
            if any(s in SKIP_DIRS for s in parts):
                continue
            if suffix in CODE_EXTENSIONS or name in CODE_EXTENSIONS:
                files.append({"path": path, "size": item.get("size", 0), "sha": item["sha"]})

    def priority(f):
        p = f["path"].lower()
        if "readme" in p: return 0
        if p in ("package.json", "setup.py", "cargo.toml", "go.mod", "pom.xml", "build.gradle"): return 1
        if p.endswith((".json", ".yml", ".yaml", ".toml", ".cfg", ".ini")): return 2
        if "main" in p or "index" in p or "app" in p: return 3
        if "src" in p.split("/"): return 4
        return 5

    files.sort(key=priority)
    return files

def fetch_file_contents(owner: str, repo: str, files: list[dict], progress_cb=None) -> list[dict]:
    result = []
    total_size = 0
    fetched = 0
    to_fetch = files[:MAX_FILES_TO_FETCH]

    for i, f in enumerate(to_fetch):
        try:
            resp = SESSION.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{f['path']}",
                headers={"Accept": "application/vnd.github.raw+json", "User-Agent": "project-helper"},
                timeout=10
            )
            if resp.status_code != 200:
                continue

            content = resp.text
            size = len(content.encode("utf-8"))
            if size > MAX_FILE_SIZE:
                content = f"[文件过大: {size} bytes]"

            if total_size + size <= MAX_TOTAL_SIZE:
                ext = "." + f["path"].rsplit(".", 1)[-1] if "." in f["path"] else ""
                result.append({"path": f["path"], "size": size, "content": content, "ext": ext})
                total_size += size
                fetched += 1
        except Exception:
            continue

        if progress_cb and (i + 1) % 5 == 0:
            pct = 0.30 + ((i + 1) / len(to_fetch)) * 0.40
            progress_cb(pct, f"读取源码... {fetched} 个文件")

        if total_size >= MAX_TOTAL_SIZE:
            break

    if progress_cb:
        progress_cb(0.70, f"已读取 {fetched} 个文件")
    return result

def build_context_from_api(files: list[dict], repo_info: dict) -> str:
    lines = []
    lines.append(f"## Repository: {repo_info.get('name', '')}")
    lines.append(f"Description: {repo_info.get('description', '')}")
    lines.append(f"Language: {repo_info.get('language', '')}")
    lines.append(f"Stars: {repo_info.get('stars', 0)}")
    lines.append(f"Topics: {', '.join(repo_info.get('topics', []))}")
    lines.append("")

    dirs = {}
    for f in files:
        parts = f["path"].split("/")
        for i in range(len(parts) - 1):
            d = "/".join(parts[:i+1])
            dirs[d] = dirs.get(d, 0) + 1

    if dirs:
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
        lines.append(f"\n### {f['path']}")
        lines.append(f["content"])

    return "\n".join(lines)
