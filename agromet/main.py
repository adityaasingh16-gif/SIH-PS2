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
from datetime import date
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pandas as pd
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse
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
from .platform import PlatformRepository
from .storage import SQLiteRepository
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
                }
            )
        else:
            updated = advisory.model_copy(
                update={
                    "status": AdvisoryStatus.APPROVED,
                    "reviewer_notes": request.reviewer_notes,
                }
            )
        self.repository.update_advisory(
            updated,
            reviewer_id=request.reviewer_id,
            action=request.action,
            notes=request.reviewer_notes,
        )
        return ReviewResponse(advisory=updated, action=request.action)


repository = SQLiteRepository()
forecast_store = ForecastStore(repository)
review_store = AdvisoryReviewStore(repository)
scorecard_builder = ScorecardBuilder()
advisory_engine = AdvisoryEngine()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    """Optional API-key guard: disabled only when AGROMET_API_KEY is unset."""
    expected = os.getenv("AGROMET_API_KEY")
    if expected and api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

def _load_scorecard_file() -> tuple[str, list[dict[str, object]]]:
    path = os.getenv("AGROMET_SCORECARD_FILE")
    if not path or not Path(path).exists():
        return scorecard_builder.markdown([]), []
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return str(payload.get("markdown", "")), list(payload.get("models", []))
    except (OSError, ValueError, TypeError) as exc:
        raise IngestionError(f"Invalid scorecard file: {exc}") from exc

platform_repo = PlatformRepository(database_path=os.getenv("AGROMET_DB_PATH"))
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
    version="1.4.0",
    description="Live terrain-aware forecasts and durable KVK review workflows.",
)


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
    review_store.add_batch(advisory_engine.generate(panchayat_id, advisory_forecast))
    return forecast


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def portal() -> HTMLResponse:
    """Serve the built-in dependency-free government-style pilot portal."""
    return HTMLResponse(content=portal_html())


@app.get("/api/v1/panchayats")
def list_panchayats() -> list[dict[str, object]]:
    """Return the configured Panchayat registry for the portal."""
    return [
        {
            "panchayat_id": config.panchayat_id,
            "name": config.panchayat_id,
            "latitude": config.latitude,
            "longitude": config.longitude,
            "elevation_m": config.elevation_m,
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
    _: None = Depends(require_api_key),
) -> list[dict[str, object]]:
    return repository.review_audit_events()


@app.get("/api/v1/grievances", response_model=list[GrievanceResponse])
def list_grievances() -> list[GrievanceResponse]:
    return [GrievanceResponse(**{k: item[k] for k in ("grievance_id", "status", "created_at", "category", "subject")}) for item in repository.list_grievances()]


@app.post("/api/v1/grievances", response_model=GrievanceResponse, status_code=201)
def create_grievance(request: GrievanceRequest) -> GrievanceResponse:
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    grievance_id = f"GRV-{now[:10].replace('-', '')}-{uuid4().hex[:6].upper()}"
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
    return GrievanceResponse(
        grievance_id=grievance_id,
        status="submitted",
        created_at=now,
        category=request.category,
        subject=request.subject,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


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


@app.get("/api/v1/advisories/kvk-pending", response_model=list[Advisory])
def get_pending_advisories(_: None = Depends(require_api_key)) -> list[Advisory]:
    return review_store.pending()


@app.post("/api/v1/advisories/approve", response_model=ReviewResponse)
def approve_advisory(request: ApprovalRequest, _: None = Depends(require_api_key)) -> ReviewResponse:
    try:
        return review_store.approve(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Advisory not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/scorecard", response_model=ScorecardResponse)
def get_scorecard() -> ScorecardResponse:
    markdown, models = _load_scorecard_file()
    return ScorecardResponse(markdown=markdown, models=models)
def _risk_from_forecast(self, forecast: PanchayatForecastResponse) -> list[dict[str, object]]:
    """Compute rule-derived risk scores from a 5-day forecast."""
    """
    Risk levels: low <35, moderate 35-59, high 60-79, critical >=80
    Based on: heavy rain probability, extreme heat, and rainfall thresholds.
    """
    risks = []
    for day in forecast.days:
        score = 0
        level = "low"
        if day.rainfall_probabilities.get("heavy", 0) >= 0.60:
            score += 30
        if day.tmax_c.p50 >= 42:
            score += 20
        if day.rainfall_probabilities.get("heavy", 0) >= 0.30:
            score += 15
        if score >= 80:
            level = "critical"
        elif score >= 60:
            level = "high"
        elif score >= 35:
            level = "moderate"
        else:
            level = "low"
        risks.append({
            "forecast_date": day.valid_date.isoformat(),
            "score": score,
            "level": level,
        })
    return risks




# Standalone risk function (called as app._risk_from_forecast(forecast))
def _risk_from_forecast(forecast: PanchayatForecastResponse) -> list[dict[str, object]]:
    """Compute rule-derived risk scores from a 5-day forecast.

    Risk levels: low <35, moderate 35-59, high 60-79, critical >=80
    Based on: heavy rain probability, extreme heat, and rainfall thresholds.
    """
    risks = []
    for day in forecast.days:
        score = 0
        level = "low"
        if day.rainfall_probabilities.get("heavy", 0) >= 0.60:
            score += 30
        if day.tmax_c.p50 >= 42:
            score += 20
        if day.rainfall_probabilities.get("heavy", 0) >= 0.30:
            score += 15
        if score >= 80:
            level = "critical"
        elif score >= 60:
            level = "high"
        elif score >= 35:
            level = "moderate"
        else:
            level = "low"
        risks.append({
            "forecast_date": day.valid_date.isoformat(),
            "score": score,
            "level": level,
        })
    return risks

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agromet.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )