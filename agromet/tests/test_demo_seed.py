"""Tests for scripts/seed_demo_data.py (runs the script in a subprocess against a temp SQLite DB)."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "seed_demo_data.py"
ANCHOR = "2026-10-04"


def _run(db: Path, *args: str, code: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "AGROMET_DB_PATH": str(db), "PYTHONWARNINGS": "ignore"}
    cmd = [sys.executable, "-c", code] if code else [sys.executable, str(SCRIPT), "--anchor-date", ANCHOR, *args]
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)


def _counts(db: Path) -> dict[str, int]:
    tables = ["forecasts", "advisories", "advisory_localizations", "review_events", "risk_scores",
              "notifications", "audit_logs", "grievances", "notices", "demo_seed_manifest"]
    with sqlite3.connect(db) as c:
        return {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    db = tmp_path_factory.mktemp("demo") / "demo.sqlite3"
    result = _run(db, "--with-accounts")
    assert result.returncode == 0, result.stdout + result.stderr
    return db


def test_seed_populates_every_area(seeded):
    counts = _counts(seeded)
    assert counts["forecasts"] == 12
    assert counts["risk_scores"] == 60
    assert counts["advisories"] >= 15
    assert counts["review_events"] >= 8
    assert counts["notifications"] >= 10 and counts["audit_logs"] >= 20
    assert counts["grievances"] == 4 and counts["notices"] == 3
    with sqlite3.connect(seeded) as c:
        statuses = {r[0] for r in c.execute("SELECT status FROM advisories")}
        levels = {r[0] for r in c.execute("SELECT level FROM risk_scores")}
        districts = c.execute("SELECT COUNT(*) FROM demo_seed_manifest WHERE entity_type='forecast'").fetchone()[0]
    assert {"pending_review", "approved", "edited", "rejected"} <= statuses
    assert {"low", "moderate", "high", "critical"} <= levels
    assert districts == 12


def test_seed_is_idempotent_and_purge_is_exact(seeded):
    before = _counts(seeded)
    again = _run(seeded)
    assert again.returncode == 0, again.stdout + again.stderr
    assert _counts(seeded) == before
    purged = _run(seeded, "--purge")
    assert purged.returncode == 0
    after = _counts(seeded)
    assert all(v == 0 for v in after.values()), after
    with sqlite3.connect(seeded) as c:  # real rows (accounts) are never touched
        assert c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 4
    assert _run(seeded).returncode == 0  # and it can be seeded again afterwards


def test_workflow_end_to_end_and_reseed_after_live_approval(tmp_path):
    db = tmp_path / "flow.sqlite3"
    assert _run(db, "--with-accounts").returncode == 0
    code = """
import json
from fastapi.testclient import TestClient
from agromet.main import app
c = TestClient(app)
tok = c.post('/api/v1/auth/login', json={'email': 'kvk@agromet.demo', 'password': 'KvkScientist@2026!'}).json()
assert tok['user']['roles'] == ['kvk'], tok
h = {'Authorization': 'Bearer ' + tok['access_token']}
pending = c.get('/api/v1/advisories/kvk-pending', headers=h).json()
hero = next(a for a in pending if a['panchayat_id'] == '206001' and a['kind'] == 'heavy_rain_drainage')
r = c.post('/api/v1/advisories/approve', headers=h, json={'advisory_id': hero['advisory_id'], 'action': 'approve', 'reviewer_id': 'kvk@agromet.demo'})
assert r.status_code == 200, r.text
kinds = [a['kind'] for a in c.get('/api/v1/advisories/published?panchayat_id=206001').json()]
assert 'heavy_rain_drainage' in kinds, kinds
assert c.get('/api/v1/audit-logs').json()['items'][0]['action'] == 'ADVISORY_APPROVE'
assert c.get('/api/v1/portal/demo-status').json()['active'] is True
fc = c.get('/api/v1/gis/panchayats').json()['features']
assert {f['properties']['risk_level'] for f in fc if f['properties']['risk_level']} == {'low', 'moderate', 'high', 'critical'}
print('OK')
"""
    flow = _run(db, code=code)
    assert flow.returncode == 0 and "OK" in flow.stdout, flow.stdout + flow.stderr
    # presenter rehearsed the approval; re-seeding must reset cleanly (no FK errors, no duplicates)
    before = _counts(db)
    assert _run(db).returncode == 0
    assert _counts(db)["advisories"] == before["advisories"]
    with sqlite3.connect(db) as c:
        status = c.execute("SELECT status FROM advisories WHERE advisory_id LIKE '206001:heavy_rain_drainage:%'").fetchone()[0]
    assert status == "pending_review"


def test_live_forecast_is_not_overwritten_without_force(tmp_path):
    db = tmp_path / "live.sqlite3"
    code = """
from datetime import date
from agromet.main import forecast_store, PanchayatForecastResponse, ForecastDayResponse, QuantileResponse
q = QuantileResponse(p10=1.0, p50=2.0, p90=3.0)
d = ForecastDayResponse(valid_date=date(2026, 10, 4), tmax_c=q, tmin_c=q, relative_humidity_pct=q, wind_speed_kmh=q, rain_mm=0.0)
forecast_store.save(PanchayatForecastResponse(panchayat_id='206001', generated_at=date(2026, 10, 4), model_version='live-model', days=[d]))
"""
    assert _run(db, code=code).returncode == 0
    out = _run(db)
    assert out.returncode == 0 and "live forecast present" in out.stdout
    with sqlite3.connect(db) as c:
        assert c.execute("SELECT model_version FROM forecasts WHERE panchayat_id='206001'").fetchone()[0] == "live-model"
        assert c.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0] == 12