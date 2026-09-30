"""Comprehensive test suite for the Agromet Government Portal upgrade."""

import pytest
from fastapi.testclient import TestClient
import agromet.main as main


@pytest.fixture
def client():
    return TestClient(main.app)


def test_public_portal_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Telangana Agromet Decision Support Portal" in response.text
    # Ensure no API key inputs are in public auth forms
    assert "loginKey" not in response.text
    assert "legacy pilot fallback" not in response.text


def test_auth_registration_and_login_flow(client):
    from uuid import uuid4
    test_email = f"ramesh.farmer.{uuid4().hex[:6]}@agromet.gov.in"
    # Register a new citizen/farmer
    reg_payload = {
        "full_name": "Ramesh Goud",
        "email": test_email,
        "mobile": "9876543210",
        "password": "SecurePassword@123",
        "role": "citizen"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in (200, 201)
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_email
    assert "citizen" in data["user"]["roles"]

    # Login with credentials
    login_res = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "SecurePassword@123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data


def test_panchayats_hierarchical_structure(client):
    response = client.get("/api/v1/panchayats")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 4
    first = items[0]
    assert "panchayat_id" in first
    assert "district" in first
    assert "mandal" in first
    assert "latitude" in first
    assert "longitude" in first


def test_crop_intelligence_endpoints(client):
    # List crops
    crops_res = client.get("/api/v1/crops")
    assert crops_res.status_code == 200
    crops = crops_res.json()
    assert len(crops) >= 4
    crop_ids = [c["crop_id"] for c in crops]
    assert "paddy" in crop_ids
    assert "cotton" in crop_ids

    # Crop advisory for paddy in 201001
    adv_res = client.get("/api/v1/crops/paddy/advisory/201001")
    assert adv_res.status_code == 200
    adv = adv_res.json()
    assert adv["crop_id"] == "paddy"
    assert "recommendations" in adv
    assert len(adv["recommendations"]) > 0


def test_early_warnings_endpoint(client):
    response = client.get("/api/v1/early-warnings")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "alerts" in data
    assert "critical" in data["summary"]


def test_system_health_endpoints(client):
    # /api/health
    h1 = client.get("/api/health")
    assert h1.status_code == 200
    assert h1.json()["status"] == "operational"

    # /api/health/database
    h2 = client.get("/api/health/database")
    assert h2.status_code == 200
    assert h2.json()["status"] == "operational"

    # /api/health/weather
    h3 = client.get("/api/health/weather")
    assert h3.status_code == 200
    assert h3.json()["status"] == "operational"

    # /api/health/ml
    h4 = client.get("/api/health/ml")
    assert h4.status_code == 200
    assert h4.json()["status"] == "operational"

    # /api/health/security
    h5 = client.get("/api/health/security")
    assert h5.status_code == 200
    assert h5.json()["status"] == "operational"


def test_governance_audit_logs(client):
    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_grievance_status_update(client):
    # Create grievance
    grv_res = client.post("/api/v1/grievances", json={
        "name": "Srinivas Rao",
        "mobile": "9123456780",
        "category": "Forecast service",
        "subject": "Rainfall anomaly in Chevella",
        "description": "Observed localized heavy rainfall not reflected in downscaled advisory."
    })
    assert grv_res.status_code == 201
    grv_id = grv_res.json()["grievance_id"]

    # Update grievance status
    update_res = client.put(f"/api/v1/grievances/{grv_id}/status", json={
        "status": "under_review",
        "notes": "Assigned to District Agromet Officer for sensor verification.",
        "assigned_to": "Officer Chevella"
    })
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "under_review"
