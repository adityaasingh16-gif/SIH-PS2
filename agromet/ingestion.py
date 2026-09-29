"""Provider adapters for live forecasts, AWS residuals, and SRTM terrain."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from math import atan, degrees, hypot
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from .data_engine import (
    AWSResidual,
    CoarseForecast,
    FeaturePipeline,
    PanchayatTarget,
)


class IngestionError(RuntimeError):
    """Raised when an upstream weather or terrain source is unavailable/invalid."""


@dataclass(frozen=True, slots=True)
class PanchayatConfig:
    """Operational location record used to refresh one Panchayat forecast."""

    panchayat_id: str
    latitude: float
    longitude: float
    elevation_m: float | None = None
    slope_deg: float | None = None
    aspect_deg: float | None = None
    distance_to_water_m: float | None = None
    coarse_latitude: float | None = None
    coarse_longitude: float | None = None
    coarse_elevation_m: float | None = None


def _fetch_json(url: str, *, timeout_seconds: float = 20.0) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "agromet-sih26074/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise IngestionError(f"Upstream request failed for {url}: {exc}") from exc


class OpenMeteoClient:
    """Fetch five-day daily block forecasts from the public Open-Meteo API."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv(
            "AGROMET_OPEN_METEO_URL",
            "https://api.open-meteo.com/v1/forecast",
        )

    def fetch(
        self,
        latitude: float,
        longitude: float,
        *,
        elevation_m: float | None = None,
    ) -> tuple[list[CoarseForecast], list[float]]:
        query = urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "daily": ",".join(
                    (
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "relative_humidity_2m_mean",
                        "wind_speed_10m_max",
                        "precipitation_sum",
                        "shortwave_radiation_sum",
                    )
                ),
                "forecast_days": 5,
                "timezone": "UTC",
            }
        )
        payload = _fetch_json(f"{self.base_url}?{query}")
        return _parse_daily_forecast_payload(payload, elevation_m=elevation_m)


class IMDClient:
    """Configurable IMD/Mausamgram adapter.

    IMD deployments differ by pilot and gateway. The adapter accepts either the
    common daily-array shape used by Open-Meteo or a list of normalized forecast
    objects, while keeping the endpoint and authentication outside source code.
    """

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or os.getenv("AGROMET_IMD_URL")

    def fetch(
        self,
        latitude: float,
        longitude: float,
        *,
        elevation_m: float | None = None,
    ) -> tuple[list[CoarseForecast], list[float]]:
        if not self.endpoint:
            raise IngestionError(
                "AGROMET_IMD_URL is required when AGROMET_FORECAST_PROVIDER=imd."
            )
        query = urlencode({"latitude": latitude, "longitude": longitude, "days": 5})
        separator = "&" if "?" in self.endpoint else "?"
        payload = _fetch_json(f"{self.endpoint}{separator}{query}")
        if isinstance(payload, dict) and (
            "daily" in payload or "forecast" in payload or "data" in payload
        ):
            if "daily" in payload:
                return _parse_daily_forecast_payload(payload, elevation_m=elevation_m)
            return _parse_imd_records(
                payload.get("forecast", payload.get("data")),
                elevation_m=elevation_m,
            )
        raise IngestionError("IMD response must contain daily, forecast, or data.")


def _parse_daily_forecast_payload(
    payload: Any,
    *,
    elevation_m: float | None,
) -> tuple[list[CoarseForecast], list[float]]:
    daily = payload.get("daily", {}) if isinstance(payload, dict) else {}
    required = (
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
        "relative_humidity_2m_mean",
        "wind_speed_10m_max",
        "precipitation_sum",
    )
    if any(key not in daily for key in required):
        raise IngestionError("Daily forecast response is missing required variables.")

    count = len(daily["time"])
    if count < 5:
        raise IngestionError(f"Forecast source returned {count} days; five are required.")
    source_elevation = float(payload.get("elevation", elevation_m or 0.0))
    radiation = [
        float(value) * 0.77 if value is not None else 0.0
        for value in daily.get("shortwave_radiation_sum", [0.0] * count)
    ]
    forecasts = [
        CoarseForecast(
            valid_date=date.fromisoformat(str(daily["time"][index])),
            lead_day=index + 1,
            tmax_c=float(daily["temperature_2m_max"][index]),
            tmin_c=float(daily["temperature_2m_min"][index]),
            relative_humidity_pct=float(daily["relative_humidity_2m_mean"][index]),
            wind_speed_kmh=float(daily["wind_speed_10m_max"][index]),
            rain_mm=max(0.0, float(daily["precipitation_sum"][index])),
            elevation_m=source_elevation,
            net_radiation_mj_m2_day=radiation[index],
        )
        for index in range(count)
    ]
    return forecasts, radiation


def _parse_imd_records(
    records: Any,
    *,
    elevation_m: float | None,
) -> tuple[list[CoarseForecast], list[float]]:
    if not isinstance(records, list) or len(records) < 5:
        raise IngestionError("IMD forecast must contain at least five daily records.")
    forecasts: list[CoarseForecast] = []
    radiation: list[float] = []
    for index, item in enumerate(records[:5]):
        if not isinstance(item, dict):
            raise IngestionError("IMD forecast records must be objects.")
        try:
            valid_date = date.fromisoformat(
                str(item.get("valid_date", item.get("date")))
            )
            record_elevation = float(item.get("elevation_m", elevation_m or 0.0))
            net_radiation = float(
                item.get("net_radiation_mj_m2_day", item.get("shortwave_radiation_sum", 0.0))
            )
            tmax = item.get("tmax_c", item.get("temperature_2m_max"))
            tmin = item.get("tmin_c", item.get("temperature_2m_min"))
            humidity = item.get(
                "relative_humidity_pct",
                item.get("relative_humidity_2m_mean"),
            )
            wind = item.get("wind_speed_kmh", item.get("wind_speed_10m_max"))
            rain = item.get("rain_mm", item.get("precipitation_sum"))
            if any(value is None for value in (tmax, tmin, humidity, wind, rain)):
                raise ValueError("IMD record is missing one or more weather variables.")
            record = CoarseForecast(
                valid_date=valid_date,
                lead_day=index + 1,
                tmax_c=float(tmax),
                tmin_c=float(tmin),
                relative_humidity_pct=float(humidity),
                wind_speed_kmh=float(wind),
                rain_mm=max(0.0, float(rain)),
                elevation_m=record_elevation,
                net_radiation_mj_m2_day=net_radiation,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IngestionError(f"Invalid IMD forecast record: {item}") from exc
        forecasts.append(record)
        radiation.append(net_radiation)
    return forecasts, radiation


def fetch_aws_residuals(
    url: str | None = None,
    *,
    timeout_seconds: float = 20.0,
) -> list[AWSResidual]:
    """Read previous-day station residuals from a configured JSON endpoint.

    Expected payload: a list or ``{"stations": [...]}``, where each station has
    ``station_id``, ``latitude``, ``longitude``, and a numeric ``residuals`` map.
    """

    endpoint = url or os.getenv("AGROMET_AWS_RESIDUAL_URL")
    if not endpoint:
        return []
    payload = _fetch_json(endpoint, timeout_seconds=timeout_seconds)
    records = payload if isinstance(payload, list) else payload.get("stations", [])
    if not isinstance(records, list):
        raise IngestionError("AWS residual response must be a list or contain stations.")
    result: list[AWSResidual] = []
    for item in records:
        if not isinstance(item, dict):
            raise IngestionError("AWS residual station record must be an object.")
        try:
            result.append(
                AWSResidual(
                    station_id=str(item["station_id"]),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    residuals={
                        str(key): float(value)
                        for key, value in dict(item["residuals"]).items()
                    },
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IngestionError(f"Invalid AWS residual record: {item}") from exc
    return result


class SrtmTerrainSampler:
    """Sample elevation, slope, and aspect from a local SRTM GeoTIFF."""

    def __init__(
        self,
        raster_path: str | Path | None = None,
        *,
        water_points: Sequence[tuple[float, float]] = (),
    ) -> None:
        configured_path = raster_path or os.getenv("AGROMET_SRTM_PATH")
        self.raster_path = Path(configured_path) if configured_path else None
        self.water_points = tuple(water_points)

    def sample(self, latitude: float, longitude: float) -> dict[str, float]:
        if self.raster_path is None:
            raise IngestionError("AGROMET_SRTM_PATH is not configured.")
        try:
            import rasterio
            from rasterio.windows import Window
        except (ImportError, OSError) as exc:
            raise IngestionError(
                "rasterio is required to sample SRTM GeoTIFF terrain data."
            ) from exc

        if not self.raster_path.exists():
            raise IngestionError(f"SRTM raster does not exist: {self.raster_path}")
        with rasterio.open(self.raster_path) as source:
            row, column = source.index(longitude, latitude)
            value = source.read(1, window=Window(column, row, 1, 1), boundless=True, fill_value=np.nan)
            elevation = float(value[0, 0])
            if not np.isfinite(elevation):
                raise IngestionError("SRTM raster has no elevation at the Panchayat coordinate.")
            window = source.read(
                1,
                window=Window(column - 1, row - 1, 3, 3),
                boundless=True,
                fill_value=elevation,
            ).astype(float)
            pixel_size = abs(float(source.transform.a))
            if source.crs and source.crs.is_geographic:
                pixel_size *= 111_320.0
            dz_dy, dz_dx = np.gradient(window, pixel_size or 1.0)
            center_dx = float(dz_dx[1, 1])
            center_dy = float(dz_dy[1, 1])
            slope_deg = degrees(atan(hypot(center_dx, center_dy)))
            aspect_deg = (degrees(np.arctan2(center_dy, -center_dx)) + 360.0) % 360.0

        return {
            "elevation_m": elevation,
            "slope_deg": slope_deg,
            "aspect_deg": aspect_deg,
            "distance_to_water_m": self._distance_to_water_m(latitude, longitude),
        }

    def _distance_to_water_m(self, latitude: float, longitude: float) -> float:
        if not self.water_points:
            return float("nan")
        distances = [
            _haversine_m(latitude, longitude, water_lat, water_lon)
            for water_lat, water_lon in self.water_points
        ]
        return min(distances)


def _haversine_m(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    radius_m = 6_371_008.8
    lat_a, lat_b = radians(latitude_a), radians(latitude_b)
    delta_lat = lat_b - lat_a
    delta_lon = radians(longitude_b - longitude_a)
    value = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    return 2.0 * radius_m * asin(sqrt(value))


def load_panchayat_registry(path: str | Path) -> dict[str, PanchayatConfig]:
    """Load Panchayat registry from JSON or CSV.

    JSON accepts the native API schema. CSV accepts the development schema used
    by the SIH26074 training data (lgd_code, lat, lon, block_id). Optional
    elevation/coarse columns are used when present.
    """

    registry_path = Path(path)
    if not registry_path.exists():
        raise IngestionError(f"Panchayat registry does not exist: {registry_path}")

    if registry_path.suffix.lower() == ".csv":
        try:
            frame = pd.read_csv(registry_path)
        except Exception as exc:
            raise IngestionError(f"Unable to read Panchayat CSV: {exc}") from exc
        records = frame.to_dict(orient="records")
        normalized: list[dict[str, object]] = []
        for item in records:
            normalized.append(
                {
                    "panchayat_id": item.get("panchayat_id", item.get("lgd_code")),
                    "latitude": item.get("latitude", item.get("lat")),
                    "longitude": item.get("longitude", item.get("lon")),
                    "elevation_m": item.get("elevation_m"),
                    "slope_deg": item.get("slope_deg"),
                    "aspect_deg": item.get("aspect_deg"),
                    "distance_to_water_m": item.get("distance_to_water_m"),
                    "coarse_latitude": item.get("coarse_latitude"),
                    "coarse_longitude": item.get("coarse_longitude"),
                    "coarse_elevation_m": item.get("coarse_elevation_m"),
                }
            )
        records = normalized
    else:
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IngestionError(f"Invalid Panchayat registry JSON: {exc}") from exc
        records = payload if isinstance(payload, list) else payload.get("panchayats", [])
    if not isinstance(records, list):
        raise IngestionError("Panchayat registry must be a list or contain panchayats.")
    registry: dict[str, PanchayatConfig] = {}
    for item in records:
        try:
            config = PanchayatConfig(
                panchayat_id=str(item["panchayat_id"]),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                elevation_m=None if item.get("elevation_m") is None else float(item["elevation_m"]),
                slope_deg=None if item.get("slope_deg") is None else float(item["slope_deg"]),
                aspect_deg=None if item.get("aspect_deg") is None else float(item["aspect_deg"]),
                distance_to_water_m=None
                if item.get("distance_to_water_m") is None
                else float(item["distance_to_water_m"]),
                coarse_latitude=None
                if item.get("coarse_latitude") is None
                else float(item["coarse_latitude"]),
                coarse_longitude=None
                if item.get("coarse_longitude") is None
                else float(item["coarse_longitude"]),
                coarse_elevation_m=None
                if item.get("coarse_elevation_m") is None
                else float(item["coarse_elevation_m"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IngestionError(f"Invalid Panchayat registry record: {item}") from exc
        registry[config.panchayat_id] = config
    return registry


def build_features(
    config: PanchayatConfig,
    forecasts: Sequence[CoarseForecast],
    *,
    terrain: Mapping[str, float] | None = None,
    aws_residuals: Sequence[AWSResidual] | None = None,
    pipeline: FeaturePipeline | None = None,
) -> tuple[object, PanchayatTarget]:
    """Combine live provider data with DEM/AWS features."""

    attributes = dict(terrain or {})
    target = PanchayatTarget(
        panchayat_id=config.panchayat_id,
        latitude=config.latitude,
        longitude=config.longitude,
        elevation_m=float(attributes.get("elevation_m", config.elevation_m or forecasts[0].elevation_m)),
        slope_deg=attributes.get("slope_deg", config.slope_deg),
        aspect_deg=attributes.get("aspect_deg", config.aspect_deg),
        distance_to_water_m=attributes.get("distance_to_water_m", config.distance_to_water_m),
    )
    result = (pipeline or FeaturePipeline()).build(
        forecasts,
        target,
        nearby_aws=aws_residuals,
    )
    return result, target