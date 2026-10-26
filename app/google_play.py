"""Google Play verification. No entitlement is derived from client purchase fields."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import time
from contextlib import closing
from datetime import datetime
from functools import lru_cache
from urllib.parse import quote

from config import Config

PACKAGE = "app.parallellingvo"
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
ROOT = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"


class PlayError(Exception):
    def __init__(self, code, status=503):
        super().__init__(code)
        self.code, self.status = code, status


def products():
    try:
        value = json.loads(os.getenv("GOOGLE_PLAY_PRODUCTS_JSON", "{}"))
        if not isinstance(value, dict) or any(
            not isinstance(k, str) or not k or v not in ("premium", "family")
            for k, v in value.items()
        ):
            raise ValueError()
        return value
    except (ValueError, TypeError):
        raise PlayError("google_play_products_not_configured") from None


def account_id(user_id):
    return hashlib.sha256(("parallellingvo:" + str(user_id)).encode()).hexdigest()


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _cipher():
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(
        ("google-play-token:" + Config.SECRET_KEY).encode()).digest()))


def ensure_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS google_play_purchases (
        token_hash TEXT PRIMARY KEY, user_id TEXT, token_cipher TEXT NOT NULL,
        product_id TEXT NOT NULL, state TEXT NOT NULL, expires_at INTEGER NOT NULL,
        acknowledged INTEGER NOT NULL DEFAULT 0, updated_at INTEGER NOT NULL,
        superseded_by TEXT, checked_at_ns INTEGER NOT NULL DEFAULT 0)""")
    if "checked_at_ns" not in {r[1] for r in conn.execute("PRAGMA table_info(google_play_purchases)")}:
        conn.execute("ALTER TABLE google_play_purchases ADD COLUMN checked_at_ns INTEGER NOT NULL DEFAULT 0")
    conn.execute("CREATE INDEX IF NOT EXISTS play_purchase_user ON google_play_purchases(user_id)")


@lru_cache(maxsize=1)
def _credentials():
    import google.auth
    return google.auth.default(scopes=[SCOPE])[0]


def _request(method, path, body=None):
    # ADC supports a service-account file or workload identity, outside source control.
    from google.auth.transport.requests import AuthorizedSession
    try:
        with AuthorizedSession(_credentials()) as http:
            response = http.request(method, ROOT + quote(PACKAGE, safe="") + path,
                                    json=body, timeout=20)
            if response.status_code in (404, 410):
                raise PlayError("purchase_not_found", 400)
            if not response.ok:
                raise PlayError("google_play_temporarily_unavailable", 503)
            return response.json() if response.content else {}
    except PlayError:
        raise
    except Exception:
        # Never surface credentials, HTTP URLs (contain tokens), or provider bodies.
        raise PlayError("google_play_temporarily_unavailable", 503) from None


def _expiry(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return int(parsed.timestamp() * 1000)
    except (ValueError, TypeError, AttributeError):
        raise PlayError("invalid_google_play_response", 502) from None


def verify(user_id, token, product_id=None, package_name=PACKAGE):
    catalog = products()
    if not catalog:
        raise PlayError("google_play_products_not_configured")
    if package_name != PACKAGE or not isinstance(token, str) or not 1 <= len(token) <= 8192:
        raise PlayError("invalid_purchase", 400)
    if product_id is not None and (not isinstance(product_id, str) or product_id not in catalog):
        raise PlayError("unknown_product", 400)
    from app.routes import _ensure_subscription_schema
    _ensure_subscription_schema()
    digest = token_hash(token)
    now = int(time.time() * 1000)
    with closing(sqlite3.connect(Config.DB_PATH, timeout=30)) as conn, conn:
        conn.row_factory = sqlite3.Row
        ensure_schema(conn)
        # Network verification must not hold the application database write lock.
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone():
            raise PlayError("unauthorized", 401)
        stored = conn.execute("SELECT * FROM google_play_purchases WHERE token_hash=?", (digest,)).fetchone()
        if stored and stored["user_id"] != str(user_id):
            raise PlayError("purchase_account_mismatch", 409)
        if stored and stored["superseded_by"]:
            raise PlayError("purchase_replaced", 409)
        started_ns = time.time_ns()
        payload = _request("GET", "/purchases/subscriptionsv2/tokens/" + quote(token, safe=""))
        now = int(time.time() * 1000)
        binding = (payload.get("externalAccountIdentifiers") or {}).get("obfuscatedExternalAccountId")
        if binding != account_id(user_id) and not (stored and not binding):
            raise PlayError("purchase_account_mismatch", 409)
        items = [item for item in payload.get("lineItems", []) if item.get("productId") in catalog]
        if product_id:
            items = [item for item in items if item.get("productId") == product_id]
        if len(items) != 1:
            raise PlayError("unknown_or_ambiguous_product", 400)
        item = items[0]
        product_id = item["productId"]
        state = payload.get("subscriptionState", "")
        expiry = _expiry(item["expiryTime"]) if item.get("expiryTime") else 0
        active = state in {"SUBSCRIPTION_STATE_ACTIVE", "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
                           "SUBSCRIPTION_STATE_CANCELED"} and expiry > now
        acknowledged = payload.get("acknowledgementState") == "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED"
        linked = payload.get("linkedPurchaseToken")
        if linked:
            old = conn.execute("SELECT user_id FROM google_play_purchases WHERE token_hash=?",
                               (token_hash(linked),)).fetchone()
            if old and old["user_id"] != str(user_id):
                raise PlayError("purchase_account_mismatch", 409)
        current = conn.execute("SELECT * FROM user_subscriptions WHERE user_id=?", (str(user_id),)).fetchone()
        if active and current and current["status"] == "active" and (
            current["current_period_ends_at"] is None or current["current_period_ends_at"] > now
        ) and current["provider"] not in (None, "", "google_play"):
            raise PlayError("existing_subscription_provider_conflict", 409)
        if active and not acknowledged:
            _request("POST", "/purchases/subscriptions/" + quote(product_id, safe="") +
                     "/tokens/" + quote(token, safe="") + ":acknowledge", {})
            acknowledged = True
        conn.execute("BEGIN IMMEDIATE")
        latest = conn.execute("SELECT * FROM google_play_purchases WHERE token_hash=?", (digest,)).fetchone()
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone():
            raise PlayError("unauthorized", 401)
        if latest and latest["user_id"] != str(user_id):
            raise PlayError("purchase_account_mismatch", 409)
        if latest and latest["superseded_by"]:
            raise PlayError("purchase_replaced", 409)
        if latest and latest["checked_at_ns"] > started_ns:
            # A newer request already committed (possibly a refund/hold). Retry
            # against Google instead of applying this older network response.
            raise PlayError("purchase_verification_raced", 503)
        current = conn.execute("SELECT * FROM user_subscriptions WHERE user_id=?", (str(user_id),)).fetchone()
        if active and current and current["status"] == "active" and (
            current["current_period_ends_at"] is None or current["current_period_ends_at"] > now
        ) and current["provider"] not in (None, "", "google_play"):
            raise PlayError("existing_subscription_provider_conflict", 409)
        if linked:
            old = conn.execute("SELECT user_id FROM google_play_purchases WHERE token_hash=?", (token_hash(linked),)).fetchone()
            if old and old["user_id"] != str(user_id):
                raise PlayError("purchase_account_mismatch", 409)
        conn.execute("""INSERT INTO google_play_purchases
            (token_hash,user_id,token_cipher,product_id,state,expires_at,acknowledged,updated_at,checked_at_ns)
            VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(token_hash) DO UPDATE SET
            state=excluded.state,expires_at=excluded.expires_at,
            acknowledged=excluded.acknowledged,updated_at=excluded.updated_at,checked_at_ns=excluded.checked_at_ns""",
            (digest, str(user_id), _cipher().encrypt(token.encode()).decode(), product_id,
             state, expiry, int(acknowledged), now, started_ns))
        if linked and active:
            conn.execute("""INSERT OR IGNORE INTO google_play_purchases
                (token_hash,user_id,token_cipher,product_id,state,expires_at,acknowledged,updated_at,superseded_by)
                VALUES(?,?,'','','REPLACED',0,0,?,?)""", (token_hash(linked), str(user_id), now, digest))
            conn.execute("UPDATE google_play_purchases SET superseded_by=? WHERE token_hash=?",
                         (digest, token_hash(linked)))
        # Do not replace existing manual/other-provider access or another live Play
        # purchase. The owner resolves cross-provider conflicts explicitly.
        if active or (current and current["provider"] == "google_play"):
            # Recompute the best live purchase, so an expired token cannot revoke
            # access granted by another verified token during restore.
            best = conn.execute("""SELECT * FROM google_play_purchases WHERE user_id=?
                AND superseded_by IS NULL AND acknowledged=1 AND expires_at>?
                AND state IN ('SUBSCRIPTION_STATE_ACTIVE','SUBSCRIPTION_STATE_IN_GRACE_PERIOD','SUBSCRIPTION_STATE_CANCELED')
                ORDER BY expires_at DESC LIMIT 1""", (str(user_id), now)).fetchone()
            if best:
                if best["product_id"] not in catalog:
                    raise PlayError("google_play_products_not_configured")
                conn.execute("""INSERT INTO user_subscriptions
                (user_id,status,trial_started_at,trial_ends_at,current_period_ends_at,provider,
                 provider_subscription_id,cancel_at_period_end,updated_at,plan)
                VALUES(?,'active',0,0,?,'google_play',?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET status='active',
                current_period_ends_at=excluded.current_period_ends_at,provider='google_play',
                provider_subscription_id=excluded.provider_subscription_id,
                cancel_at_period_end=excluded.cancel_at_period_end,updated_at=excluded.updated_at,plan=excluded.plan""",
                    (str(user_id), best["expires_at"], best["token_hash"],
                     int(best["state"] == "SUBSCRIPTION_STATE_CANCELED"), now, catalog[best["product_id"]]))
            elif current and current["provider"] == "google_play":
                conn.execute("UPDATE user_subscriptions SET status='expired',current_period_ends_at=?,updated_at=? WHERE user_id=?",
                             (min(expiry, now), now, str(user_id)))
        return {"ok": True, "verified": True, "active": active, "acknowledged": acknowledged,
                "state": state, "expires_at": expiry, "product_id": product_id}


def reconcile():
    """Scheduled server reconciliation; credentials/errors never appear in output."""
    with closing(sqlite3.connect(Config.DB_PATH)) as conn, conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT user_id,token_cipher FROM google_play_purchases WHERE user_id IS NOT NULL AND superseded_by IS NULL").fetchall()
    checked = failed = 0
    for user_id, encrypted in rows:
        try:
            verify(user_id, _cipher().decrypt(encrypted.encode()).decode())
            checked += 1
        except Exception:
            failed += 1
    return {"checked": checked, "failed": failed}


def sync_user(user_id):
    with closing(sqlite3.connect(Config.DB_PATH)) as conn, conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT token_cipher FROM google_play_purchases WHERE user_id=? AND superseded_by IS NULL",
                            (str(user_id),)).fetchall()
    for (encrypted,) in rows:
        verify(user_id, _cipher().decrypt(encrypted.encode()).decode())


def register(web):
    from flask import jsonify, request

    @web.post("/api/subscription/sync")
    def sync_play_subscriptions():
        from app.routes import _bearer_user_id
        user_id = _bearer_user_id()
        if not user_id:
            return jsonify(ok=False, error="unauthorized"), 401
        try:
            sync_user(user_id)
        except PlayError as exc:
            return jsonify(ok=False, error=exc.code), exc.status
        return jsonify(ok=True)

    @web.post("/api/subscription/google-play-notifications")
    def play_notifications():
        from google.auth.transport.requests import Request
        from google.oauth2.id_token import verify_oauth2_token
        audience = os.getenv("GOOGLE_PLAY_RTDN_AUDIENCE", "")
        email = os.getenv("GOOGLE_PLAY_RTDN_SERVICE_ACCOUNT", "")
        if not audience or not email:
            return jsonify(ok=False), 503
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or request.content_length is None or request.content_length > 65536:
            return jsonify(ok=False), 401
        try:
            claims = verify_oauth2_token(auth[7:], Request(), audience=audience)
            if claims.get("email") != email or claims.get("email_verified") is not True:
                return jsonify(ok=False), 401
        except Exception:
            return jsonify(ok=False), 401
        try:
            message = request.get_json()["message"]
            data = json.loads(base64.b64decode(message["data"], validate=True))
            if data.get("packageName") != PACKAGE:
                return jsonify(ok=False), 400
            notification = data.get("subscriptionNotification")
            if not notification:  # Google's test notification
                return jsonify(ok=True)
            if not isinstance(notification, dict) or not isinstance(notification.get("purchaseToken"), str):
                return jsonify(ok=False), 400
            digest = token_hash(notification["purchaseToken"])
            with closing(sqlite3.connect(Config.DB_PATH)) as conn, conn:
                ensure_schema(conn)
                row = conn.execute("SELECT user_id FROM google_play_purchases WHERE token_hash=?", (digest,)).fetchone()
            if row and row[0]:
                verify(row[0], notification["purchaseToken"])
            # Unknown purchases cannot be assigned without an authenticated restore.
            return jsonify(ok=True)
        except PlayError as exc:
            return jsonify(ok=exc.status < 500), 503 if exc.status >= 500 else 200
        except (ValueError, TypeError, KeyError):
            return jsonify(ok=False), 400


if __name__ == "__main__":
    import sys
    result = reconcile()
    print(json.dumps(result))
    sys.exit(1 if result["failed"] else 0)
