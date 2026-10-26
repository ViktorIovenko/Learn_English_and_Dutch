"""Server-owned AI configuration and adapter; Android keeps its existing API."""
import base64
import hashlib
import json
import math
import sqlite3
import time
from contextlib import closing
from urllib.parse import urlsplit

import requests
from flask import jsonify, redirect, request

from config import Config
from app.content_db import connect, transaction

TASKS = {
    "translate_word": "Перевод слов",
    "translate_sentence": "Перевод предложений",
    "generate_examples": "Примеры предложений",
    "suggest_words": "Подбор слов по теме",
}
CONTRACTS = {
    "translate_word": 'Translate text from source_language to target_language, respecting sense and context. Return {"text":"translation"}.',
    "translate_sentence": 'Translate the sentence text from source_language to target_language, respecting sense and context. Return {"text":"translation"}.',
    "generate_examples": 'Return an object with ex_<language> string keys for exactly the requested languages. Use the supplied words at the requested CEFR level. Preserve the meaning of any supplied examples: translate them into the missing languages. Otherwise create one aligned sentence in all requested languages. Mark the vocabulary word with **bold**.',
    "suggest_words": 'Suggest count vocabulary words in language about topic at the requested CEFR level. Return {"words":["word", "word"]}.',
}


class SettingsConflict(ValueError):
    pass


def defaults():
    return {"revision": 0, "enabled": False, "endpoint": "", "model": "", "timeout": 60,
            "tasks": {task: {"model": "", "prompt": ""} for task in TASKS}, "api_key": ""}


def _cipher():
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(
        ("ai-gateway-key:" + Config.SECRET_KEY).encode()).digest()))


def read_settings():
    # Read only: providers can run inside an existing content write transaction.
    with closing(connect(Config.DB_PATH)) as conn:
        try:
            row = conn.execute("SELECT revision, config_json, encrypted_key FROM ai_gateway_settings WHERE id=1").fetchone()
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc):
                raise
            return defaults()
    if not row:
        return defaults()
    result = json.loads(row["config_json"])
    result["revision"] = row["revision"]
    result["api_key"] = _cipher().decrypt(row["encrypted_key"].encode()).decode() if row["encrypted_key"] else ""
    return result


def public_settings(value=None):
    value = dict(read_settings() if value is None else value)
    value["key_configured"] = bool(value.pop("api_key"))
    value["paid_ai_allowed"] = bool(getattr(Config, "PAID_AI_ENABLED", False))
    value["active"] = bool(value["paid_ai_allowed"] and value["enabled"])
    value["managed"] = value["revision"] > 0
    return value


def _text(data, name, limit):
    value = data.get(name, "")
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise ValueError("Некорректное поле: " + name)
    return value.strip()


def save_settings(data):
    if not isinstance(data, dict) or type(data.get("revision")) is not int or type(data.get("enabled")) is not bool:
        raise ValueError("Некорректные настройки")
    endpoint, model = _text(data, "endpoint", 1000), _text(data, "model", 200)
    try:
        url = urlsplit(endpoint)
        valid = url.scheme == "https" and url.hostname and url.port != 0 and not (
            url.username or url.password or url.query or url.fragment or any(c.isspace() for c in endpoint))
    except ValueError:
        valid = False
    if endpoint and not valid:
        raise ValueError("Укажите полный HTTPS URL без пароля, параметров и фрагмента")
    timeout = data.get("timeout", 60)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 5 <= timeout <= 120:
        raise ValueError("Таймаут должен быть от 5 до 120 секунд")
    tasks = data.get("tasks", {})
    if not isinstance(tasks, dict) or set(tasks) - set(TASKS):
        raise ValueError("Некорректный список задач")
    cleaned_tasks = {}
    for task in TASKS:
        item = tasks.get(task, {})
        if not isinstance(item, dict):
            raise ValueError("Некорректная задача")
        cleaned_tasks[task] = {"model": _text(item, "model", 200), "prompt": _text(item, "prompt", 8000)}
    api_key = _text(data, "api_key", 4000)
    if any(c.isspace() for c in api_key):
        raise ValueError("Ключ не должен содержать пробелы или переносы строк")
    with transaction(Config.DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS ai_gateway_settings (
            id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL,
            config_json TEXT NOT NULL, encrypted_key TEXT NOT NULL)''')
        current = read_settings()
        if current["revision"] != data["revision"]:
            raise SettingsConflict("Настройки изменены в другой вкладке. Обновите страницу.")
        previous = urlsplit(current["endpoint"])
        if (current["api_key"] and not api_key and data.get("clear_key") is not True
                and (previous.scheme, previous.hostname, previous.port) != (url.scheme, url.hostname, url.port)):
            raise ValueError("При смене сервиса задайте новый ключ или отметьте удаление текущего")
        key = api_key or ("" if data.get("clear_key") is True else current["api_key"])
        if data["enabled"] and (not endpoint or not model):
            raise ValueError("Для включения заполните адрес сервиса и общую модель")
        value = {"enabled": data["enabled"], "endpoint": endpoint, "model": model,
                 "timeout": timeout, "tasks": cleaned_tasks}
        conn.execute('''INSERT INTO ai_gateway_settings VALUES(1,?,?,?)
            ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,
            config_json=excluded.config_json, encrypted_key=excluded.encrypted_key''',
                     (current["revision"] + 1, json.dumps(value, ensure_ascii=False),
                      _cipher().encrypt(key.encode()).decode() if key else ""))
    return public_settings({**value, "revision": current["revision"] + 1, "api_key": key})


def configured_adapter(operation):
    """None means unmanaged legacy config; False means explicitly disabled."""
    settings = read_settings()
    if not settings["revision"]:
        return None
    if not settings["enabled"] or operation not in TASKS:
        return False
    return lambda **kwargs: generate(settings, operation, kwargs)


def generate(settings, operation, arguments):
    if not getattr(Config, "PAID_AI_ENABLED", False):
        raise RuntimeError("paid_ai_disabled")
    task = settings["tasks"][operation]
    # User data is sent as data, with no IDs, credentials or session information.
    arguments = {key: value for key, value in arguments.items() if key != "request_key"}
    prompt = ("You help people learn languages. Return only a JSON object, without Markdown fences. "
              "Language codes: nl, en, ru, de, fr, es, it, pt, pl, uk. " + CONTRACTS[operation])
    payload = {"model": task["model"] or settings["model"], "stream": False,
               "messages": [{"role": "system", "content": prompt + "\n" + task["prompt"]},
                            {"role": "user", "content": json.dumps(arguments, ensure_ascii=False)}]}
    headers = {"Content-Type": "application/json"}
    if settings["api_key"]:
        headers["Authorization"] = "Bearer " + settings["api_key"]
    try:
        response = requests.post(settings["endpoint"], json=payload, headers=headers,
                                 timeout=settings["timeout"], allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("ИИ-сервис вернул HTTP " + str(response.status_code))
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str) or len(content) > 100000:
            raise ValueError()
        # Reuse the existing JSON decoder for fenced responses from compatible servers.
        from app.ai_platform import _extract_json, TokenUsage, AiPlatformError
        try:
            result = _extract_json(content)
        except AiPlatformError:
            raise ValueError() from None
        if not isinstance(result, dict):
            raise ValueError()
        if operation in ("translate_word", "translate_sentence"):
            if not isinstance(result.get("text"), str) or not result["text"].strip():
                raise ValueError()
            result = {"text": result["text"].strip()}
        elif operation == "generate_examples":
            keys = ["ex_" + lang for lang in arguments["languages"]]
            if not all(isinstance(result.get(key), str) and result[key].strip() for key in keys):
                raise ValueError()
            result = {key: result[key].strip() for key in keys}
        else:
            words = result.get("words")
            if not isinstance(words, list) or not words or not all(isinstance(word, str) and word.strip() for word in words):
                raise ValueError()
            result = {"words": [word.strip() for word in words[:arguments["count"]]]}
        usage = TokenUsage.from_payload(body.get("usage"))
        result["_usage"] = {"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
                            "total_tokens": usage.total_tokens}
        return result
    except requests.RequestException:
        # Never expose provider responses, URLs containing secrets or request headers.
        raise RuntimeError("ИИ-сервис недоступен или истекло время ожидания") from None
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        raise RuntimeError("ИИ-сервис вернул ответ неподходящего формата") from None


# ------------------------------------------------------------ request log
# One row per AI attempt that missed the stored-content cache: the call (ok /
# error / invalid answer) or a refusal (blocked: paid AI off / plan). Only
# metadata: operation, client channel, user id, model, timing, tokens; never
# prompts, answers, keys or provider responses.
LOG_RETENTION_DAYS = 180
CHANNELS = ("web", "telegram", "android", "mcp", "bot", "admin")


def _ensure_log(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS ai_gateway_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL, operation TEXT NOT NULL,
        channel TEXT NOT NULL, user_id TEXT NOT NULL DEFAULT '', model TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', latency_ms INTEGER NOT NULL DEFAULT 0,
        prompt_tokens INTEGER NOT NULL DEFAULT 0, completion_tokens INTEGER NOT NULL DEFAULT 0,
        total_tokens INTEGER NOT NULL DEFAULT 0)""")
    conn.execute("CREATE INDEX IF NOT EXISTS ai_gateway_requests_at ON ai_gateway_requests(at)")


def _client():
    """(channel, user_id) of the current call; detected on the server."""
    from flask import g, has_request_context, request, session
    if not has_request_context():
        return "bot", ""
    if g.get("ai_channel"):
        return g.ai_channel, ""
    path = request.path or ""
    if path.startswith(("/api/mcp", "/mcp")):
        channel = "mcp"
    elif request.headers.get("X-Client") == "android" or (
            str(request.headers.get("Authorization") or "").lower().startswith("bearer ")
            and not session.get("is_auth")):
        channel = "android"
    elif request.cookies.get("pl_client") == "telegram":
        channel = "telegram"  # set by the page inside Telegram's own webview
    else:
        channel = "web"
    try:
        from app.routes import _request_user_id
        user_id = _request_user_id()
    except Exception:
        user_id = ""
    return channel, str(user_id or "")[:64]


def _model_for(operation):
    try:
        settings = read_settings()
    except Exception:
        return ""
    if not settings["revision"]:
        return "legacy"
    return ((settings["tasks"].get(operation) or {}).get("model") or settings["model"] or "")[:200]


def log_request(operation, status, *, started=None, usage=None, error=""):
    try:
        channel, user_id = _client()
        usage = usage if isinstance(usage, dict) else {}
        row = (int(time.time() * 1000), str(operation)[:40], channel, user_id,
               _model_for(operation) if status != "blocked" else "", status, str(error or "")[:300],
               int((time.monotonic() - started) * 1000) if started else 0,
               *(max(int(usage.get(k) or 0), 0) for k in ("prompt_tokens", "completion_tokens", "total_tokens")))
    except Exception:
        return

    def write():
        # Own short connection after the content transaction ends: an error
        # row survives its rollback and never waits on that write lock.
        with closing(sqlite3.connect(Config.DB_PATH, timeout=5)) as conn:
            _ensure_log(conn)
            conn.execute("""INSERT INTO ai_gateway_requests (at, operation, channel, user_id, model, status,
                error, latency_ms, prompt_tokens, completion_tokens, total_tokens)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", row)
            if row[0] % 50 == 0:
                conn.execute("DELETE FROM ai_gateway_requests WHERE at < ?",
                             (row[0] - LOG_RETENTION_DAYS * 86400000,))
            conn.commit()
    try:
        from app.content_db import after_transaction
        after_transaction(write)
    except Exception:
        pass


_TOTALS = """COUNT(*) AS requests, SUM(r.status='ok') AS ok, SUM(r.status='error') AS errors,
    SUM(r.status='invalid') AS invalid, SUM(r.status='blocked') AS blocked,
    SUM(r.prompt_tokens) AS prompt_tokens, SUM(r.completion_tokens) AS completion_tokens,
    SUM(r.total_tokens) AS total_tokens,
    CAST(AVG(CASE WHEN r.status != 'blocked' THEN r.latency_ms END) AS INTEGER) AS avg_latency_ms"""


def request_stats(days=30):
    days = max(1, min(int(days), 365))
    since = int(time.time() * 1000) - days * 86400000
    with closing(sqlite3.connect(Config.DB_PATH, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        _ensure_log(conn)

        def rows(sql):
            return [dict(r) for r in conn.execute(sql, (since,))]

        def group(column):
            return rows(f"SELECT r.{column} AS key, {_TOTALS} FROM ai_gateway_requests r "
                        f"WHERE r.at>=? GROUP BY r.{column} ORDER BY requests DESC")
        summary = rows(f"SELECT {_TOTALS} FROM ai_gateway_requests r WHERE r.at>=?")[0]
        by_day = rows(f"SELECT date(r.at/1000,'unixepoch') AS key, {_TOTALS} FROM ai_gateway_requests r "
                      f"WHERE r.at>=? GROUP BY key ORDER BY key")
        try:
            by_user = rows(f"""SELECT r.user_id AS key,
                    COALESCE(NULLIF(TRIM(COALESCE(u.first_name,'')||' '||COALESCE(u.last_name,'')),''), u.username, '') AS name,
                    {_TOTALS}
                FROM ai_gateway_requests r LEFT JOIN users u ON u.user_id = r.user_id
                WHERE r.at>=? AND r.user_id != '' GROUP BY r.user_id ORDER BY requests DESC LIMIT 50""")
        except sqlite3.OperationalError:  # no users table (isolated tests)
            by_user = rows(f"""SELECT r.user_id AS key, '' AS name, {_TOTALS} FROM ai_gateway_requests r
                WHERE r.at>=? AND r.user_id != '' GROUP BY r.user_id ORDER BY requests DESC LIMIT 50""")
        recent = [dict(r) for r in conn.execute(
            """SELECT at, operation, channel, user_id, model, status, error, latency_ms, total_tokens
               FROM ai_gateway_requests ORDER BY id DESC LIMIT 100""")]
        result = {"days": days, "summary": summary, "by_day": by_day, "by_user": by_user, "recent": recent,
                  "by_channel": group("channel"), "by_operation": group("operation"), "by_model": group("model")}
    for item in [result["summary"], *by_day, *by_user, *result["by_channel"],
                 *result["by_operation"], *result["by_model"]]:
        for key, value in list(item.items()):
            if value is None and key != "avg_latency_ms":
                item[key] = 0
    return result


def install_legacy_bridge(module):
    """Keep an older deployed facade working until its first managed save."""
    import inspect
    if "allow_provider" in inspect.signature(module.translate_word).parameters or getattr(module, "_gateway_bridge", False):
        return
    from app import content_service
    original = {name: getattr(module, name) for name in ("is_configured", "translate_word", "translate_language", "suggest_topic_words")}

    def configured():
        settings = read_settings()
        if not settings["revision"]:
            return original["is_configured"]()
        return bool(settings["enabled"] and getattr(Config, "PAID_AI_ENABLED", False))

    def invoke(name, args, kwargs):
        if not read_settings()["revision"]:
            return original[name](*args, **kwargs)
        try:
            if name == "translate_word":
                bound = inspect.signature(original[name]).bind(*args, **kwargs)
                bound.apply_defaults()
                data = bound.arguments
                supplied = {"ru": data["known_ru"]} if data.get("known_ru") else {}
                result = content_service.resolve_word(data["word"], data["from_lang"], level=data["level"], supplied=supplied)
                return result, module.TokenUsage.from_payload(result.get("usage"))
            if name == "translate_language":
                data = inspect.signature(original[name]).bind(*args, **kwargs).arguments
                result = content_service.translate_language(data["source_word"], data["source_sentence"],
                                                            data["source_lang_name"], data["target_lang_name"])
                return result, module.TokenUsage.from_payload(result.get("usage"))
            bound = inspect.signature(original[name]).bind(*args, **kwargs)
            bound.apply_defaults()
            data = bound.arguments
            from app.content_providers import language_code
            request_data = {"topic": data["topic"], "language": language_code(data["lang"]),
                            "level": data["level"], "count": max(1, min(50, data["count"]))}
            with transaction(Config.DB_PATH) as conn:
                content_service.ensure_schema(conn)
                result, calls = content_service._request(conn, "suggest_words", request_data)
            if not result:
                raise RuntimeError("Подключение ИИ выключено или не настроено")
            words = [word for word in result["words"] if word not in data["existing_words"]]
            return words, module.TokenUsage.from_payload(result.get("_usage") if calls else {})
        except (ValueError, RuntimeError) as exc:
            raise module.AiPlatformError(str(exc)) from exc

    module.is_configured = configured
    # Bind the operation per closure, preserving the old public signatures.
    from functools import wraps
    def wrapper(name):
        @wraps(original[name])
        def call(*args, **kwargs):
            return invoke(name, args, kwargs)
        return call
    for name in ("translate_word", "translate_language", "suggest_topic_words"):
        setattr(module, name, wrapper(name))
    module._gateway_bridge = True


def register(web):
    if not hasattr(Config, "PAID_AI_ENABLED"):
        import os
        Config.PAID_AI_ENABLED = os.getenv("PAID_AI_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
    from app import ai_platform
    install_legacy_bridge(ai_platform)
    @web.get("/admin/ai")
    def admin_ai_page():
        from app.routes import _admin_site_url, _require_admin
        _, error = _require_admin()
        if error:
            return error
        # Интерфейс перенесён во вкладку «ИИ» админки на основном сайте.
        return redirect(_admin_site_url("ai"))

    @web.get("/api/admin/ai/settings")
    def admin_ai_get():
        from app.admin_api import csrf_token
        from app.routes import _require_admin
        _, error = _require_admin()
        if error:
            return error
        csrf_token()
        # API key itself is never returned: only key_configured.
        return jsonify(ok=True, settings=public_settings(), tasks=TASKS), 200, {"Cache-Control": "no-store"}

    @web.get("/api/admin/ai/stats")
    def admin_ai_stats():
        from app.routes import _require_admin
        _, error = _require_admin()
        if error:
            return error
        try:
            days = int(request.args.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        return jsonify(ok=True, **request_stats(days)), 200, {"Cache-Control": "no-store"}

    @web.post("/api/admin/ai/test")
    def admin_ai_test():
        """One real call through the saved connection (logged as channel "admin")."""
        from flask import g
        from app.admin_api import csrf_valid
        from app.routes import _require_admin
        _, error = _require_admin()
        if error:
            return error
        if not request.is_json or not csrf_valid():
            return jsonify(ok=False, error="Обновите страницу и повторите"), 403
        settings = read_settings()
        if not settings["revision"] or not settings["enabled"]:
            return jsonify(ok=False, error="Подключение выключено или ещё не сохранено"), 409
        g.ai_channel = "admin"
        operation = "translate_word"
        started = time.monotonic()
        arguments = {"text": "house", "source_language": "en", "target_language": "nl", "sense": "", "context": ""}
        try:
            result = generate(settings, operation, arguments)
        except RuntimeError as exc:
            message = ("Платный ИИ выключен на сервере (PAID_AI_ENABLED)"
                       if str(exc) == "paid_ai_disabled" else str(exc))
            log_request(operation, "error", started=started, error=message)
            return jsonify(ok=False, error=message), 502
        log_request(operation, "ok", started=started, usage=result.get("_usage"))
        return jsonify(ok=True, answer=result.get("text", ""), model=_model_for(operation),
                       latency_ms=int((time.monotonic() - started) * 1000), usage=result.get("_usage") or {})

    @web.post("/api/admin/ai/settings")
    def admin_ai_save():
        from app.admin_api import csrf_valid
        from app.routes import _require_admin
        _, error = _require_admin()
        if error:
            return error
        if not request.is_json or not csrf_valid():
            return jsonify(ok=False, error="Обновите страницу и повторите сохранение"), 403
        try:
            value = save_settings(request.get_json(silent=True))
        except SettingsConflict as exc:
            return jsonify(ok=False, error=str(exc)), 409
        except ValueError as exc:
            return jsonify(ok=False, error=str(exc)), 400
        return jsonify(ok=True, settings=value), 200, {"Cache-Control": "no-store"}
