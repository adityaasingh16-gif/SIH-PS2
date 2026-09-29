# SIH26074 Agromet Portal v1.5 — Backend completeness release

This release extends the existing v1.4 pilot without replacing the working
forecast/ML/advisory pipeline.

## Added
- Persistent user accounts and signed sessions
- PBKDF2 password hashing and password policy
- Password recovery tokens and optional OTP recovery delivery
- TOTP MFA enrollment/verification
- RBAC for citizen/officer/KVK/admin
- User, role and department administration
- Persistent server-side notifications/read receipts
- 0–100 deterministic forecast risk score with factor contributions
- Defensive security telemetry, summaries and rate limiting
- Project/GIS GeoJSON endpoint
- Project records, milestones and inspections
- Analytics summary, financial progress and trends
- Notices CMS API
- Documents/report metadata API
- Advisory created/updated timestamps
- English/Telugu/Hindi persisted advisory localization
- Server-side paging parameters on production lists
- Profile update and password change
- Security headers

## Existing functionality preserved
- FastAPI forecast API
- Open-Meteo/IMD ingestion
- AWS residual interface
- SRTM terrain processing
- LightGBM M1 artifact loading
- probabilistic forecasts
- deterministic advisories
- KVK review/audit
- scorecard
- grievance service
- government-style portal

## Verification
- Python compile check passed
- 15 automated tests passed
- Isolated smoke tests passed for identity, RBAC, notifications, projects,
  security telemetry, analytics, GIS, notices, documents and forecast/risk APIs.

## Operational requirements
Set a strong `AGROMET_SESSION_SECRET`.
Provision `AGROMET_BOOTSTRAP_ADMIN_*` only during initial setup.
For password recovery, configure SMTP or `AGROMET_OTP_WEBHOOK_URL`.
For real operational deployment, migrate SQLite to PostgreSQL and connect the
approved departmental identity, data, document and monitoring systems.
