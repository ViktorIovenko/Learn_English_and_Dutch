"""Language catalog and normalized translation API for ParallelLingvo."""

from __future__ import annotations

import sqlite3
from typing import Any

from flask import Blueprint, jsonify, request, session

from app.languages import MIN_PARALLEL_LANGUAGES, public_language_catalog
from app.multilingual import (
    ensure_multilingual_schema,
    get_user_languages,
    get_word_translations,
    set_user_languages,
    upsert_word_translation,
)
from config import Config


language_api = Blueprint("language_api", __name__)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _current_user_id() -> str | None:
    uid = session.get("tg_user_id") or request.headers.get("X-User-Id") or None
    return str(uid) if uid else None


def _word_is_visible_to_user(conn: sqlite3.Connection, word_id: int, user_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM words WHERE id = ? AND (user_id = ? OR status = 'test')",
        (int(word_id), str(user_id)),
    ).fetchone()
    return bool(row)


@language_api.get("/api/languages")
def api_languages():
    return jsonify({
        "ok": True,
        "count": len(public_language_catalog()),
        "minimum_parallel_languages": MIN_PARALLEL_LANGUAGES,
        "languages": public_language_catalog(),
    })


@language_api.get("/api/user_languages")
def api_user_languages_get():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    with _conn() as conn:
        languages = get_user_languages(conn, user_id)
    return jsonify({"ok": True, "languages": languages})


@language_api.put("/api/user_languages")
def api_user_languages_put():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    languages = data.get("languages")
    if not isinstance(languages, list):
        return jsonify({"ok": False, "error": "languages_must_be_list"}), 400

    try:
        with _conn() as conn:
            saved = set_user_languages(conn, user_id, languages)
            conn.commit()
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, "languages": saved})


@language_api.get("/api/words/<int:word_id>/translations")
def api_word_translations_get(word_id: int):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    with _conn() as conn:
        ensure_multilingual_schema(conn, backfill_legacy=True)
        if not _word_is_visible_to_user(conn, word_id, user_id):
            return jsonify({"ok": False, "error": "not_found"}), 404
        translations = get_word_translations(conn, word_id)

    return jsonify({"ok": True, "word_id": word_id, "translations": translations})


@language_api.put("/api/words/<int:word_id>/translations")
def api_word_translations_put(word_id: int):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data: dict[str, Any] = request.get_json(silent=True) or {}
    translations = data.get("translations")
    if not isinstance(translations, dict) or not translations:
        return jsonify({"ok": False, "error": "translations_required"}), 400

    with _conn() as conn:
        ensure_multilingual_schema(conn, backfill_legacy=True)
        if not _word_is_visible_to_user(conn, word_id, user_id):
            return jsonify({"ok": False, "error": "not_found"}), 404

        try:
            for language_code, payload in translations.items():
                if isinstance(payload, str):
                    payload = {"text": payload}
                if not isinstance(payload, dict):
                    return jsonify({
                        "ok": False,
                        "error": f"bad_translation_payload:{language_code}",
                    }), 400
                upsert_word_translation(
                    conn,
                    word_id,
                    str(language_code),
                    text=str(payload.get("text") or ""),
                    example=str(payload.get("example") or ""),
                    audio_url=str(payload.get("audio_url") or ""),
                    sync_legacy=True,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

        conn.commit()
        saved = get_word_translations(conn, word_id)

    return jsonify({"ok": True, "word_id": word_id, "translations": saved})


def init_app(app) -> None:
    app.register_blueprint(language_api)
