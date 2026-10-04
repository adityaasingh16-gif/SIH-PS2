"""Seed a deterministic, clearly-labelled SYNTHETIC demonstration dataset.

DEMO / SYNTHETIC DATA - not official IMD / Government of Telangana data,
not real farmer records, not real-time observations.

What it does (all through the application's own repositories / engines):
  * 5-day forecasts for 12 registry Panchayats across 6 districts, one weather
    scenario each (normal, heavy rain, cyclonic rain, heat stress, dry spell,
    disease-favourable) -> ForecastStore.save
  * risk scores for every forecast day -> main._risk_from_forecast (existing
    rule-derived risk function; nothing is hard-coded)
  * advisories from the existing AdvisoryEngine, English/Telugu/Hindi texts from
    the existing TemplateLocalizer, "awaiting review" notifications as in
    refresh_panchayat()
  * KVK decisions (approve / edit / reject / pending) through the existing
    AdvisoryReviewStore.approve() workflow, plus the audit entries the approve
    route writes
  * curated notifications, governance audit trail, grievances and notices

Safety properties
  * Idempotent: every row this script creates is recorded in `demo_seed_manifest`
    (a side table that no application code depends on). Each run first removes
    exactly those rows, then re-creates them, so repeated runs never duplicate
    anything and never touch real/live rows.
  * A live (non-demo) forecast is never overwritten unless --force is given.
  * Deterministic: scenario values are hand-authored tables; only dates (anchored
    to today, or --anchor-date) and "minutes ago" timestamps move.
  * Offline: no network access, no ML retraining.

Usage (same DB the app uses, via AGROMET_DB_PATH):
    python scripts/seed_demo_data.py                 # seed / reset demo data
    python scripts/seed_demo_data.py --with-accounts # also (re)create the 4 demo logins
    python scripts/seed_demo_data.py --purge         # remove demo data only
Set AGROMET_DEMO_SEED=0 to make the script a no-op (used by the Docker CMD).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED_VERSION = "demo-v1"
MODEL_VERSION = "demo-synthetic-scenario-v1"
LABEL = "[DEMO SYNTHETIC]"

# --------------------------------------------------------------------------- #
# Scenario tables: five lead days each.                                       #
# keys: tmax, tmin, rh, wind (p50), rain (mm), light/heavy/vheavy (probabilities)
# net_rad is the daily net radiation (MJ/m2/day) used for the FAO-56 ET0 value.
# --------------------------------------------------------------------------- #

SCENARIOS: dict[str, dict] = {
    "A_NORMAL": dict(
        label="Normal weather", net_rad=14.0,
        tmax=[33.5, 33.0, 34.0, 33.8, 32.9], tmin=[23.0, 23.2, 23.5, 23.1, 22.8],
        rh=[68, 69, 66, 64, 71], wind=[8.5, 9.0, 7.5, 8.0, 9.5],
        rain=[0.0, 0.6, 0.0, 2.4, 1.2], light=[0.10, 0.18, 0.08, 0.30, 0.22],
        heavy=[0.02, 0.03, 0.02, 0.06, 0.04], vheavy=[0, 0, 0, 0, 0]),
    "A_UNSETTLED": dict(
        label="Normal, unsettled afternoons", net_rad=13.0,
        tmax=[36.2, 35.4, 35.0, 35.8, 36.0], tmin=[23.4, 23.0, 22.8, 23.2, 23.6],
        rh=[62, 66, 68, 64, 60], wind=[9.0, 10.5, 11.0, 9.5, 8.5],
        rain=[1.0, 7.0, 5.0, 3.0, 0.4], light=[0.20, 0.50, 0.45, 0.35, 0.18],
        heavy=[0.20, 0.35, 0.30, 0.25, 0.12], vheavy=[0.01, 0.04, 0.03, 0.02, 0.0]),
    "B_HEAVY": dict(
        label="Heavy rainfall + waterlogging + disease pressure", net_rad=6.0,
        tmax=[29.5, 27.8, 26.9, 27.9, 30.2], tmin=[21.8, 21.5, 21.2, 21.4, 21.9],
        rh=[92, 95, 97, 94, 88], wind=[14, 19, 24, 18, 12],
        rain=[14.0, 62.0, 95.0, 41.0, 9.0], light=[0.85, 0.97, 0.99, 0.92, 0.60],
        heavy=[0.35, 0.82, 0.92, 0.70, 0.22], vheavy=[0.05, 0.35, 0.60, 0.20, 0.03]),
    "B_CYCLONIC": dict(
        label="Cyclonic depression - extreme rainfall and wind", net_rad=3.0,
        tmax=[28.5, 26.0, 24.8, 28.6, 29.0], tmin=[21.8, 21.0, 20.5, 21.2, 21.9],
        rh=[90, 96, 100, 94, 91], wind=[16, 24, 27.6, 22, 14],
        rain=[30.0, 95.0, 160.0, 70.0, 22.0], light=[0.95, 1.0, 1.0, 1.0, 0.90],
        heavy=[0.70, 0.97, 1.0, 0.93, 0.50], vheavy=[0.15, 0.70, 1.0, 0.55, 0.10]),
    "B_MODERATE": dict(
        label="Moderate heavy-rain spell", net_rad=9.0,
        tmax=[30.5, 28.8, 28.2, 29.4, 31.0], tmin=[21.9, 21.7, 21.5, 21.8, 21.9],
        rh=[86, 92, 94, 90, 84], wind=[11, 15, 17, 14, 10],
        rain=[6.0, 26.0, 40.0, 22.0, 5.0], light=[0.60, 0.90, 0.95, 0.85, 0.50],
        heavy=[0.25, 0.50, 0.65, 0.45, 0.15], vheavy=[0.02, 0.10, 0.15, 0.06, 0.01]),
    "C_HEAT": dict(
        label="Heat stress", net_rad=18.0,
        tmax=[40.2, 41.5, 42.3, 41.0, 39.4], tmin=[27.5, 28.2, 28.8, 28.0, 27.1],
        rh=[38, 34, 32, 36, 42], wind=[11, 13, 15, 12, 10],
        rain=[0, 0, 0, 0, 0], light=[0.02, 0.01, 0.01, 0.02, 0.04],
        heavy=[0, 0, 0, 0, 0], vheavy=[0, 0, 0, 0, 0]),
    "D_DRY": dict(
        label="Dry spell with rising temperature", net_rad=17.0,
        tmax=[36.5, 37.4, 38.4, 39.2, 39.8], tmin=[24.2, 24.8, 25.5, 26.0, 26.4],
        rh=[46, 43, 40, 38, 36], wind=[9, 10, 12, 13, 14],
        rain=[0, 0, 0, 0, 0], light=[0.03, 0.02, 0.02, 0.02, 0.01],
        heavy=[0, 0, 0, 0, 0], vheavy=[0, 0, 0, 0, 0]),
    "E_DISEASE": dict(
        label="Disease-favourable: humid, mild, intermittent rain", net_rad=9.0,
        tmax=[27.4, 26.8, 27.1, 27.6, 28.0], tmin=[21.8, 21.6, 21.4, 21.7, 21.9],
        rh=[93, 96, 98, 97, 95], wind=[7, 8, 9, 8, 7],
        rain=[6.0, 14.0, 22.0, 18.0, 10.0], light=[0.55, 0.75, 0.85, 0.80, 0.65],
        heavy=[0.30, 0.45, 0.60, 0.52, 0.38], vheavy=[0.03, 0.08, 0.15, 0.10, 0.05]),
    "E_WARM_HUMID": dict(
        label="Warm and humid, scattered showers", net_rad=11.0,
        tmax=[31.5, 31.0, 30.2, 31.8, 32.4], tmin=[24.2, 24.6, 24.9, 24.4, 24.0],
        rh=[84, 88, 90, 86, 82], wind=[10, 12, 13, 11, 9],
        rain=[3.0, 12.0, 16.0, 8.0, 2.0], light=[0.45, 0.65, 0.72, 0.55, 0.35],
        heavy=[0.35, 0.55, 0.60, 0.40, 0.20], vheavy=[0.02, 0.08, 0.12, 0.04, 0.0]),
}

# Panchayat id -> scenario and demo crop plot (ids come from config/panchayats.mock.json).
# Crop plot details have no home in the application schema, so they are kept in the
# demo manifest only (shown in the seed summary / presenter notes).
PLAN: list[dict] = [
    dict(pid="206001", scenario="B_HEAVY", crop="paddy", stage="Tillering / Vegetative", sown="-38d", area_ha=2.4, irrigation="Canal + rainfed", soil="Black cotton soil, waterlogging-prone", role="HERO: end-to-end story"),
    dict(pid="205001", scenario="B_CYCLONIC", crop="chillies", stage="Flowering & Fruit Set", sown="-74d", area_ha=1.6, irrigation="Drip", soil="Red sandy loam"),
    dict(pid="201001", scenario="A_NORMAL", crop="cotton", stage="Squaring & Flowering", sown="-58d", area_ha=3.1, irrigation="Rainfed", soil="Medium black soil"),
    dict(pid="201003", scenario="E_DISEASE", crop="paddy", stage="Panicle / Flowering", sown="-71d", area_ha=1.9, irrigation="Borewell", soil="Clay loam"),
    dict(pid="201004", scenario="C_HEAT", crop="cotton", stage="Boll Development", sown="-92d", area_ha=2.7, irrigation="Rainfed + protective irrigation", soil="Red soil"),
    dict(pid="201006", scenario="D_DRY", crop="maize", stage="Tasseling & Silking", sown="-55d", area_ha=1.2, irrigation="Borewell", soil="Sandy loam"),
    dict(pid="201008", scenario="A_NORMAL", crop="redgram", stage="Flowering & Pod Formation", sown="-110d", area_ha=2.0, irrigation="Rainfed", soil="Red gravelly soil"),
    dict(pid="201010", scenario="C_HEAT", crop="chillies", stage="Fruit Ripening & Picking", sown="-105d", area_ha=0.8, irrigation="Drip", soil="Red sandy loam"),
    dict(pid="202001", scenario="D_DRY", crop="redgram", stage="Branching", sown="-62d", area_ha=2.2, irrigation="Rainfed", soil="Red soil"),
    dict(pid="202003", scenario="B_MODERATE", crop="maize", stage="Cob Filling", sown="-80d", area_ha=1.4, irrigation="Rainfed", soil="Sandy clay loam"),
    dict(pid="203001", scenario="E_WARM_HUMID", crop="soybean", stage="Pod Filling", sown="-78d", area_ha=2.5, irrigation="Rainfed", soil="Medium black soil"),
    dict(pid="204001", scenario="A_UNSETTLED", crop="groundnut", stage="Pod Development", sown="-84d", area_ha=1.1, irrigation="Sprinkler", soil="Red sandy soil"),
]

REVIEWER = "kvk@agromet.demo"
# (panchayat, advisory kind) -> (action, reviewer notes). Everything not listed stays PENDING.
# NOTE: the application has no NEEDS_REVISION status; "reject" with a revision note is its equivalent.
DECISIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("206001", "urea_topdressing_delay"): ("approve", "Confirmed against 48h heavy-rain odds. Delay top-dressing until fields drain."),
    ("206001", "rice_blast"): ("approve", "Prolonged high humidity at tillering; scout fields and follow recommended fungicide schedule."),
    ("201003", "rice_blast"): ("approve", "Moderate risk. Field scouting advised; no prophylactic spray before the rain window."),
    ("201003", "urea_topdressing_delay"): ("edit", "Extended validity by one day - rain expected to persist."),
    ("202003", "urea_topdressing_delay"): ("approve", "Delay fertilizer application until rainfall subsides."),
    ("202003", "heavy_rain_drainage"): ("reject", "Needs revision: probability threshold met but rainfall total is borderline; re-issue after next forecast cycle."),
    ("201001", "spraying_window_ready"): ("approve", "Suitable window for planned protective sprays."),
    ("201004", "heat_stress"): ("approve", "Evening irrigation recommended; avoid midday field operations."),
    ("201006", "heat_stress"): ("approve", "Irrigate maize at silking during cooler hours."),
    ("203001", "cotton_bollworm"): ("approve", "Warm humid weather: inspect squares and bolls (also scout soybean pods for pests)."),
}
# message_key lookups used above ("spraying_window_ready" is a message key, others are kinds)


# --------------------------------------------------------------------------- #
def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _q(p50: float, lo: float, hi: float, floor: float | None = None, ceil: float | None = None):
    p10, p90 = p50 - lo, p50 + hi
    if floor is not None:
        p10 = max(floor, p10)
    if ceil is not None:
        p90 = min(ceil, p90)
    return round(p10, 1), round(p50, 1), round(p90, 1)


# --------------------------------------------------------------------------- #
# Manifest: side table recording every row this script created (so reruns/purges are exact).
# --------------------------------------------------------------------------- #


class Manifest:
    """Side table recording every row this script created (so reruns/purges are exact)."""

    def __init__(self, platform_repo):
        self.repo = platform_repo
        with platform_repo.connection() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS demo_seed_manifest (
                entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, detail TEXT, seeded_at TEXT NOT NULL,
                PRIMARY KEY(entity_type, entity_id))""")

    def add(self, etype: str, eid: str, detail: str | None = None) -> None:
        with self.repo.connection() as c:
            c.execute("INSERT OR REPLACE INTO demo_seed_manifest VALUES(?,?,?,?)",
                      (etype, str(eid), detail, _iso(datetime.now(timezone.utc))))

    def ids(self, etype: str) -> list[str]:
        with self.repo.connection() as c:
            return [r[0] for r in c.execute("SELECT entity_id FROM demo_seed_manifest WHERE entity_type=?", (etype,))]

    def purge(self) -> dict[str, int]:
        """Delete exactly the rows recorded in the manifest, then clear the manifest."""
        removed: dict[str, int] = {}
        with self.repo.connection() as c:
            def run(label, sql, params_list):
                n = 0
                for p in params_list:
                    n += c.execute(sql, p).rowcount
                removed[label] = n

            ids = lambda t: [r[0] for r in c.execute("SELECT entity_id FROM demo_seed_manifest WHERE entity_type=?", (t,))]
            adv = ids("advisory")
            # Also remove review events / notifications created later by live actions on demo advisories
            # (e.g. approving a seeded advisory while rehearsing); they would otherwise block the delete (FK).
            run("review_events", "DELETE FROM review_events WHERE advisory_id=?", [(i,) for i in adv])
            run("advisory_notifications", "DELETE FROM notifications WHERE reference_type='advisory' AND reference_id=?", [(i,) for i in adv])
            run("advisory_localizations", "DELETE FROM advisory_localizations WHERE advisory_id=?", [(i,) for i in adv])
            run("advisories", "DELETE FROM advisories WHERE advisory_id=?", [(i,) for i in adv])
            run("risk_scores", "DELETE FROM risk_scores WHERE panchayat_id=? AND forecast_date=?",
                [tuple(i.split("|")) for i in ids("risk")])
            run("forecasts", "DELETE FROM forecasts WHERE panchayat_id=?", [(i,) for i in ids("forecast")])
            run("notifications", "DELETE FROM notifications WHERE notification_id=?", [(i,) for i in ids("notification")])
            run("grievances", "DELETE FROM grievances WHERE grievance_id=?", [(i,) for i in ids("grievance")])
            run("notices", "DELETE FROM notices WHERE notice_id=?", [(i,) for i in ids("notice")])
            removed["audit_logs"] = c.execute("DELETE FROM audit_logs WHERE details LIKE ?", (LABEL + "%",)).rowcount
            c.execute("DELETE FROM demo_seed_manifest")
        return removed


# --------------------------------------------------------------------------- #
# Seed helper functions
# --------------------------------------------------------------------------- #


def _ids(repo, table: str, id_column: str) -> list[str]:
    """Return list of IDs from a table, filtering out non-demo rows if needed."""
    with repo.connection() as c:
        rows = c.execute(f"SELECT {id_column} FROM {table}").fetchall()
    return [r[0] for r in rows]


def _run(db: Path, *args: str, code: str | None = None) -> subprocess.CompletedProcess:
    import subprocess
    env = {**os.environ, "AGROMET_DB_PATH": str(db), "PYTHONWARNINGS": "ignore"}
    cmd = [sys.executable, "-c", code] if code else [sys.executable, str(ROOT / "scripts" / "seed_demo_data.py"), "--anchor-date", "2026-10-04", *args]
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)


# --------------------------------------------------------------------------- #
# Main seed function
# --------------------------------------------------------------------------- #


def seed(args) -> int:
    if os.getenv("AGROMET_DEMO_SEED", "1") == "0" and not args.purge:
        print("AGROMET_DEMO_SEED=0 - demo seeding skipped.")
        return 0

    db_path = args.db or os.getenv("AGROMET_DB_PATH") or str(ROOT / "data" / "agromet.sqlite3")
    os.environ["AGROMET_DB_PATH"] = db_path  # must be set before importing agromet.main

    if args.with_accounts:
        import seed_demo_accounts
        seed_demo_accounts.seed()

    from agromet import main as app
    from agromet.advisory_engine import AdvisoryStatus, ForecastDay, TemplateLocalizer

    repo, platform_repo = app.repository, app.platform_repo
    manifest = Manifest(platform_repo)

    removed = manifest.purge()
    if any(removed.values()):
        print("Removed previous demo rows:", {k: v for k, v in removed.items() if v})
    if args.purge:
        print("Demo data purged.")
        return 0

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    anchor = date.fromisoformat(args.anchor_date) if args.anchor_date else date.today()
    users = {u: platform_repo.get_user_by_email(u) for u in
             ("admin@agromet.demo", "officer@agromet.demo", "kvk@agromet.demo", "citizen@agromet.demo")}
    uid = lambda email: (users.get(email) or {}).get("user_id")

    def audit(minutes_ago: float, action: str, resource: str, details: str, email: str | None = None, role: str = "system") -> None:
        platform_repo.log_audit(action, resource, "SUCCESS", user_id=uid(email) if email else None, role=role,
                                details=f"{LABEL} {details}", user_email=email,
                                created_at=_iso(now - timedelta(minutes=minutes_ago)))

    audit(240, "DEMO_DATA_INITIALIZED", "system/demo-seed",
          f"Synthetic demonstration dataset {SEED_VERSION} initialised ({len(PLAN)} Panchayats, anchor {anchor}).")
    for i, (email, role) in enumerate([("admin@agromet.demo", "admin"), ("officer@agromet.demo", "officer"),
                                       ("kvk@agromet.demo", "kvk"), ("citizen@agromet.demo", "citizen")]):
        audit(230 - 4 * i, "USER_LOGIN", f"auth/{role}", f"{role} session started (demo account).", email, role)

    # ---- forecasts, risk, advisories ------------------------------------------------- #
    summary: list[dict] = []
    all_advisories: dict[tuple[str, str], object] = {}
    skipped = 0
    for idx, plan in enumerate(PLAN):
        pid = plan["pid"]
        cfg = app.registry.get(pid)
        if cfg is None:
            print(f"  ! {pid} not in the Panchayat registry - skipped")
            skipped += 1
            continue
        existing = repo.get_forecast_payload(pid)
        if existing and not str(existing.get("model_version", "")).startswith("demo-synthetic") and not args.force:
            print(f"  ! {pid} {cfg.panchayat_id}: live forecast present - kept (use --force to overwrite)")
            skipped += 1
            continue
        scen = SCENARIOS[plan["scenario"]]
        shift = 0.5 * (idx % 3) if not plan["scenario"].startswith(("B_", "E_")) else 0.0
        forecast = build_forecast(app, cfg, scen, anchor, shift)
        app.forecast_store.save(forecast)
        manifest.add("forecast", pid)
        t_fc = 100 - idx
        audit(t_fc, "FORECAST_GENERATED", f"forecasts/{pid}", f"5-day synthetic scenario '{scen['label']}' stored for {cfg.panchayat_id}.", "officer@agromet.demo", "officer")

        risks = app._risk_from_forecast(forecast)
        for r in risks:
            manifest.add("risk", f"{pid}|{r['forecast_date']}")
        peak = max(risks, key=lambda r: r["score"])
        audit(t_fc - 0.5, "RISK_ASSESSMENT_COMPLETED", f"risk/{pid}",
              f"Peak risk {peak['level'].upper()} ({peak['score']}) on {peak['forecast_date']}.")

        advisory_days = [ForecastDay(
            valid_date=d.valid_date, tmax_c=d.tmax_c.p50, tmin_c=d.tmin_c.p50,
            relative_humidity_pct=d.relative_humidity_pct.p50, wind_speed_kmh=d.wind_speed_kmh.p50,
            rain_probability_next_6h=d.rainfall_probabilities.get("light", 0.02),
            rain_probability_15_6mm=d.rainfall_probabilities.get("heavy", 0.02)) for d in forecast.days]
        batch = app.advisory_engine.generate(pid, advisory_days)
        app.review_store.add_batch(batch)
        loc = TemplateLocalizer()
        for adv in batch.advisories:
            manifest.add("advisory", adv.advisory_id)
            all_advisories[(pid, adv.kind.value)] = adv
            all_advisories[(pid, adv.message_key)] = adv
            for lang in ("en", "te", "hi"):
                lz = loc.render(adv, lang)
                platform_repo.save_localization(adv.advisory_id, lang, lz.text, lz.source_metrics)
        audit(t_fc - 1, "ADVISORY_CREATED", f"advisories/{pid}",
              f"{len(batch.advisories)} rule-derived advisories generated for {cfg.panchayat_id}.")

        manifest.add("scenario", pid, json.dumps({"scenario": plan["scenario"], "label": scen["label"]}))
        sown = anchor + timedelta(days=int(plan["sown"].rstrip("d")))
        manifest.add("crop_plot", pid, json.dumps({
            "crop": plan["crop"], "stage": plan["stage"], "sowing_date": sown.isoformat(),
            "area_ha": plan["area_ha"], "irrigation": plan["irrigation"], "soil": plan["soil"],
            "data": "DEMO / SYNTHETIC DATA"}))
        summary.append(dict(plan=plan, cfg=cfg, peak=peak, advisories=[a.kind.value for a in batch.advisories]))

    # ---- "awaiting review" notifications exactly as refresh_panchayat() creates them -- #
    before_n = _ids(platform_repo, "notifications", "notification_id")
    for (pid, kind), adv in sorted({(k[0], k[1]): v for k, v in all_advisories.items() if k[1] == v.kind.value}.items()):
        platform_repo.create_notification(
            title="New advisory awaiting KVK review",
            body=f"{adv.kind.value} advisory generated for Panchayat {pid}. (Synthetic demo data)",
            category="advisory", severity="warning", reference_type="advisory", reference_id=adv.advisory_id)
    new_n = sorted(_ids(platform_repo, "notifications", "notification_id") - before_n)
    with platform_repo.connection() as c:
        for k, nid in enumerate(new_n):
            c.execute("UPDATE notifications SET created_at=? WHERE notification_id=?",
                      (_iso(now - timedelta(minutes=95 - 0.5 * k)), nid))
    for nid in new_n:  # manifest writes happen outside the open transaction (SQLite lock)
        manifest.add("notification", nid)

    # ---- KVK review queue demo decisions ------------------------------------------ #
    before_r = _ids(platform_repo, "review_events", "event_id")
    for (pid, kind), (action, notes) in DECISIONS.items():
        adv_key = (pid, kind)
        if adv_key in all_advisories:
            adv = all_advisories[adv_key]
            # The approve route writes a review_event; we pre-seed it here
            # so the demo story is complete on first load.
            # We check if it already exists to avoid FK issues.
            with platform_repo.connection() as c:
                existing = c.execute("SELECT event_id FROM review_events WHERE advisory_id=?", (adv.advisory_id,)).fetchone()
            if not existing:
                platform_repo.update_grievance_status  # just to test, not used here
                # Insert review event directly
                with platform_repo.connection() as c:
                    c.execute(
                        "INSERT INTO review_events (advisory_id, reviewer_id, action, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                        (adv.advisory_id, REVIEWER, action, notes, _iso(now)))
    new_r = sorted(_ids(platform_repo, "review_events", "event_id") - before_r)
    for eid in new_r:
        manifest.add("review_event", eid)

    # ---- Notices --------------------------------------------------------------- #
    before_obs = _ids(platform_repo, "notices", "notice_id")
    notice_texts = [
        "High rainfall alert for Nalgonda district.",
        "Rice disease risk increased in Demo Panchayat.",
        "KVK advisory approved for the selected crop.",
        "Heat stress warning generated for cotton fields.",
    ]
    for i, text in enumerate(notice_texts):
        nid = f"NOTICE-{i+1:03d}"
        platform_repo.create_notification(
            title="Agromet Advisory",
            body=text,
            category="notice", severity="info",
            reference_type="system", reference_id=nid)
        with platform_repo.connection() as c:
            c.execute("INSERT OR IGNORE INTO notices VALUES (?,?,?,?,?,?)",
                      (nid, text, text, "info", _iso(now), _iso(now)))
    new_obs = sorted(_ids(platform_repo, "notices", "notice_id") - before_obs)
    for oid in new_obs:
        manifest.add("notice", oid)

    # ---- Summary --------------------------------------------------------------- #
    print(f"\nDemo seeding complete: {len(PLAN)} Panchayats seeded.")
    print(f"  Forecasts: {sum(1 for _ in summary)}")
    print(f"  Risks: {len(platform_repo.ids('risk'))}")
    print(f"  Advisories: {sum(len(b.advisories) for b in advisories_used)}")
    print(f"  Reviews: {len(platform_repo.ids('review_event'))}")
    print(f"  Notifications: {len(platform_repo.ids('notification'))}")
    print(f"  Notices: {len(platform_repo.ids('notice'))}")
    print(f"  Anchored at: {anchor}")
    return 0


# --------------------------------------------------------------------------- #
# Forecast builder
# --------------------------------------------------------------------------- #


def build_forecast(app, cfg, scen: dict, anchor: date, shift: float = 0.0):
    """Build a PanchayatForecastResponse from a scenario table.

    `shift` is a small deterministic temperature offset so Panchayats that share a
    scenario do not show identical numbers. Elevation feeds the FAO-56 ET0 value.
    """
    from agromet.advisory_engine import ET0Inputs, calculate_et0_fao56

    days = []
    for i in range(5):
        tmax, tmin = scen["tmax"][i] + shift, scen["tmin"][i] + shift
        rh, wind = float(scen["rh"][i]), float(scen["wind"][i])
        light, heavy, vheavy = scen["light"][i], scen["heavy"][i], scen["vheavy"][i]
        probs = {
            "light": float(light),
            "moderate": round((light + heavy) / 2.0, 3),
            "heavy": float(heavy),
            "very_heavy": float(vheavy),
        }
        wind2m = max(0.0, wind / 3.6 * 4.87 / math.log(67.8 * 10.0 - 5.42))
        et0 = calculate_et0_fao56(ET0Inputs(
            tmax_c=tmax, tmin_c=tmin, relative_humidity_pct=min(100.0, rh), wind_speed_2m_ms=wind2m,
            net_radiation_mj_m2_day=scen["net_rad"], elevation_m=float(cfg.elevation_m or 530.0)))
        t10, t50, t90 = _q(tmax, 1.4, 1.6)
        n10, n50, n90 = _q(tmin, 1.0, 1.2)
        h10, h50, h90 = _q(rh, 6.0, 4.0, floor=0.0, ceil=100.0)
        w10, w50, w90 = _q(wind, wind * 0.4, wind * 0.45, floor=0.0)
        Q = app.QuantileResponse
        days.append(app.ForecastDayResponse(
            valid_date=anchor + timedelta(days=i),
            tmax_c=Q(p10=t10, p50=t50, p90=t90), tmin_c=Q(p10=n10, p50=n50, p90=n90),
            relative_humidity_pct=Q(p10=h10, p50=h50, p90=h90),
            wind_speed_kmh=Q(p10=w10, p50=w50, p90=w90),
            rain_mm=float(scen["rain"][i]), rainfall_probabilities=probs, et0_mm_day=round(et0, 2)))
    return app.PanchayatForecastResponse(
        panchayat_id=cfg.panchayat_id, generated_at=anchor, model_version=MODEL_VERSION, days=days)


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed deterministic SYNTHETIC demonstration dataset.")
    parser.add_argument("--db", type=str, help="Path to SQLite database (overrides AGROMET_DB_PATH)")
    parser.add_argument("--with-accounts", action="store_true",
                        help="Also (re)create the 4 demo logins")
    parser.add_argument("--purge", action="store_true", help="Remove demo data only, keep accounts")
    parser.add_argument("--force", action="store_true", help="Overwrite existing live forecasts")
    parser.add_argument("--anchor-date", type=str, default=None,
                        help="Anchor date for forecasts (default: today, YYYY-MM-DD)")
    args = parser.parse_args()
    return seed(args)


if __name__ == "__main__":
    sys.exit(main() or 0)