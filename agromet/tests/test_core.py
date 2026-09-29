from datetime import date, timedelta

import agromet.ingestion as ingestion
from agromet.advisory_engine import (
    AdvisoryStatus,
    AdvisoryEngine,
    ET0Inputs,
    ForecastDay,
    calculate_et0_fao56,
)
from agromet.data_engine import CoarseForecast, FeaturePipeline, PanchayatTarget
from agromet.evaluator import ScorecardBuilder
from agromet.ingestion import IMDClient, OpenMeteoClient, PanchayatConfig, build_features
from agromet.storage import SQLiteRepository


def test_feature_pipeline_contains_lapse_and_cyclical_features() -> None:
    record = CoarseForecast(
        valid_date=date(2026, 6, 1),
        lead_day=1,
        tmax_c=35.0,
        tmin_c=25.0,
        relative_humidity_pct=70.0,
        wind_speed_kmh=8.0,
        rain_mm=2.0,
        elevation_m=100.0,
    )
    result = FeaturePipeline().build(
        [record],
        PanchayatTarget(
            panchayat_id="TG-001",
            latitude=17.4,
            longitude=78.4,
            elevation_m=600.0,
            aspect_deg=90.0,
        ),
    )
    row = result.features.iloc[0]
    assert row["tmax_lapse_adjusted_c"] == 31.75
    assert "doy_sin" in result.features
    assert "aspect_cos" in result.features
    assert result.warnings


def test_advisory_rules_and_et0_are_deterministic() -> None:
    start = date(2026, 6, 1)
    forecast = [
        ForecastDay(
            valid_date=start + timedelta(days=index),
            tmax_c=25.0,
            tmin_c=22.0,
            relative_humidity_pct=92.0,
            wind_speed_kmh=5.0,
            rain_probability_next_6h=0.1,
            rain_probability_15_6mm=0.4,
        )
        for index in range(3)
    ]
    batch = AdvisoryEngine().generate("TG-001", forecast)
    assert any(item.message_key == "rice_blast_risk" for item in batch.advisories)
    assert calculate_et0_fao56(
        ET0Inputs(
            tmax_c=32.0,
            tmin_c=24.0,
            relative_humidity_pct=65.0,
            wind_speed_2m_ms=2.0,
            net_radiation_mj_m2_day=18.0,
            elevation_m=500.0,
        )
    ) >= 0.0


def test_scorecard_markdown_has_all_requested_columns() -> None:
    markdown = ScorecardBuilder().compare_baselines(
        {
            "B0": ([1.0], [1.0], [True], [True], [0.6]),
            "B1": ([1.2], [1.0], [True], [True], [0.7]),
            "B1b": ([1.1], [1.0], [True], [True], [0.7]),
            "B2": ([1.0], [1.0], [True], [True], [0.8]),
            "M1": ([1.0], [1.0], [True], [True], [0.9]),
        },
        climatology_probability=[0.5],
        block_probability=[0.7],
    )
    assert "B1b" in markdown
    assert "BSS vs B0" in markdown


def test_open_meteo_payload_is_normalized_into_five_coarse_records(monkeypatch) -> None:
    daily = {
        "time": [f"2026-06-0{index}" for index in range(1, 6)],
        "temperature_2m_max": [35, 35, 34, 34, 33],
        "temperature_2m_min": [25, 25, 24, 24, 23],
        "relative_humidity_2m_mean": [70, 71, 72, 73, 74],
        "wind_speed_10m_max": [8, 9, 7, 8, 6],
        "precipitation_sum": [0, 2, 16, 0, 65],
        "shortwave_radiation_sum": [20, 20, 19, 19, 18],
    }
    monkeypatch.setattr(
        ingestion,
        "_fetch_json",
        lambda url: {"elevation": 480, "daily": daily},
    )
    forecasts, radiation = OpenMeteoClient().fetch(17.5, 78.5)
    assert len(forecasts) == 5
    assert forecasts[2].rain_mm == 16.0
    assert forecasts[0].net_radiation_mj_m2_day == 15.4
    assert radiation[-1] == 13.86


def test_imd_adapter_accepts_normalized_forecast_records(monkeypatch) -> None:
    records = [
        {
            "valid_date": f"2026-06-0{index}",
            "tmax_c": 35.0,
            "tmin_c": 25.0,
            "relative_humidity_pct": 70.0,
            "wind_speed_kmh": 8.0,
            "rain_mm": 2.0,
        }
        for index in range(1, 6)
    ]
    monkeypatch.setattr(ingestion, "_fetch_json", lambda url: {"forecast": records})
    forecasts, _ = IMDClient("https://imd.example/forecast").fetch(17.5, 78.5)
    assert len(forecasts) == 5
    assert forecasts[0].tmax_c == 35.0


def test_sqlite_repository_persists_and_audits_review_decisions(tmp_path) -> None:
    repository = SQLiteRepository(tmp_path / "pilot.sqlite3")
    forecast = [
        ForecastDay(
            valid_date=date(2026, 6, 1) + timedelta(days=index),
            tmax_c=25.0,
            tmin_c=22.0,
            relative_humidity_pct=92.0,
            wind_speed_kmh=5.0,
            rain_probability_next_6h=0.1,
            rain_probability_15_6mm=0.4,
        )
        for index in range(3)
    ]
    batch = AdvisoryEngine().generate("TG-001", forecast)
    repository.add_advisory_batch(batch)
    pending = repository.pending_advisories()
    assert pending

    approved = pending[0].model_copy(update={"status": AdvisoryStatus.APPROVED})
    repository.update_advisory(
        approved,
        reviewer_id="kvk-scientist-1",
        action="approve",
        notes="Reviewed against station observations.",
    )
    assert repository.pending_advisories() == [
        item for item in pending if item.advisory_id != approved.advisory_id
    ]
    assert repository.get_advisory(approved.advisory_id).status == AdvisoryStatus.APPROVED


def test_live_feature_builder_uses_registry_terrain_and_forecast_elevation() -> None:
    record = CoarseForecast(
        valid_date=date(2026, 6, 1),
        lead_day=1,
        tmax_c=35.0,
        tmin_c=25.0,
        relative_humidity_pct=70.0,
        wind_speed_kmh=8.0,
        rain_mm=2.0,
        elevation_m=480.0,
    )
    result, target = build_features(
        PanchayatConfig("TG-001", 17.4, 78.4, elevation_m=540.0, slope_deg=4.0),
        [record],
    )
    assert target.elevation_m == 540.0
    assert result.features.iloc[0]["elevation_delta_m"] == 60.0