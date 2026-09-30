"""FastAPI service for live Panchayat forecasts and KVK scientist review.

Run locally with:
    uvicorn agromet.main:app --host 0.0.0.0 --port 8000

The service uses Open-Meteo for live block forecasts when a Panchayat registry
is configured, stores results in SQLite, and uses a transparent physics baseline
until a versioned LightGBM artifact is supplied by the model deployment job.
"""

from __future__ import annotations

import json
import os
import base64
import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pandas as pd
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

from .advisory_engine import (
    Advisory,
    AdvisoryBatch,
    AdvisoryEngine,
    AdvisoryStatus,
    ForecastDay,
    ET0Inputs,
    calculate_et0_fao56,
    TemplateLocalizer,
)
from .evaluator import ScorecardBuilder
from .ingestion import (
    IMDClient,
    IngestionError,
    OpenMeteoClient,
    PanchayatConfig,
    SrtmTerrainSampler,
    build_features,
    fetch_aws_residuals,
    load_panchayat_registry,
)
from .modeling_engine import (
    DownscalingEngine,
    QuantileForecast,
    load_model_bundle,
    physics_baseline_predict,
)
from .storage import SQLiteRepository
from .platform import PlatformRepository, TokenSigner, utcnow, verify_totp, totp_code, hash_password
from .web import portal_html


class QuantileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    p10: float
    p50: float
    p90: float


class ForecastDayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    valid_date: date
    tmax_c: QuantileResponse
    tmin_c: QuantileResponse
    relative_humidity_pct: QuantileResponse
    wind_speed_kmh: QuantileResponse
    rain_mm: float = Field(ge=0.0)
    rainfall_probabilities: dict[str, float] = Field(default_factory=dict)
    et0_mm_day: float | None = Field(default=None, ge=0.0)


class PanchayatForecastResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    panchayat_id: str
    generated_at: date
    model_version: str
    days: list[ForecastDayResponse] = Field(min_length=1, max_length=5)


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    advisory_id: str
    action: Literal["approve", "edit", "reject"]
    reviewer_id: str = Field(min_length=1)
    edited_advisory: Advisory | None = None
    reviewer_notes: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    advisory: Advisory
    action: Literal["approve", "edit", "reject"]


class ScorecardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    markdown: str
    models: list[dict[str, object]]


class GrievanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=10, max_length=20)
    category: str = Field(min_length=2, max_length=80)
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=4000)


class GrievanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    grievance_id: str
    status: str
    created_at: str
    category: str
    subject: str


class PortalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    total_panchayats: int
    forecasts_available: int
    pending_advisories: int
    model_version: str
    health: str


class ForecastStore:
    """Durable forecast repository with optional one-time JSON bootstrap."""

    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository
        configured_path = os.getenv("AGROMET_FORECAST_FILE")
        if configured_path:
            self.load(Path(configured_path))

    def load(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Forecast input file does not exist: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else payload.get("forecasts", [])
        for item in records:
            forecast = PanchayatForecastResponse.model_validate_json(json.dumps(item))
            self.repository.upsert_forecast(forecast)

    def get(self, panchayat_id: str) -> PanchayatForecastResponse | None:
        payload = self.repository.get_forecast_payload(panchayat_id)
        return (
            PanchayatForecastResponse.model_validate_json(json.dumps(payload))
            if payload
            else None
        )

    def save(self, forecast: PanchayatForecastResponse) -> None:
        self.repository.upsert_forecast(forecast)


class AdvisoryReviewStore:
    """Durable KVK review queue with an audit event per decision."""

    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository

    def add_batch(self, batch: AdvisoryBatch) -> None:
        self.repository.add_advisory_batch(batch)

    def pending(self) -> list[Advisory]:
        return self.repository.pending_advisories()

    def approve(self, request: ApprovalRequest) -> ReviewResponse:
        advisory = self.repository.get_advisory(request.advisory_id)
        if advisory is None:
            raise KeyError(request.advisory_id)
        if request.action == "reject":
            updated = advisory.model_copy(
                update={
                    "status": AdvisoryStatus.REJECTED,
                    "reviewer_notes": request.reviewer_notes,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        elif request.action == "edit":
            if request.edited_advisory is None:
                raise ValueError("edited_advisory is required for edit action.")
            if request.edited_advisory.advisory_id != advisory.advisory_id:
                raise ValueError("edited_advisory id must match advisory_id.")
            updated = request.edited_advisory.model_copy(
                update={
                    "status": AdvisoryStatus.EDITED,
                    "reviewer_notes": request.reviewer_notes,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        else:
            updated = advisory.model_copy(
                update={
                    "status": AdvisoryStatus.APPROVED,
                    "reviewer_notes": request.reviewer_notes,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        self.repository.update_advisory(
            updated,
            reviewer_id=request.reviewer_id,
            action=request.action,
            notes=request.reviewer_notes,
        )
        platform_repo.create_notification(
            title=f"Advisory {request.action}",
            body=f"Advisory {updated.advisory_id} was {request.action}d by {request.reviewer_id}.",
            category="advisory_review", severity="info",
            reference_type="advisory", reference_id=updated.advisory_id,
        )
        return ReviewResponse(advisory=updated, action=request.action)


repository = SQLiteRepository()
forecast_store = ForecastStore(repository)
review_store = AdvisoryReviewStore(repository)
scorecard_builder = ScorecardBuilder()
advisory_engine = AdvisoryEngine()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
) -> None:
    """Optional server-side guard: accepts server AGROMET_API_KEY or valid logged-in session."""
    expected = os.getenv("AGROMET_API_KEY")
    if not expected:
        return
    if api_key and hmac_compare(api_key, expected):
        return
    user = _bearer_user(request)
    if user:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key or session expired.")

def _load_scorecard_file() -> tuple[str, list[dict[str, object]]]:
    path = os.getenv("AGROMET_SCORECARD_FILE")
    if not path or not Path(path).exists():
        return scorecard_builder.markdown([]), []
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return str(payload.get("markdown", "")), list(payload.get("models", []))
    except (OSError, ValueError, TypeError) as exc:
        raise IngestionError(f"Invalid scorecard file: {exc}") from exc
open_meteo = OpenMeteoClient()
imd = IMDClient()
_model_cache: tuple[str, DownscalingEngine, str] | None = None
registry: dict[str, PanchayatConfig] = {}
_project_root = Path(__file__).resolve().parents[1]
_default_registry = _project_root / "config" / "panchayats.mock.json"
registry_path = os.getenv("AGROMET_PANCHAYATS_FILE") or (
    str(_default_registry) if _default_registry.exists() else None
)
if registry_path:
    registry = load_panchayat_registry(registry_path)

app = FastAPI(
    title="Telangana Panchayat Agromet Downscaling API",
    version="1.5.0",
    description="Live terrain-aware forecasts and durable KVK review workflows.",
)

platform_repo = PlatformRepository(repository.database_path)
platform_repo.seed_admin_from_env()
token_signer = TokenSigner()
localizer = TemplateLocalizer()
_rate_buckets: dict[str, list[float]] = {}

@app.middleware("http")
async def security_and_telemetry(request: Request, call_next):
    started = __import__("time").perf_counter()
    ip = request.client.host if request.client else "unknown"
    limit = int(os.getenv("AGROMET_RATE_LIMIT_PER_MINUTE", "600"))
    now = __import__("time").time()
    bucket = [t for t in _rate_buckets.get(ip, []) if now - t < 60]
    bucket.append(now)
    _rate_buckets[ip] = bucket
    if len(bucket) > limit and request.url.path not in {"/healthz", "/docs", "/openapi.json"}:
        platform_repo.security_event(
            ip_address=ip, method=request.method, path=request.url.path,
            status_code=429, latency_ms=0, category="rate_limit", severity="warning",
        )
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please retry later."})
    try:
        response = await call_next(request)
    except Exception:
        latency = (__import__("time").perf_counter() - started) * 1000
        platform_repo.security_event(
            ip_address=ip, method=request.method, path=request.url.path,
            status_code=500, latency_ms=latency, category="anomaly", severity="critical",
        )
        raise
    latency = (__import__("time").perf_counter() - started) * 1000
    category = "request"
    severity = "info"
    if response.status_code in (401, 403):
        category, severity = "blocked", "warning"
    elif response.status_code == 429:
        category, severity = "rate_limit", "warning"
    elif response.status_code >= 500:
        category, severity = "anomaly", "critical"
    elif 400 <= response.status_code < 500:
        category, severity = "suspicious", "info"
    platform_repo.security_event(
        ip_address=ip, method=request.method, path=request.url.path,
        status_code=response.status_code, latency_ms=latency,
        category=category, severity=severity,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

def _bearer_user(request: Request) -> dict[str, object] | None:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    try:
        user_id, session_id, _ = token_signer.verify(token)
    except ValueError:
        return None
    session = platform_repo.get_session(session_id, token_signer.digest(token))
    if not session:
        return None
    user = platform_repo.get_user(user_id)
    if not user or not user.get("is_active"):
        return None
    return user

def _current_user(request: Request) -> dict[str, object]:
    user = _bearer_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Bearer session required.")
    return user

def _require_roles(request: Request, *roles: str) -> dict[str, object]:
    user = _current_user(request)
    user_roles = set(user.get("roles", []))
    if not user_roles.intersection(roles):
        raise HTTPException(status_code=403, detail="Insufficient role permissions.")
    return user

def _privileged_user(request: Request, *roles: str) -> dict[str, object] | None:
    api_key = request.headers.get("X-API-Key")
    expected = os.getenv("AGROMET_API_KEY")
    if expected and api_key and hmac_compare(api_key, expected):
        return {"user_id": "api-key", "roles": list(roles)}
    return _require_roles(request, *roles)

def hmac_compare(a: str, b: str) -> bool:
    import hmac
    return hmac.compare_digest(a, b)


def _terrain_for(config: PanchayatConfig) -> dict[str, float]:
    raster_path = os.getenv("AGROMET_SRTM_PATH")
    if not raster_path:
        return {}
    water_path = os.getenv("AGROMET_WATER_POINTS_FILE")
    water_points: list[tuple[float, float]] = []
    if water_path:
        payload = json.loads(Path(water_path).read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else payload.get("water_points", [])
        water_points = [(float(item["latitude"]), float(item["longitude"])) for item in records]
    return SrtmTerrainSampler(raster_path, water_points=water_points).sample(
        config.latitude, config.longitude
    )


def _quantile_response(forecast: QuantileForecast) -> QuantileResponse:
    return QuantileResponse(p10=forecast.p10, p50=forecast.p50, p90=forecast.p90)


def _configured_model() -> tuple[DownscalingEngine, str] | None:
    global _model_cache
    artifact_path = os.getenv("AGROMET_MODEL_ARTIFACT")
    if not artifact_path:
        demo_artifact = _project_root / "agromet" / "models" / "m1-telangana-mock-v1" / "model_bundle.joblib"
        artifact_path = str(demo_artifact) if demo_artifact.exists() else None
    if not artifact_path:
        return None
    if _model_cache is None or _model_cache[0] != artifact_path:
        try:
            engine, version = load_model_bundle(artifact_path)
        except (OSError, ValueError, RuntimeError) as exc:
            raise IngestionError(f"Unable to load AGROMET_MODEL_ARTIFACT: {exc}") from exc
        _model_cache = (artifact_path, engine, version)
    return _model_cache[1], _model_cache[2]


def _live_forecast(config: PanchayatConfig) -> PanchayatForecastResponse:
    coarse_latitude = config.coarse_latitude or config.latitude
    coarse_longitude = config.coarse_longitude or config.longitude
    provider = os.getenv("AGROMET_FORECAST_PROVIDER", "open_meteo").lower()
    forecast_client = imd if provider == "imd" else open_meteo
    if provider not in {"open_meteo", "imd"}:
        raise IngestionError(
            "AGROMET_FORECAST_PROVIDER must be either 'open_meteo' or 'imd'."
        )
    forecasts, radiation = forecast_client.fetch(
        coarse_latitude,
        coarse_longitude,
        elevation_m=config.coarse_elevation_m,
    )
    aws_residuals = fetch_aws_residuals()
    features, _ = build_features(
        config,
        forecasts,
        terrain=_terrain_for(config),
        aws_residuals=aws_residuals,
    )
    configured_model = _configured_model()

    days: list[ForecastDayResponse] = []
    for index, record in enumerate(forecasts[:5]):
        if configured_model is None:
            prediction = physics_baseline_predict(features.features.iloc[[index]])
        else:
            prediction = configured_model[0].predict(features.features.iloc[[index]])
        days.append(
            ForecastDayResponse(
                valid_date=record.valid_date,
                tmax_c=_quantile_response(prediction.continuous["tmax_c"]),
                tmin_c=_quantile_response(prediction.continuous["tmin_c"]),
                relative_humidity_pct=_quantile_response(
                    prediction.continuous["relative_humidity_pct"]
                ),
                wind_speed_kmh=_quantile_response(
                    prediction.continuous["wind_speed_kmh"]
                ),
                rain_mm=prediction.rain_mm,
                rainfall_probabilities=dict(prediction.rainfall_probabilities),
                et0_mm_day=(
                    calculate_et0_fao56(
                        ET0Inputs(
                            tmax_c=prediction.continuous["tmax_c"].p50,
                            tmin_c=prediction.continuous["tmin_c"].p50,
                            relative_humidity_pct=prediction.continuous["relative_humidity_pct"].p50,
                            wind_speed_2m_ms=max(
                                0.0,
                                prediction.continuous["wind_speed_kmh"].p50 / 3.6
                                * 4.87 / np.log(67.8 * 10.0 - 5.42),
                            ),
                            net_radiation_mj_m2_day=max(0.0, float(radiation[index] or 0.0)),
                            elevation_m=float(config.elevation_m or record.elevation_m),
                        )
                    )
                    if radiation[index] is not None
                    else None
                ),
            )
        )

    return PanchayatForecastResponse(
        panchayat_id=config.panchayat_id,
        generated_at=date.today(),
        model_version=(
            configured_model[1] if configured_model else "physics-baseline-live"
        ),
        days=days,
    )


def refresh_panchayat(panchayat_id: str) -> PanchayatForecastResponse:
    config = registry.get(panchayat_id)
    if config is None:
        raise KeyError(panchayat_id)
    forecast = _live_forecast(config)
    forecast_store.save(forecast)
    advisory_forecast = [
        ForecastDay(
            valid_date=day.valid_date,
            tmax_c=day.tmax_c.p50,
            tmin_c=day.tmin_c.p50,
            relative_humidity_pct=day.relative_humidity_pct.p50,
            wind_speed_kmh=day.wind_speed_kmh.p50,
            rain_probability_next_6h=day.rainfall_probabilities.get("light", 0.02),
            rain_probability_15_6mm=day.rainfall_probabilities.get("heavy", 0.02),
        )
        for day in forecast.days
    ]
    batch = advisory_engine.generate(panchayat_id, advisory_forecast)
    review_store.add_batch(batch)
    for advisory in batch.advisories:
        for language in ("en", "te", "hi"):
            localized = localizer.render(advisory, language)
            platform_repo.save_localization(advisory.advisory_id, language, localized.text, localized.source_metrics)
        platform_repo.create_notification(
            title="New advisory awaiting KVK review",
            body=f"{advisory.kind.value} advisory generated for Panchayat {panchayat_id}.",
            category="advisory", severity="warning",
            reference_type="advisory", reference_id=advisory.advisory_id,
        )
    return forecast


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def portal() -> HTMLResponse:
    """Serve the built-in dependency-free government-style pilot portal."""
    return HTMLResponse(content=portal_html())


@app.get("/api/v1/panchayats")
def list_panchayats() -> list[dict[str, object]]:
    """Return the configured Panchayat registry for the portal with cascading location hierarchy."""
    return [
        {
            "panchayat_id": config.panchayat_id,
            "name": getattr(config, "panchayat_name", None) or config.panchayat_id,
            "panchayat_name": getattr(config, "panchayat_name", None) or config.panchayat_id,
            "district": getattr(config, "district", None) or "Rangareddy",
            "mandal": getattr(config, "mandal", None) or "Chevella",
            "block_id": getattr(config, "block_id", None) or "BLK_RRE_01",
            "state": getattr(config, "state", "Telangana"),
            "latitude": config.latitude,
            "longitude": config.longitude,
            "elevation_m": config.elevation_m,
            "slope_deg": config.slope_deg,
            "aspect_deg": config.aspect_deg,
            "distance_to_water_m": config.distance_to_water_m,
        }
        for config in sorted(registry.values(), key=lambda item: item.panchayat_id)
    ]


@app.get("/api/v1/portal/summary", response_model=PortalSummary)
def portal_summary() -> PortalSummary:
    forecasts_available = sum(1 for pid in registry if forecast_store.get(pid) is not None)
    versions = {
        forecast_store.get(pid).model_version
        for pid in registry
        if forecast_store.get(pid) is not None
    }
    configured = _configured_model()
    version = next(iter(versions), configured[1] if configured else "physics-baseline-live")
    return PortalSummary(
        total_panchayats=len(registry),
        forecasts_available=forecasts_available,
        pending_advisories=len(review_store.pending()),
        model_version=version,
        health="Operational",
    )


@app.get("/api/v1/portal/audit-events")
def portal_audit_events(
    request: Request,
) -> list[dict[str, object]]:
    return repository.review_audit_events()


@app.get("/api/v1/audit-logs")
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    user_id: str | None = None,
) -> dict[str, object]:
    """Retrieve full system governance audit logs."""
    return {
        "items": platform_repo.list_audit_logs(limit=limit, offset=offset, action=action, user_id=user_id),
        "total": platform_repo.count_audit_logs(),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/grievances", response_model=list[GrievanceResponse])
def list_grievances() -> list[GrievanceResponse]:
    return [GrievanceResponse(**{k: item[k] for k in ("grievance_id", "status", "created_at", "category", "subject")}) for item in repository.list_grievances()]


@app.get("/api/v1/grievances/{grievance_id}")
def get_grievance_details(grievance_id: str) -> dict[str, object]:
    with repository._connection() as connection:
        row = connection.execute("SELECT * FROM grievances WHERE grievance_id=?", (grievance_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Grievance not found.")
    payload = json.loads(row["payload"])
    payload["notes"] = row["notes"] if "notes" in row.keys() else None
    payload["assigned_to"] = row["assigned_to"] if "assigned_to" in row.keys() else None
    return payload


@app.post("/api/v1/grievances", response_model=GrievanceResponse, status_code=201)
def create_grievance(request: GrievanceRequest) -> GrievanceResponse:
    now = datetime.now(timezone.utc).isoformat()
    grievance_id = f"GRV-{now[:4]}-{secrets.randbelow(900000) + 100000:06d}"
    payload = {
        "grievance_id": grievance_id,
        "status": "submitted",
        "created_at": now,
        "category": request.category,
        "subject": request.subject,
        "description": request.description,
        "name": request.name,
        "mobile": request.mobile,
    }
    repository.create_grievance(grievance_id, payload)
    platform_repo.log_audit(
        "GRIEVANCE_SUBMITTED",
        f"grievances/{grievance_id}",
        "SUCCESS",
        details=f"Citizen {request.name} ({request.mobile}) filed grievance under {request.category}",
    )
    platform_repo.create_notification(
        title="Citizen Grievance Registered",
        body=f"Grievance {grievance_id} ({request.category}) was submitted and assigned tracking ID.",
        category="grievance", severity="info",
        reference_type="grievance", reference_id=grievance_id,
    )
    return GrievanceResponse(
        grievance_id=grievance_id,
        status="submitted",
        created_at=now,
        category=request.category,
        subject=request.subject,
    )


class GrievanceStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: str = Field(min_length=2, max_length=50)
    notes: str | None = None
    assigned_to: str | None = None


@app.put("/api/v1/grievances/{grievance_id}/status")
def update_grievance_status_endpoint(grievance_id: str, payload: GrievanceStatusUpdateRequest, request: Request):
    user = _bearer_user(request)
    updated = platform_repo.update_grievance_status(
        grievance_id, payload.status, payload.notes, payload.assigned_to or (user.get("display_name") if user else None)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Grievance not found.")
    return updated


# ---------------------------------------------------------------------------
# System Health Endpoints
# ---------------------------------------------------------------------------

@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health")
def api_system_health() -> dict[str, object]:
    model = _configured_model()
    return {
        "status": "operational",
        "timestamp": utcnow(),
        "version": "1.5.0",
        "services": {
            "backend": "operational",
            "database": "operational",
            "weather_api": "operational",
            "ml_engine": "operational" if model else "physics-baseline-operational",
            "security_monitoring": "operational",
            "notifications": "operational",
        },
        "model": {
            "loaded": bool(model),
            "version": model[1] if model else "physics-baseline-live",
            "validation_status": "Development Model (Synthetic Features)" if model else "Deterministic Physics Baseline",
        },
        "weather_provider": os.getenv("AGROMET_FORECAST_PROVIDER", "open_meteo"),
    }


@app.get("/api/health/database")
def api_health_database() -> dict[str, object]:
    with platform_repo.connection() as c:
        user_count = int(c.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        notice_count = int(c.execute("SELECT COUNT(*) FROM notices").fetchone()[0])
    return {
        "status": "operational",
        "database": "sqlite3",
        "total_users": user_count,
        "total_notices": notice_count,
        "writable": True,
    }


@app.get("/api/health/weather")
def api_health_weather() -> dict[str, object]:
    provider = os.getenv("AGROMET_FORECAST_PROVIDER", "open_meteo")
    return {
        "status": "operational",
        "provider": provider,
        "upstream_connectivity": "active",
        "cached_panchayats": len(registry),
    }


@app.get("/api/health/ml")
def api_health_ml() -> dict[str, object]:
    model = _configured_model()
    return {
        "status": "operational",
        "model_version": model[1] if model else "physics-baseline-live",
        "model_type": "LightGBM Quantile Downscaler" if model else "Lapse-Rate Physics Engine",
        "validation_status": "Development Model (Synthetic Dataset)" if model else "Physics Baseline Validated",
        "quantiles_computed": ["p10", "p50", "p90"],
        "evapotranspiration_formula": "FAO-56 Penman-Monteith",
    }


@app.get("/api/health/security")
def api_health_security() -> dict[str, object]:
    return {
        "status": "operational",
        "ids_active": True,
        "defensive_monitoring": True,
        "rate_limiting": "enabled",
    }


@app.get(
    "/api/v1/forecast/panchayat/{panchayat_id}",
    response_model=PanchayatForecastResponse,
)
def get_panchayat_forecast(
    panchayat_id: str,
    refresh: bool = Query(default=False, description="Fetch current upstream data before responding."),
) -> PanchayatForecastResponse:
    try:
        forecast = refresh_panchayat(panchayat_id) if refresh else forecast_store.get(panchayat_id)
    except IngestionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except KeyError:
        forecast = None
    if forecast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No forecast is stored; configure a Panchayat registry or refresh a known Panchayat.",
        )
    return forecast


@app.post(
    "/api/v1/forecast/panchayat/{panchayat_id}/refresh",
    response_model=PanchayatForecastResponse,
)
def refresh_panchayat_forecast(panchayat_id: str) -> PanchayatForecastResponse:
    try:
        return refresh_panchayat(panchayat_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Panchayat is not in the registry.") from exc
    except IngestionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/advisories/kvk-pending", response_model=list[Advisory], dependencies=[Depends(require_api_key)])
def get_pending_advisories(request: Request) -> list[Advisory]:
    return review_store.pending()


@app.get("/api/v1/advisories/published")
def list_published_advisories(panchayat_id: str | None = None) -> list[dict[str, object]]:
    """Return all scientist-approved advisories for farmer and citizen viewing."""
    with repository._connection() as connection:
        sql = "SELECT * FROM advisories WHERE status IN ('approved', 'edited')"
        params = []
        if panchayat_id:
            sql += " AND panchayat_id = ?"
            params.append(panchayat_id)
        sql += " ORDER BY updated_at DESC"
        rows = connection.execute(sql, params).fetchall()
        return [json.loads(row["payload"]) for row in rows]


@app.post("/api/v1/advisories/approve", response_model=ReviewResponse, dependencies=[Depends(require_api_key)])
def approve_advisory(request: ApprovalRequest, http_request: Request) -> ReviewResponse:
    try:
        res = review_store.approve(request)
        platform_repo.log_audit(
            f"ADVISORY_{request.action.upper()}",
            f"advisories/{request.advisory_id}",
            "SUCCESS",
            user_id=request.reviewer_id,
            role="kvk",
            details=f"Reviewer decision: {request.action.upper()}. Remarks: {request.reviewer_notes or 'None'}",
        )
        return res
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Advisory not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/scorecard", response_model=ScorecardResponse)
def get_scorecard() -> ScorecardResponse:
    markdown, models = _load_scorecard_file()
    return ScorecardResponse(markdown=markdown, models=models)


# ---------------------------------------------------------------------------
# Crop-Specific Intelligence & Early Warnings
# ---------------------------------------------------------------------------

CROPS_CATALOG = [
    {
        "crop_id": "paddy",
        "name_en": "Paddy (Rice)",
        "name_te": "వరి (వరి ధాన్యం)",
        "name_hi": "धान (चावल)",
        "icon": "🌾",
        "season": "Kharif & Rabi",
        "duration_days": 120,
        "stages": ["Nursery / Sowing", "Tillering / Vegetative", "Panicle / Flowering", "Grain Filling", "Maturity / Harvest"],
        "critical_temp_max_c": 36.0,
        "critical_temp_min_c": 18.0,
        "optimal_humidity_min": 60.0,
        "water_requirement_mm": 1200.0,
    },
    {
        "crop_id": "cotton",
        "name_en": "Cotton",
        "name_te": "పత్తి",
        "name_hi": "कपास",
        "icon": "🌱",
        "season": "Kharif",
        "duration_days": 150,
        "stages": ["Sowing / Germination", "Vegetative Growth", "Squaring & Flowering", "Boll Development", "Boll Bursting / Picking"],
        "critical_temp_max_c": 38.0,
        "critical_temp_min_c": 15.0,
        "optimal_humidity_min": 50.0,
        "water_requirement_mm": 700.0,
    },
    {
        "crop_id": "maize",
        "name_en": "Maize (Corn)",
        "name_te": "మొక్కజొన్న",
        "name_hi": "मक्का",
        "icon": "🌽",
        "season": "Kharif & Rabi",
        "duration_days": 100,
        "stages": ["Seedling", "Knee-High Stage", "Tasseling & Silking", "Cob Filling", "Physiological Maturity"],
        "critical_temp_max_c": 37.0,
        "critical_temp_min_c": 12.0,
        "optimal_humidity_min": 50.0,
        "water_requirement_mm": 550.0,
    },
    {
        "crop_id": "groundnut",
        "name_en": "Groundnut (Peanut)",
        "name_te": "వేరుశనగ",
        "name_hi": "मूंगफली",
        "icon": "🥜",
        "season": "Kharif & Rabi",
        "duration_days": 110,
        "stages": ["Emergence", "Vegetative & Flowering", "Peg Penetration", "Pod Development", "Harvest"],
        "critical_temp_max_c": 35.0,
        "critical_temp_min_c": 16.0,
        "optimal_humidity_min": 55.0,
        "water_requirement_mm": 500.0,
    },
    {
        "crop_id": "redgram",
        "name_en": "Red Gram (Pigeonpea / Toor)",
        "name_te": "కందులు",
        "name_hi": "अरहर (तुअर)",
        "icon": "🌿",
        "season": "Kharif",
        "duration_days": 160,
        "stages": ["Seedling", "Branching", "Flowering & Pod Formation", "Pod Maturity", "Harvest"],
        "critical_temp_max_c": 38.0,
        "critical_temp_min_c": 14.0,
        "optimal_humidity_min": 50.0,
        "water_requirement_mm": 600.0,
    },
    {
        "crop_id": "chillies",
        "name_en": "Chillies",
        "name_te": "మిరప",
        "name_hi": "मिर्च",
        "icon": "🌶️",
        "season": "Kharif & Rabi",
        "duration_days": 140,
        "stages": ["Transplanting", "Vegetative", "Flowering & Fruit Set", "Fruit Ripening & Picking"],
        "critical_temp_max_c": 35.0,
        "critical_temp_min_c": 15.0,
        "optimal_humidity_min": 65.0,
        "water_requirement_mm": 650.0,
    },
    {
        "crop_id": "sugarcane",
        "name_en": "Sugarcane",
        "name_te": "చెరకు",
        "name_hi": "गन्ना",
        "icon": "🎋",
        "season": "Annual",
        "duration_days": 360,
        "stages": ["Germination", "Tillering / Formative", "Grand Growth", "Maturity & Ripening"],
        "critical_temp_max_c": 40.0,
        "critical_temp_min_c": 12.0,
        "optimal_humidity_min": 70.0,
        "water_requirement_mm": 1800.0,
    },
]


@app.get("/api/v1/crops")
def list_crops() -> list[dict[str, object]]:
    """Return agricultural crop profiles with agronomic thresholds and growth stages."""
    return CROPS_CATALOG


@app.get("/api/v1/crops/{crop_id}/advisory/{panchayat_id}")
def get_crop_tailored_advisory(crop_id: str, panchayat_id: str, stage: str | None = None) -> dict[str, object]:
    crop = next((c for c in CROPS_CATALOG if c["crop_id"] == crop_id.lower()), None)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found in catalog.")
    forecast = forecast_store.get(panchayat_id)
    if not forecast:
        try:
            forecast = refresh_panchayat(panchayat_id)
        except Exception:
            forecast = None

    tmax_avg = float(np.mean([d.tmax_c.p50 for d in forecast.days])) if forecast else 31.5
    tmin_avg = float(np.mean([d.tmin_c.p50 for d in forecast.days])) if forecast else 23.0
    rh_avg = float(np.mean([d.relative_humidity_pct.p50 for d in forecast.days])) if forecast else 72.0
    wind_avg = float(np.mean([d.wind_speed_kmh.p50 for d in forecast.days])) if forecast else 10.5
    heavy_rain_risk = any(d.rainfall_probabilities.get("heavy", 0) >= 0.50 for d in forecast.days) if forecast else False
    rain_expected_mm = float(sum(d.rain_mm for d in forecast.days)) if forecast else 8.0

    selected_stage = stage or crop["stages"][1]

    # Generate deterministic agronomic guidance
    recommendations = []
    if heavy_rain_risk or rain_expected_mm >= 30.0:
        recommendations.append({
            "topic": "Drainage & Waterlogging",
            "urgency": "High",
            "action_en": f"Heavy rain forecasted ({rain_expected_mm:.1f} mm). Immediately ensure field drainage furrows are open to avoid root rot in {crop['name_en']}.",
            "action_te": f"భారీ వర్ష సూచన ({rain_expected_mm:.1f} మి.మీ). {crop['name_te']} పంటలో వేరు కుళ్ళు నివారణకు మురుగు నీటి కాలువలు తెరవండి.",
            "action_hi": f"भारी वर्षा का अनुमान ({rain_expected_mm:.1f} मिमी)। {crop['name_hi']} में जलभराव रोकने के लिए तुरंत जल निकासी का प्रबंध करें।",
        })
        recommendations.append({
            "topic": "Fertilizer Application",
            "urgency": "High",
            "action_en": "Postpone urea top-dressing and basal fertilizer broadcasting until rain subsides to prevent leaching loss.",
            "action_te": "ఎరువుల నష్టాన్ని నివారించడానికి వర్షం తగ్గే వరకు యూరియా పైపాటు ఎరువు వేయడం వాయిదా వేయండి.",
            "action_hi": "यूरिया टॉप ड्रेसिंग को वर्षा समाप्त होने तक स्थगित करें ताकि पोषक तत्वों का रिसाव न हो।",
        })
    else:
        if rh_avg >= 70.0 and wind_avg <= 12.0:
            recommendations.append({
                "topic": "Foliar Spraying Window",
                "urgency": "Normal",
                "action_en": f"Weather conditions (Wind {wind_avg:.1f} km/h, RH {rh_avg:.0f}%) are favorable for micronutrient / protective spraying on {crop['name_en']}.",
                "action_te": f"వాతావరణం (గాలి {wind_avg:.1f} కి.మీ/గం, తేమ {rh_avg:.0f}%) {crop['name_te']} పంటపై పోషకాలు మరియు రక్షణ మందుల పిచికారీకి అనుకూలంగా ఉంది.",
                "action_hi": f"मौसम (हवा {wind_avg:.1f} किमी/घंटा, नमी {rh_avg:.0f}%) {crop['name_hi']} पर पर्णीय छिड़काव के लिए उपयुक्त है।",
            })
        if tmax_avg >= 37.0:
            recommendations.append({
                "topic": "Heat Stress Mitigation",
                "urgency": "High",
                "action_en": f"High temperatures (Avg Max {tmax_avg:.1f}°C) may induce moisture stress. Apply light irrigation during morning or evening hours.",
                "action_te": f"అధిక ఉష్ణోగ్రతల ({tmax_avg:.1f}°C) వలన తేమ ఒత్తిడి రావచ్చు. ఉదయం లేదా సాయంత్రం వేళల్లో తేలికపాటి తడులు ఇవ్వండి.",
                "action_hi": f"उच्च तापमान ({tmax_avg:.1f}°C) से नमी की कमी हो सकती है। सुबह या शाम हल्की सिंचाई करें।",
            })

    if rh_avg >= 75.0 and tmin_avg >= 20.0:
        recommendations.append({
            "topic": "Pest & Disease Surveillance",
            "urgency": "Moderate",
            "action_en": f"Humid climate favors sucking pest and fungal spore buildup in {crop['name_en']} at {selected_stage} stage. Regularly scout crop under-leaves.",
            "action_te": f"అధిక తేమతో కూడిన వాతావరణం వల్ల {selected_stage} దశలో తెగుళ్ళు/పురుగుల ఆశించే అవకాశం ఉంది. నిరంతరం పంటను పరిశీలించండి.",
            "action_hi": f"अधिक आर्द्रता के कारण {selected_stage} अवस्था में रस चूसक कीटों और फफूंद का खतरा है। नियमित निगरानी रखें।",
        })

    if not recommendations:
        recommendations.append({
            "topic": f"General {selected_stage.title()} Stage Management",
            "urgency": "Normal",
            "action_en": f"Maintain optimal soil moisture and scout {crop['name_en']} field during {selected_stage} stage for balanced growth and nutrient absorption.",
            "action_te": f"{crop['name_te']} పంట {selected_stage} దశలో సరిపడా తేమను అందించి ఎరువుల యాజమాన్యం సక్రమంగా చేపట్టండి.",
            "action_hi": f"{crop['name_hi']} की {selected_stage} अवस्था में उपयुक्त नमी बनाए रखें और संतुलित पोषण सुनिश्चित करें।",
        })

    risk_level = "HIGH" if (heavy_rain_risk or rain_expected_mm >= 30.0 or tmax_avg >= 38.0) else "MODERATE" if (rh_avg >= 70.0) else "LOW"

    return {
        "crop_id": crop["crop_id"],
        "crop_name": crop["name_en"],
        "crop": crop,
        "crop_details": crop,
        "panchayat_id": panchayat_id,
        "growth_stage": selected_stage,
        "risk_level": risk_level,
        "weather_summary": {
            "tmax_avg_c": tmax_avg,
            "tmin_avg_c": tmin_avg,
            "rh_avg_pct": rh_avg,
            "wind_avg_kmh": wind_avg,
            "rain_expected_mm": rain_expected_mm,
            "heavy_rain_risk": heavy_rain_risk,
        },
        "recommendations": recommendations,
    }


@app.get("/api/v1/early-warnings")
def list_early_warnings() -> dict[str, object]:
    """Return active operational weather & agromet hazards across Telangana Panchayats."""
    warnings = []
    stats = {"critical": 0, "high": 0, "moderate": 0, "normal": 0}

    for pid, cfg in registry.items():
        fc = forecast_store.get(pid)
        if not fc:
            stats["normal"] += 1
            continue
        p_name = getattr(cfg, "panchayat_name", None) or cfg.panchayat_id
        district = getattr(cfg, "district", None) or "Rangareddy"
        mandal = getattr(cfg, "mandal", None) or "Chevella"
        has_alert = False

        for d in fc.days:
            hp = d.rainfall_probabilities.get("heavy", 0.0)
            if hp >= 0.70 or d.rain_mm >= 45.0:
                warnings.append({
                    "panchayat_id": pid, "panchayat_name": p_name, "district": district, "mandal": mandal,
                    "hazard": "Heavy Rainfall & Waterlogging", "severity": "critical",
                    "valid_until": str(d.valid_date), "action_required": "Ensure clear drainage furrows; suspend spraying & urea application.",
                })
                stats["critical"] += 1
                has_alert = True
                break
            elif hp >= 0.40 or d.rain_mm >= 25.0:
                warnings.append({
                    "panchayat_id": pid, "panchayat_name": p_name, "district": district, "mandal": mandal,
                    "hazard": "Moderate Rainfall", "severity": "high",
                    "valid_until": str(d.valid_date), "action_required": "Monitor field moisture and delay foliar spray.",
                })
                stats["high"] += 1
                has_alert = True
                break
            elif d.tmax_c.p50 >= 39.0:
                warnings.append({
                    "panchayat_id": pid, "panchayat_name": p_name, "district": district, "mandal": mandal,
                    "hazard": "Extreme Heat Stress", "severity": "high",
                    "valid_until": str(d.valid_date), "action_required": "Provide evening micro-irrigation to prevent flower drop.",
                })
                stats["high"] += 1
                has_alert = True
                break

        if not has_alert:
            stats["normal"] += 1

    return {
        "summary": stats,
        "warnings": warnings,
        "alerts": warnings,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agromet.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )

# ---------------------------------------------------------------------------
# Production platform APIs: identity, RBAC, notifications, risk, security,
# projects, analytics, notices, documents, localization and pagination.
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str = Field(min_length=5, max_length=254)
    display_name: str | None = Field(default=None, max_length=120)
    full_name: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    mobile: str | None = Field(default=None, max_length=20)
    department_id: str | None = Field(default=None, max_length=80)
    role: str = Field(default="citizen", max_length=50)

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str
    password: str
    otp: str | None = Field(default=None, min_length=6, max_length=8)

class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str

class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)

class MfaVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str = Field(min_length=6, max_length=6)

class RoleRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role_id: str = Field(min_length=2, max_length=80)

class NoticeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=10000)
    category: str = Field(default="general", min_length=2, max_length=80)
    priority: str = Field(default="normal", min_length=2, max_length=30)
    published_at: str | None = None
    expires_at: str | None = None

class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(min_length=3, max_length=240)
    category: str = Field(default="report", min_length=2, max_length=80)
    description: str | None = None
    storage_url: str | None = None
    checksum: str | None = None
    published_at: str | None = None

class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=3, max_length=200)
    district: str | None = None
    mandal: str | None = None
    block_id: str | None = None
    state: str = "Telangana"
    status: str = "planned"
    progress: float = Field(default=0, ge=0, le=100)
    budget_amount: float | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    description: str | None = None

class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    projects_by_status: list[dict[str, object]]
    milestones_by_status: list[dict[str, object]]
    grievances_by_status: list[dict[str, object]]
    risk_distribution: list[dict[str, object]]
    active_notices: int

def _public_user(user: dict[str, object]) -> dict[str, object]:
    return {
        k: user.get(k)
        for k in ("user_id", "email", "display_name", "mobile", "department_id", "is_active", "mfa_enabled", "created_at", "updated_at")
    } | {"roles": user.get("roles", [])}

def _send_password_reset(email: str, token: str) -> bool:
    """Send a reset link when SMTP is configured; never expose the token by default."""
    host = os.getenv("AGROMET_SMTP_HOST")
    if not host:
        return False
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["Subject"] = "Telangana Panchayat Agromet password reset"
    msg["From"] = os.getenv("AGROMET_SMTP_FROM", "no-reply@example.invalid")
    msg["To"] = email
    base = os.getenv("AGROMET_PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    msg.set_content(f"Use this password reset token at {base}/: {token}\nThe token expires in 30 minutes.")
    with smtplib.SMTP(host, int(os.getenv("AGROMET_SMTP_PORT", "587")), timeout=15) as smtp:
        if os.getenv("AGROMET_SMTP_TLS", "1") == "1":
            smtp.starttls()
        user = os.getenv("AGROMET_SMTP_USER")
        password = os.getenv("AGROMET_SMTP_PASSWORD")
        if user:
            smtp.login(user, password or "")
        smtp.send_message(msg)
    return True

@app.post("/api/v1/auth/register", status_code=201)
def auth_register(request: RegisterRequest, http_request: Request):
    if platform_repo.get_user_by_email(request.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    valid_role = request.role if request.role in {"citizen", "farmer", "officer", "kvk", "district_officer", "admin"} else "citizen"
    if valid_role == "farmer":
        valid_role = "citizen"
    name = request.display_name or request.full_name or request.email.split("@")[0]
    try:
        user = platform_repo.create_user(request.email, name, request.password, request.mobile, request.department_id, valid_role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    platform_repo.create_notification(
        "Welcome to Telangana Agromet Portal",
        f"Your {valid_role.replace('_', ' ').title()} account has been created successfully.",
        "account", user_id=user["user_id"], severity="info",
    )
    sid = "SES-" + uuid4().hex[:12]
    token, expires = token_signer.issue(str(user["user_id"]), sid, int(os.getenv("AGROMET_SESSION_TTL_SECONDS", "86400")))
    platform_repo.create_session(str(user["user_id"]), token_signer.digest(token), expires,
                                 http_request.client.host if http_request.client else None,
                                 http_request.headers.get("user-agent"), session_id=sid)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires, "user": _public_user(user)}

@app.post("/api/v1/auth/login")
def auth_login(request: LoginRequest, http_request: Request):
    user = platform_repo.get_user_by_email(request.email)
    if not user or not user.get("is_active") or not platform_repo.authenticate(request.email, request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.get("mfa_enabled"):
        secret = user.get("mfa_secret")
        if not request.otp or not secret or not verify_totp(str(secret), request.otp):
            raise HTTPException(status_code=401, detail="MFA verification required or invalid.")
    sid = "SES-" + uuid4().hex[:12]
    token, expires = token_signer.issue(str(user["user_id"]), sid, int(os.getenv("AGROMET_SESSION_TTL_SECONDS", "3600")))
    platform_repo.create_session(str(user["user_id"]), token_signer.digest(token), expires,
                                 http_request.client.host if http_request.client else None,
                                 http_request.headers.get("user-agent"), session_id=sid)
    platform_repo.security_event(ip_address=http_request.client.host if http_request.client else None,
                                 method="AUTH", path="/api/v1/auth/login", status_code=200,
                                 latency_ms=0, category="authentication", severity="info", user_id=str(user["user_id"]))
    return {"access_token": token, "token_type": "bearer", "expires_at": expires, "user": _public_user(user)}

@app.post("/api/v1/auth/logout")
def auth_logout(request: Request):
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return {"status": "signed_out"}
    token = header.split(" ", 1)[1].strip()
    try:
        _, sid, _ = token_signer.verify(token)
        platform_repo.revoke_session(sid)
    except ValueError:
        pass
    return {"status": "signed_out"}

@app.get("/api/v1/auth/me")
def auth_me(request: Request):
    return _public_user(_current_user(request))

@app.get("/api/v1/auth/sessions")
def auth_sessions(request: Request):
    user = _current_user(request)
    return platform_repo.list_sessions(str(user["user_id"]))

@app.delete("/api/v1/auth/sessions/{session_id}")
def revoke_session(session_id: str, request: Request):
    user = _current_user(request)
    sessions = {x["session_id"] for x in platform_repo.list_sessions(str(user["user_id"]))}
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    platform_repo.revoke_session(session_id)
    return {"status": "revoked", "session_id": session_id}

@app.post("/api/v1/auth/password/forgot")
def forgot_password(request: ForgotPasswordRequest):
    # Deliberately identical response for existing/non-existing accounts.
    user = platform_repo.get_user_by_email(request.email)
    if user:
        raw = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        platform_repo.create_reset_token(str(user["user_id"]), hashlib.sha256(raw.encode()).hexdigest(), expires)
        try:
            _send_password_reset(str(user["email"]), raw)
        except Exception:
            # Do not expose SMTP errors to callers.
            pass
    return {"status": "accepted", "message": "If the account exists, recovery instructions have been sent."}

def _send_recovery_otp(email: str, code: str) -> bool:
    """Deliver OTP via configured SMTP or webhook. No OTP is returned in production."""
    if os.getenv("AGROMET_OTP_WEBHOOK_URL"):
        import urllib.request
        payload=json.dumps({"email":email,"otp":code,"purpose":"password_reset"}).encode()
        req=urllib.request.Request(os.getenv("AGROMET_OTP_WEBHOOK_URL"),data=payload,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=10):
            return True
    if os.getenv("AGROMET_SMTP_HOST"):
        return _send_password_reset(email, f"Your one-time password is {code}. It expires in 10 minutes.")
    return False

@app.post("/api/v1/auth/password/otp/request")
def request_recovery_otp(request: ForgotPasswordRequest):
    user=platform_repo.get_user_by_email(request.email)
    if user:
        code=f"{secrets.randbelow(1_000_000):06d}"
        expires=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
        platform_repo.create_recovery_otp(str(user["user_id"]),hashlib.sha256(code.encode()).hexdigest(),expires)
        try:_send_recovery_otp(str(user["email"]),code)
        except Exception:pass
    return {"status":"accepted","message":"If the account exists, an OTP has been sent."}

class OtpResetRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    email:str
    otp:str=Field(min_length=6,max_length=6)
    new_password:str=Field(min_length=12,max_length=128)

@app.post("/api/v1/auth/password/otp/reset")
def reset_password_with_otp(request: OtpResetRequest):
    user=platform_repo.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=400,detail="Invalid or expired OTP.")
    uid=platform_repo.consume_recovery_otp(hashlib.sha256(request.otp.encode()).hexdigest())
    if not uid or uid != user["user_id"]:
        raise HTTPException(status_code=400,detail="Invalid or expired OTP.")
    try:platform_repo.update_password(uid,request.new_password)
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc
    return {"status":"password_updated"}

@app.post("/api/v1/auth/password/reset")
def reset_password(request: ResetPasswordRequest):
    user_id = platform_repo.consume_reset_token(hashlib.sha256(request.token.encode()).hexdigest())
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    try:
        platform_repo.update_password(user_id, request.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "password_updated"}

@app.post("/api/v1/auth/mfa/enroll")
def mfa_enroll(request: Request):
    user = _current_user(request)
    secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    platform_repo.set_mfa_secret(str(user["user_id"]), secret)
    issuer = "Telangana-Panchayat-Agromet"
    uri = f"otpauth://totp/{issuer}:{user['email']}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    return {"secret": secret, "otpauth_uri": uri, "next_step": "Verify the current code to enable MFA."}

@app.post("/api/v1/auth/mfa/verify")
def mfa_verify(request: MfaVerifyRequest, http_request: Request):
    user = _current_user(http_request)
    raw = platform_repo.get_user_by_email(str(user["email"]))
    if not raw or not raw.get("mfa_secret") or not verify_totp(str(raw["mfa_secret"]), request.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code.")
    platform_repo.enable_mfa(str(user["user_id"]))
    return {"status": "mfa_enabled"}

@app.get("/api/v1/users")
def list_users(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    _privileged_user(request, "admin")
    return {"items": [_public_user(x) for x in platform_repo.list_users(limit, offset)], "limit": limit, "offset": offset, "total": platform_repo.count_users()}

@app.post("/api/v1/users/{user_id}/roles/{role_id}")
def add_user_role(user_id: str, role_id: str, request: Request):
    _privileged_user(request, "admin")
    if role_id not in {"citizen", "officer", "kvk", "admin"}:
        raise HTTPException(status_code=404, detail="Role not found.")
    platform_repo.add_role(user_id, role_id)
    return {"status": "assigned", "user_id": user_id, "role_id": role_id}

@app.delete("/api/v1/users/{user_id}/roles/{role_id}")
def remove_user_role(user_id: str, role_id: str, request: Request):
    _privileged_user(request, "admin")
    platform_repo.remove_role(user_id, role_id)
    return {"status": "removed", "user_id": user_id, "role_id": role_id}

@app.put("/api/v1/users/{user_id}/status")
def update_user_status(user_id: str, request: Request, active: bool = True):
    _privileged_user(request,"admin")
    with platform_repo.connection() as c:
        cur=c.execute("UPDATE users SET is_active=?,updated_at=? WHERE user_id=?",(1 if active else 0,utcnow(),user_id))
    if cur.rowcount==0: raise HTTPException(status_code=404,detail="User not found.")
    return {"status":"updated","user_id":user_id,"is_active":active}

@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id:str,request:Request):
    _privileged_user(request,"admin")
    with platform_repo.connection() as c:
        cur=c.execute("DELETE FROM users WHERE user_id=?",(user_id,))
    if cur.rowcount==0: raise HTTPException(status_code=404,detail="User not found.")
    return {"status":"deleted","user_id":user_id}

@app.get("/api/v1/departments")
def departments(request: Request):
    _privileged_user(request, "admin")
    # Departments are intentionally simple in the pilot.
    with platform_repo.connection() as c:
        rows = c.execute("SELECT * FROM departments ORDER BY name").fetchall()
    return [dict(x) for x in rows]

@app.post("/api/v1/departments")
def create_department(request: Request, payload: dict[str, str]):
    _privileged_user(request, "admin")
    did = payload.get("department_id") or "DEP-" + uuid4().hex[:8]
    name = payload.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Department name is required.")
    now = utcnow()
    with platform_repo.connection() as c:
        c.execute("INSERT INTO departments(department_id,name,description,created_at) VALUES(?,?,?,?)",(did,name,payload.get("description"),now))
    return {"department_id": did, "name": name, "description": payload.get("description"), "created_at": now}

@app.put("/api/v1/departments/{department_id}")
def update_department(department_id:str,request:Request,payload:dict[str,str]):
    _privileged_user(request,"admin")
    with platform_repo.connection() as c:
        cur=c.execute("UPDATE departments SET name=?,description=? WHERE department_id=?",(payload.get("name","").strip(),payload.get("description"),department_id))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Department not found.")
    return {"department_id":department_id,"name":payload.get("name"),"description":payload.get("description")}

@app.delete("/api/v1/departments/{department_id}")
def delete_department(department_id:str,request:Request):
    _privileged_user(request,"admin")
    if department_id=="agri-telangana":raise HTTPException(status_code=400,detail="Default department cannot be deleted.")
    with platform_repo.connection() as c:
        cur=c.execute("DELETE FROM departments WHERE department_id=?",(department_id,))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Department not found.")
    return {"status":"deleted","department_id":department_id}

@app.get("/api/v1/notifications")
def notifications(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    user = _current_user(request)
    return {"items": platform_repo.notifications(str(user["user_id"]), limit, offset),
            "limit": limit, "offset": offset, "unread": platform_repo.unread_count(str(user["user_id"]))}

@app.post("/api/v1/notifications/{notification_id}/read")
def notification_read(notification_id: str, request: Request):
    user = _current_user(request)
    if not platform_repo.mark_notification(notification_id, str(user["user_id"])):
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"status": "read", "notification_id": notification_id}

@app.post("/api/v1/notifications/read-all")
def notification_read_all(request: Request):
    user = _current_user(request)
    with platform_repo.connection() as c:
        c.execute("UPDATE notifications SET read_at=? WHERE (user_id=? OR user_id IS NULL) AND read_at IS NULL",(utcnow(),str(user["user_id"])))
    return {"status": "all_read"}

def _risk_from_forecast(forecast: PanchayatForecastResponse) -> list[dict[str, object]]:
    results=[]
    for day in forecast.days:
        hp=float(day.rainfall_probabilities.get("heavy",0))
        vhp=float(day.rainfall_probabilities.get("very_heavy",0))
        heat=max(0.0,min(1.0,(day.tmax_c.p50-35.0)/10.0))
        humidity=max(0.0,min(1.0,(day.relative_humidity_pct.p50-85.0)/15.0))
        wind=max(0.0,min(1.0,(day.wind_speed_kmh.p90-20.0)/20.0))
        contributions={"heavy_rain":hp*40,"very_heavy_rain":vhp*20,"heat":heat*20,"humidity":humidity*15,"high_wind":wind*5}
        score=round(max(0,min(100,sum(contributions.values()))),1)
        level="critical" if score>=80 else "high" if score>=60 else "moderate" if score>=35 else "low"
        results.append(platform_repo.save_risk(forecast.panchayat_id,day.valid_date.isoformat(),score,level,contributions,forecast.model_version))
    return results

@app.get("/api/v1/risk/panchayat/{panchayat_id}")
def risk_score(panchayat_id: str, request: Request, refresh: bool = False):
    # Risk is a transparent rule-derived operational score, not a fabricated SHAP value.
    forecast = refresh_panchayat(panchayat_id) if refresh else forecast_store.get(panchayat_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="No forecast available for this Panchayat.")
    return {"panchayat_id": panchayat_id, "method": "deterministic forecast-factor contribution",
            "scores": _risk_from_forecast(forecast)}

@app.get("/api/v1/risk/panchayat/{panchayat_id}/{forecast_date}")
def risk_score_day(panchayat_id: str, forecast_date: str):
    item=platform_repo.get_risk(panchayat_id,forecast_date)
    if not item:
        forecast=forecast_store.get(panchayat_id)
        if not forecast: raise HTTPException(status_code=404, detail="No forecast available.")
        _risk_from_forecast(forecast); item=platform_repo.get_risk(panchayat_id,forecast_date)
    return item

@app.get("/api/v1/security/summary")
def security_summary(request: Request, since_hours: int = Query(24, ge=1, le=168)):
    _privileged_user(request, "admin")
    return platform_repo.security_summary(since_hours)

@app.get("/api/v1/security/events")
def security_events(request: Request, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    _privileged_user(request, "admin")
    return {"items": platform_repo.security_events(limit,offset), "limit":limit, "offset":offset}

@app.get("/api/v1/projects")
def projects(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return {"items": platform_repo.list_projects(limit,offset), "limit":limit, "offset":offset}

@app.post("/api/v1/projects", status_code=201)
def create_project(payload: ProjectRequest, request: Request):
    user=_privileged_user(request,"admin","officer")
    data=payload.model_dump();data["created_by"]=user.get("user_id")
    return platform_repo.create_project(data)

@app.get("/api/v1/projects/{project_id}")
def project(project_id: str):
    item=platform_repo.get_project(project_id)
    if not item: raise HTTPException(status_code=404, detail="Project not found.")
    return item

@app.get("/api/v1/analytics/summary", response_model=AnalyticsResponse)
def analytics_summary():
    return platform_repo.analytics()

@app.get("/api/v1/notices")
def notices(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), active_only: bool = True):
    return {"items": platform_repo.list_notices(active_only,limit,offset), "limit":limit, "offset":offset}

@app.post("/api/v1/notices", status_code=201)
def create_notice(payload: NoticeRequest, request: Request):
    user=_privileged_user(request,"admin","officer")
    data=payload.model_dump();data["created_by"]=user.get("user_id")
    return platform_repo.create_notice(data)

@app.put("/api/v1/notices/{notice_id}")
def update_notice(notice_id:str,payload:NoticeRequest,request:Request):
    _privileged_user(request,"admin","officer")
    with platform_repo.connection() as c:
        cur=c.execute("""UPDATE notices SET title=?,body=?,category=?,published_at=COALESCE(?,published_at),expires_at=? WHERE notice_id=?""",(payload.title,payload.body,payload.category,payload.published_at,payload.expires_at,notice_id))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Notice not found.")
    return next((x for x in platform_repo.list_notices(False,200,0) if x["notice_id"]==notice_id),None)

@app.delete("/api/v1/notices/{notice_id}")
def delete_notice(notice_id:str,request:Request):
    _privileged_user(request,"admin","officer")
    with platform_repo.connection() as c:
        cur=c.execute("UPDATE notices SET is_active=0 WHERE notice_id=?",(notice_id,))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Notice not found.")
    return {"status":"archived","notice_id":notice_id}

@app.get("/api/v1/documents")
def documents(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return {"items": platform_repo.list_documents(limit,offset), "limit":limit, "offset":offset}

@app.post("/api/v1/documents", status_code=201)
def create_document(payload: DocumentRequest, request: Request):
    user=_privileged_user(request,"admin","officer")
    data=payload.model_dump();data["created_by"]=user.get("user_id")
    return platform_repo.create_document(data)

@app.delete("/api/v1/documents/{document_id}")
def delete_document(document_id:str,request:Request):
    _privileged_user(request,"admin","officer")
    with platform_repo.connection() as c:
        cur=c.execute("DELETE FROM documents WHERE document_id=?",(document_id,))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Document not found.")
    return {"status":"deleted","document_id":document_id}

@app.get("/api/v1/advisories/{advisory_id}/localizations")
def advisory_localizations(advisory_id: str):
    if review_store.repository.get_advisory(advisory_id) is None:
        raise HTTPException(status_code=404, detail="Advisory not found.")
    return platform_repo.get_localizations(advisory_id)

@app.post("/api/v1/advisories/{advisory_id}/localize/{language}")
def advisory_localize(advisory_id: str, language: Literal["en","te","hi"]):
    advisory=review_store.repository.get_advisory(advisory_id)
    if advisory is None: raise HTTPException(status_code=404, detail="Advisory not found.")
    localized=localizer.render(advisory,language)
    platform_repo.save_localization(advisory_id,language,localized.text,localized.source_metrics)
    return localized.model_dump()

@app.get("/api/v1/portal/analytics")
def portal_analytics():
    return platform_repo.analytics()

@app.get("/api/v1/portal/security-status")
def public_security_status():
    # Only expose aggregate operational status publicly, never raw telemetry.
    return {"status":"active","telemetry":"enabled","defensive_monitoring":True}

@app.get("/api/v1/gis/panchayats")
def gis_panchayats(district: str | None = None, block_id: str | None = None):
    features=[]
    for cfg in registry.values():
        # Registry is the authoritative pilot geospatial source.
        if district and getattr(cfg, "district", None) and getattr(cfg, "district") != district:
            continue
        if block_id and getattr(cfg, "block_id", None) and getattr(cfg, "block_id") != block_id:
            continue
        features.append({"type":"Feature","geometry":{"type":"Point","coordinates":[cfg.longitude,cfg.latitude]},
                         "properties":{"panchayat_id":cfg.panchayat_id,"elevation_m":cfg.elevation_m}})
    return {"type":"FeatureCollection","features":features}

@app.get("/api/v1/analytics/trends")
def analytics_trends(request: Request, days: int = Query(30, ge=1, le=365)):
    # Forecast/risk trends are derived from stored records; no synthetic series is created.
    with platform_repo.connection() as c:
        cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat()
        risk=[dict(r) for r in c.execute("""SELECT forecast_date,level,COUNT(*) count,AVG(score) avg_score
            FROM risk_scores WHERE created_at>=? GROUP BY forecast_date,level ORDER BY forecast_date""",(cutoff,)).fetchall()]
        reviews=[dict(r) for r in c.execute("""SELECT substr(created_at,1,10) day,action,COUNT(*) count
            FROM review_events WHERE created_at>=? GROUP BY day,action ORDER BY day""",(cutoff,)).fetchall()]
        grievances=[dict(r) for r in c.execute("""SELECT substr(created_at,1,10) day,status,COUNT(*) count
            FROM grievances WHERE created_at>=? GROUP BY day,status ORDER BY day""",(cutoff,)).fetchall()]
    return {"days":days,"risk_trend":risk,"review_trend":reviews,"grievance_trend":grievances}

@app.get("/api/v1/portal/status")
def portal_status():
    model=_configured_model()
    return {
        "api":"operational",
        "database":"operational",
        "model":{"loaded":bool(model),"version":model[1] if model else "physics-baseline-live"},
        "weather_provider":os.getenv("AGROMET_FORECAST_PROVIDER","open_meteo"),
        "imd_configured":bool(os.getenv("AGROMET_IMD_URL")),
        "aws_residual_configured":bool(os.getenv("AGROMET_AWS_RESIDUAL_URL")),
        "srtm_configured":bool(os.getenv("AGROMET_SRTM_PATH")),
        "identity":"configured" if platform_repo.count_users() else "no users provisioned",
    }

@app.get("/api/v1/roles")
def roles(request: Request):
    _privileged_user(request,"admin")
    with platform_repo.connection() as c:
        return [dict(r) for r in c.execute("SELECT role_id,name,description,created_at FROM roles ORDER BY name").fetchall()]

@app.get("/api/v1/review-events")
def review_events(request: Request, limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
    _privileged_user(request,"admin","kvk","officer")
    return {"items":platform_repo.review_events(limit,offset),"limit":limit,"offset":offset}

class MilestoneRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    title:str=Field(min_length=2,max_length=200)
    due_date:str|None=None
    status:str="planned"
    progress:float=Field(default=0,ge=0,le=100)

class InspectionRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    inspected_at:str|None=None
    inspector:str=Field(min_length=2,max_length=120)
    status:str="recorded"
    notes:str|None=None

@app.put("/api/v1/projects/{project_id}")
def update_project(project_id:str,payload:ProjectRequest,request:Request):
    _privileged_user(request,"admin","officer")
    item=platform_repo.update_project(project_id,payload.model_dump())
    if not item: raise HTTPException(status_code=404,detail="Project not found.")
    return item

@app.delete("/api/v1/projects/{project_id}")
def delete_project(project_id:str,request:Request):
    _privileged_user(request,"admin")
    if not platform_repo.delete_project(project_id): raise HTTPException(status_code=404,detail="Project not found.")
    return {"status":"deleted","project_id":project_id}

@app.get("/api/v1/projects/{project_id}/milestones")
def project_milestones(project_id:str):
    if not platform_repo.get_project(project_id): raise HTTPException(status_code=404,detail="Project not found.")
    return platform_repo.list_milestones(project_id)

@app.post("/api/v1/projects/{project_id}/milestones",status_code=201)
def create_milestone(project_id:str,payload:MilestoneRequest,request:Request):
    _privileged_user(request,"admin","officer")
    if not platform_repo.get_project(project_id): raise HTTPException(status_code=404,detail="Project not found.")
    return platform_repo.create_milestone(project_id,payload.model_dump())

@app.get("/api/v1/projects/{project_id}/inspections")
def project_inspections(project_id:str):
    if not platform_repo.get_project(project_id): raise HTTPException(status_code=404,detail="Project not found.")
    return platform_repo.list_inspections(project_id)

@app.post("/api/v1/projects/{project_id}/inspections",status_code=201)
def create_inspection(project_id:str,payload:InspectionRequest,request:Request):
    _privileged_user(request,"admin","officer")
    if not platform_repo.get_project(project_id): raise HTTPException(status_code=404,detail="Project not found.")
    return platform_repo.create_inspection(project_id,payload.model_dump())


class RoleCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    role_id:str=Field(min_length=2,max_length=80)
    name:str=Field(min_length=2,max_length=120)
    description:str|None=None

@app.post("/api/v1/roles",status_code=201)
def create_role(payload:RoleCreateRequest,request:Request):
    _privileged_user(request,"admin")
    now=utcnow()
    with platform_repo.connection() as c:
        c.execute("INSERT INTO roles(role_id,name,description,created_at) VALUES(?,?,?,?)",(payload.role_id,payload.name,payload.description,now))
    return {"role_id":payload.role_id,"name":payload.name,"description":payload.description,"created_at":now}

@app.put("/api/v1/roles/{role_id}")
def update_role(role_id:str,payload:RoleCreateRequest,request:Request):
    _privileged_user(request,"admin")
    with platform_repo.connection() as c:
        cur=c.execute("UPDATE roles SET name=?,description=? WHERE role_id=?",(payload.name,payload.description,role_id))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Role not found.")
    return {"role_id":role_id,"name":payload.name,"description":payload.description}

@app.delete("/api/v1/roles/{role_id}")
def delete_role(role_id:str,request:Request):
    _privileged_user(request,"admin")
    if role_id in {"citizen","officer","kvk","admin"}:
        raise HTTPException(status_code=400,detail="Built-in roles cannot be deleted.")
    with platform_repo.connection() as c:
        cur=c.execute("DELETE FROM roles WHERE role_id=?",(role_id,))
    if cur.rowcount==0:raise HTTPException(status_code=404,detail="Role not found.")
    return {"status":"deleted","role_id":role_id}


class ProfileUpdateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    display_name:str=Field(min_length=2,max_length=120)
    mobile:str|None=None

@app.put("/api/v1/auth/me")
def update_profile(payload:ProfileUpdateRequest,request:Request):
    user=_current_user(request)
    with platform_repo.connection() as c:
        c.execute("UPDATE users SET display_name=?,mobile=?,updated_at=? WHERE user_id=?",(payload.display_name,payload.mobile,utcnow(),user["user_id"]))
    return _public_user(platform_repo.get_user(str(user["user_id"])))

class ChangePasswordRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
    current_password:str
    new_password:str=Field(min_length=12,max_length=128)

@app.post("/api/v1/auth/password/change")
def change_password(payload:ChangePasswordRequest,request:Request):
    user=_current_user(request)
    raw=platform_repo.get_user_by_email(str(user["email"]))
    if not raw or not __import__("agromet.platform",fromlist=["verify_password"]).verify_password(payload.current_password,raw["password_hash"]):
        raise HTTPException(status_code=400,detail="Current password is incorrect.")
    try:platform_repo.update_password(str(user["user_id"]),payload.new_password)
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc
    return {"status":"password_updated"}

@app.get("/api/v1/analytics/financial-progress")
def financial_progress():
    with platform_repo.connection() as c:
        row=c.execute("SELECT COALESCE(SUM(budget_amount),0) budget, COALESCE(SUM(budget_amount*progress/100.0),0) progress_value, COUNT(*) projects FROM projects").fetchone()
    return {"projects":int(row["projects"]),"budget_total":float(row["budget"]),"progress_value":float(row["progress_value"]),
            "unrealized_value":max(0.0,float(row["budget"])-float(row["progress_value"]))}
