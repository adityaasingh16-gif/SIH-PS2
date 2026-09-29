# SIH26074 Agromet Government Portal v1.4

## Included
- Government-style public portal and navigation
- Panchayat forecast dashboard using the existing real API/model pipeline
- P10/P50/P90 weather presentation and rainfall probabilities
- Deterministic advisory/KVK review workflow
- Citizen grievance submission with durable SQLite tracking
- Officer monitoring workspace
- Administration/audit workspace
- Defensive security monitoring presentation without fabricated telemetry
- Reports/model-evaluation section
- Accessibility controls and responsive layout
- Explicit empty/unconnected states instead of fabricated government data
- Existing Swagger API remains available at `/docs`
- Existing trained `m1-telangana-mock-v1` artifact preserved

## Verification
- 14 automated tests passed
- Python compilation passed
- Portal, health, Panchayat registry, portal summary, grievances and Swagger endpoints smoke-tested with HTTP 200

## Production boundary
The bundled M1 artifact uses synthetic development data. Production operation requires approved IMD/TGDPS/AWS data, validated historical evaluation, departmental identity/RBAC, and production security/monitoring integrations.
