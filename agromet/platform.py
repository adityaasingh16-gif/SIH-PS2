"""Production-oriented platform services: auth, RBAC, notifications, governance,
security telemetry, projects, analytics, notices, documents, and explainable risk.

This module uses only Python standard-library primitives plus SQLite so the pilot
does not require another runtime service. For production, email/SMS providers,
PostgreSQL and an enterprise identity provider can be configured behind the same
service interfaces.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def hash_password(password: str, *, iterations: int = 240_000) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class TokenSigner:
    """HMAC-signed opaque session tokens; token contents are non-sensitive."""

    def __init__(self, secret: str | None = None) -> None:
        configured = secret or os.getenv("AGROMET_SESSION_SECRET")
        if not configured:
            configured = secrets.token_urlsafe(48)
        self.secret = configured.encode()

    def issue(self, user_id: str, session_id: str, ttl_seconds: int = 3600) -> tuple[str, str]:
        expires = int(time.time()) + ttl_seconds
        payload = f"{user_id}.{session_id}.{expires}"
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=") + "." + base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return token, datetime.fromtimestamp(expires, timezone.utc).isoformat()

    def verify(self, token: str) -> tuple[str, str, int]:
        try:
            payload_b64, signature_b64 = token.split(".", 1)
            payload = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode()
            signature = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
            expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("invalid signature")
            user_id, session_id, expires_s = payload.split(".", 2)
            expires = int(expires_s)
            if expires < int(time.time()):
                raise ValueError("expired")
            return user_id, session_id, expires
        except (ValueError, TypeError, UnicodeDecodeError):
            raise ValueError("Invalid session token") from None

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()


def totp_code(secret_b32: str, at_time: int | None = None) -> str:
    import struct
    timestamp = int(time.time()) if at_time is None else int(at_time)
    counter = timestamp // 30
    key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret_b32: str, code: str, window: int = 1) -> bool:
    now = int(time.time())
    return any(hmac.compare_digest(totp_code(secret_b32, now + step * 30), str(code).zfill(6)) for step in range(-window, window + 1))


class PlatformRepository:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = str(database_path or os.getenv("AGROMET_DB_PATH", "agromet.sqlite3"))
        self._lock = threading.RLock()
        self._memory_connection: sqlite3.Connection | None = None
        if self.database_path == ":memory:":
            self._memory_connection = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_connection.row_factory = sqlite3.Row
        else:
            Path(self.database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = self._memory_connection or sqlite3.connect(self.database_path, check_same_thread=False, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        c = self._conn()
        try:
            yield c
            c.commit()
        except sqlite3.Error:
            c.rollback()
            raise
        finally:
            if c is not self._memory_connection:
                c.close()

    def _init(self) -> None:
        with self._lock, self.connection() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL, mobile TEXT, department_id TEXT, is_active INTEGER NOT NULL DEFAULT 1,
                mfa_enabled INTEGER NOT NULL DEFAULT 0, mfa_secret TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS departments (
                department_id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL, role_id TEXT NOT NULL, PRIMARY KEY(user_id, role_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(role_id) REFERENCES roles(role_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT,
                ip_address TEXT, user_agent TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL,
                purpose TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS recovery_otps (
                otp_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, code_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL, used_at TEXT, attempts INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY, user_id TEXT, category TEXT NOT NULL, title TEXT NOT NULL,
                body TEXT NOT NULL, severity TEXT NOT NULL DEFAULT 'info', reference_type TEXT, reference_id TEXT,
                created_at TEXT NOT NULL, read_at TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS risk_scores (
                risk_id TEXT PRIMARY KEY, panchayat_id TEXT NOT NULL, forecast_date TEXT NOT NULL,
                score REAL NOT NULL, level TEXT NOT NULL, contributions TEXT NOT NULL, model_version TEXT,
                created_at TEXT NOT NULL, UNIQUE(panchayat_id, forecast_date)
            );
            CREATE TABLE IF NOT EXISTS security_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, ip_address TEXT,
                method TEXT NOT NULL, path TEXT NOT NULL, status_code INTEGER NOT NULL, latency_ms REAL NOT NULL,
                category TEXT NOT NULL, severity TEXT NOT NULL, user_id TEXT, detail TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, user_id TEXT,
                user_email TEXT, role TEXT, action TEXT NOT NULL, resource TEXT NOT NULL,
                result TEXT NOT NULL, details TEXT
            );
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY, name TEXT NOT NULL, district TEXT, mandal TEXT, block_id TEXT,
                state TEXT NOT NULL DEFAULT 'Telangana', status TEXT NOT NULL, progress REAL NOT NULL DEFAULT 0,
                budget_amount REAL, latitude REAL, longitude REAL, description TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS project_milestones (
                milestone_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
                due_date TEXT, status TEXT NOT NULL, progress REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS project_inspections (
                inspection_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, inspected_at TEXT NOT NULL,
                inspector TEXT NOT NULL, status TEXT NOT NULL, notes TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS notices (
                notice_id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, category TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal', published_at TEXT NOT NULL, expires_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1, created_by TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT,
                storage_url TEXT, checksum TEXT, published_at TEXT NOT NULL, created_by TEXT
            );
            CREATE TABLE IF NOT EXISTS grievances (
                grievance_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL,
                notes TEXT, assigned_to TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS advisory_localizations (
                advisory_id TEXT NOT NULL, language TEXT NOT NULL, text TEXT NOT NULL,
                source_metrics TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(advisory_id, language)
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_security_created ON security_events(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_security_severity ON security_events(severity);
            CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_risk_panchayat ON risk_scores(panchayat_id, forecast_date);
            CREATE INDEX IF NOT EXISTS idx_grievance_status ON grievances(status);
            """)
            now = utcnow()
            defaults = [
                ("citizen", "Public / Farmer", "Farmer, citizen, and general public user"),
                ("officer", "Field / Department Officer", "Mandal and field agriculture officer"),
                ("kvk", "KVK Scientist", "KVK/AMFU agromet reviewer and scientist"),
                ("district_officer", "District Officer", "District Agriculture Officer (DAO) and district monitoring"),
                ("admin", "Administrator", "System administrator and governance manager"),
                ("superadmin", "Super Administrator", "Full state platform administrator"),
            ]
            for rid, name, desc in defaults:
                c.execute("INSERT OR IGNORE INTO roles(role_id,name,description,created_at) VALUES(?,?,?,?)", (rid, name, desc, now))
            c.execute("INSERT OR IGNORE INTO departments(department_id,name,description,created_at) VALUES(?,?,?,?)",
                      ("agri-telangana", "Department of Agriculture, Telangana", "State Agriculture & Agromet Decision Support Pilot", now))

            # Add columns to legacy tables if needed
            cols = {row["name"] for row in c.execute("PRAGMA table_info(advisories)").fetchall()}
            if "created_at" not in cols:
                c.execute("ALTER TABLE advisories ADD COLUMN created_at TEXT")
                c.execute("UPDATE advisories SET created_at=updated_at WHERE created_at IS NULL")
            if "reviewed_at" not in cols:
                c.execute("ALTER TABLE advisories ADD COLUMN reviewed_at TEXT")

            g_cols = {row["name"] for row in c.execute("PRAGMA table_info(grievances)").fetchall()}
            if "notes" not in g_cols:
                c.execute("ALTER TABLE grievances ADD COLUMN notes TEXT")
            if "assigned_to" not in g_cols:
                c.execute("ALTER TABLE grievances ADD COLUMN assigned_to TEXT")

            n_cols = {row["name"] for row in c.execute("PRAGMA table_info(notices)").fetchall()}
            if "priority" not in n_cols:
                c.execute("ALTER TABLE notices ADD COLUMN priority TEXT DEFAULT 'normal'")

    def log_audit(self, action: str, resource: str, result: str = "SUCCESS", user_id: str | None = None, user_email: str | None = None, role: str | None = None, details: str | None = None) -> int:
        now = utcnow()
        with self._lock, self.connection() as c:
            cur = c.execute(
                "INSERT INTO audit_logs(created_at, user_id, user_email, role, action, resource, result, details) VALUES(?,?,?,?,?,?,?,?)",
                (now, user_id, user_email, role, action, resource, result, details)
            )
            return int(cur.lastrowid or 0)

    def list_audit_logs(self, limit: int = 100, offset: int = 0, action: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM audit_logs WHERE 1=1"
        params: list[Any] = []
        if action:
            sql += " AND action = ?"
            params.append(action)
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        sql += " ORDER BY log_id DESC LIMIT ? OFFSET ?"
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute(sql, params).fetchall()]

    def count_audit_logs(self) -> int:
        with self._lock, self.connection() as c:
            return int(c.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])

    def create_user(self, email: str, display_name: str, password: str, mobile: str | None, department_id: str | None, role: str = "citizen") -> dict[str, Any]:
        uid = "USR-" + uuid4().hex[:12].upper()
        now = utcnow()
        ph = hash_password(password)
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO users(user_id,email,display_name,password_hash,mobile,department_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                      (uid, email.lower().strip(), display_name.strip(), ph, mobile, department_id, now, now))
            c.execute("INSERT OR IGNORE INTO user_roles(user_id,role_id) VALUES(?,?)", (uid, role))
        self.log_audit("USER_REGISTER", f"users/{uid}", "SUCCESS", user_id=uid, user_email=email, role=role, details=f"Created account for {display_name}")
        return self.get_user(uid)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self._lock, self.connection() as c:
            row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
            if not row: return None
            roles = [r["role_id"] for r in c.execute("SELECT role_id FROM user_roles WHERE user_id=?", (user_id,))]
        d = dict(row)
        d.pop("password_hash", None)
        d.pop("mfa_secret", None)
        d["roles"] = roles
        return d

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._lock, self.connection() as c:
            row = c.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
            if not row: return None
            user_id = row["user_id"]
            roles = [r["role_id"] for r in c.execute("SELECT role_id FROM user_roles WHERE user_id=?", (user_id,))]
        d = dict(row)
        d["roles"] = roles
        return d

    def authenticate(self, email: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_email(email)
        if not user or not user.get("is_active") or not verify_password(password, user.get("password_hash", "")):
            return None
        return user

    def set_mfa_secret(self, user_id: str, secret: str) -> None:
        with self._lock, self.connection() as c:
            c.execute("UPDATE users SET mfa_secret=?,mfa_enabled=0,updated_at=? WHERE user_id=?", (secret, utcnow(), user_id))

    def enable_mfa(self, user_id: str) -> None:
        with self._lock, self.connection() as c:
            c.execute("UPDATE users SET mfa_enabled=1,updated_at=? WHERE user_id=?", (utcnow(), user_id))

    def get_roles(self, user_id: str) -> list[str]:
        with self._lock, self.connection() as c:
            return [r["role_id"] for r in c.execute("SELECT role_id FROM user_roles WHERE user_id=?", (user_id,))]

    def add_role(self, user_id: str, role_id: str) -> None:
        with self._lock, self.connection() as c:
            c.execute("INSERT OR IGNORE INTO user_roles(user_id,role_id) VALUES(?,?)", (user_id, role_id))
        self.log_audit("ROLE_ASSIGN", f"users/{user_id}/roles/{role_id}", "SUCCESS", user_id=user_id, details=f"Assigned role {role_id}")

    def remove_role(self, user_id: str, role_id: str) -> None:
        with self._lock, self.connection() as c:
            c.execute("DELETE FROM user_roles WHERE user_id=? AND role_id=?", (user_id, role_id))
        self.log_audit("ROLE_REVOKE", f"users/{user_id}/roles/{role_id}", "SUCCESS", user_id=user_id, details=f"Revoked role {role_id}")

    def list_users(self, limit=50, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            rows = c.execute("SELECT user_id,email,display_name,mobile,department_id,is_active,mfa_enabled,created_at,updated_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (max(1, min(limit, 200)), max(0, offset))).fetchall()
        out = []
        for row in rows:
            d = dict(row); d["roles"] = self.get_roles(d["user_id"]); out.append(d)
        return out

    def count_users(self) -> int:
        with self._lock, self.connection() as c: return int(c.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def create_session(self, user_id: str, token_hash: str, expires_at: str, ip: str | None, ua: str | None, session_id: str | None = None) -> str:
        sid = session_id or ("SES-" + uuid4().hex[:12])
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO sessions(session_id,user_id,token_hash,created_at,expires_at,ip_address,user_agent) VALUES(?,?,?,?,?,?,?)",
                      (sid, user_id, token_hash, utcnow(), expires_at, ip, ua))
        user = self.get_user(user_id)
        role = user["roles"][0] if user and user.get("roles") else "citizen"
        self.log_audit("USER_LOGIN", f"sessions/{sid}", "SUCCESS", user_id=user_id, user_email=user.get("email") if user else None, role=role, details=f"Session issued from IP {ip}")
        return sid

    def get_session(self, session_id: str, token_hash: str) -> dict[str, Any] | None:
        with self._lock, self.connection() as c:
            row = c.execute("SELECT * FROM sessions WHERE session_id=? AND token_hash=? AND revoked_at IS NULL", (session_id, token_hash)).fetchone()
        return dict(row) if row else None

    def revoke_session(self, session_id: str) -> None:
        with self._lock, self.connection() as c:
            session = c.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            c.execute("UPDATE sessions SET revoked_at=? WHERE session_id=?", (utcnow(), session_id))
        if session:
            self.log_audit("USER_LOGOUT", f"sessions/{session_id}", "SUCCESS", user_id=session["user_id"], details="Session revoked")

    def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT session_id,created_at,expires_at,revoked_at,ip_address,user_agent FROM sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()]

    def create_reset_token(self, user_id: str, token_hash: str, expires_at: str) -> str:
        tid = "RST-" + uuid4().hex[:12]
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO password_reset_tokens(token_id,user_id,token_hash,purpose,expires_at) VALUES(?,?,?,?,?)", (tid, user_id, token_hash, "password_reset", expires_at))
        return tid

    def consume_reset_token(self, token_hash: str) -> str | None:
        now = utcnow()
        with self._lock, self.connection() as c:
            row = c.execute("SELECT token_id,user_id FROM password_reset_tokens WHERE token_hash=? AND used_at IS NULL AND expires_at>?", (token_hash, now)).fetchone()
            if not row: return None
            c.execute("UPDATE password_reset_tokens SET used_at=? WHERE token_id=?", (now, row["token_id"]))
            return row["user_id"]

    def update_password(self, user_id: str, password: str) -> None:
        with self._lock, self.connection() as c:
            c.execute("UPDATE users SET password_hash=?,updated_at=? WHERE user_id=?", (hash_password(password), utcnow(), user_id))
        self.log_audit("PASSWORD_UPDATE", f"users/{user_id}", "SUCCESS", user_id=user_id, details="Password updated successfully")

    def create_recovery_otp(self, user_id: str, code_hash: str, expires_at: str) -> str:
        oid = "OTP-" + uuid4().hex[:12]
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO recovery_otps(otp_id,user_id,code_hash,expires_at) VALUES(?,?,?,?)", (oid, user_id, code_hash, expires_at))
        return oid

    def consume_recovery_otp(self, code_hash: str) -> str | None:
        now = utcnow()
        with self._lock, self.connection() as c:
            row = c.execute("SELECT otp_id,user_id FROM recovery_otps WHERE code_hash=? AND used_at IS NULL AND expires_at>? AND attempts<5 ORDER BY expires_at DESC LIMIT 1", (code_hash, now)).fetchone()
            if not row: return None
            c.execute("UPDATE recovery_otps SET used_at=? WHERE otp_id=?", (now, row["otp_id"]))
            return row["user_id"]

    def notifications(self, user_id: str | None, limit=50, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            if user_id:
                rows = c.execute("SELECT * FROM notifications WHERE user_id=? OR user_id IS NULL ORDER BY created_at DESC LIMIT ? OFFSET ?", (user_id, max(1, min(limit, 200)), max(0, offset))).fetchall()
            else:
                rows = c.execute("SELECT * FROM notifications WHERE user_id IS NULL ORDER BY created_at DESC LIMIT ? OFFSET ?", (max(1, min(limit, 200)), max(0, offset))).fetchall()
        return [dict(r) for r in rows]

    def create_notification(self, title: str, body: str, category: str, severity="info", user_id=None, reference_type=None, reference_id=None) -> str:
        nid = "NTF-" + uuid4().hex[:12]
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO notifications(notification_id,user_id,category,title,body,severity,reference_type,reference_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (nid, user_id, category, title, body, severity, reference_type, reference_id, utcnow()))
        return nid

    def mark_notification(self, notification_id: str, user_id: str) -> bool:
        with self._lock, self.connection() as c:
            cur = c.execute("UPDATE notifications SET read_at=? WHERE notification_id=? AND (user_id=? OR user_id IS NULL)", (utcnow(), notification_id, user_id))
            return cur.rowcount > 0

    def unread_count(self, user_id: str) -> int:
        with self._lock, self.connection() as c:
            return int(c.execute("SELECT COUNT(*) FROM notifications WHERE (user_id=? OR user_id IS NULL) AND read_at IS NULL", (user_id,)).fetchone()[0])

    def save_risk(self, panchayat_id: str, forecast_date: str, score: float, level: str, contributions: dict[str, float], model_version: str) -> dict[str, Any]:
        rid = "RSK-" + uuid4().hex[:12]
        now = utcnow()
        with self._lock, self.connection() as c:
            c.execute("""INSERT INTO risk_scores(risk_id,panchayat_id,forecast_date,score,level,contributions,model_version,created_at)
                         VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(panchayat_id,forecast_date) DO UPDATE SET score=excluded.score,level=excluded.level,contributions=excluded.contributions,model_version=excluded.model_version,created_at=excluded.created_at""",
                      (rid, panchayat_id, forecast_date, score, level, json.dumps(contributions), model_version, now))
        return self.get_risk(panchayat_id, forecast_date)

    def get_risk(self, panchayat_id: str, forecast_date: str | None = None) -> dict[str, Any] | None:
        with self._lock, self.connection() as c:
            row = c.execute("SELECT * FROM risk_scores WHERE panchayat_id=? ORDER BY forecast_date DESC LIMIT 1" if not forecast_date else "SELECT * FROM risk_scores WHERE panchayat_id=? AND forecast_date=?", (panchayat_id,) if not forecast_date else (panchayat_id, forecast_date)).fetchone()
        if not row: return None
        d = dict(row); d["contributions"] = json.loads(d["contributions"]); return d

    def security_event(self, **event: Any) -> None:
        with self._lock, self.connection() as c:
            c.execute("""INSERT INTO security_events(created_at,ip_address,method,path,status_code,latency_ms,category,severity,user_id,detail)
                         VALUES(?,?,?,?,?,?,?,?,?,?)""", (event.get("created_at", utcnow()), event.get("ip_address"), event.get("method", ""), event.get("path", ""), int(event.get("status_code", 0)), float(event.get("latency_ms", 0)), event.get("category", "request"), event.get("severity", "info"), event.get("user_id"), event.get("detail")))

    def security_summary(self, since_hours: int = 24) -> dict[str, Any]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        with self._lock, self.connection() as c:
            total = int(c.execute("SELECT COUNT(*) FROM security_events WHERE created_at>=?", (cutoff,)).fetchone()[0])
            blocked = int(c.execute("SELECT COUNT(*) FROM security_events WHERE created_at>=? AND status_code IN (401,403,429)", (cutoff,)).fetchone()[0])
            suspicious = int(c.execute("SELECT COUNT(*) FROM security_events WHERE created_at>=? AND category IN ('suspicious','anomaly','rate_limit')", (cutoff,)).fetchone()[0])
            critical = int(c.execute("SELECT COUNT(*) FROM security_events WHERE created_at>=? AND severity='critical'", (cutoff,)).fetchone()[0])
            categories = [dict(r) for r in c.execute("SELECT category,COUNT(*) count FROM security_events WHERE created_at>=? GROUP BY category ORDER BY count DESC", (cutoff,)).fetchall()]
            severities = [dict(r) for r in c.execute("SELECT severity,COUNT(*) count FROM security_events WHERE created_at>=? GROUP BY severity ORDER BY count DESC", (cutoff,)).fetchall()]
            timeline = [dict(r) for r in c.execute("SELECT substr(created_at,1,13) hour,COUNT(*) count FROM security_events WHERE created_at>=? GROUP BY hour ORDER BY hour", (cutoff,)).fetchall()]
        return {"window_hours": since_hours, "requests": total, "blocked": blocked, "suspicious": suspicious, "critical": critical, "categories": categories, "severity_distribution": severities, "timeline": timeline}

    def security_events(self, limit=100, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM security_events ORDER BY event_id DESC LIMIT ? OFFSET ?", (max(1, min(limit, 500)), max(0, offset))).fetchall()]

    def update_project(self, pid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_project(pid)
        if not current: return None
        merged = {**current, **data, "updated_at": utcnow()}
        with self._lock, self.connection() as c:
            c.execute("""UPDATE projects SET name=?,district=?,mandal=?,block_id=?,state=?,status=?,progress=?,budget_amount=?,latitude=?,longitude=?,description=?,updated_at=? WHERE project_id=?""",
                      (merged["name"], merged.get("district"), merged.get("mandal"), merged.get("block_id"), merged.get("state", "Telangana"), merged.get("status", "planned"), float(merged.get("progress", 0)), merged.get("budget_amount"), merged.get("latitude"), merged.get("longitude"), merged.get("description"), merged["updated_at"], pid))
        self.log_audit("PROJECT_UPDATE", f"projects/{pid}", "SUCCESS", details=f"Updated project {merged['name']}")
        return self.get_project(pid)

    def delete_project(self, pid: str) -> bool:
        with self._lock, self.connection() as c:
            cur = c.execute("DELETE FROM projects WHERE project_id=?", (pid,))
        ok = cur.rowcount > 0
        if ok:
            self.log_audit("PROJECT_DELETE", f"projects/{pid}", "SUCCESS", details="Project deleted")
        return ok

    def create_milestone(self, pid: str, data: dict[str, Any]) -> dict[str, Any]:
        mid = "MS-" + uuid4().hex[:10].upper()
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO project_milestones(milestone_id,project_id,title,due_date,status,progress,created_at) VALUES(?,?,?,?,?,?,?)", (mid, pid, data["title"], data.get("due_date"), data.get("status", "planned"), float(data.get("progress", 0)), utcnow()))
        with self._lock, self.connection() as c:
            r = c.execute("SELECT * FROM project_milestones WHERE milestone_id=?", (mid,)).fetchone()
        return dict(r)

    def list_milestones(self, pid: str) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM project_milestones WHERE project_id=? ORDER BY due_date", (pid,)).fetchall()]

    def create_inspection(self, pid: str, data: dict[str, Any]) -> dict[str, Any]:
        iid = "INS-" + uuid4().hex[:10].upper()
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO project_inspections(inspection_id,project_id,inspected_at,inspector,status,notes) VALUES(?,?,?,?,?,?)", (iid, pid, data.get("inspected_at") or utcnow(), data["inspector"], data.get("status", "recorded"), data.get("notes")))
        with self._lock, self.connection() as c:
            r = c.execute("SELECT * FROM project_inspections WHERE inspection_id=?", (iid,)).fetchone()
        return dict(r)

    def list_inspections(self, pid: str) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM project_inspections WHERE project_id=? ORDER BY inspected_at DESC", (pid,)).fetchall()]

    def list_projects(self, limit=50, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT ? OFFSET ?", (max(1, min(limit, 200)), max(0, offset))).fetchall()]

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        pid = data.get("project_id") or "PRJ-" + uuid4().hex[:10].upper(); now = utcnow()
        with self._lock, self.connection() as c:
            c.execute("""INSERT INTO projects(project_id,name,district,mandal,block_id,state,status,progress,budget_amount,latitude,longitude,description,created_at,updated_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (pid, data["name"], data.get("district"), data.get("mandal"), data.get("block_id"), data.get("state", "Telangana"), data.get("status", "planned"), float(data.get("progress", 0)), data.get("budget_amount"), data.get("latitude"), data.get("longitude"), data.get("description"), now, now))
        self.log_audit("PROJECT_CREATE", f"projects/{pid}", "SUCCESS", details=f"Created project {data['name']}")
        return self.get_project(pid)

    def get_project(self, pid: str) -> dict[str, Any] | None:
        with self._lock, self.connection() as c:
            r = c.execute("SELECT * FROM projects WHERE project_id=?", (pid,)).fetchone()
        return dict(r) if r else None

    def analytics(self) -> dict[str, Any]:
        with self._lock, self.connection() as c:
            projects = [dict(r) for r in c.execute("SELECT status,COUNT(*) count,AVG(progress) avg_progress,COALESCE(SUM(budget_amount),0) budget FROM projects GROUP BY status")]
            milestones = [dict(r) for r in c.execute("SELECT status,COUNT(*) count FROM project_milestones GROUP BY status")]
            grievances = [dict(r) for r in c.execute("SELECT status,COUNT(*) count FROM grievances GROUP BY status")]
            risks = [dict(r) for r in c.execute("SELECT level,COUNT(*) count FROM risk_scores GROUP BY level")]
            notices = int(c.execute("SELECT COUNT(*) FROM notices WHERE is_active=1").fetchone()[0])
            users_count = int(c.execute("SELECT COUNT(*) FROM users").fetchone()[0])
            audits_count = int(c.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])
        return {
            "projects_by_status": projects,
            "milestones_by_status": milestones,
            "grievances_by_status": grievances,
            "risk_distribution": risks,
            "active_notices": notices,
            "total_users": users_count,
            "total_audit_events": audits_count,
        }

    def list_notices(self, active_only=True, limit=50, offset=0) -> list[dict[str, Any]]:
        sql = "SELECT * FROM notices " + ("WHERE is_active=1 " if active_only else "") + "ORDER BY published_at DESC LIMIT ? OFFSET ?"
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute(sql, (max(1, min(limit, 200)), max(0, offset))).fetchall()]

    def create_notice(self, data: dict[str, Any]) -> dict[str, Any]:
        nid = "NOT-" + uuid4().hex[:10].upper(); now = data.get("published_at") or utcnow()
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO notices(notice_id,title,body,category,priority,published_at,expires_at,is_active,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                      (nid, data["title"], data["body"], data.get("category", "general"), data.get("priority", "normal"), now, data.get("expires_at"), 1, data.get("created_by")))
        self.log_audit("NOTICE_CREATE", f"notices/{nid}", "SUCCESS", details=f"Published notice: {data['title']}")
        return self.list_notices(False, 1, 0)[0]

    def list_documents(self, limit=50, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM documents ORDER BY published_at DESC LIMIT ? OFFSET ?", (max(1, min(limit, 200)), max(0, offset))).fetchall()]

    def create_document(self, data: dict[str, Any]) -> dict[str, Any]:
        did = "DOC-" + uuid4().hex[:10].upper()
        with self._lock, self.connection() as c:
            c.execute("INSERT INTO documents(document_id,title,category,description,storage_url,checksum,published_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
                      (did, data["title"], data.get("category", "report"), data.get("description"), data.get("storage_url"), data.get("checksum"), data.get("published_at") or utcnow(), data.get("created_by")))
        return next(x for x in self.list_documents() if x["document_id"] == did)

    def save_localization(self, advisory_id: str, language: str, text: str, metrics: dict[str, Any]) -> None:
        with self._lock, self.connection() as c:
            c.execute("""INSERT INTO advisory_localizations(advisory_id,language,text,source_metrics,created_at)
            VALUES(?,?,?,?,?) ON CONFLICT(advisory_id,language) DO UPDATE SET text=excluded.text,source_metrics=excluded.source_metrics,created_at=excluded.created_at""",
                      (advisory_id, language, text, json.dumps(metrics), utcnow()))

    def get_localizations(self, advisory_id: str) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            rows = c.execute("SELECT * FROM advisory_localizations WHERE advisory_id=? ORDER BY language", (advisory_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r); d["source_metrics"] = json.loads(d["source_metrics"]); out.append(d)
        return out

    def update_grievance_status(self, grievance_id: str, status: str, notes: str | None = None, assigned_to: str | None = None) -> dict[str, Any] | None:
        now = utcnow()
        with self._lock, self.connection() as c:
            row = c.execute("SELECT * FROM grievances WHERE grievance_id=?", (grievance_id,)).fetchone()
            if not row:
                return None
            payload = json.loads(row["payload"])
            payload["status"] = status
            if notes:
                payload["notes"] = notes
            if assigned_to:
                payload["assigned_to"] = assigned_to
            c.execute("UPDATE grievances SET status=?, payload=?, notes=?, assigned_to=?, updated_at=? WHERE grievance_id=?",
                      (status, json.dumps(payload), notes or row["notes"], assigned_to or row["assigned_to"], now, grievance_id))
        self.log_audit("GRIEVANCE_STATUS_UPDATE", f"grievances/{grievance_id}", "SUCCESS", details=f"Status changed to {status}")
        self.create_notification(
            title=f"Grievance {grievance_id} Updated",
            body=f"Status changed to {status.upper()}. Notes: {notes or 'No remarks'}",
            category="grievance", severity="info",
            reference_type="grievance", reference_id=grievance_id,
        )
        return {"grievance_id": grievance_id, "status": status, "updated_at": now, "notes": notes, "assigned_to": assigned_to}

    def review_events(self, limit=100, offset=0) -> list[dict[str, Any]]:
        with self._lock, self.connection() as c:
            return [dict(r) for r in c.execute("SELECT event_id,advisory_id,reviewer_id,action,notes,created_at FROM review_events ORDER BY event_id DESC LIMIT ? OFFSET ?", (max(1, min(limit, 500)), max(0, offset))).fetchall()]

    def seed_defaults(self) -> None:
        # 1. Seed demo users for every supported role if not already existing
        demo_users = [
            ("admin@agromet.gov.in", "State Administrator", "Admin@Agromet2026!", "admin", "9876543210"),
            ("scientist.kvk@agromet.gov.in", "Dr. R. K. Sharma (KVK Scientist)", "Scientist@Agromet2026!", "kvk", "9876543211"),
            ("officer.field@agromet.gov.in", "M. Venkata Rao (Field Officer)", "Officer@Agromet2026!", "officer", "9876543212"),
            ("officer.district@agromet.gov.in", "S. Anitha (District Agriculture Officer)", "District@Agromet2026!", "district_officer", "9876543213"),
            ("farmer@agromet.gov.in", "Aditya Singh (Farmer)", "Farmer@Agromet2026!", "citizen", "9876543214"),
        ]
        for email, name, pwd, role, mob in demo_users:
            if not self.get_user_by_email(email):
                try:
                    self.create_user(email, name, pwd, mob, "agri-telangana", role)
                except Exception:
                    pass

        # Also support bootstrap admin from ENV if specified
        env_email = os.getenv("AGROMET_BOOTSTRAP_ADMIN_EMAIL")
        env_password = os.getenv("AGROMET_BOOTSTRAP_ADMIN_PASSWORD")
        if env_email and env_password and not self.get_user_by_email(env_email):
            try:
                self.create_user(env_email, "System Administrator", env_password, None, "agri-telangana", "admin")
            except Exception:
                pass

        # 2. Seed realistic official notices if notices table is empty
        with self._lock, self.connection() as c:
            count = int(c.execute("SELECT COUNT(*) FROM notices").fetchone()[0])
            if count == 0:
                notices_data = [
                    {
                        "title": "Monsoon Preparedness Bulletin & Field Drainage Advisory (Kharif 2026)",
                        "body": "Department of Agriculture urges all farmers across Rangareddy, Medak, and Vikarabad districts to ensure field bunds and drainage outlets are cleared ahead of anticipated intense convective rainfall spells. Review specific block-level advisories on this portal.",
                        "category": "Weather Alert",
                        "priority": "high",
                        "created_by": "Director of Agriculture, Telangana",
                    },
                    {
                        "title": "Kharif 2026 Paddy Sowing & Seed Treatment Protocol",
                        "body": "Farmers undertaking nursery sowing of Paddy (varieties Telangana Sona, RNR 15048, MTU 1010) are advised to treat seed with Carbendazim @ 2g/kg or Trichoderma viride @ 10g/kg to prevent seed-borne blast infection. Ensure seedbeds have adequate drainage.",
                        "category": "Agricultural Advisory",
                        "priority": "normal",
                        "created_by": "KVK Scientist Cell",
                    },
                    {
                        "title": "Cotton Pink Bollworm Integrated Pest Management (IPM) Guidelines",
                        "body": "Install pheromone traps @ 8 per acre at 45 days after sowing for monitoring pink bollworm male moths. Maintain weekly trap observation logs. Avoid unnecessary broad-spectrum chemical sprays during initial squaring stage.",
                        "category": "Pest Advisory",
                        "priority": "normal",
                        "created_by": "State Extension Directorate",
                    },
                ]
                for n in notices_data:
                    self.create_notice(n)

            # 3. Seed realistic irrigation/agriculture projects if projects table is empty
            prj_count = int(c.execute("SELECT COUNT(*) FROM projects").fetchone()[0])
            if prj_count == 0:
                projects_data = [
                    {
                        "name": "Mission Kakatiya Minor Irrigation Tank Restoration — Chevella Cluster",
                        "district": "Rangareddy",
                        "mandal": "Chevella",
                        "block_id": "BLK_RRE_01",
                        "status": "in_progress",
                        "progress": 78.5,
                        "budget_amount": 4500000.0,
                        "latitude": 17.308,
                        "longitude": 78.134,
                        "description": "Desiltation and bund strengthening of 14 minor irrigation tanks to ensure Kharif irrigation water availability for 1,200 acres.",
                    },
                    {
                        "name": "Telangana Micro-Irrigation Scheme (TMIS) Drip Deployment — Parigi",
                        "district": "Vikarabad",
                        "mandal": "Parigi",
                        "block_id": "BLK_VIK_02",
                        "status": "in_progress",
                        "progress": 64.0,
                        "budget_amount": 3200000.0,
                        "latitude": 17.182,
                        "longitude": 77.887,
                        "description": "Installation of subsidized automated drip and sprinkler systems for cotton and vegetable cultivators across 400 hectares.",
                    },
                    {
                        "name": "Automatic Agromet Weather Station (AWS) Solar Sensor Grid — Sangareddy",
                        "district": "Sangareddy",
                        "mandal": "Sangareddy",
                        "block_id": "BLK_SNG_01",
                        "status": "completed",
                        "progress": 100.0,
                        "budget_amount": 1800000.0,
                        "latitude": 17.618,
                        "longitude": 78.082,
                        "description": "Solar-powered telemetry station for live rainfall, soil moisture, and evapotranspiration monitoring linked to state data center.",
                    },
                ]
                for p in projects_data:
                    self.create_project(p)

    def seed_admin_from_env(self) -> None:
        self.seed_defaults()

