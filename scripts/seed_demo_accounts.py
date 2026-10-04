"""Seed demo accounts across all 4 RBAC roles for local testing and evaluation.

Roles:
1. admin    - System Administrator
2. officer  - Agricultural / Administrative Officer
3. kvk      - KVK Scientist / Reviewer
4. citizen  - Farmer / Public Citizen
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from agromet.platform import PlatformRepository

DEMO_ACCOUNTS = [
    {
        "role": "admin",
        "email": "admin@agromet.demo",
        "password": "AdminDemo@2026!",
        "display_name": "Demo System Admin",
        "mobile": "9800000001",
        "department_id": "agri-telangana",
    },
    {
        "role": "officer",
        "email": "officer@agromet.demo",
        "password": "OfficerDemo@2026!",
        "display_name": "Demo Agri Officer",
        "mobile": "9800000002",
        "department_id": "agri-telangana",
    },
    {
        "role": "kvk",
        "email": "kvk@agromet.demo",
        "password": "KvkScientist@2026!",
        "display_name": "Demo KVK Scientist",
        "mobile": "9800000003",
        "department_id": "agri-telangana",
    },
    {
        "role": "citizen",
        "email": "citizen@agromet.demo",
        "password": "CitizenDemo@2026!",
        "display_name": "Demo Farmer Citizen",
        "mobile": "9800000004",
        "department_id": None,
    },
]

def seed():
    db_path = os.getenv("AGROMET_DB_PATH") or str(root_dir / "data" / "agromet.sqlite3")
    print(f"Connecting to database: {db_path}")
    repo = PlatformRepository(db_path)

    print("\n--- Seeding Demo Testing Accounts ---")
    for acc in DEMO_ACCOUNTS:
        existing = repo.get_user_by_email(acc["email"])
        if existing:
            # Update password and ensure role is assigned
            repo.update_password(existing["user_id"], acc["password"])
            repo.add_role(existing["user_id"], acc["role"])
            print(f"[UPDATED] {acc['role'].upper():<8} -> {acc['email']} (Password: {acc['password']})")
        else:
            created = repo.create_user(
                email=acc["email"],
                display_name=acc["display_name"],
                password=acc["password"],
                mobile=acc["mobile"],
                department_id=acc["department_id"],
                role=acc["role"],
            )
            print(f"[CREATED] {acc['role'].upper():<8} -> {acc['email']} (Password: {acc['password']})")

    print("\n[OK] Demo accounts ready for testing!")

if __name__ == "__main__":
    seed()
