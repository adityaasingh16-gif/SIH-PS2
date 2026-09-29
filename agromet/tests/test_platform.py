
import os
from pathlib import Path

from fastapi.testclient import TestClient

def test_platform_identity_notifications_rbac_and_security(tmp_path, monkeypatch):
    db=tmp_path/"platform.sqlite3"
    monkeypatch.setenv("AGROMET_DB_PATH", str(db))
    monkeypatch.setenv("AGROMET_SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("AGROMET_BOOTSTRAP_ADMIN_EMAIL", "admin@example.test")
    monkeypatch.setenv("AGROMET_BOOTSTRAP_ADMIN_PASSWORD", "StrongAdminPassword123!")
    import importlib
    import agromet.main as main
    importlib.reload(main)
    client=TestClient(main.app)

    reg=client.post("/api/v1/auth/register",json={
        "email":"citizen@example.test","display_name":"Citizen Test",
        "password":"StrongCitizenPassword123!","mobile":"9876543210"})
    assert reg.status_code==201
    login=client.post("/api/v1/auth/login",json={"email":"citizen@example.test","password":"StrongCitizenPassword123!"})
    assert login.status_code==200
    token=login.json()["access_token"]
    h={"Authorization":f"Bearer {token}"}
    assert client.get("/api/v1/auth/me",headers=h).status_code==200
    assert client.get("/api/v1/auth/sessions",headers=h).status_code==200
    assert client.get("/api/v1/notifications",headers=h).status_code==200
    assert client.post("/api/v1/auth/mfa/enroll",headers=h).status_code==200

    admin=client.post("/api/v1/auth/login",json={"email":"admin@example.test","password":"StrongAdminPassword123!"})
    assert admin.status_code==200
    ah={"Authorization":f"Bearer {admin.json()['access_token']}"}
    assert client.get("/api/v1/users",headers=ah).status_code==200
    assert client.get("/api/v1/roles",headers=ah).status_code==200
    assert client.get("/api/v1/security/summary",headers=ah).status_code==200

    project=client.post("/api/v1/projects",headers=ah,json={"name":"Pilot Project","district":"Rangareddy","status":"planned"})
    assert project.status_code==201
    pid=project.json()["project_id"]
    assert client.post(f"/api/v1/projects/{pid}/milestones",headers=ah,json={"title":"Data integration"}).status_code==201
    assert client.get(f"/api/v1/projects/{pid}/milestones").status_code==200
    assert client.post(f"/api/v1/projects/{pid}/inspections",headers=ah,json={"inspector":"Officer"}).status_code==201
    assert client.get(f"/api/v1/projects/{pid}/inspections").status_code==200

    notice=client.post("/api/v1/notices",headers=ah,json={"title":"Test notice","body":"Test body","category":"general"})
    assert notice.status_code==201
    nid=notice.json()["notice_id"]
    assert client.put(f"/api/v1/notices/{nid}",headers=ah,json={"title":"Updated notice","body":"Updated body","category":"general"}).status_code==200

    doc=client.post("/api/v1/documents",headers=ah,json={"title":"Test report","category":"report"})
    assert doc.status_code==201
    did=doc.json()["document_id"]
    assert client.delete(f"/api/v1/documents/{did}",headers=ah).status_code==200

    assert client.get("/api/v1/analytics/trends").status_code==200
    assert client.get("/api/v1/gis/panchayats").status_code==200
