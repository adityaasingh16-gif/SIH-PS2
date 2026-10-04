"""Minimal platform repository for demo data support.

Provides the PlatformRepository class used by the seed script and main application.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from .advisory_engine import Advisory, AdvisoryBatch, AdvisoryStatus


class PlatformRepository:
    """Repository with demo-data and audit support."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        configured = database_path or os.getenv("AGROMET_DB_PATH", "agromet.sqlite3")
        self.database_path = str(configured)
        self._lock = threading.RLock()
        self._memory_connection: sqlite3.Connection | None = None
        if self.database_path == ":memory:":
            self._memory_connection = self._new_connection()
        else:
            Path(self.database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _new_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=30,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._memory_connection or self._new_connection()
        try:
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise RuntimeError(str(exc)) from exc
        finally:
            if connection is not self._memory_connection:
                connection.close()

    def connection(self) -> sqlite3.Connection | None:
        """Return the current database connection, or None if not available."""
        if self._memory_connection:
            return self._memory_connection
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def _initialise(self) -> None:
        with self._lock, self._connection() as connection:
            connection.executescript(
                """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS forecasts (
                panchayat_id TEXT PRIMARY KEY,
                generated_at TEXT NOT NULL,
                model_version TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS advisories (
                advisory_id TEXT PRIMARY KEY,
                panchayat_id TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS review_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                advisory_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                action TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(advisory_id) REFERENCES advisories(advisory_id)
            );
            CREATE TABLE IF NOT EXISTS demo_seed_manifest (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                detail TEXT,
                seeded_at TEXT NOT NULL,
                PRIMARY KEY(entity_type, entity_id)
            );
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                reference_type TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notices (
                notice_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS advisory_localizations (
                advisory_id TEXT NOT NULL,
                language TEXT NOT NULL,
                text TEXT NOT NULL,
                source_metrics TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
            )

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self._lock, self._connection() as c:
            row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._lock, self._connection() as c:
            row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None

    def utcnow(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log_audit(self, action: str, resource: str, result: str = "SUCCESS", *, user_id: str | None = None,
                  role: str | None = None, details: str | None = None, user_email: str | None = None,
                  created_at: str | None = None) -> None:
        """Append one governance audit entry (user actions, reviews, system events)."""
        if user_id and not user_email:
            user = self.get_user(user_id)
            user_email = user["email"] if user else None
        with self._lock, self._connection() as c:
            c.execute("INSERT INTO audit_logs(created_at,user_id,user_email,role,action,resource,result,details) VALUES(?,?,?,?,?,?,?,?)",
                      (created_at or self.utcnow(), user_id, user_email, role, action, resource, result, details))

    def list_audit_logs(self, limit: int = 100, offset: int = 0, action: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM audit_logs WHERE 1=1"
        params: list[Any] = []
        if action:
            sql += " AND action=?"; params.append(action)
        if user_id:
            sql += " AND user_id=?"; params.append(user_id)
        sql += " ORDER BY created_at DESC, audit_id DESC LIMIT ? OFFSET ?"
        params += [max(1, min(limit, 500)), max(0, offset)]
        with self._lock, self._connection() as c:
            return [dict(r) for r in c.execute(sql, params).fetchall()]

    def count_audit_logs(self) -> int:
        with self._lock, self._connection() as c:
            return int(c.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])

    def save_localization(self, advisory_id: str, language: str, text: str, source_metrics: dict[str, float | int | str]) -> None:
        """Save an advisory localization (translated text)."""
        with self._lock, self._connection() as c:
            c.execute("INSERT INTO advisory_localizations (advisory_id, language, text, source_metrics, created_at) VALUES (?, ?, ?, ?, ?)",
                      (advisory_id, language, text, json.dumps(source_metrics, separators=(",", ":")), self.utcnow()))

    def peak_risk(self, panchayat_id: str) -> dict[str, object]:
        """Highest stored 5-day risk score for a Panchayat (None when no risk has been computed)."""
        with self._connection() as c:
            row = c.execute("SELECT score, level FROM risk_scores WHERE panchayat_id=? ORDER BY score DESC LIMIT 1", (panchayat_id,)).fetchone()
        return {"risk_score": row["score"], "risk_level": row["level"]} if row else {"risk_score": None, "risk_level": None}