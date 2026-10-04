"""Seed the four intended demo user accounts.

Creates the following accounts if they do not already exist:

* admin@agromet.demo / AdminDemo@2026!  (role: admin)
* officer@agromet.demo / OfficerDemo@2026!  (role: officer)
* kvk@agromet.demo / KvkScientist@2026!    (role: kvk)
* citizen@agromet.demo / CitizenDemo@2026!  (role: citizen)

Uses the platform_repo's users table. Designed to be called from
scripts/seed_demo_data.py --with-accounts.
"""

from __future__ import annotations
import sys

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agromet.platform import PlatformRepository


def seed() -> None:
    """Create the four demo accounts if they do not already exist."""
    db_path = os.getenv("AGROMET_DB_PATH") or str(ROOT / "data" / "agromet.sqlite3")
    repo = PlatformRepository(database_path=db_path)

    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    demo_users = {
        "admin@agromet.demo": {"password": "AdminDemo@2026!", "role": "admin", "email": "admin@agromet.demo"},
        "officer@agromet.demo": {"password": "OfficerDemo@2026!", "role": "officer", "email": "officer@agromet.demo"},
        "kvk@agromet.demo": {"password": "KvkScientist@2026!", "role": "kvk", "email": "kvk@agromet.demo"},
        "citizen@agromet.demo": {"password": "CitizenDemo@2026!", "role": "citizen", "email": "citizen@agromet.demo"},
    }

    with repo._lock, repo._connection() as c:
        for email, cfg in demo_users.items():
            # Extract user_id from email (everything before @)
            user_id = email.split("@")[1]
            c.execute(
                """
                INSERT OR IGNORE INTO users (user_id, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, email, cfg["password"], cfg["role"], now),
            )
    print(f"Demo accounts seeded: {', '.join(demo_users.keys())}")