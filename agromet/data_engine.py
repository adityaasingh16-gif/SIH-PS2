"""Forecast and terrain feature engineering for Panchayat downscaling.

The module deliberately keeps input records small and serialisable. A caller can
build the records from Open-Meteo, IMD, a raster sampler, or a database without
coupling the model to an ingestion provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from math import cos, radians, sin
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


class MissingInputError(ValueError):
    """Raised when strict feature extraction cannot continue."""


@dataclass(frozen=True, slots=True)
class CoarseForecast:
    """A single block/grid forecast valid for one lead day."""

    valid_date: date
    lead_day: int
    tmax_c: float
    tmin_c: float
    relative_humidity_pct: float
    wind_speed_kmh: float
    rain_mm: float
    elevation_m: float
    net_radiation_mj_m2_day: float | None = None


@dataclass(frozen=True, slots=True)
class PanchayatTarget:
    """Target Panchayat coordinate and terrain attributes sampled from DEM."""

    panchayat_id: str
    latitude: float
    longitude: float
    elevation_m: float
    slope_deg: float | None = None
    aspect_deg: float | None = None
    distance_to_water_m: float | None = None


@dataclass(frozen=True, slots=True)
class AWSResidual:
    """Previous-day station residual used for spatial residual nudging."""

    station_id: str
    latitude: float
    longitude: float
    residuals: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Physical and data-quality settings for feature extraction."""

    lapse_rate_c_per_km: float = -6.5
    idw_power: float = 2.0
    max_aws_distance_km: float = 100.0
    strict_missing_inputs: bool = False


@dataclass(frozen=True, slots=True)
class FeatureResult:
    """Combined model features and non-fatal ingestion warnings."""

    features: pd.DataFrame
    warnings: tuple[str, ...] = ()


def _great_circle_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return haversine distance; sufficient precision for station IDW weights."""

    earth_radius_km = 6371.0088
    lat_a, lat_b = radians(latitude_a), radians(latitude_b)
    delta_lat = lat_b - lat_a
    delta_lon = radians(longitude_b - longitude_a)
    hav = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * np.arcsin(np.sqrt(hav))


class FeaturePipeline:
    """Build terrain-aware, lag/lead-aware model matrices."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()

    def build(
        self,
        forecasts: Sequence[CoarseForecast],
        target: PanchayatTarget,
        *,
        nearby_aws: Sequence[AWSResidual] | None = None,
        satellite_features: Mapping[str, float] | None = None,
    ) -> FeatureResult:
        if not forecasts:
            raise MissingInputError("At least one coarse forecast record is required.")
        if not target.panchayat_id.strip():
            raise MissingInputError("panchayat_id cannot be empty.")

        warnings: list[str] = []
        ordered = sorted(forecasts, key=lambda item: item.lead_day)
        by_lead = {record.lead_day: record for record in ordered}
        residuals = self._interpolate_residuals(target, nearby_aws, warnings)

        if satellite_features is None:
            message = "Satellite features were not provided; satellite columns use NaN."
            self._handle_missing(message, warnings)
            satellite_features = {}

        rows: list[dict[str, float | int | str]] = []
        for record in ordered:
            delta_elevation = target.elevation_m - record.elevation_m
            lapse_delta = self.config.lapse_rate_c_per_km * delta_elevation / 1000.0
            doy = record.valid_date.timetuple().tm_yday
            aspect = target.aspect_deg if target.aspect_deg is not None else 0.0
            slope = target.slope_deg if target.slope_deg is not None else np.nan
            water = (
                target.distance_to_water_m
                if target.distance_to_water_m is not None
                else np.nan
            )

            row: dict[str, float | int | str] = {
                "panchayat_id": target.panchayat_id,
                "lead_day": record.lead_day,
                "valid_date_ordinal": record.valid_date.toordinal(),
                "latitude": target.latitude,
                "longitude": target.longitude,
                "tmax_c": record.tmax_c,
                "tmin_c": record.tmin_c,
                "relative_humidity_pct": record.relative_humidity_pct,
                "wind_speed_kmh": record.wind_speed_kmh,
                "rain_mm": record.rain_mm,
                "elevation_panchayat_m": target.elevation_m,
                "elevation_coarse_m": record.elevation_m,
                "elevation_delta_m": delta_elevation,
                "slope_deg": slope,
                "distance_to_water_m": water,
                "aspect_sin": sin(radians(aspect)),
                "aspect_cos": cos(radians(aspect)),
                "doy_sin": sin(2 * np.pi * doy / 365.25),
                "doy_cos": cos(2 * np.pi * doy / 365.25),
                "tmax_lapse_adjusted_c": record.tmax_c + lapse_delta,
                "tmin_lapse_adjusted_c": record.tmin_c + lapse_delta,
                "residual_tmax_c": residuals.get("tmax_c", 0.0),
                "residual_tmin_c": residuals.get("tmin_c", 0.0),
                "residual_relative_humidity_pct": residuals.get(
                    "relative_humidity_pct", 0.0
                ),
                "residual_wind_speed_kmh": residuals.get("wind_speed_kmh", 0.0),
                "residual_rain_mm": residuals.get("rain_mm", 0.0),
            }

            for key, value in satellite_features.items():
                row[f"satellite_{key}"] = float(value)

            for variable in (
                "tmax_c",
                "tmin_c",
                "relative_humidity_pct",
                "wind_speed_kmh",
                "rain_mm",
            ):
                for offset, suffix in ((-1, "lag1"), (1, "lead1")):
                    neighbor = by_lead.get(record.lead_day + offset)
                    row[f"{variable}_{suffix}"] = (
                        getattr(neighbor, variable) if neighbor is not None else np.nan
                    )
            rows.append(row)

        return FeatureResult(pd.DataFrame(rows), tuple(warnings))

    def _interpolate_residuals(
        self,
        target: PanchayatTarget,
        stations: Sequence[AWSResidual] | None,
        warnings: list[str],
    ) -> dict[str, float]:
        if not stations:
            self._handle_missing(
                "No previous-day AWS residuals were supplied; nudging is zero.",
                warnings,
            )
            return {}

        weighted: dict[str, float] = {}
        weights: dict[str, float] = {}
        for station in stations:
            distance = _great_circle_km(
                target.latitude,
                target.longitude,
                station.latitude,
                station.longitude,
            )
            if distance > self.config.max_aws_distance_km:
                continue
            if distance == 0:
                return {key: float(value) for key, value in station.residuals.items()}
            weight = 1.0 / distance**self.config.idw_power
            for key, value in station.residuals.items():
                weighted[key] = weighted.get(key, 0.0) + float(value) * weight
                weights[key] = weights.get(key, 0.0) + weight

        if not weights:
            self._handle_missing(
                "AWS stations were supplied but none were within the configured radius.",
                warnings,
            )
            return {}
        return {key: weighted[key] / weights[key] for key in weighted}

    def _handle_missing(self, message: str, warnings: list[str]) -> None:
        if self.config.strict_missing_inputs:
            raise MissingInputError(message)
        warnings.append(message)


def apply_lapse_rate(
    temperature_c: float,
    coarse_elevation_m: float,
    target_elevation_m: float,
    lapse_rate_c_per_km: float = -6.5,
) -> float:
    """Apply the standard environmental lapse rate of -6.5 C per km."""

    return temperature_c + lapse_rate_c_per_km * (
        target_elevation_m - coarse_elevation_m
    ) / 1000.0