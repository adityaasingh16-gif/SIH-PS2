# SIH26074 Government Portal

The root route `/` serves a dependency-free, responsive government-style portal.

## Public
- Home and pilot overview
- Panchayat coverage transparency
- Forecast dashboard
- Reports and model evaluation
- Notices/empty-state handling
- Citizen services and grievance submission
- Help/accessibility information

## Officer / KVK
- Forecast generation and stored forecasts
- Deterministic advisories
- KVK review with optional API-key protection
- Review audit events

## Administration / Security
- Governance/RBAC presentation
- Defensive security monitoring placeholder that never fabricates events
- Audit event view backed by persisted KVK review events

## Data integrity
The UI uses real backend endpoints for registry, forecast, advisory, scorecard, grievances and audit events. It explicitly shows empty/unconnected states rather than inventing government projects, notices, users or security telemetry.

The bundled M1 model remains a synthetic development artifact until real Telangana/TGDPS/AWS training data are supplied.

## Access control

- The portal opens on a **sign-in view**. Public pages stay browsable, but the
  Officer, KVK Scientist and Administrator workspaces require a workspace
  session (role + display name, kept in `sessionStorage`).
- Privileged actions reuse the existing optional `X-API-Key` mechanism. The
  sign-in view verifies a key against the real
  `/api/v1/advisories/kvk-pending` endpoint and reports open-pilot mode when
  the server has no key configured. No users, passwords or sessions exist on
  the backend, so nothing is fabricated.
- The Projects view includes a schematic SVG location map plotted from real
  registry coordinates; marker color reflects stored-forecast availability.
- Tables support column sorting (coverage), expandable detail rows (forecast
  quantiles) and pagination with record counts (coverage, grievances, audit).
- The header bell opens a **Notifications** view built only from real sources
  (KVK queue, forecast-derived warnings, grievance timestamps); read/dismiss
  state is device-local and no timestamp is ever invented.
- KVK cards show "why this triggered" probability factor bars computed from
  real advisory `trigger_metrics`, labeled as analytical cues.
- **Settings** provides profile (display name with unsaved-change detection),
  appearance, toast preferences and device-data controls — all client-side.
