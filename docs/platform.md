# Platform services

The portal now includes server-side support for the UI's governance and identity
surfaces.

## Identity

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/me`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`
- `POST /api/v1/auth/password/forgot`
- `POST /api/v1/auth/password/reset`
- `POST /api/v1/auth/password/otp/request`
- `POST /api/v1/auth/password/otp/reset`
- `POST /api/v1/auth/password/change`
- `POST /api/v1/auth/mfa/enroll`
- `POST /api/v1/auth/mfa/verify`

Sessions are signed with HMAC and persisted by hash. Passwords use PBKDF2-SHA256.
MFA implements TOTP (30-second codes). Recovery delivery requires SMTP or an
operator-controlled OTP webhook; the server does not expose recovery secrets in
production responses.

## RBAC

Built-in roles:

- citizen
- officer
- kvk
- admin

Admin-only directory endpoints manage users, roles and departments. Privileged
project, notice and document operations require an authenticated role. The
legacy `X-API-Key` can still authorize configured pilot endpoints for backwards
compatibility.

## Notifications

Notifications are persisted and support:

- global and user-targeted events
- read receipts
- unread counts
- server-side paging

Forecast refreshes create KVK-review notifications; grievance submission creates
a service notification; review decisions create audit/notification events.

## Risk

`GET /api/v1/risk/panchayat/{panchayat_id}` returns a transparent 0–100
deterministic risk score with factor contributions. These are forecast-factor
contributions, not fabricated SHAP values. A real per-prediction SHAP explainer
should only be added after the production M1 feature schema and explainer
contract are frozen.

## Security telemetry

Every request is recorded in the defensive security event table. Aggregates are
available to administrators through:

- `/api/v1/security/summary`
- `/api/v1/security/events`

The middleware records blocked, rate-limited, suspicious and anomalous responses.
It does not provide offensive security functionality.

## GIS / projects

- `/api/v1/gis/panchayats` returns GeoJSON.
- `/api/v1/projects` supports project records with district, mandal, block, state,
  status, progress and budget.
- Project milestones and inspections have their own endpoints.

## Analytics

Available:

- portal summary
- aggregate analytics
- financial progress
- risk/review/grievance trends

All analytics are derived from persisted records. Empty datasets remain empty.

## Notices and documents

Notices have a server-side CMS API with create/update/archive operations.
Documents have a metadata store with create/delete operations. A document
`storage_url` points to an externally managed object store or approved document
repository; the pilot does not silently turn SQLite into a file server.

## Localization

Advisories can be rendered and persisted in:

- English (`en`)
- Telugu (`te`)
- Hindi (`hi`)

Numerical source metrics are stored alongside each localization and are not
changed by the localization layer.

## Production deployment boundary

SQLite is retained for the pilot. For multi-instance production, move the
repository layer to managed PostgreSQL and use shared object storage, a
centralized identity provider, distributed rate limiting, centralized telemetry,
and a managed email/SMS gateway.

The bundled M1 artifact remains synthetic development data and must be replaced
with a validated historical AWS/forecast model before operational use.
