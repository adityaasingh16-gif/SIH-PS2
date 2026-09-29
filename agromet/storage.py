"""Durable SQLite persistence for forecasts and KVK review decisions.

The repository intentionally stores validated JSON payloads rather than coupling
the API models to a particular ORM. SQLite is suitable for the pilot and can be
replaced behind this interface when the deployment moves to managed Postgres.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .advisory_engine import Advisory, AdvisoryBatch, AdvisoryStatus


class StorageError(RuntimeError):
    """Raised when a persistence operation cannot be completed."""


class SQLiteRepository:
    """Thread-safe repository with transactional forecast and review writes."""

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
            raise StorageError(str(exc)) from exc
        finally:
            if connection is not self._memory_connection:
                connection.close()

    def _initialise(self) -> None:
        with self._lock, self._connection() as connection:
            connection.executescript(
                """
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
                CREATE INDEX IF NOT EXISTS idx_advisories_status
                    ON advisories(status);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_forecast(self, forecast: object) -> None:
        """Persist any Pydantic forecast object with model_dump(mode='json')."""

        payload = getattr(forecast, "model_dump")(mode="json")
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO forecasts
                    (panchayat_id, generated_at, model_version, payload, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(panchayat_id) DO UPDATE SET
                    generated_at = excluded.generated_at,
                    model_version = excluded.model_version,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (
                    payload["panchayat_id"],
                    payload["generated_at"],
                    payload["model_version"],
                    json.dumps(payload, separators=(",", ":")),
                    self._now(),
                ),
            )

    def get_forecast_payload(self, panchayat_id: str) -> dict[str, object] | None:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM forecasts WHERE panchayat_id = ?",
                (panchayat_id,),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def add_advisory_batch(self, batch: AdvisoryBatch) -> None:
        with self._lock, self._connection() as connection:
            for advisory in batch.advisories:
                payload = advisory.model_dump(mode="json")
                connection.execute(
                    """
                    INSERT INTO advisories
                        (advisory_id, panchayat_id, status, payload, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(advisory_id) DO UPDATE SET
                        panchayat_id = excluded.panchayat_id,
                        status = excluded.status,
                        payload = excluded.payload,
                        updated_at = excluded.updated_at
                    """,
                    (
                        advisory.advisory_id,
                        advisory.panchayat_id,
                        advisory.status.value,
                        json.dumps(payload, separators=(",", ":")),
                        self._now(),
                    ),
                )

    def pending_advisories(self) -> list[Advisory]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM advisories WHERE status = ? ORDER BY updated_at",
                (AdvisoryStatus.PENDING_REVIEW.value,),
            ).fetchall()
        return [Advisory.model_validate_json(row["payload"]) for row in rows]

    def get_advisory(self, advisory_id: str) -> Advisory | None:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM advisories WHERE advisory_id = ?",
                (advisory_id,),
            ).fetchone()
        return Advisory.model_validate_json(row["payload"]) if row else None

    def update_advisory(
        self,
        advisory: Advisory,
        *,
        reviewer_id: str,
        action: str,
        notes: str | None,
    ) -> None:
        payload = advisory.model_dump(mode="json")
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                UPDATE advisories
                SET status = ?, payload = ?, updated_at = ?
                WHERE advisory_id = ?
                """,
                (
                    advisory.status.value,
                    json.dumps(payload, separators=(",", ":")),
                    self._now(),
                    advisory.advisory_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO review_events
                    (advisory_id, reviewer_id, action, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (advisory.advisory_id, reviewer_id, action, notes, self._now()),
            )

    def create_grievance(self, grievance_id: str, payload: dict[str, object]) -> None:
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS grievances (
                    grievance_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            now = self._now()
            connection.execute(
                """
                INSERT INTO grievances
                    (grievance_id, status, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (grievance_id, str(payload.get("status", "submitted")),
                 json.dumps(payload, separators=(",", ":")), now, now),
            )

    def list_grievances(self) -> list[dict[str, object]]:
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS grievances (
                    grievance_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            rows = connection.execute(
                "SELECT payload FROM grievances ORDER BY created_at DESC"
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def review_audit_events(self, limit: int = 100) -> list[dict[str, object]]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, advisory_id, reviewer_id, action, notes, created_at
                FROM review_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [dict(row) for row in rows]

