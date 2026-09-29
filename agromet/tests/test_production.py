import json
from pathlib import Path

from fastapi.testclient import TestClient

import agromet.main as main


def test_optional_api_key_protects_kvk_actions(monkeypatch):
    monkeypatch.setenv("AGROMET_API_KEY", "secret")
    client = TestClient(main.app)
    assert client.get("/api/v1/advisories/kvk-pending").status_code == 401
    assert client.get("/api/v1/advisories/kvk-pending", headers={"X-API-Key": "secret"}).status_code == 200


def test_scorecard_endpoint_reads_persisted_evaluation(monkeypatch, tmp_path: Path):
    path = tmp_path / "scorecard.json"
    path.write_text(json.dumps({"markdown": "# evaluated", "models": [{"model": "M1"}]}))
    monkeypatch.setenv("AGROMET_SCORECARD_FILE", str(path))
    client = TestClient(main.app)
    response = client.get("/api/v1/scorecard")
    assert response.status_code == 200
    assert response.json()["markdown"] == "# evaluated"
    assert response.json()["models"] == [{"model": "M1"}]


def test_panchayat_registry_accepts_training_csv():
    from agromet.ingestion import load_panchayat_registry

    path = Path(__file__).parents[2] / "training_data" / "panchayat_registry.csv"
    registry = load_panchayat_registry(path)
    assert set(registry) == {"201001", "201002", "201003", "201004"}
    assert registry["201001"].latitude == 17.308


def test_trained_model_refresh_with_mock_upstream(monkeypatch):
    from datetime import date, timedelta
    from agromet.data_engine import CoarseForecast

    monkeypatch.setenv(
        "AGROMET_MODEL_ARTIFACT",
        str(Path(__file__).parents[2] / "agromet" / "models" / "m1-telangana-mock-v1" / "model_bundle.joblib"),
    )
    monkeypatch.setitem(main.registry, "201001", main.registry.get("201001") or main.PanchayatConfig(
        panchayat_id="201001",
        latitude=17.308,
        longitude=78.134,
        elevation_m=530,
        slope_deg=2.1,
        aspect_deg=140,
        distance_to_water_m=1200,
        coarse_latitude=17.385,
        coarse_longitude=78.4867,
        coarse_elevation_m=490,
    ))
    records = [
        CoarseForecast(
            valid_date=date.today() + timedelta(days=i),
            lead_day=i,
            tmax_c=32.0,
            tmin_c=22.0,
            relative_humidity_pct=70.0,
            wind_speed_kmh=10.0,
            rain_mm=2.0,
            elevation_m=490.0,
        )
        for i in range(1, 6)
    ]
    monkeypatch.setattr(main.open_meteo, "fetch", lambda *args, **kwargs: (records, [20.0] * 5))
    monkeypatch.setattr(main, "fetch_aws_residuals", lambda: [])
    client = TestClient(main.app)
    response = client.post("/api/v1/forecast/panchayat/201001/refresh")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_version"] == "m1-telangana-mock-v1"
    assert len(payload["days"]) == 5
    assert payload["days"][0]["et0_mm_day"] is not None


def test_portal_and_panchayat_registry_endpoints(monkeypatch):
    monkeypatch.delenv("AGROMET_API_KEY", raising=False)
    client = TestClient(main.app)
    page = client.get("/")
    assert page.status_code == 200
    assert "Telangana Panchayat Agromet Portal" in page.text
    response = client.get("/api/v1/panchayats")
    assert response.status_code == 200
    assert {item["panchayat_id"] for item in response.json()} >= {"201001", "201002", "201003", "201004"}


def test_portal_summary_and_government_navigation():
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    page = client.get("/")
    assert page.status_code == 200
    for marker in [
        "Public information", "Citizen Services", "Officer Monitoring Workspace",
        "Administration & Governance", "Defensive Security Monitoring",
        "KVK / AMFU Scientist Review", "AI-enabled Panchayat-level",
    ]:
        assert marker in page.text
    summary = client.get("/api/v1/portal/summary")
    assert summary.status_code == 200
    assert summary.json()["total_panchayats"] >= 4


def test_grievance_submission_and_listing():
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    response = client.post(
        "/api/v1/grievances",
        json={
            "name": "Test Citizen",
            "mobile": "9876543210",
            "category": "Portal access",
            "subject": "Test grievance",
            "description": "This is a test grievance for the pilot portal.",
        },
    )
    assert response.status_code == 201
    grievance_id = response.json()["grievance_id"]
    assert grievance_id.startswith("GRV-")
    listed = client.get("/api/v1/grievances")
    assert listed.status_code == 200
    assert any(item["grievance_id"] == grievance_id for item in listed.json())
