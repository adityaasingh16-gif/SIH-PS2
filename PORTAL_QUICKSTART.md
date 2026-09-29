# SIH26074 Portal Quick Start (Windows)

1. Open PowerShell in this project folder.
2. Run:

```powershell
uv sync --all-groups
```

3. Start the portal without PowerShell script execution-policy issues:

```text
scripts\run_demo.cmd
```

Or directly:

```powershell
uv run uvicorn agromet.main:app --host 127.0.0.1 --port 8000
```

4. Open:

`http://127.0.0.1:8000/`

API docs:

`http://127.0.0.1:8000/docs`

5. Run tests:

```text
scripts\test.cmd
```

Expected: `12 passed`.

The bundled M1 model is `m1-telangana-mock-v1` and is trained on synthetic development data. It is for demonstration and integration testing, not production accuracy claims.


## v1.5 production platform services

Set a strong session secret and provision the first administrator only during
initial deployment:

```powershell
$env:AGROMET_SESSION_SECRET="<long-random-secret>"
$env:AGROMET_BOOTSTRAP_ADMIN_EMAIL="admin@your-domain"
$env:AGROMET_BOOTSTRAP_ADMIN_PASSWORD="<strong-password>"
```

Optional recovery delivery:

```powershell
$env:AGROMET_SMTP_HOST="<smtp-host>"
$env:AGROMET_SMTP_PORT="587"
$env:AGROMET_SMTP_TLS="1"
$env:AGROMET_SMTP_USER="<smtp-user>"
$env:AGROMET_SMTP_PASSWORD="<smtp-password>"
$env:AGROMET_SMTP_FROM="no-reply@your-domain"
```

See `docs/platform.md` for the identity, RBAC, notification, security
telemetry, project/GIS, analytics, notices, documents and localization APIs.

For multi-instance production, migrate the repository implementation to
PostgreSQL and use a shared identity provider, object storage, centralized
telemetry and distributed rate limiting.
