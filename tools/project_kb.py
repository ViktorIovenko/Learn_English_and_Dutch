#!/usr/bin/env python3
"""Compact, metadata-only project knowledge base for Codex.

The index deliberately stores paths, hashes, signatures and relationships, not
full source code, secrets, database rows or logs.  Only the Python standard
library is used.
"""
from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / ".codex" / "project_kb.sqlite"
DOCS_DIR = ROOT / "docs" / "codex"
SNAPSHOT_PATH = DOCS_DIR / "PRODUCTION_SNAPSHOT.md"
MANIFEST_PATH = DOCS_DIR / "project_manifest.json"
NOW = lambda: dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

TEXT_EXTENSIONS = {
    ".py", ".js", ".html", ".css", ".kt", ".java", ".kts", ".gradle",
    ".sql", ".md", ".json", ".yml", ".yaml", ".toml", ".ini", ".conf",
    ".properties", ".xml", ".txt", ".ps1", ".dockerignore", ".gitignore",
}
SKIP_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".gradle", ".idea", "build", "dist",
    "staticfiles", "audio", "downloads", "logs", "media",
}
SKIP_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".mp3", ".wav", ".ogg", ".m4a", ".flac",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".apk", ".aab",
    ".zip", ".tar", ".gz", ".7z", ".pem", ".key", ".p12", ".jks",
}
SECRET_NAME_RE = re.compile(r"(?i)(token|secret|password|api[_-]?key|private[_-]?key|cookie)")
TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"'`\[]?([\w]+)[\"'`\]]?\s*\((.*?)\)",
    re.I | re.S,
)
INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w]+)\s+ON\s+([\w]+)\s*\(([^)]+)\)",
    re.I | re.S,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
 path TEXT NOT NULL, source_scope TEXT NOT NULL, language TEXT, layer TEXT,
 purpose TEXT, size_bytes INTEGER, sha256 TEXT, indexed_at TEXT,
 is_generated INTEGER NOT NULL DEFAULT 0, is_entrypoint INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(path, source_scope));
CREATE TABLE IF NOT EXISTS symbols (
 id INTEGER PRIMARY KEY, name TEXT, symbol_type TEXT, signature TEXT,
 file_path TEXT, line_start INTEGER, line_end INTEGER, docstring TEXT,
 parent_symbol TEXT, source_scope TEXT);
CREATE TABLE IF NOT EXISTS imports (
 id INTEGER PRIMARY KEY, source_file TEXT, target_module TEXT, imported_name TEXT,
 import_type TEXT, source_scope TEXT);
CREATE TABLE IF NOT EXISTS routes (
 id INTEGER PRIMARY KEY, route_type TEXT, method_or_trigger TEXT,
 route_or_command TEXT, handler TEXT, file_path TEXT, line_number INTEGER,
 auth_type TEXT, purpose TEXT, source_scope TEXT);
CREATE TABLE IF NOT EXISTS database_tables (
 id INTEGER PRIMARY KEY, table_name TEXT, defined_in TEXT, definition_line INTEGER,
 columns_json TEXT, indexes_json TEXT, environment TEXT,
 UNIQUE(table_name, defined_in, environment));
CREATE TABLE IF NOT EXISTS database_usage (
 id INTEGER PRIMARY KEY, table_name TEXT, file_path TEXT, symbol_name TEXT,
 operation TEXT, line_number INTEGER, source_scope TEXT);
CREATE TABLE IF NOT EXISTS frontend_links (
 id INTEGER PRIMARY KEY, source_file TEXT, target_type TEXT, target_value TEXT,
 line_number INTEGER, source_scope TEXT);
CREATE TABLE IF NOT EXISTS android_contracts (
 id INTEGER PRIMARY KEY, endpoint TEXT, http_method TEXT, android_file TEXT,
 android_symbol TEXT, request_model TEXT, response_model TEXT,
 auth_headers_json TEXT, backend_file TEXT, backend_handler TEXT,
 status TEXT, notes TEXT, UNIQUE(endpoint, http_method, android_file));
CREATE TABLE IF NOT EXISTS services (
 id INTEGER PRIMARY KEY, environment TEXT, service_name TEXT, service_type TEXT,
 working_directory TEXT, exec_start_redacted TEXT, user_name TEXT, group_name TEXT,
 environment_file_path TEXT, port TEXT, source_file TEXT, last_indexed_at TEXT,
 UNIQUE(environment, service_name));
CREATE TABLE IF NOT EXISTS deployment_routes (
 id INTEGER PRIMARY KEY, server_name TEXT, public_path TEXT, proxy_target TEXT,
 nginx_config_path TEXT, backend_service TEXT, notes TEXT,
 UNIQUE(server_name, public_path, proxy_target));
CREATE TABLE IF NOT EXISTS environment_snapshots (
 id INTEGER PRIMARY KEY, environment TEXT, git_branch TEXT, git_commit TEXT,
 git_dirty INTEGER, project_path TEXT, captured_at TEXT,
 tracked_files_json TEXT, entrypoints_json TEXT, schema_hash TEXT,
 UNIQUE(environment));
CREATE TABLE IF NOT EXISTS task_routes (
 id INTEGER PRIMARY KEY, topic TEXT UNIQUE, keywords TEXT, primary_files_json TEXT,
 secondary_files_json TEXT, excluded_paths_json TEXT, recommended_checks_json TEXT,
 environment_scope TEXT);
CREATE TABLE IF NOT EXISTS docs (
 id INTEGER PRIMARY KEY, key TEXT UNIQUE, title TEXT, content TEXT, source_path TEXT);
"""

TASK_ROUTES = [
    ("telegram registration", "telegram registration регистрация onboarding start auth",
     ["bot/auth.py", "bot/onboarding.py", "config.py"], ["run.py", "bot/db.py"], ["app/static", "android"], ["python -m unittest tests.test_telegram_onboarding"], "local"),
    ("word import", "import words upload csv импорт слов",
     ["bot/upload.py", "app/static/upload.js"], ["app/routes.py", "android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt"], ["bot/reminder.py"], ["python tools/project_kb.py route /api/import-words"], "local"),
    ("learning", "learn lesson обучение progress",
     ["app/static/learn.js", "app/templates/learn.html"], ["app/routes.py", "app/models.py"], ["nginx", "bot/reminder.py"], ["python tools/project_kb.py query learning"], "local"),
    ("offline sync", "offline sync indexeddb outbox delta progress синхронизация",
     ["app/static/sync.js", "app/static/idb.js"], ["app/routes.py", "android/app/src/main/java/com/learnwords/app/data/repository/AppRepository.kt"], ["bot/reminder.py"], ["python tools/project_kb.py route /api/progress/sync", "python tools/project_kb.py route /api/sync/updates"], "local android"),
    ("android api", "android api retrofit dto authentication synchronization",
     ["docs/codex/ANDROID_API.md", "android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt"], ["android/app/src/main/java/com/learnwords/app/data/api/ApiModels.kt", "app/routes.py"], ["app/templates"], ["python tools/project_kb.py android-api /api/progress/sync"], "android local"),
    ("difficult words", "difficult words сложные слова flags",
     ["app/static/difficult.js"], ["app/routes.py", "android/app/src/main/java/com/learnwords/app/ui/difficult"], ["bot/reminder.py"], ["python tools/project_kb.py table user_word_flags"], "local android"),
    ("audio", "audio tts generation cache аудио",
     ["app/audio_gen.py", "app/static/audio_worker.js"], ["app/routes.py", "android/app/src/main/java/com/learnwords/app/utils/AudioPlayer.kt", "config.py"], ["bot/auth.py"], ["python tools/project_kb.py route /api/audio/ensure"], "local android"),
    ("reminders", "reminder telegram notification напоминания",
     ["bot/reminder.py"], ["run.py", "docs/codex/DEPLOYMENT.md"], ["app/static"], ["python -m py_compile bot/reminder.py"], "local production"),
    ("database change", "database schema table migration sqlite база таблица",
     ["docs/codex/DATABASE.md"], ["run.py", "db_init.py", "app/routes.py", "bot/db.py"], ["unrelated javascript"], ["python tools/project_kb.py table words"], "local production"),
    ("production error", "production error deploy nginx service logs ошибка продакшн",
     ["docs/codex/DEPLOYMENT.md", "docs/codex/PRODUCTION_SNAPSHOT.md"], ["relevant handler", "relevant service logs", "Nginx route"], ["whole repository"], ["python tools/project_kb.py server-status", "python tools/project_kb.py compare-environments"], "production"),
    ("deployment", "deploy deployment production деплой",
     ["docs/codex/DEPLOYMENT.md", "AGENTS.md"], ["changed files", "targeted tests"], ["unrelated modules"], ["git status --short", "python tools/project_kb.py compare-environments"], "local production"),
]


def run(args: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                          capture_output=True, check=check)


def git_value(*args: str, default: str = "unknown") -> str:
    try:
        return run(["git", *args]).stdout.strip() or default
    except (OSError, subprocess.CalledProcessError):
        return default


def tracked_paths() -> list[Path]:
    try:
        raw = run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]).stdout
        names = [n for n in raw.split("\0") if n]
    except (OSError, subprocess.CalledProcessError):
        names = []
    return [ROOT / n for n in names if should_index(Path(n))]


def should_index(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & SKIP_PARTS or (rel.parts and rel.parts[0] == "data") or rel.name == ".env" or rel.name.startswith(".env."):
        return False
    if rel.suffix.lower() in SKIP_SUFFIXES:
        return False
    if rel.name in {"project_kb.sqlite", "bot_persistence.pkl"}:
        return False
    return rel.suffix.lower() in TEXT_EXTENSIONS or rel.name in {"Dockerfile", ".gitignore", ".dockerignore"}


def language(path: str) -> str:
    return {".py": "python", ".js": "javascript", ".html": "html", ".css": "css",
            ".kt": "kotlin", ".java": "java", ".sql": "sql", ".xml": "xml",
            ".yml": "yaml", ".yaml": "yaml", ".md": "markdown"}.get(Path(path).suffix.lower(), "text")


def layer(path: str) -> str:
    if path.startswith("android/"): return "android"
    if path.startswith("bot/"): return "telegram"
    if path.startswith("app/static/") or path.startswith("app/templates/"): return "frontend"
    if path.startswith("app/") or path in {"run.py", "config.py", "db_init.py"}: return "backend"
    if path.startswith("nginx/") or "docker" in path.lower() or path.endswith(".ps1"): return "deployment"
    if path.startswith("docs/") or path == "AGENTS.md": return "documentation"
    if path.startswith("tests/"): return "tests"
    return "project"


def purpose(path: str) -> str:
    known = {
        "run.py": "Flask and Telegram entrypoint; database initialization",
        "config.py": "Environment-variable names and application configuration",
        "db_init.py": "Base words table initialization and migrations",
        "app/routes.py": "Flask pages, API, sync, database and audio orchestration",
        "app/models.py": "Lesson persistence and queries",
        "app/audio_gen.py": "TTS audio generation and metadata updates",
        "app/telegram_auth.py": "Telegram Mini App init-data verification",
        "bot/auth.py": "Telegram registration, navigation and authentication handlers",
        "bot/upload.py": "Telegram word import handlers",
        "bot/reminder.py": "Telegram reminder scheduling and delivery",
        "app/static/idb.js": "IndexedDB stores and primitives",
        "app/static/sync.js": "Offline outbox upload and delta synchronization",
        "app/static/sw.js": "Service Worker caching strategy",
        "android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt": "Retrofit backend contract",
        "android/app/src/main/java/com/learnwords/app/data/api/ApiClient.kt": "Android base URL and request headers",
    }
    if path in known: return known[path]
    return f"{layer(path).capitalize()} file: {Path(path).name}"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    ensure_fts(con)
    return con


def ensure_fts(con: sqlite3.Connection, force_disable: bool = False) -> bool:
    if force_disable or os.getenv("PROJECT_KB_DISABLE_FTS5") == "1":
        con.execute("CREATE TABLE IF NOT EXISTS kb_capabilities(name TEXT PRIMARY KEY, enabled INTEGER)")
        con.execute("INSERT OR REPLACE INTO kb_capabilities VALUES('fts5',0)")
        return False
    try:
        for name, cols in {
            "symbols_fts": "name, signature, docstring, file_path",
            "files_fts": "path, purpose, layer",
            "routes_fts": "route_or_command, handler, purpose, file_path",
            "android_contracts_fts": "endpoint, android_symbol, backend_handler, notes",
            "docs_fts": "key, title, content, source_path",
            "task_routes_fts": "topic, keywords, primary_files_json, secondary_files_json",
        }.items():
            con.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {name} USING fts5({cols})")
        con.execute("CREATE TABLE IF NOT EXISTS kb_capabilities(name TEXT PRIMARY KEY, enabled INTEGER)")
        con.execute("INSERT OR REPLACE INTO kb_capabilities VALUES('fts5',1)")
        return True
    except sqlite3.OperationalError:
        con.execute("CREATE TABLE IF NOT EXISTS kb_capabilities(name TEXT PRIMARY KEY, enabled INTEGER)")
        con.execute("INSERT OR REPLACE INTO kb_capabilities VALUES('fts5',0)")
        return False


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > 2_000_000:
            return None
        text = path.read_text(encoding="utf-8", errors="replace")
        return text if "\x00" not in text else None
    except OSError:
        return None


def signature(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        try: return f"{node.name}{ast.unparse(node.args)}"
        except Exception: return node.name
    return getattr(node, "name", "")


def python_metadata(con: sqlite3.Connection, rel: str, text: str, scope: str) -> None:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return
    parents: list[str] = []
    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            con.execute("INSERT INTO symbols(name,symbol_type,signature,file_path,line_start,line_end,docstring,parent_symbol,source_scope) VALUES(?,?,?,?,?,?,?,?,?)",
                        (node.name, "class", node.name, rel, node.lineno, getattr(node,"end_lineno",node.lineno), trim_doc(ast.get_docstring(node)), parents[-1] if parents else None, scope))
            parents.append(node.name); self.generic_visit(node); parents.pop()
        def _func(self, node: ast.AST) -> None:
            con.execute("INSERT INTO symbols(name,symbol_type,signature,file_path,line_start,line_end,docstring,parent_symbol,source_scope) VALUES(?,?,?,?,?,?,?,?,?)",
                        (node.name, "async_function" if isinstance(node,ast.AsyncFunctionDef) else "function", signature(node), rel, node.lineno, getattr(node,"end_lineno",node.lineno), trim_doc(ast.get_docstring(node)), parents[-1] if parents else None, scope))
            for dec in node.decorator_list:
                parsed = parse_flask_decorator(dec)
                if parsed:
                    method, route = parsed
                    con.execute("INSERT INTO routes(route_type,method_or_trigger,route_or_command,handler,file_path,line_number,auth_type,purpose,source_scope) VALUES(?,?,?,?,?,?,?,?,?)",
                                ("flask", method, route, node.name, rel, getattr(dec,"lineno",node.lineno), infer_auth(text, node.lineno), (ast.get_docstring(node) or "")[:300], scope))
            parents.append(node.name); self.generic_visit(node); parents.pop()
        visit_FunctionDef = _func
        visit_AsyncFunctionDef = _func
        def visit_Import(self, node: ast.Import) -> None:
            for n in node.names:
                con.execute("INSERT INTO imports(source_file,target_module,imported_name,import_type,source_scope) VALUES(?,?,?,?,?)", (rel,n.name,n.asname,"import",scope))
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for n in node.names:
                con.execute("INSERT INTO imports(source_file,target_module,imported_name,import_type,source_scope) VALUES(?,?,?,?,?)", (rel,node.module or "",n.name,"from",scope))
    Visitor().visit(tree)


def trim_doc(value: str | None) -> str | None:
    if not value: return None
    return re.sub(r"\s+", " ", value)[:500]


def parse_flask_decorator(dec: ast.AST) -> tuple[str, str] | None:
    if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute): return None
    if dec.func.attr not in {"route", "get", "post", "put", "delete", "patch"}: return None
    if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str): return None
    method = dec.func.attr.upper()
    if method == "ROUTE":
        method = "GET"
        for kw in dec.keywords:
            if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                method = ",".join(str(x.value).upper() for x in kw.value.elts if isinstance(x,ast.Constant))
    return method, dec.args[0].value


def infer_auth(text: str, line: int) -> str:
    chunk = "\n".join(text.splitlines()[max(0,line-6):line+12]).lower()
    if "admin" in chunk: return "admin"
    if "android" in chunk or "x-user-id" in chunk: return "android headers/session"
    if "telegram" in chunk or "initdata" in chunk: return "telegram init data/session"
    if "require_user" in chunk or "user_id" in chunk or "session" in chunk: return "authenticated user"
    return "public or handler-validated"


def generic_symbols(con: sqlite3.Connection, rel: str, text: str, scope: str) -> None:
    patterns = []
    if rel.endswith((".kt", ".java")):
        patterns = [("class", r"\b(?:data\s+)?class\s+(\w+)"), ("interface", r"\binterface\s+(\w+)"), ("function", r"\b(?:suspend\s+)?fun\s+(\w+)\s*\(([^)]*)\)")]
    elif rel.endswith(".js"):
        patterns = [("function", r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"), ("function", r"\b(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>")]
    for typ, pattern in patterns:
        for m in re.finditer(pattern, text):
            line = text.count("\n",0,m.start())+1
            sig = re.sub(r"\s+"," ",m.group(0))[:300]
            con.execute("INSERT INTO symbols(name,symbol_type,signature,file_path,line_start,line_end,docstring,parent_symbol,source_scope) VALUES(?,?,?,?,?,?,?,?,?)",
                        (m.group(1),typ,sig,rel,line,line,None,None,scope))


def telegram_routes(con: sqlite3.Connection, rel: str, text: str, scope: str) -> None:
    patterns = [
        ("command", re.compile(r"CommandHandler\(\s*[\"']([^\"']+)[\"']\s*,\s*([\w.]+)")),
        ("callback", re.compile(r"CallbackQueryHandler\(\s*([\w.]+)(?:\s*,\s*pattern\s*=\s*([^,)]+))?")),
        ("message", re.compile(r"MessageHandler\((.{0,250}?),\s*([\w.]+)\s*\)", re.S)),
    ]
    for typ, pattern in patterns:
        for m in pattern.finditer(text):
            line = text.count("\n",0,m.start())+1
            if typ == "command": trigger, handler = "/"+m.group(1), m.group(2)
            elif typ == "callback": handler, trigger = m.group(1), (m.group(2) or "callback")[:200]
            else: trigger, handler = re.sub(r"\s+"," ",m.group(1))[:200], m.group(2)
            con.execute("INSERT INTO routes(route_type,method_or_trigger,route_or_command,handler,file_path,line_number,auth_type,purpose,source_scope) VALUES(?,?,?,?,?,?,?,?,?)",
                        ("telegram",typ,trigger,handler,rel,line,"telegram user","Telegram handler",scope))


def split_columns(body: str) -> list[dict[str, str]]:
    parts, buf, depth = [], [], 0
    for ch in body:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            parts.append("".join(buf)); buf=[]
        else: buf.append(ch)
    if buf: parts.append("".join(buf))
    out=[]
    for raw in parts:
        clean=re.sub(r"\s+"," ",raw.strip())
        if not clean or re.match(r"(?i)^(primary|foreign|unique|check|constraint)\b",clean): continue
        bits=clean.replace('"','').split(None,2)
        if bits: out.append({"name":bits[0],"type":bits[1] if len(bits)>1 else "","constraints":bits[2] if len(bits)>2 else ""})
    return out


def database_metadata(con: sqlite3.Connection, rel: str, text: str, scope: str) -> None:
    indexes: dict[str,list[dict[str,str]]] = {}
    for m in INDEX_RE.finditer(text):
        indexes.setdefault(m.group(2),[]).append({"name":m.group(1),"columns":re.sub(r"\s+"," ",m.group(3)).strip()})
    for m in TABLE_RE.finditer(text):
        name=m.group(1); line=text.count("\n",0,m.start())+1
        con.execute("INSERT OR REPLACE INTO database_tables(table_name,defined_in,definition_line,columns_json,indexes_json,environment) VALUES(?,?,?,?,?,?)",
                    (name,rel,line,json.dumps(split_columns(m.group(2)),ensure_ascii=False),json.dumps(indexes.get(name,[]),ensure_ascii=False),"production" if scope=="production" else "local"))
    known_tables = set(re.findall(r"(?i)\b(?:FROM|JOIN|INTO|UPDATE|TABLE|DELETE\s+FROM)\s+[\"'`]?([a-z_][\w]*)", text))
    lines=text.splitlines()
    for table in known_tables:
        if table.lower() in {"if","set","where","select","values"}: continue
        for i,line_text in enumerate(lines,1):
            if not re.search(rf"(?i)\b{re.escape(table)}\b",line_text): continue
            op = "migration" if re.search(r"(?i)CREATE|ALTER",line_text) else "insert" if re.search(r"(?i)INSERT",line_text) else "update" if re.search(r"(?i)UPDATE",line_text) else "delete" if re.search(r"(?i)DELETE",line_text) else "read"
            con.execute("INSERT INTO database_usage(table_name,file_path,symbol_name,operation,line_number,source_scope) VALUES(?,?,?,?,?,?)",(table,rel,None,op,i,scope))


def frontend_metadata(con: sqlite3.Connection, rel: str, text: str, scope: str) -> None:
    patterns = [
        ("api", r"(?:fetch\s*\(|SYNC_URL\s*=\s*)[\"'`]([^\"'`]+)"),
        ("template_script", r"<script[^>]+src=[\"']([^\"']+)"),
        ("template_style", r"<link[^>]+href=[\"']([^\"']+)"),
        ("indexeddb_store", r"(?:createObjectStore\s*\(|STORES\s*=\s*\{)[\"']?([\w-]+)"),
        ("service_worker", r"serviceWorker\.register\s*\(\s*[\"']([^\"']+)"),
        ("global", r"window\.([A-Za-z_$][\w$]*)\s*="),
    ]
    for typ, pattern in patterns:
        for m in re.finditer(pattern,text,re.I):
            value=m.group(1)
            if typ=="api" and not (value.startswith("/") or value.startswith("http")): continue
            con.execute("INSERT INTO frontend_links(source_file,target_type,target_value,line_number,source_scope) VALUES(?,?,?,?,?)",
                        (rel,typ,value,text.count("\n",0,m.start())+1,scope))


def android_metadata(con: sqlite3.Connection, rel: str, text: str) -> None:
    annotations=list(re.finditer(r"@(GET|POST|PUT|DELETE|PATCH)\(\s*[\"']([^\"']+)[\"']\s*\)",text))
    for pos,m in enumerate(annotations):
        chunk=text[m.end():annotations[pos+1].start() if pos+1<len(annotations) else len(text)]
        fm=re.search(r"(?:suspend\s+)?fun\s+(\w+)\s*\(",chunk)
        if not fm: continue
        open_pos=fm.end()-1; depth=0; close_pos=None
        for i,ch in enumerate(chunk[open_pos:],open_pos):
            depth += (ch=="(")-(ch==")")
            if depth==0: close_pos=i; break
        if close_pos is None: continue
        args=chunk[open_pos+1:close_pos]
        rm=re.search(r":\s*Response<([^\r\n]+)>",chunk[close_pos+1:])
        if not rm: continue
        method,endpoint,symbol,response=m.group(1),m.group(2),fm.group(1),rm.group(1).strip()
        endpoint="/"+endpoint.lstrip("/")
        body=re.search(r"@Body\s+\w+\s*:\s*([\w<>?.]+)",args)
        con.execute("INSERT OR REPLACE INTO android_contracts(endpoint,http_method,android_file,android_symbol,request_model,response_model,auth_headers_json,backend_file,backend_handler,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (endpoint,method,rel,symbol,body.group(1) if body else None,response,json.dumps(["X-User-Id","X-Client","X-Device-Language"]),None,None,"unresolved","Retrofit declaration parsed from local Android source"))


def link_android(con: sqlite3.Connection) -> None:
    routes=con.execute("SELECT route_or_command,method_or_trigger,handler,file_path FROM routes WHERE route_type='flask' AND source_scope='local'").fetchall()
    for row in con.execute("SELECT id,endpoint,http_method FROM android_contracts").fetchall():
        match=next((r for r in routes if normalize_route(r["route_or_command"])==normalize_route(row["endpoint"]) and row["http_method"] in r["method_or_trigger"]),None)
        if match:
            con.execute("UPDATE android_contracts SET backend_file=?,backend_handler=?,status='confirmed',notes=? WHERE id=?",(match["file_path"],match["handler"],"Confirmed by matching local Flask method and normalized route",row["id"]))
        else:
            con.execute("UPDATE android_contracts SET status='unresolved',notes=? WHERE id=?",("No matching local Flask route found; compatibility review required",row["id"]))


def normalize_route(route: str) -> str:
    route="/"+route.lstrip("/")
    route=re.sub(r"<(?:(?:int|string|path):)?[^>]+>","{}",route)
    route=re.sub(r"\{[^}]+\}","{}",route)
    return route.rstrip("/") or "/"


def index_file(con: sqlite3.Connection, path: Path, scope: str="local", force: bool=False) -> bool:
    try: rel=path.relative_to(ROOT).as_posix()
    except ValueError: rel=path.as_posix()
    text=read_text(path)
    if text is None: return False
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    old=con.execute("SELECT sha256 FROM files WHERE path=? AND source_scope=?",(rel,scope)).fetchone()
    if old and old[0]==digest and not force: return False
    for table,column in [("symbols","file_path"),("imports","source_file"),("routes","file_path"),("database_tables","defined_in"),("database_usage","file_path"),("frontend_links","source_file")]:
        con.execute(f"DELETE FROM {table} WHERE {column}=? AND source_scope=?" if table not in {"database_tables"} else f"DELETE FROM {table} WHERE {column}=? AND environment=?",(rel,scope if table!="database_tables" else ("production" if scope=="production" else "local")))
    if rel.startswith("android/"): con.execute("DELETE FROM android_contracts WHERE android_file=?",(rel,))
    con.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?,?,?)",(rel,scope,language(rel),layer(rel),purpose(rel),path.stat().st_size,digest,NOW(),0,int(rel in {"run.py","app/routes.py","android/app/src/main/AndroidManifest.xml"})))
    if rel.endswith(".py"): python_metadata(con,rel,text,scope)
    else: generic_symbols(con,rel,text,scope)
    if rel.startswith("bot/") and rel.endswith(".py"): telegram_routes(con,rel,text,scope)
    database_metadata(con,rel,text,scope)
    if rel.endswith((".js",".html")): frontend_metadata(con,rel,text,scope)
    if rel.endswith(("ApiService.kt","ApiService.java")): android_metadata(con,rel,text)
    return True


def refresh_fts(con: sqlite3.Connection) -> None:
    cap=con.execute("SELECT enabled FROM kb_capabilities WHERE name='fts5'").fetchone()
    if not cap or not cap[0]: return
    pairs={
        "symbols_fts":("symbols",["name","signature","docstring","file_path"]),
        "files_fts":("files",["path","purpose","layer"]),
        "routes_fts":("routes",["route_or_command","handler","purpose","file_path"]),
        "android_contracts_fts":("android_contracts",["endpoint","android_symbol","backend_handler","notes"]),
        "docs_fts":("docs",["key","title","content","source_path"]),
        "task_routes_fts":("task_routes",["topic","keywords","primary_files_json","secondary_files_json"]),
    }
    for fts,(table,cols) in pairs.items():
        con.execute(f"DELETE FROM {fts}")
        con.execute(f"INSERT INTO {fts}({','.join(cols)}) SELECT {','.join(cols)} FROM {table}")


def index_docs(con: sqlite3.Connection) -> None:
    if not DOCS_DIR.exists(): return
    for p in DOCS_DIR.glob("*.md"):
        text=read_text(p) or ""
        con.execute("INSERT OR REPLACE INTO docs(key,title,content,source_path) VALUES(?,?,?,?)",(p.stem,p.stem.replace("_"," ").title(),text[:100000],p.relative_to(ROOT).as_posix()))


def generate_catalog_docs(con: sqlite3.Connection) -> None:
    """Regenerate line-numbered catalogs from indexed metadata."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    table_lines = [
        "# Database map", "",
        "Схема ниже извлечена из SQL в исходниках и production `sqlite_master`; строки пользователей не читаются.", "",
        "Создание/миграции распределены между `run.py`, `db_init.py`, `app/routes.py`, `app/models.py`, `bot/db.py`, `bot/auth.py` и специализированными модулями. Это известное дублирование; менять схему следует только после проверки всех владельцев.", "",
    ]
    names = [r[0] for r in con.execute("SELECT DISTINCT table_name FROM database_tables ORDER BY table_name")]
    for name in names:
        table_lines += [f"## `{name}`", ""]
        for d in con.execute("SELECT * FROM database_tables WHERE table_name=? ORDER BY environment,defined_in", (name,)):
            cols = json.loads(d["columns_json"] or "[]"); indexes = json.loads(d["indexes_json"] or "[]")
            table_lines.append(f"- {d['environment']}: `{d['defined_in']}`{':' + str(d['definition_line']) if d['definition_line'] else ''}.")
            table_lines.append("- Колонки: " + (", ".join(f"`{c.get('name')}` {c.get('type','')} {c.get('constraints','')}".strip() for c in cols) or "не распознаны статически") + ".")
            table_lines.append("- Индексы: " + (", ".join(f"`{i.get('name')}` ({i.get('columns','')})" for i in indexes) or "не найдены в этом определении") + ".")
        uses = con.execute("SELECT file_path,operation,line_number,source_scope FROM database_usage WHERE table_name=? ORDER BY file_path,line_number LIMIT 30", (name,)).fetchall()
        table_lines.append("- Чтение/запись/миграции: " + (", ".join(f"`{u['file_path']}:{u['line_number']}` ({u['operation']}, {u['source_scope']})" for u in uses) or "статически не найдены") + ".")
        apis = con.execute("SELECT DISTINCT route_or_command FROM routes r JOIN database_usage u ON r.file_path=u.file_path WHERE u.table_name=? AND r.route_type='flask' LIMIT 30",(name,)).fetchall()
        bots = con.execute("SELECT DISTINCT route_or_command FROM routes r JOIN database_usage u ON r.file_path=u.file_path WHERE u.table_name=? AND r.route_type='telegram' LIMIT 20",(name,)).fetchall()
        table_lines.append("- Связанные API файла-владельца: " + (", ".join(f"`{x[0]}`" for x in apis) or "проверять по handler") + ".")
        table_lines.append("- Telegram handlers файла-владельца: " + (", ".join(f"`{x[0]}`" for x in bots) or "нет прямой связи") + ".")
        table_lines.append("")
    (DOCS_DIR/"DATABASE.md").write_text("\n".join(table_lines),encoding="utf-8")

    api_lines=["# API and Telegram map","","Строки и методы получены автоматически. Авторизация эвристически определяется по коду около handler; перед изменением контракта откройте handler и соответствующий DTO/consumer.",""]
    for r in con.execute("SELECT * FROM routes WHERE route_type='flask' ORDER BY file_path,line_number"):
        consumers=[x[0] for x in con.execute("SELECT android_file FROM android_contracts WHERE backend_handler=?",(r["handler"],))]
        front=[x[0] for x in con.execute("SELECT source_file FROM frontend_links WHERE target_type='api' AND target_value LIKE ? LIMIT 10",(f"%{r['route_or_command']}%",))]
        api_lines += [f"## `{r['method_or_trigger']} {r['route_or_command']}`", "",
                      f"- Handler: `{r['handler']}` — `{r['file_path']}:{r['line_number']}`.",
                      f"- Назначение: {r['purpose'] or purpose(r['file_path'])}.",
                      f"- Авторизация: {r['auth_type']}.",
                      "- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.",
                      f"- Frontend consumers: {', '.join(f'`{x}`' for x in sorted(set(front))) or 'не найдены статически'}.",
                      f"- Android consumers: {', '.join(f'`{x}`' for x in consumers) or 'нет подтверждённого Retrofit соответствия'}.",
                      "- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.",""]
    api_lines += ["# Telegram handlers",""]
    for r in con.execute("SELECT * FROM routes WHERE route_type='telegram' ORDER BY file_path,line_number"):
        api_lines += [f"- `{r['method_or_trigger']} {r['route_or_command']}` → `{r['handler']}` (`{r['file_path']}:{r['line_number']}`); сценарий: {r['purpose']}; таблицы смотреть через `table`/`query`."]
    (DOCS_DIR/"API_MAP.md").write_text("\n".join(api_lines)+"\n",encoding="utf-8")

    android_lines=["# Android API map","","Подтверждённые факты извлечены из локального Retrofit-клиента. Base URL задаётся `BuildConfig.BASE_URL`/пользовательской настройкой; `ApiClient.kt` добавляет `X-User-Id`, `X-Client: android`, `X-Device-Language`. Клиент хранит offline-данные в Room и очередь progress sync в repository/database слоях.",""]
    for r in con.execute("SELECT * FROM android_contracts ORDER BY endpoint,http_method"):
        android_lines += [f"## `{r['http_method']} {r['endpoint']}` — {r['status']}","",f"- Android: `{r['android_file']}` / `{r['android_symbol']}`.",f"- Request DTO: `{r['request_model'] or 'query/path/none'}`; response DTO: `{r['response_model'] or 'unresolved'}`.",f"- Headers: `{r['auth_headers_json']}`.",f"- Backend: `{r['backend_file'] or 'not matched'}` / `{r['backend_handler'] or 'not matched'}`.",f"- Примечание: {r['notes']}.",""]
    android_lines += ["## Offline/sync compatibility","","`AppRepository.kt` сохраняет локальные данные через Room, ставит progress events в очередь и отправляет их в `/api/progress/sync`; `/api/sync/updates` используется для серверных delta-обновлений. Новые обязательные поля должны иметь совместимые defaults; URL, headers и DTO меняются одновременно на backend и Android.",""]
    (DOCS_DIR/"ANDROID_API.md").write_text("\n".join(android_lines),encoding="utf-8")

    front_lines=["# Frontend map","","HTML-шаблоны рендерятся Flask, используют общие функции `base.html`; IndexedDB и Service Worker обеспечивают offline-first работу.",""]
    for f in con.execute("SELECT DISTINCT source_file FROM frontend_links ORDER BY source_file"):
        links=con.execute("SELECT target_type,target_value,line_number FROM frontend_links WHERE source_file=? ORDER BY line_number",(f[0],)).fetchall()
        front_lines += [f"## `{f[0]}`","",*([f"- {x['target_type']}: `{x['target_value']}` (`{f[0]}:{x['line_number']}`)." for x in links] or ["- Связи не распознаны."]),""]
    front_lines += ["## Offline flow","","`idb.js` открывает IndexedDB/stores → действия без сети попадают в outbox → `sync.js` отправляет progress в `/api/progress/sync` → `/api/sync/updates?since=...` возвращает delta → локальные stores обновляются. `sw.js` обслуживает кэш shell/static; `audio_worker.js` координирует аудиокэш.",""]
    (DOCS_DIR/"FRONTEND_MAP.md").write_text("\n".join(front_lines),encoding="utf-8")


def seed_task_routes(con: sqlite3.Connection) -> None:
    for row in TASK_ROUTES:
        con.execute("INSERT OR REPLACE INTO task_routes(topic,keywords,primary_files_json,secondary_files_json,excluded_paths_json,recommended_checks_json,environment_scope) VALUES(?,?,?,?,?,?,?)",
                    (row[0],row[1],json.dumps(row[2],ensure_ascii=False),json.dumps(row[3],ensure_ascii=False),json.dumps(row[4],ensure_ascii=False),json.dumps(row[5],ensure_ascii=False),row[6]))


def local_snapshot(con: sqlite3.Connection) -> None:
    dirty=bool(git_value("status","--short",default=""))
    files=[r[0] for r in con.execute("SELECT path FROM files WHERE source_scope='local' ORDER BY path")]
    entries=[r[0] for r in con.execute("SELECT path FROM files WHERE source_scope='local' AND is_entrypoint=1 ORDER BY path")]
    con.execute("INSERT OR REPLACE INTO environment_snapshots(environment,git_branch,git_commit,git_dirty,project_path,captured_at,tracked_files_json,entrypoints_json,schema_hash) VALUES(?,?,?,?,?,?,?,?,?)",
                ("local",git_value("branch","--show-current"),git_value("rev-parse","HEAD"),int(dirty),str(ROOT),NOW(),json.dumps(files),json.dumps(entries),schema_hash(con,"local")))


def schema_hash(con: sqlite3.Connection, env: str) -> str:
    rows=con.execute("SELECT table_name,columns_json,indexes_json FROM database_tables WHERE environment=? ORDER BY table_name,defined_in",(env,)).fetchall()
    return hashlib.sha256(json.dumps([tuple(r) for r in rows],sort_keys=True).encode()).hexdigest() if rows else ""


def build(db_path: Path=DB_PATH) -> dict[str,int]:
    if db_path.exists(): db_path.unlink()
    con=connect(db_path); changed=0
    for path in tracked_paths(): changed += int(index_file(con,path,force=True))
    seed_task_routes(con); link_android(con); generate_catalog_docs(con); index_docs(con); local_snapshot(con); refresh_fts(con)
    con.commit(); counts={t:con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ["files","symbols","routes","database_tables","android_contracts"]}; con.close()
    if db_path==DB_PATH: write_manifest()
    return counts


def update(files: list[str] | None=None, db_path: Path=DB_PATH) -> tuple[int,int]:
    con=connect(db_path); current={p.relative_to(ROOT).as_posix():p for p in tracked_paths()}
    targets=current if not files else {Path(f).as_posix():ROOT/f for f in files}
    changed=sum(int(index_file(con,p)) for p in targets.values() if p.exists() and should_index(Path(p.name) if p.is_absolute() else p))
    removed=0
    if not files:
        for row in con.execute("SELECT path FROM files WHERE source_scope='local'").fetchall():
            if row[0] not in current:
                rel=row[0]
                for table,column in [("files","path"),("symbols","file_path"),("imports","source_file"),("routes","file_path"),("database_tables","defined_in"),("database_usage","file_path"),("frontend_links","source_file")]: con.execute(f"DELETE FROM {table} WHERE {column}=?",(rel,))
                con.execute("DELETE FROM android_contracts WHERE android_file=?",(rel,)); removed+=1
    seed_task_routes(con); link_android(con); generate_catalog_docs(con); index_docs(con); local_snapshot(con); refresh_fts(con); con.commit(); con.close()
    if db_path==DB_PATH: write_manifest()
    return changed,removed


def redact_command(value: str) -> str:
    value=re.sub(r"(?i)(--?(?:token|password|secret|api[_-]?key))(?:=|\s+)\S+",r"\1=<redacted>",value)
    value=re.sub(r"(?i)\b([A-Z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY)[A-Z0-9_]*)=\S+",r"\1=<redacted>",value)
    return value


def parse_production_payload(text: str) -> dict:
    result={"services":[],"routes":[],"tables":[],"meta":{},"hashes":{}}
    for line in text.splitlines():
        if line.startswith("META|"):
            _,key,value=line.split("|",2); result["meta"][key]=value
        elif line.startswith("SERVICE|"):
            parts=line.split("|",8); result["services"].append(parts[1:])
        elif line.startswith("ROUTE|"):
            parts=line.split("|",5); result["routes"].append(parts[1:])
        elif line.startswith("SCHEMA|"):
            parts=line.split("|",5); result["tables"].append(parts[1:])
        elif line.startswith("HASH|"):
            _,digest,path=line.split("|",2); result["hashes"][path]=digest
    return result


REMOTE_SCAN = r'''set -u
echo 'META|project_path|/opt/learn-words'
echo 'META|git_branch|unavailable'
echo 'META|git_commit|unavailable'
if test -d /opt/learn-words/.git; then
  echo "META|git_branch|$(git -C /opt/learn-words branch --show-current 2>/dev/null || true)"
  echo "META|git_commit|$(git -C /opt/learn-words rev-parse HEAD 2>/dev/null || true)"
  test -n "$(git -C /opt/learn-words status --short 2>/dev/null)" && echo 'META|git_dirty|1' || echo 'META|git_dirty|0'
else echo 'META|git_dirty|unknown'; fi
if command -v docker >/dev/null 2>&1; then
 docker inspect learn-words-learn-words-1 2>/dev/null | python3 -c 'import json,sys; x=json.load(sys.stdin)[0]; print("SERVICE|"+"|".join([x["Name"].lstrip("/"),"docker",x["Config"].get("WorkingDir", ""),"python run.py","root","root","/opt/learn-words/.env","7001"]))' 2>/dev/null || true
 docker exec proxy-nginx sh -c 'grep -R -n -E "server_name learn\.iovenko\.eu|location /|proxy_pass.*learn-words" /etc/nginx/conf.d/learn.conf 2>/dev/null' | while IFS= read -r line; do echo "ROUTE|learn.iovenko.eu|/|http://learn-words:7001|/opt/proxy/nginx/conf.d/learn.conf|$line"; done
 docker exec -i learn-words-learn-words-1 python - <<'PY' 2>/dev/null || true
import sqlite3
c=sqlite3.connect('/app/words.db')
for kind,name,tbl,sql in c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE type IN ('table','index') AND name NOT LIKE 'sqlite_%' ORDER BY type,name"):
 print('SCHEMA|'+kind+'|'+name+'|'+tbl+'|'+('' if sql is None else sql.replace('\n',' ')))
c.close()
PY
fi
cd /opt/learn-words 2>/dev/null || exit 0
for f in run.py config.py db_init.py app/routes.py app/models.py app/audio_gen.py app/telegram_auth.py bot/auth.py bot/upload.py bot/reminder.py app/static/idb.js app/static/sync.js app/static/learn.js app/static/difficult.js app/static/upload.js app/static/sw.js app/static/audio_worker.js; do test -f "$f" && echo "HASH|$(sha256sum "$f" | cut -d' ' -f1)|$f"; done
'''


def server_scan(host: str, key: str, mock_file: str | None=None, db_path: Path=DB_PATH) -> dict:
    if mock_file:
        raw=Path(mock_file).read_text(encoding="utf-8")
    else:
        payload=base64.b64encode(REMOTE_SCAN.encode()).decode()
        cp=run(["ssh","-i",str(Path(key).expanduser()),"-o","BatchMode=yes","-o","ConnectTimeout=15",host,f"echo {payload} | base64 -d | bash"],check=True)
        raw=cp.stdout
    data=parse_production_payload(raw); con=connect(db_path)
    con.execute("DELETE FROM services WHERE environment='production'"); con.execute("DELETE FROM deployment_routes")
    for s in data["services"]:
        vals=(s+[""]*8)[:8]
        con.execute("INSERT OR REPLACE INTO services(environment,service_name,service_type,working_directory,exec_start_redacted,user_name,group_name,environment_file_path,port,source_file,last_indexed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",("production",vals[0],vals[1],vals[2],redact_command(vals[3]),vals[4],vals[5],vals[6],vals[7],"docker inspect",NOW()))
    for r in data["routes"]:
        vals=(r+[""]*5)[:5]
        con.execute("INSERT OR REPLACE INTO deployment_routes(server_name,public_path,proxy_target,nginx_config_path,backend_service,notes) VALUES(?,?,?,?,?,?)",(vals[0],vals[1],vals[2],vals[3],"learn-words-learn-words-1",vals[4]))
    con.execute("DELETE FROM database_tables WHERE environment='production'")
    idx: dict[str,list[dict[str,str]]]={}; tables=[]
    for kind,name,tbl,sql,*_ in data["tables"]:
        if kind=="index":
            m=INDEX_RE.search(sql); idx.setdefault(tbl,[]).append({"name":name,"columns":m.group(3).strip() if m else ""})
        elif kind=="table": tables.append((name,sql))
    for name,sql in tables:
        m=TABLE_RE.search(sql)
        con.execute("INSERT OR REPLACE INTO database_tables(table_name,defined_in,definition_line,columns_json,indexes_json,environment) VALUES(?,?,?,?,?,?)",(name,"/app/words.db sqlite_master",None,json.dumps(split_columns(m.group(2)) if m else [],ensure_ascii=False),json.dumps(idx.get(name,[]),ensure_ascii=False),"production"))
    meta=data["meta"]
    con.execute("INSERT OR REPLACE INTO environment_snapshots(environment,git_branch,git_commit,git_dirty,project_path,captured_at,tracked_files_json,entrypoints_json,schema_hash) VALUES(?,?,?,?,?,?,?,?,?)",("production",meta.get("git_branch","unavailable"),meta.get("git_commit","unavailable"),None if meta.get("git_dirty")=="unknown" else int(meta.get("git_dirty","0")),meta.get("project_path","unknown"),NOW(),json.dumps(sorted(data["hashes"])),json.dumps(["run.py"]),schema_hash(con,"production")))
    generate_catalog_docs(con); index_docs(con); refresh_fts(con); con.commit(); con.close()
    if db_path==DB_PATH: write_snapshot(data); write_manifest()
    return data


def write_snapshot(data: dict) -> None:
    DOCS_DIR.mkdir(parents=True,exist_ok=True); meta=data["meta"]
    local_commit=git_value("rev-parse","HEAD"); local_branch=git_value("branch","--show-current"); dirty=bool(git_value("status","--short",default=""))
    local_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked_paths() if p.relative_to(ROOT).as_posix() in data["hashes"]}
    diffs=[p for p,h in data["hashes"].items() if local_hashes.get(p)!=h]
    service_lines=[f"- `{s[0]}`: {s[1]}, working directory `{s[2]}`, port `{s[7] if len(s)>7 else ''}`." for s in data["services"]] or ["- Не обнаружены."]
    unique_routes=[]
    for r in data["routes"]:
        key=tuple(r[:4])
        if key not in unique_routes: unique_routes.append(key)
    route_lines=[f"- `https://{r[0]}{r[1]}` → `{r[2]}` (`{r[3]}`)." for r in unique_routes] or ["- Не обнаружены."]
    content=f"""# Production snapshot

Проверено: `{NOW()}`. Снимок содержит только обезличенные метаданные.

## Git и размещение

- Local: `{ROOT}`, branch `{local_branch}`, commit `{local_commit}`, dirty: `{str(dirty).lower()}`.
- Production: `{meta.get('project_path','unknown')}`, branch `{meta.get('git_branch','unavailable')}`, commit `{meta.get('git_commit','unavailable')}`, dirty: `{meta.get('git_dirty','unknown')}`.
- Production Git SHA недоступен, если каталог развёртывания не содержит `.git`; идентичность файлов тогда определяется только по SHA-256.

## Runtime

{chr(10).join(service_lines)}

## Nginx

{chr(10).join(route_lines)}

## Расхождения

- Основные файлы с отличающимся SHA-256: {', '.join(f'`{x}`' for x in diffs) if diffs else 'не обнаружены среди проверенных файлов'}.
- Production schema: {len([x for x in data['tables'] if x[0]=='table'])} таблиц; содержимое строк не читалось.
- В production есть runtime/data-каталоги, которые намеренно не индексировались.
"""
    SNAPSHOT_PATH.write_text(content,encoding="utf-8")


def write_manifest() -> None:
    if not DB_PATH.exists(): return
    con=connect(); local=con.execute("SELECT * FROM environment_snapshots WHERE environment='local'").fetchone(); prod=con.execute("SELECT * FROM environment_snapshots WHERE environment='production'").fetchone()
    manifest={
        "format_version":1,"generated_at":NOW(),"local_git_commit":local["git_commit"] if local else None,
        "production_git_commit":prod["git_commit"] if prod else None,"production_project_path":prod["project_path"] if prod else None,
        "entrypoints":[r[0] for r in con.execute("SELECT path FROM files WHERE is_entrypoint=1 ORDER BY path")],
        "components":["Flask backend","Telegram bot","Telegram Mini App","SQLite","offline IndexedDB","Android client","Docker/Nginx production"],
        "main_files":[r[0] for r in con.execute("SELECT path FROM files WHERE purpose NOT LIKE '%file:%' ORDER BY path")],
        "tables":sorted({r[0] for r in con.execute("SELECT table_name FROM database_tables")}),
        "api":[dict(r) for r in con.execute("SELECT method_or_trigger AS method,route_or_command AS url,handler,file_path,line_number FROM routes WHERE route_type='flask' ORDER BY file_path,line_number")],
        "telegram_handlers":[dict(r) for r in con.execute("SELECT method_or_trigger AS trigger_type,route_or_command AS trigger,handler,file_path,line_number FROM routes WHERE route_type='telegram' ORDER BY file_path,line_number")],
        "android_contracts":[dict(r) for r in con.execute("SELECT endpoint,http_method,android_symbol,backend_handler,status FROM android_contracts ORDER BY endpoint")],
        "frontend_entrypoints":["app/templates/base.html","app/templates/index.html","app/static/idb.js","app/static/sync.js","app/static/sw.js"],
        "systemd_services":[dict(r) for r in con.execute("SELECT service_name,service_type,working_directory,port FROM services")],
        "nginx_routes":[dict(r) for r in con.execute("SELECT server_name,public_path,proxy_target,nginx_config_path FROM deployment_routes")],
        "verification_commands":["python -m compileall tools","python -m unittest tests.test_project_kb","python tools/project_kb.py status"],
        "sqlite_index":".codex/project_kb.sqlite",
        "cli_commands":["build","update","server-scan","server-status","compare-environments","query","files-for","symbol","route","table","android-api","service","deployment","status"],
    }
    con.close(); MANIFEST_PATH.parent.mkdir(parents=True,exist_ok=True)
    if MANIFEST_PATH.exists():
        try:
            previous=json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            old_time=previous.pop("generated_at",None); current=dict(manifest); current.pop("generated_at",None)
            if previous==current:
                manifest["generated_at"]=old_time or manifest["generated_at"]
                return
        except (OSError,json.JSONDecodeError):
            pass
    MANIFEST_PATH.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def search_rows(con: sqlite3.Connection, q: str, limit: int) -> list[sqlite3.Row]:
    like=f"%{q}%"; tokens=[t for t in re.findall(r"[\w/-]+",q.lower()) if len(t)>2]
    rows=con.execute("SELECT path,purpose,source_scope,layer FROM files WHERE lower(path) LIKE lower(?) OR lower(purpose) LIKE lower(?) LIMIT ?",(like,like,limit)).fetchall()
    if len(rows)<limit and tokens:
        clauses=" OR ".join(["lower(path||' '||purpose) LIKE ?"]*len(tokens))
        extra=con.execute(f"SELECT path,purpose,source_scope,layer FROM files WHERE {clauses} LIMIT ?",(*[f"%{t}%" for t in tokens],limit-len(rows))).fetchall()
        seen={r["path"] for r in rows}; rows.extend(r for r in extra if r["path"] not in seen)
    return rows[:limit]


def print_result(value, as_json: bool=False) -> None:
    if as_json:
        if isinstance(value,list): value=[dict(x) if isinstance(x,sqlite3.Row) else x for x in value]
        elif isinstance(value,sqlite3.Row): value=dict(value)
        print(json.dumps(value,ensure_ascii=False,indent=2,default=str))
    elif isinstance(value,str): print(value)
    elif isinstance(value,dict):
        for key,item in value.items():
            rendered=json.dumps(item,ensure_ascii=False,default=str) if isinstance(item,(dict,list)) else str(item)
            print(f"{key}={rendered}")
    else:
        for item in value:
            print(" | ".join(f"{k}={v}" for k,v in dict(item).items() if v not in (None,"")))


def files_for(con: sqlite3.Connection, topic: str) -> dict:
    words=[w for w in re.findall(r"[\w-]+",topic.lower()) if len(w)>2]
    routes=con.execute("SELECT * FROM task_routes").fetchall()
    forced_topic = None
    lowered = topic.lower()
    if any(x in lowered for x in ("таблиц", "schema", "схем", "migration", "миграц")):
        forced_topic = "database change"
    elif any(x in lowered for x in ("production", "продакшн", "nginx", "сервис")) and any(x in lowered for x in ("ошиб", "error", "problem", "не работает")):
        forced_topic = "production error"
    if forced_topic:
        r=next((row for row in routes if row["topic"]==forced_topic),None)
    else:
        r=None
    scored=[]
    if r is None:
        for candidate in routes:
            hay=(candidate["topic"]+" "+candidate["keywords"]).lower(); score=sum(1 for w in words if w in hay)
            if score: scored.append((score,candidate))
        r=max(scored,key=lambda x:x[0])[1] if scored else None
    if not r:
        found=search_rows(con,topic,10)
        return {"primary_files":[x["path"] for x in found],"secondary_files":[],"android_files":[],"production_components":[],"recommended_checks":[],"excluded_paths":[".git","venv","audio","data"],"server_check_required":False}
    primary=json.loads(r["primary_files_json"]); secondary=json.loads(r["secondary_files_json"])
    return {"matched_topic":r["topic"],"primary_files":primary,"secondary_files":secondary,
            "android_files":[x for x in primary+secondary if str(x).startswith("android/")],
            "production_components":["docs/codex/DEPLOYMENT.md"] if "production" in r["environment_scope"] else [],
            "recommended_checks":json.loads(r["recommended_checks_json"]),"excluded_paths":json.loads(r["excluded_paths_json"]),
            "server_check_required":"production" in r["environment_scope"]}


def main(argv: list[str] | None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--json",action="store_true"); p.add_argument("--limit",type=int,default=10); p.add_argument("--verbose",action="store_true"); p.add_argument("--scope",choices=["local","production","android"])
    sub=p.add_subparsers(dest="command",required=True)
    def output_options(sp: argparse.ArgumentParser) -> argparse.ArgumentParser:
        sp.add_argument("--json",action="store_true",default=argparse.SUPPRESS)
        sp.add_argument("--limit",type=int,default=argparse.SUPPRESS)
        sp.add_argument("--verbose",action="store_true",default=argparse.SUPPRESS)
        sp.add_argument("--scope",choices=["local","production","android"],default=argparse.SUPPRESS)
        return sp
    output_options(sub.add_parser("build"))
    u=output_options(sub.add_parser("update")); u.add_argument("--files",nargs="+")
    ss=output_options(sub.add_parser("server-scan")); ss.add_argument("--ssh-host",default=os.getenv("PROJECT_KB_SSH_HOST","root@204.168.186.69")); ss.add_argument("--ssh-key",default=os.getenv("PROJECT_KB_SSH_KEY",str(Path.home()/"Desktop"/"id_ed25519"))); ss.add_argument("--mock-file")
    for cmd in ["server-status","compare-environments","deployment","status"]: output_options(sub.add_parser(cmd))
    for cmd,arg in [("query","query"),("files-for","topic"),("symbol","name"),("route","url"),("table","name"),("android-api","url"),("service","name")]:
        sp=output_options(sub.add_parser(cmd)); sp.add_argument(arg)
    a=p.parse_args(argv)
    if a.command=="build": print_result(build(),a.json); return 0
    if a.command=="update": changed,removed=update(a.files); print_result({"changed":changed,"removed":removed},a.json); return 0
    if a.command=="server-scan": data=server_scan(a.ssh_host,a.ssh_key,a.mock_file); print_result({"services":len(data["services"]),"routes":len(data["routes"]),"schema_objects":len(data["tables"]),"hashes":len(data["hashes"])},a.json); return 0
    if not DB_PATH.exists(): print("Knowledge base is missing; run: python tools/project_kb.py build",file=sys.stderr); return 2
    con=connect()
    try:
        if a.command=="query":
            out=[]
            for r in search_rows(con,a.query,a.limit):
                syms=[x[0] for x in con.execute("SELECT name FROM symbols WHERE file_path=? LIMIT 5",(r["path"],))]
                apis=[x[0] for x in con.execute("SELECT route_or_command FROM routes WHERE file_path=? LIMIT 5",(r["path"],))]
                tables=sorted({x[0] for x in con.execute("SELECT table_name FROM database_usage WHERE file_path=? LIMIT 10",(r["path"],))})
                out.append({"file":r["path"],"why":r["purpose"],"scope":r["source_scope"],"symbols":syms,"api":apis,"tables":tables})
            print_result(out,a.json)
        elif a.command=="files-for": print_result(files_for(con,a.topic),a.json)
        elif a.command=="symbol": print_result(con.execute("SELECT name,symbol_type,signature,file_path,line_start,line_end,source_scope FROM symbols WHERE name=? OR name LIKE ? LIMIT ?",(a.name,f"%{a.name}%",a.limit)).fetchall(),a.json)
        elif a.command=="route": print_result(con.execute("SELECT route_type,method_or_trigger,route_or_command,handler,file_path,line_number,auth_type,source_scope FROM routes WHERE route_or_command=? OR route_or_command LIKE ? LIMIT ?",(a.url,f"%{a.url}%",a.limit)).fetchall(),a.json)
        elif a.command=="table":
            defs=[dict(r) for r in con.execute("SELECT * FROM database_tables WHERE table_name=?",(a.name,))]; uses=[dict(r) for r in con.execute("SELECT file_path,symbol_name,operation,line_number,source_scope FROM database_usage WHERE table_name=? LIMIT ?",(a.name,a.limit))]; print_result({"definitions":defs,"usage":uses},a.json)
        elif a.command=="android-api": print_result(con.execute("SELECT endpoint,http_method,android_file,android_symbol,request_model,response_model,backend_file,backend_handler,status,notes FROM android_contracts WHERE endpoint=? OR endpoint LIKE ? LIMIT ?",(a.url,f"%{a.url}%",a.limit)).fetchall(),a.json)
        elif a.command=="service": print_result(con.execute("SELECT * FROM services WHERE service_name=? OR service_name LIKE ? LIMIT ?",(a.name,f"%{a.name}%",a.limit)).fetchall(),a.json)
        elif a.command=="server-status": print_result(con.execute("SELECT service_name,service_type,working_directory,port,last_indexed_at FROM services WHERE environment='production'").fetchall(),a.json)
        elif a.command=="deployment": print_result(con.execute("SELECT server_name,public_path,proxy_target,nginx_config_path,backend_service FROM deployment_routes").fetchall(),a.json)
        elif a.command=="compare-environments":
            snaps={r["environment"]:dict(r) for r in con.execute("SELECT * FROM environment_snapshots")}; local=snaps.get("local",{}); prod=snaps.get("production",{}); result={"local":{"branch":local.get("git_branch"),"commit":local.get("git_commit"),"dirty":local.get("git_dirty"),"path":local.get("project_path")},"production":{"branch":prod.get("git_branch"),"commit":prod.get("git_commit"),"dirty":prod.get("git_dirty"),"path":prod.get("project_path")},"same_commit":bool(local.get("git_commit") and local.get("git_commit")==prod.get("git_commit")),"same_schema":bool(local.get("schema_hash") and local.get("schema_hash")==prod.get("schema_hash")),"note":"Production Git comparison is unavailable when the deployed directory has no .git metadata."}; print_result(result,a.json)
        elif a.command=="status":
            caps=con.execute("SELECT name,enabled FROM kb_capabilities").fetchall(); counts={t:con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ["files","symbols","routes","database_tables","android_contracts","services"]}; snaps=[dict(r) for r in con.execute("SELECT environment,git_branch,git_commit,git_dirty,project_path,captured_at FROM environment_snapshots")]; print_result({"database":str(DB_PATH),"counts":counts,"capabilities":{r[0]:bool(r[1]) for r in caps},"snapshots":snaps},a.json)
    finally: con.close()
    return 0


if __name__=="__main__": raise SystemExit(main())
