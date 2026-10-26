"""Self-service erasure and draft legal pages. No production publication by default."""
import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import closing

from flask import jsonify, render_template, request, session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import Config


def subject_hash(user_id):
    return hmac.new(Config.SECRET_KEY.encode(), ("erasure:" + str(user_id)).encode(), hashlib.sha256).hexdigest()


def ensure_schema(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS account_revocations (subject_hash TEXT PRIMARY KEY, generation TEXT NOT NULL)")


def generation(user_id):
    with closing(sqlite3.connect(Config.DB_PATH)) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_revocations'").fetchone():
            return "0"
        row = conn.execute("SELECT generation FROM account_revocations WHERE subject_hash=?", (subject_hash(user_id),)).fetchone()
        return row[0] if row else "0"


def challenge(user_id):
    nonce = secrets.token_urlsafe(32)
    session["account_delete_csrf"] = nonce
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt="account-delete-v1").dumps(
        {"user_id": str(user_id), "generation": generation(user_id), "nonce": nonce})


def erase(user_id):
    """One transaction. Keep shared dictionary content, never delete another account.

    Retain only a pseudonymous purchase fingerprint and HMAC revocation subject
    to prevent replay/reassignment. No payment token, email, or user ID retained.
    """
    uid = str(user_id)
    with closing(sqlite3.connect(Config.DB_PATH, timeout=30)) as conn, conn:
        ensure_schema(conn)
        conn.execute("BEGIN IMMEDIATE")
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            return False
        def cols(table):
            return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        # Erase setup/reset links by email before removing authentication records.
        emails = set()
        for table in ("email_auth_credentials", "auth_identities"):
            if table in tables and "email" in cols(table):
                emails.update(r[0] for r in conn.execute(f'SELECT email FROM "{table}" WHERE user_id=?', (uid,)) if r[0])
        for email in emails:
            if "email_auth_links" in tables:
                conn.execute("DELETE FROM email_auth_links WHERE email=? COLLATE NOCASE", (email,))
            if "email_auth_attempts" in tables:
                email_hash = hmac.new(Config.SECRET_KEY.encode(), email.encode(), hashlib.sha256).hexdigest()
                conn.execute("DELETE FROM email_auth_attempts WHERE email_hash=?", (email_hash,))
        # All flags referencing this user's removed words, including shared flags.
        if "words" in tables:
            for table, column in (("user_word_flags", "word_id"), ("shared_lesson_words", "parent_word_id"),
                                  ("shared_lesson_words", "child_word_id")):
                if table in tables:
                    conn.execute(f'DELETE FROM "{table}" WHERE "{column}" IN (SELECT id FROM words WHERE user_id=?)', (uid,))
        for table in ("family_pairing_codes", "family_invite_codes"):
            if table in tables and "family_invitation_aliases" in tables:
                owner = "child_user_id" if table == "family_pairing_codes" else "parent_user_id"
                conn.execute(f'DELETE FROM family_invitation_aliases WHERE code IN (SELECT code FROM "{table}" WHERE "{owner}"=?)', (uid,))
        if "google_play_purchases" in tables:
            conn.execute("UPDATE google_play_purchases SET user_id=NULL,token_cipher='',product_id='',state='DELETED',expires_at=0 WHERE user_id=?", (uid,))
        owned = (
            "user_word_flags", "shared_lesson_words", "family_lesson_assignments", "parent_child_links",
            "child_lesson_priorities", "child_lesson_priority_history", "child_goal_notifications",
            "family_pairing_codes", "family_invite_codes", "family_invitation_uses", "family_invitation_attempts",
            "mcp_oauth_codes", "mcp_access_grants", "mcp_user_settings", "mcp_idempotency", "mcp_admin_audit_log",
            "email_auth_credentials", "auth_identities", "android_auth_flows", "ad_consent",
            "content_import_requests", "content_pending", "progress_events", "user_daily_goals",
            "user_language_preferences", "user_settings", "user_lessons", "user_subscriptions",
            "google_tts_usage_monthly", "google_tts_budget_monthly", "translation_token_usage",
            "reminder_state", "shared_word_sets", "words", "users",
        )
        identity_columns = {"user_id", "owner_user_id", "parent_user_id", "child_user_id", "admin_user_id", "target_user_id"}
        for table in owned:
            if table in tables:
                keys = sorted(cols(table) & identity_columns)
                if keys:
                    where = " OR ".join(f'"{key}"=?' for key in keys)
                    conn.execute(f'DELETE FROM "{table}" WHERE {where}', [uid] * len(keys))
        if "google_tts_limits" in tables:
            conn.execute("DELETE FROM google_tts_limits WHERE scope=?", ("user:" + uid,))
        if "mcp_audit_log" in tables:
            # Matches the existing audit hash implementation; no identifying log remains.
            from app.mcp_service import token_hash
            conn.execute("DELETE FROM mcp_audit_log WHERE user_hash=?", (token_hash(uid)[:16],))
        conn.execute("INSERT INTO account_revocations VALUES (?,?) ON CONFLICT(subject_hash) DO UPDATE SET generation=excluded.generation",
                     (subject_hash(uid), secrets.token_hex(16)))
    return True


def register(web):
    from app.routes import _bearer_user_id, _current_user_id

    @web.before_app_request
    def revoked_session():
        if session.get("is_auth"):
            uid = str(session.get("tg_user_id") or "")
            if session.get("account_generation", "0") != generation(uid):
                session.clear()

    @web.after_app_request
    def bind_session_generation(response):
        if session.get("is_auth"):
            session.setdefault("account_generation", generation(str(session.get("tg_user_id") or "")))
        if request.path in ("/privacy", "/account/delete") or request.path.startswith("/api/account/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Robots-Tag"] = "noindex"
        return response

    @web.get("/privacy")
    def privacy_page():
        # Owner must review text AND provide operator/support details before publication.
        approved = os.getenv("PRIVACY_POLICY_APPROVED", "0") == "1"
        contact = os.getenv("PRIVACY_CONTACT_EMAIL", "info@parallellingvo.app")
        operator = os.getenv("PRIVACY_OPERATOR_NAME", "Виктор Иовенко")
        if not approved or not contact or not operator:
            from flask import abort, current_app
            if not current_app.testing:
                abort(404)
        return render_template("privacy.html", approved=approved, contact=contact, operator=operator)

    @web.get("/account/delete")
    def deletion_page():
        uid = _bearer_user_id() or (str(session.get("tg_user_id")) if session.get("is_auth") else "")
        return render_template("account_delete.html", authenticated=bool(uid),
                               challenge=challenge(uid) if uid else "", deleted=False)

    @web.get("/api/account/deletion-challenge")
    def deletion_challenge():
        uid = _bearer_user_id() or (str(session.get("tg_user_id")) if session.get("is_auth") else "")
        if not uid:
            return jsonify(ok=False, error="unauthorized"), 401
        return jsonify(ok=True, challenge=challenge(uid))

    @web.post("/api/account/delete")
    def delete_account():
        bearer = _bearer_user_id()
        uid = bearer or (str(session.get("tg_user_id")) if session.get("is_auth") else "")
        if not uid:
            return jsonify(ok=False, error="unauthorized"), 401
        data = request.get_json(silent=True) if request.is_json else request.form
        data = data if hasattr(data, "get") else {}
        try:
            proof = URLSafeTimedSerializer(Config.SECRET_KEY, salt="account-delete-v1").loads(
                str(data.get("challenge", "")), max_age=600)
            valid = (proof["user_id"] == uid and proof["generation"] == generation(uid)
                     and (bool(bearer) or hmac.compare_digest(proof["nonce"], session.get("account_delete_csrf", ""))))
        except (BadSignature, SignatureExpired, KeyError, TypeError):
            valid = False
        if data.get("confirm") != "DELETE" or not valid:
            return jsonify(ok=False, error="confirmation_required"), 400
        erase(uid)
        session.clear()
        if not request.is_json:
            return render_template("account_delete.html", authenticated=False, challenge="", deleted=True)
        return jsonify(ok=True)
