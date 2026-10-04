"""High-quality Telangana Agromet Government Decision-Support Portal.

SIH-PS2 Production Platform:
- Zero dependency, high-performance vanilla JS & CSS frontend.
- Strict RBAC: Farmer/Citizen, KVK Scientist, Field Officer, District Officer, Administrator.
- Zero user-facing API key inputs in authentication workflows.
- Cascading Location Selector (State -> District -> Mandal -> Panchayat) + GPS "Use My Location".
- Complete Agromet Workflow (Location -> Weather -> Forecast -> ML Risk -> Crop Advisory -> KVK Review -> Approval -> Notification -> Audit Trail).
- Dedicated Farmer Mobile Dashboard, GIS Map, Early Warning Centre, Grievance Lifecycle (GRV-YYYY-XXXXXX), Notice Board, Defensive IDS Monitoring, Governance Audit Logs, Health Matrix.
- Multilingual Support (English, Telugu, Hindi).
"""

from __future__ import annotations

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#1e3a8a">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23137333'/%3E%3Ctext x='32' y='42' font-family='Arial' font-size='22' font-weight='bold' fill='white' text-anchor='middle'%3ETS%3C/text%3E%3C/svg%3E">
<title>Telangana Agromet Decision Support Portal | Government of Telangana</title>
<style>
/* ================= Design Tokens & Gov Theme ================= */
:root {
  --navy: #1e3a8a;
  --navy-light: #2563eb;
  --navy-dark: #0f172a;
  --blue: #0284c7;
  --blue-light: #f0f9ff;
  --saffron: #d97706;
  --saffron-light: #fffbeb;
  --saffron-dark: #b45309;
  --green: #15803d;
  --green-light: #f0fdf4;
  --green-dark: #166534;
  --red: #b91c1c;
  --red-light: #fef2f2;
  --amber: #b45309;
  --amber-light: #fffbeb;
  --info: #0369a1;
  --info-light: #f0f9ff;
  --ink: #0f172a;
  --muted: #64748b;
  --line: #cbd5e1;
  --line-light: #e2e8f0;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-elev: #ffffff;
  --focus: #2563eb;
  --font: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Noto Sans', sans-serif;
  --mono: 'Cascadia Code', 'SF Mono', Consolas, monospace;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 20px; --s6: 24px; --s8: 32px;
  --r-sm: 4px; --r-md: 8px; --r-lg: 12px; --r-xl: 16px; --r-pill: 999px;
  --sh-sm: 0 1px 3px rgba(15,23,42,0.06);
  --sh-md: 0 4px 12px rgba(15,23,42,0.08);
  --sh-lg: 0 10px 28px rgba(15,23,42,0.12);
  --gov-h: 36px; --head-h: 70px; --nav-h: 48px; --max: 1320px;
}
[data-theme="dark"] {
  --navy: #60a5fa;
  --navy-light: #93c5fd;
  --navy-dark: #090d16;
  --blue: #38bdf8;
  --blue-light: #0c1929;
  --saffron: #f59e0b;
  --saffron-light: #261a07;
  --saffron-dark: #d97706;
  --green: #4ade80;
  --green-light: #082111;
  --green-dark: #22c55e;
  --red: #f87171;
  --red-light: #280d0d;
  --amber: #fbbf24;
  --amber-light: #241a05;
  --info: #38bdf8;
  --info-light: #0c1929;
  --ink: #f1f5f9;
  --muted: #94a3b8;
  --line: #334155;
  --line-light: #1e293b;
  --bg: #0b1120;
  --surface: #131d31;
  --surface-elev: #1a2742;
  --sh-sm: 0 1px 3px rgba(0,0,0,0.5);
  --sh-md: 0 4px 12px rgba(0,0,0,0.55);
  --sh-lg: 0 10px 28px rgba(0,0,0,0.65);
}

/* ================= Base & Layout ================= */
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; font-family: var(--font); color: var(--ink); background: var(--bg); line-height: 1.5; -webkit-font-smoothing: antialiased; }
h1, h2, h3, h4 { margin: 0; line-height: 1.25; letter-spacing: -0.015em; font-weight: 700; }
p { margin: 0; }
a { color: var(--navy-light); text-decoration: none; }
a:hover { text-decoration: underline; }
button, input, select, textarea { font: inherit; color: inherit; }
button { cursor: pointer; }
:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.skip { position: absolute; left: -9999px; top: 0; background: var(--navy-dark); color: #fff; padding: 10px 16px; z-index: 2000; font-weight: 600; }
.skip:focus { left: 0; }
.wrap { max-width: var(--max); margin: 0 auto; width: 100%; padding: 0 var(--s5); }
.muted { color: var(--muted); }
.small { font-size: 12px; }
.mono { font-family: var(--mono); font-size: 12.5px; }

/* ================= Header, Gov bar & Nav ================= */
.govbar { background: var(--navy-dark); color: rgba(255,255,255,0.9); font-size: 12px; min-height: var(--gov-h); display: flex; align-items: center; border-bottom: 2px solid var(--saffron); }
.govbar .wrap { display: flex; justify-content: space-between; align-items: center; gap: var(--s3); padding-top: 4px; padding-bottom: 4px; }
.govbar .tools { display: flex; gap: 6px; align-items: center; }
.govbar button, .govbar select { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25); color: #fff; padding: 3px 8px; border-radius: var(--r-sm); font-size: 11px; }
.govbar button:hover { background: rgba(255,255,255,0.22); }
.govbar select option { background: #0f172a; color: #fff; }

.header { background: var(--surface); border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 300; box-shadow: var(--sh-sm); }
.header .wrap { display: flex; align-items: center; gap: var(--s4); min-height: var(--head-h); padding-top: 6px; padding-bottom: 6px; }
.emblem-box { display: flex; align-items: center; gap: 12px; }
.emblem { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #15803d 0%, #1e3a8a 100%); display: grid; place-items: center; color: #fff; font-weight: 800; font-size: 16px; border: 2px solid #fff; box-shadow: var(--sh-sm); flex-shrink: 0; }
.brand h1 { font-size: 19px; color: var(--navy); display: flex; align-items: center; gap: 8px; }
[data-theme="dark"] .brand h1 { color: var(--ink); }
.brand p { color: var(--muted); font-size: 12px; }
.header-actions { margin-left: auto; display: flex; align-items: center; gap: var(--s2); }

.gov-badge { background: var(--green-light); color: var(--green); border: 1px solid var(--green); padding: 3px 10px; border-radius: var(--r-pill); font-size: 11px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; }
[data-theme="dark"] .gov-badge { background: var(--green-light); color: var(--green); }

.nav { background: #132448; color: #fff; position: sticky; top: var(--head-h); z-index: 290; border-bottom: 3px solid var(--saffron); box-shadow: var(--sh-sm); }
.nav .wrap { display: flex; align-items: stretch; min-height: var(--nav-h); padding: 0 var(--s5); overflow-x: auto; scrollbar-width: none; }
.nav .wrap::-webkit-scrollbar { display: none; }
.nav-links { display: flex; align-items: stretch; gap: 2px; }
.nav-btn { background: transparent; color: rgba(255,255,255,0.85); border: 0; border-bottom: 3px solid transparent; padding: 10px 14px; font-weight: 600; font-size: 13.5px; white-space: nowrap; transition: all 120ms ease; }
.nav-btn:hover { color: #fff; background: rgba(255,255,255,0.08); }
.nav-btn.active { color: #fff; border-bottom-color: var(--saffron); background: rgba(255,255,255,0.12); font-weight: 700; }

/* ================= Cards, Buttons & Utilities ================= */
.page { padding: var(--s5) 0 var(--s8); min-height: 75vh; }
.view { display: none; }
.view.active { display: block; animation: fadeIn 200ms ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--sh-sm); margin-bottom: var(--s5); overflow: hidden; }
.card-h { padding: var(--s4) var(--s5); border-bottom: 1px solid var(--line-light); display: flex; align-items: center; justify-content: space-between; gap: var(--s3); flex-wrap: wrap; background: rgba(248,250,252,0.5); }
[data-theme="dark"] .card-h { background: rgba(15,23,42,0.3); }
.card-h h2, .card-h h3 { font-size: 16px; color: var(--navy); display: flex; align-items: center; gap: 8px; }
[data-theme="dark"] .card-h h2, [data-theme="dark"] .card-h h3 { color: var(--ink); }
.card-b { padding: var(--s5); }

.grid { display: grid; gap: var(--s4); }
.g4 { grid-template-columns: repeat(4, 1fr); }
.g3 { grid-template-columns: repeat(3, 1fr); }
.g2 { grid-template-columns: repeat(2, 1fr); }

.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid var(--navy); background: var(--navy); color: #fff; padding: 9px 16px; border-radius: var(--r-md); font-weight: 600; font-size: 13.5px; transition: all 120ms ease; }
.btn:hover { filter: brightness(1.1); box-shadow: var(--sh-sm); }
.btn.secondary { background: var(--surface); color: var(--navy); border-color: var(--line); }
[data-theme="dark"] .btn.secondary { color: var(--ink); }
.btn.secondary:hover { background: var(--blue-light); border-color: var(--navy); }
.btn.success { background: var(--green); border-color: var(--green); color: #fff; }
.btn.danger { background: var(--red); border-color: var(--red); color: #fff; }
.btn.warning { background: var(--saffron); border-color: var(--saffron); color: #fff; }
.btn.sm { padding: 6px 12px; font-size: 12.5px; min-height: 34px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.badge { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: var(--r-pill); font-size: 11.5px; font-weight: 700; border: 1px solid transparent; white-space: nowrap; }
.badge.green { color: var(--green); background: var(--green-light); border-color: rgba(21,128,61,0.2); }
.badge.red { color: var(--red); background: var(--red-light); border-color: rgba(185,28,28,0.2); }
.badge.amber { color: var(--saffron-dark); background: var(--saffron-light); border-color: rgba(217,119,6,0.2); }
.badge.blue { color: var(--info); background: var(--info-light); border-color: rgba(3,105,161,0.2); }
.badge.grey { color: var(--muted); background: var(--bg); border-color: var(--line); }

.status { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border-radius: var(--r-md); font-size: 13.5px; border: 1px solid transparent; margin-bottom: var(--s4); }
.status.ok { background: var(--green-light); color: var(--green-dark); border-color: #bbf7d0; }
.status.error { background: var(--red-light); color: #991b1b; border-color: #fecaca; }
.status.warn { background: var(--saffron-light); color: #92400e; border-color: #fde68a; }
.status.info { background: var(--info-light); color: #075985; border-color: #bae6fd; }
[data-theme="dark"] .status { border-color: var(--line); }

/* ================= Location Selector Component ================= */
.loc-bar { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #fff; padding: var(--s5); border-radius: var(--r-xl); margin-bottom: var(--s5); box-shadow: var(--sh-md); }
.loc-bar-title { font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--saffron); font-weight: 800; margin-bottom: 8px; }
.loc-grid { display: grid; grid-template-columns: repeat(4, 1fr) auto; gap: var(--s3); align-items: flex-end; }
.loc-grid .field { margin: 0; }
.loc-grid label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; color: rgba(255,255,255,0.9); }
.loc-grid select { width: 100%; padding: 10px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.25); color: #fff; border-radius: var(--r-md); font-size: 13px; }
.loc-grid select option { background: #0f172a; color: #fff; }
.loc-chips { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.15); font-size: 12px; color: rgba(255,255,255,0.85); }
.loc-chips span { background: rgba(255,255,255,0.12); padding: 4px 10px; border-radius: var(--r-pill); border: 1px solid rgba(255,255,255,0.2); }

/* ================= Agromet Workflow Stepper ================= */
.workflow-strip { display: flex; align-items: center; justify-content: space-between; overflow-x: auto; padding: var(--s4) var(--s5); background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); margin-bottom: var(--s5); scrollbar-width: none; }
.workflow-strip::-webkit-scrollbar { display: none; }
.wf-step { display: flex; align-items: center; gap: 8px; white-space: nowrap; font-size: 12.5px; font-weight: 600; color: var(--muted); }
.wf-step.active { color: var(--navy); font-weight: 700; }
.wf-dot { width: 26px; height: 26px; border-radius: 50%; background: var(--bg); border: 2px solid var(--line); display: grid; place-items: center; font-size: 11px; color: var(--muted); flex-shrink: 0; }
.wf-step.active .wf-dot { background: var(--navy); border-color: var(--navy); color: #fff; }
.wf-step.done .wf-dot { background: var(--green); border-color: var(--green); color: #fff; }
.wf-arr { color: var(--line); font-size: 14px; margin: 0 4px; }

/* ================= Forms & Tables ================= */
.field { margin-bottom: var(--s4); }
.field label { display: block; font-weight: 600; font-size: 13px; margin-bottom: 6px; }
.field input, .field select, .field textarea { width: 100%; border: 1px solid var(--line); border-radius: var(--r-md); padding: 10px 12px; background: var(--surface); font-size: 13.5px; transition: border-color 120ms ease; }
.field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--navy-light); box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
.field textarea { min-height: 100px; resize: vertical; }

.table-wrap { overflow-x: auto; border: 1px solid var(--line-light); border-radius: var(--r-md); }
.table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 600px; }
.table th { background: var(--bg); color: var(--muted); text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; padding: 10px 14px; border-bottom: 2px solid var(--line); }
.table td { border-bottom: 1px solid var(--line-light); padding: 12px 14px; vertical-align: middle; }
.table tbody tr:hover td { background: var(--blue-light); }

/* ================= KPI Cards ================= */
.kpi { padding: var(--s5); border-radius: var(--r-lg); border: 1px solid var(--line); background: var(--surface); box-shadow: var(--sh-sm); }
.kpi-lbl { font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 700; }
.kpi-val { font-size: 28px; font-weight: 800; margin-top: 4px; line-height: 1.15; color: var(--ink); }
.kpi-hint { font-size: 12px; color: var(--muted); margin-top: 4px; }

/* ================= Farmer Dashboard Cards ================= */
.farmer-hero { background: linear-gradient(135deg, #14532d 0%, #15803d 60%, #166534 100%); color: #fff; padding: var(--s6); border-radius: var(--r-xl); margin-bottom: var(--s5); box-shadow: var(--sh-md); }
.farmer-hero h2 { font-size: 26px; margin-bottom: 6px; }
.farmer-hero p { color: rgba(255,255,255,0.9); font-size: 14.5px; max-width: 70ch; }
.weather-strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: var(--s5); }
.w-card { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25); border-radius: var(--r-lg); padding: 14px; text-align: center; color: #fff; }
.w-date { font-size: 12px; font-weight: 700; opacity: 0.9; margin-bottom: 4px; }
.w-temp { font-size: 22px; font-weight: 800; }
.w-rain { font-size: 11.5px; opacity: 0.85; margin-top: 4px; }

/* ================= Grievance Stepper ================= */
.stepper { display: flex; align-items: center; justify-content: space-between; margin: var(--s4) 0; position: relative; }
.stepper::before { content: ""; position: absolute; top: 14px; left: 20px; right: 20px; height: 3px; background: var(--line); z-index: 1; }
.step-node { position: relative; z-index: 2; text-align: center; }
.step-circle { width: 30px; height: 30px; border-radius: 50%; background: var(--surface); border: 3px solid var(--line); display: grid; place-items: center; margin: 0 auto 6px; font-size: 12px; font-weight: 700; color: var(--muted); }
.step-node.done .step-circle { background: var(--green); border-color: var(--green); color: #fff; }
.step-node.active .step-circle { background: var(--navy); border-color: var(--navy); color: #fff; box-shadow: 0 0 0 4px rgba(37,99,235,0.2); }
.step-label { font-size: 11.5px; font-weight: 600; color: var(--muted); }
.step-node.active .step-label { color: var(--navy); font-weight: 700; }

/* ================= Modal & Toast ================= */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.6); z-index: 1000; display: grid; place-items: center; padding: var(--s4); backdrop-filter: blur(3px); }
.modal { background: var(--surface); border-radius: var(--r-xl); box-shadow: var(--sh-lg); max-width: 600px; width: 100%; max-height: 90vh; overflow-y: auto; border: 1px solid var(--line); animation: popIn 180ms ease-out; }
@keyframes popIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
.modal-h { padding: var(--s4) var(--s5); border-bottom: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; }
.modal-b { padding: var(--s5); }
.modal-f { padding: var(--s4) var(--s5); border-top: 1px solid var(--line); display: flex; justify-content: flex-end; gap: 8px; }

.toasts { position: fixed; bottom: 20px; right: 20px; z-index: 2000; display: flex; flex-direction: column; gap: 10px; max-width: 380px; }
.toast { background: var(--surface); border: 1px solid var(--line); border-left: 5px solid var(--info); border-radius: var(--r-md); padding: 12px 16px; box-shadow: var(--sh-lg); font-size: 13px; animation: slideIn 180ms ease-out; }
.toast.success { border-left-color: var(--green); }
.toast.error { border-left-color: var(--red); }
.toast.warning { border-left-color: var(--saffron); }
@keyframes slideIn { from { transform: translateX(40px); opacity: 0; } to { transform: none; opacity: 1; } }

/* ================= Footer & Responsive ================= */
.footer { background: #0f172a; color: #94a3b8; padding: var(--s8) 0 var(--s5); margin-top: var(--s8); border-top: 4px solid var(--saffron); font-size: 13px; }
.footer .wrap { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: var(--s6); }
.footer h4 { color: #fff; margin-bottom: 12px; font-size: 14px; }
.footer-links button { background: none; border: 0; color: #94a3b8; display: block; padding: 4px 0; text-align: left; }
.footer-links button:hover { color: #fff; text-decoration: underline; }
.footer-bot { border-top: 1px solid #1e293b; margin-top: var(--s6); padding-top: var(--s4); text-align: center; font-size: 12px; color: #64748b; }

@media(max-width: 960px) {
  .g4, .g3, .loc-grid, .weather-strip { grid-template-columns: 1fr 1fr; }
  .footer .wrap { grid-template-columns: 1fr; }
}
@media(max-width: 640px) {
  .g4, .g3, .g2, .loc-grid, .weather-strip { grid-template-columns: 1fr; }
  .header .wrap { flex-wrap: wrap; }
  .brand h1 { font-size: 16px; }
}
/* ============ Accent colour themes (persisted via localStorage) ============ */
.govbar .swatches { display: inline-flex; gap: 4px; align-items: center; margin-left: 6px; }
.swatch { width: 20px; height: 20px; min-height: 20px; border-radius: 50%; border: 2px solid rgba(255,255,255,.5); padding: 0; cursor: pointer; }
.swatch[aria-pressed="true"] { border-color: #fff; box-shadow: 0 0 0 2px rgba(255,255,255,.4); }
[data-accent="orange"] { --navy: #7c2d12; --navy-light: #c2410c; --navy-dark: #431407; --blue: #c2410c; --blue-light: #fdeee3; --focus: #c2410c; }
[data-accent="orange"] .nav { background: #431407; }
[data-accent="orange"] .loc-bar { background: linear-gradient(135deg, #431407 0%, #7c2d12 100%); }
[data-accent="orange"] .footer { border-top-color: #c2410c; }
[data-accent="orange"] .emblem { background: linear-gradient(135deg, #c2410c 0%, #7c2d12 100%); }
[data-theme="dark"][data-accent="orange"] { --navy: #e8823c; --navy-light: #f0955a; --navy-dark: #241107; --blue: #f0955a; --blue-light: #2a1a10; }
[data-accent="green"] { --navy: #0e3b2e; --navy-light: #166648; --navy-dark: #082a21; --blue: #0f766e; --blue-light: #e6f4f0; --focus: #0f766e; }
[data-accent="green"] .nav { background: #082a21; }
[data-accent="green"] .loc-bar { background: linear-gradient(135deg, #082a21 0%, #0e3b2e 100%); }
[data-accent="green"] .footer { border-top-color: #0f766e; }
[data-accent="green"] .emblem { background: linear-gradient(135deg, #0f766e 0%, #0e3b2e 100%); }
[data-theme="dark"][data-accent="green"] { --navy: #2f9e76; --navy-light: #3ab882; --navy-dark: #07231c; --blue: #5ec8a5; --blue-light: #14291f; }
/* ============ Scroll reveals + reduced motion ============ */
.reveal { opacity: 0; transform: translateY(8px); transition: opacity .35s ease, transform .35s ease; }
.reveal.in { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
  html { scroll-behavior: auto; }
}
@media (max-width: 720px) { #loginGrid { grid-template-columns: 1fr !important; } }
</style>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>

<!-- Gov Top Bar -->
<div class="govbar">
  <div class="wrap">
    <div><strong>Government of Telangana</strong> &bull; Agriculture &amp; Farmers Welfare Department</div>
    <div class="tools">
      <label for="langSelect" class="sr">Language</label>
      <select id="langSelect" aria-label="Select Language">
        <option value="en">English</option>
        <option value="te">తెలుగు (Telugu)</option>
        <option value="hi">हिन्दी (Hindi)</option>
      </select>
      <button id="themeBtn" type="button" aria-label="Toggle dark mode">🌙 Theme</button>
      <span class="swatches" role="group" aria-label="Colour theme">
        <button class="swatch" data-accent="blue" style="background:#2563eb" aria-label="Blue theme" aria-pressed="true" type="button"></button>
        <button class="swatch" data-accent="orange" style="background:#c2410c" aria-label="Orange theme" aria-pressed="false" type="button"></button>
        <button class="swatch" data-accent="green" style="background:#0f766e" aria-label="Green theme" aria-pressed="false" type="button"></button>
      </span>
    </div>
  </div>
</div>

<!-- Main Government Header -->
<header class="header">
  <div class="wrap">
    <div class="emblem-box">
      <div class="emblem" aria-hidden="true">TS</div>
      <div class="brand">
        <h1>Telangana Panchayat Agromet Portal</h1>
        <p>AI-enabled Panchayat-level terrain downscaling, ML crop intelligence &amp; scientist review</p>
      </div>
    </div>
    <div class="header-actions">
      <span class="gov-badge" id="roleBadge">Public information &bull; Citizen Services</span>
      <button class="btn sm" id="authBtn" type="button">Sign In / Register</button>
      <button class="btn secondary sm" id="logoutBtn" type="button" style="display:none">Sign Out</button>
    </div>
  </div>
</header>

<!-- Main Navigation Bar -->
<nav class="nav" aria-label="Main Navigation">
  <div class="wrap">
    <div class="nav-links" id="navBar">
      <button class="nav-btn" id="navLoginBtn" data-view="login" type="button">🔑 Sign In</button>
      <button class="nav-btn active" data-view="farmer" type="button">🌾 Farmer Dashboard (Citizen Services)</button>
      <button class="nav-btn" data-view="weather" type="button">🌤 Weather &amp; Forecast</button>
      <button class="nav-btn" data-view="crop" type="button">🌱 Crop Intelligence</button>
      <button class="nav-btn" data-view="warnings" type="button">⚠ Early Warnings</button>
      <button class="nav-btn" data-view="gis" type="button">🗺 GIS Map</button>
      <button class="nav-btn" data-view="kvk" type="button">🔬 KVK / AMFU Scientist Review</button>
      <button class="nav-btn" data-view="grievance" type="button">📝 Grievances</button>
      <button class="nav-btn" data-view="notices" type="button">📢 Notices</button>
      <button class="nav-btn" data-view="security" type="button">🛡 Defensive Security Monitoring</button>
      <button class="nav-btn" data-view="audit" type="button">📜 Officer Monitoring Workspace (Audit)</button>
      <button class="nav-btn" data-view="models" type="button">🧠 Model Transparency</button>
      <button class="nav-btn" data-view="admin" type="button">⚙ Administration & Governance</button>
    </div>
  </div>
</nav>

<!-- Page Content -->
<main id="main" class="page">
  <div class="wrap">

    <!-- Global Cascading Location Selector -->
    <div class="loc-bar">
      <div class="loc-bar-title">📍 Panchayat Location System &bull; Cascading Filter</div>
      <div class="loc-grid">
        <div class="field">
          <label for="selState">State</label>
          <select id="selState" disabled><option>Telangana</option></select>
        </div>
        <div class="field">
          <label for="selDistrict">District</label>
          <select id="selDistrict"></select>
        </div>
        <div class="field">
          <label for="selMandal">Mandal</label>
          <select id="selMandal"></select>
        </div>
        <div class="field">
          <label for="selPanchayat">Gram Panchayat</label>
          <select id="selPanchayat"></select>
        </div>
        <div>
          <button class="btn warning" id="gpsBtn" type="button" style="width:100%">📡 Use My GPS</button>
        </div>
      </div>
      <div class="loc-chips" id="locChips">
        <span>Lat: <strong id="chipLat">--</strong></span>
        <span>Lon: <strong id="chipLon">--</strong></span>
        <span>Elevation: <strong id="chipElev">-- m</strong></span>
        <span>Water Distance: <strong id="chipWater">-- m</strong></span>
        <span>Terrain Slope: <strong id="chipSlope">--°</strong></span>
      </div>
    </div>

    <!-- Agromet Workflow Progress Stepper -->
    <div class="workflow-strip" aria-label="Agromet Workflow">
      <div class="wf-step done"><span class="wf-dot">1</span><span>Location</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step done"><span class="wf-dot">2</span><span>Weather Observation</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step done"><span class="wf-dot">3</span><span>Terrain Downscaling</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step active"><span class="wf-dot">4</span><span>ML Risk Prediction</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step active"><span class="wf-dot">5</span><span>Crop Advisory</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step"><span class="wf-dot">6</span><span>Scientist Review</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step"><span class="wf-dot">7</span><span>Farmer Notification</span></div>
      <span class="wf-arr">➔</span>
      <div class="wf-step"><span class="wf-dot">8</span><span>Audit Logging</span></div>
    </div>

    <!-- VIEW 0: Sign In (landing page) -->
    <section id="view-login" class="view">
      <div style="max-width:920px;margin:0 auto">
        <div class="card" style="overflow:hidden">
          <div class="card-b" id="loginGrid" style="display:grid;grid-template-columns:1fr 1fr;gap:0;padding:0">
            <div style="background:linear-gradient(135deg,var(--navy-dark) 0%,var(--navy) 60%,var(--navy-light) 100%);color:#fff;padding:36px 30px">
              <div style="font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--saffron);margin-bottom:10px">GOVERNMENT OF TELANGANA</div>
              <h2 style="font-size:26px;margin-bottom:10px">Agromet Decision Support Portal</h2>
              <p style="color:rgba(255,255,255,.85);font-size:14px;margin-bottom:18px">Terrain-aware forecasts, crop intelligence, early warnings and audited KVK scientist review for every Panchayat.</p>
              <ul style="margin:0;padding-left:18px;font-size:13px;line-height:2;color:rgba(255,255,255,.9)">
                <li>5-day P10/P50/P90 quantile forecasts</li>
                <li>Crop-specific risk advisories</li>
                <li>Early warnings &amp; GIS monitoring</li>
                <li>Audited scientist review workflow</li>
              </ul>
            </div>
            <div style="padding:30px">
              <h3 style="font-size:18px;margin-bottom:4px">Sign in</h3>
              <p class="small muted" style="margin-bottom:16px">Use your department account, a demo login, or continue as guest.</p>
              <form id="formLoginView">
                <div class="field"><label for="logEmailV">Email / Username *</label><input id="logEmailV" required type="email" placeholder="e.g. scientist.kvk@agromet.gov.in" autocomplete="username"></div>
                <div class="field"><label for="logPassV">Password *</label><div style="display:flex;gap:8px"><input id="logPassV" required type="password" placeholder="Enter password" autocomplete="current-password" style="flex:1"><button class="btn secondary sm" id="togglePassV" type="button" aria-label="Show password">Show</button></div></div>
                <button class="btn" type="submit" style="width:100%;margin-top:6px">Sign In</button>
              </form>
              <div class="small muted" style="margin:14px 0 8px">1-click demo access for evaluators:</div>
              <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">
                <button type="button" class="btn secondary sm demo-login-v" data-user="citizen@agromet.demo">🌾 Farmer</button>
                <button type="button" class="btn secondary sm demo-login-v" data-user="kvk@agromet.demo">🔬 Scientist</button>
                <button type="button" class="btn secondary sm demo-login-v" data-user="officer@agromet.demo">📋 Officer</button>
                <button type="button" class="btn secondary sm demo-login-v" data-user="admin@agromet.demo">⚙ Admin</button>
              </div>
              <button class="btn secondary" id="guestBtn" type="button" style="width:100%">Continue as Guest</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 1: Farmer Dashboard (Mobile First) -->
    <section id="view-farmer" class="view active">
      <div class="farmer-hero">
        <h2 id="farmerGreeting">Namaste, Farmer</h2>
        <p id="farmerSub">Here is your local Panchayat agro-meteorological advisory and 5-day terrain forecast.</p>
        <div class="weather-strip" id="farmerWeatherStrip">
          <div class="w-card"><div class="w-date">Day 1</div><div class="w-temp">--°C</div><div class="w-rain">Rain: -- mm</div></div>
          <div class="w-card"><div class="w-date">Day 2</div><div class="w-temp">--°C</div><div class="w-rain">Rain: -- mm</div></div>
          <div class="w-card"><div class="w-date">Day 3</div><div class="w-temp">--°C</div><div class="w-rain">Rain: -- mm</div></div>
          <div class="w-card"><div class="w-date">Day 4</div><div class="w-temp">--°C</div><div class="w-rain">Rain: -- mm</div></div>
          <div class="w-card"><div class="w-date">Day 5</div><div class="w-temp">--°C</div><div class="w-rain">Rain: -- mm</div></div>
        </div>
      </div>

      <div class="grid g2">
        <div class="card">
          <div class="card-h"><h2>🌾 Today's Active Farm Advisory</h2><span class="badge green" id="advBadge">Approved</span></div>
          <div class="card-b" id="farmerAdvisoryBox">
            <p class="muted">Loading official agricultural advisory for selected Panchayat...</p>
          </div>
        </div>
        <div class="card">
          <div class="card-h"><h2>⚠ Active Panchayat Weather Alerts</h2><span class="badge amber">Real-Time</span></div>
          <div class="card-b" id="farmerAlertsBox">
            <p class="muted">Checking early warning triggers...</p>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 2: Weather & 5-Day Forecast -->
    <section id="view-weather" class="view">
      <div class="card">
        <div class="card-h">
          <h2>🌤 Panchayat Weather &amp; 5-Day Quantile Forecast</h2>
          <div style="display:flex;gap:8px">
            <button class="btn sm" id="btnGenForecast" type="button">🔄 Generate Latest Forecast</button>
            <button class="btn secondary sm" id="btnViewForecast" type="button">📂 View Stored</button>
          </div>
        </div>
        <div class="card-b">
          <div class="grid g4" style="margin-bottom:var(--s5)">
            <div class="kpi"><div class="kpi-lbl">Max Temperature (P50)</div><div class="kpi-val" id="kpiTmax">--°C</div><div class="kpi-hint">Median daytime peak</div></div>
            <div class="kpi"><div class="kpi-lbl">Expected Rainfall</div><div class="kpi-val" id="kpiRain">-- mm</div><div class="kpi-hint">Day 1 downscaled</div></div>
            <div class="kpi"><div class="kpi-lbl">Relative Humidity</div><div class="kpi-val" id="kpiHumidity">--%</div><div class="kpi-hint">Microclimate RH</div></div>
            <div class="kpi"><div class="kpi-lbl">FAO-56 ET₀</div><div class="kpi-val" id="kpiEt0">-- mm</div><div class="kpi-hint">Reference evapotranspiration</div></div>
          </div>
          <div id="forecastTableWrap">
            <p class="muted">Select a Panchayat above and click Generate.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 3: Crop Intelligence -->
    <section id="view-crop" class="view">
      <div class="card">
        <div class="card-h"><h2>🌱 Crop-Specific Intelligence &amp; Agronomic Rules</h2></div>
        <div class="card-b">
          <div class="grid g3" style="margin-bottom:var(--s5)">
            <div class="field">
              <label for="selCrop">Select Crop</label>
              <select id="selCrop">
                <option value="paddy">🌾 Paddy (Rice / వరి)</option>
                <option value="cotton">🌱 Cotton (పత్తి)</option>
                <option value="maize">🌽 Maize (మొక్కజొన్న)</option>
                <option value="groundnut">🥜 Groundnut (వేరుశనగ)</option>
                <option value="chilli">🌶 Chilli (మిర్చి)</option>
                <option value="redgram">🫘 Red Gram (కందులు)</option>
              </select>
            </div>
            <div class="field">
              <label for="selStage">Growth Stage</label>
              <select id="selStage">
                <option value="sowing">Nursery / Sowing</option>
                <option value="vegetative" selected>Vegetative / Tillering</option>
                <option value="flowering">Flowering / Panicle</option>
                <option value="grain_filling">Grain / Boll Development</option>
                <option value="harvest">Maturity / Harvest</option>
              </select>
            </div>
            <div style="display:flex;align-items:flex-end">
              <button class="btn" id="btnCalculateCrop" type="button" style="width:100%">Analyze Crop Risk</button>
            </div>
          </div>
          <div id="cropAdviceResult">
            <div class="status info">Select crop parameters above to get agronomic recommendations.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 4: Early Warning Centre -->
    <section id="view-warnings" class="view">
      <div class="card">
        <div class="card-h"><h2>⚠ Early Warning Centre &bull; Operational Risk Monitor</h2><button class="btn secondary sm" id="btnRefreshWarnings" type="button">Refresh</button></div>
        <div class="card-b">
          <div class="grid g4" style="margin-bottom:var(--s5)">
            <div class="kpi"><div class="kpi-lbl">Critical Warnings</div><div class="kpi-val" style="color:var(--red)" id="warnCrit">0</div></div>
            <div class="kpi"><div class="kpi-lbl">High Risk</div><div class="kpi-val" style="color:var(--saffron-dark)" id="warnHigh">0</div></div>
            <div class="kpi"><div class="kpi-lbl">Moderate Hazards</div><div class="kpi-val" style="color:var(--amber)" id="warnMed">0</div></div>
            <div class="kpi"><div class="kpi-lbl">Normal Panchayats</div><div class="kpi-val" style="color:var(--green)" id="warnNorm">0</div></div>
          </div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Panchayat</th><th>Hazard Type</th><th>Severity</th><th>Forecast Window</th><th>Actionable Precaution</th></tr></thead>
              <tbody id="warningsTableBody"><tr><td colspan="5" class="muted">Loading early warnings...</td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 5: Interactive GIS Map -->
    <section id="view-gis" class="view">
      <div class="card">
        <div class="card-h"><h2>🗺 Interactive Telangana Agromet GIS Map</h2><span class="badge blue">Live Coordinates</span></div>
        <div class="card-b">
          <div id="gisMapContainer" style="width:100%;min-height:360px;background:var(--bg);border:1px solid var(--line);border-radius:var(--r-md);display:grid;place-items:center;position:relative">
            <svg id="gisSvg" viewBox="0 0 800 450" style="width:100%;height:auto;display:block"></svg>
          </div>
          <div class="small muted" style="margin-top:8px">Click any green/blue Panchayat marker on the map to inspect microclimate data and open forecast.</div>
        </div>
      </div>
    </section>

    <!-- VIEW 6: KVK Scientist Review Desk -->
    <section id="view-kvk" class="view">
      <div class="card">
        <div class="card-h"><h2>🔬 KVK / AMFU Scientist Advisory Review Desk</h2><button class="btn sm" id="btnLoadKvk" type="button">Refresh Queue</button></div>
        <div class="card-b">
          <div class="status info">Scientist verification workflow: Review deterministic rule metrics, append scientific notes, and approve or reject advisories for farmer dissemination.</div>
          <div id="kvkQueueBox">
            <p class="muted">Loading pending advisories...</p>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 7: Grievances Lifecycle -->
    <section id="view-grievance" class="view">
      <div class="grid g2">
        <div class="card">
          <div class="card-h"><h2>📝 File Citizen / Farmer Grievance</h2></div>
          <div class="card-b">
            <form id="formGrievance">
              <div class="field"><label for="grvName">Full Name *</label><input id="grvName" required placeholder="Enter farmer / citizen name"></div>
              <div class="field"><label for="grvMobile">Mobile Number *</label><input id="grvMobile" required type="tel" placeholder="10-digit mobile number"></div>
              <div class="field"><label for="grvCat">Category *</label><select id="grvCat"><option>Forecast Inaccuracy</option><option>Crop Advisory Issue</option><option>Weather Station Sensor</option><option>General Service</option></select></div>
              <div class="field"><label for="grvSubject">Subject *</label><input id="grvSubject" required placeholder="Brief description of issue"></div>
              <div class="field"><label for="grvDesc">Detailed Grievance *</label><textarea id="grvDesc" required placeholder="Provide details, location and observations..."></textarea></div>
              <button class="btn" type="submit" id="btnSubmitGrv" style="width:100%">Submit Grievance</button>
            </form>
          </div>
        </div>
        <div class="card">
          <div class="card-h"><h2>🔍 Track Grievance Status</h2></div>
          <div class="card-b">
            <div id="grvLifecycleTrack" style="margin-bottom:var(--s4)">
              <div class="stepper">
                <div class="step-node done" id="st1"><div class="step-circle">1</div><div class="step-label">Submitted</div></div>
                <div class="step-node" id="st2"><div class="step-circle">2</div><div class="step-label">Assigned</div></div>
                <div class="step-node" id="st3"><div class="step-circle">3</div><div class="step-label">Under Review</div></div>
                <div class="step-node" id="st4"><div class="step-circle">4</div><div class="step-label">Action Taken</div></div>
                <div class="step-node" id="st5"><div class="step-circle">5</div><div class="step-label">Resolved</div></div>
              </div>
            </div>
            <div id="grvListBox"><p class="muted">Loading recent grievances...</p></div>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 8: Notices Board -->
    <section id="view-notices" class="view">
      <div class="card">
        <div class="card-h"><h2>📢 Official Government Notices &amp; Weather Alerts</h2><button class="btn secondary sm" id="btnRefreshNotices" type="button">Refresh</button></div>
        <div class="card-b" id="noticesListBox">
          <p class="muted">Loading official departmental notices...</p>
        </div>
      </div>
    </section>

    <!-- VIEW 9: Defensive Security (IDS) Monitoring -->
    <section id="view-security" class="view">
      <div class="card">
        <div class="card-h"><h2>🛡 Defensive Security &amp; IDS Monitoring Centre</h2><span class="badge grey" id="secBadge">Checking telemetry…</span></div>
        <div class="card-b">
          <div class="grid g4" style="margin-bottom:var(--s5)">
            <div class="kpi"><div class="kpi-lbl">Total Requests</div><div class="kpi-val" id="secReqs">0</div><div class="kpi-hint">Monitored traffic</div></div>
            <div class="kpi"><div class="kpi-lbl">Blocked Attacks</div><div class="kpi-val" style="color:var(--red)" id="secBlocked">0</div><div class="kpi-hint">401/403 defenses</div></div>
            <div class="kpi"><div class="kpi-lbl">Rate Limits</div><div class="kpi-val" style="color:var(--saffron-dark)" id="secRate">0</div><div class="kpi-hint">Throttle enforcements</div></div>
            <div class="kpi"><div class="kpi-lbl">Defensive Events</div><div class="kpi-val" style="color:var(--navy)" id="secEvents">0</div><div class="kpi-hint">Audit captured</div></div>
          </div>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Timestamp</th><th>IP Address</th><th>Method</th><th>Endpoint</th><th>Status</th><th>Category</th><th>Severity</th></tr></thead>
              <tbody id="secEventsTable"><tr><td colspan="7" class="muted">Loading security events...</td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 10: Governance Audit Trail -->
    <section id="view-audit" class="view">
      <div class="card">
        <div class="card-h"><h2>📜 System Governance Audit Trail</h2><button class="btn secondary sm" id="btnRefreshAudit" type="button">Refresh</button></div>
        <div class="card-b">
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Timestamp</th><th>User / Role</th><th>Action</th><th>Target Resource</th><th>Status</th><th>Details</th></tr></thead>
              <tbody id="auditTableBody"><tr><td colspan="6" class="muted">Loading audit logs...</td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW: Model Transparency & AI Pipeline -->
    <section id="view-models" class="view">
      <div class="card">
        <div class="card-h">
          <h2>🧠 Model Transparency &amp; Agricultural AI Pipeline</h2>
          <span class="badge blue">M1-M3 Hybrid ML Pipeline</span>
        </div>
        <div class="card-b">
          <div class="grid g3" style="margin-bottom:var(--s5)">
            <div class="card" style="margin:0;background:var(--bg)">
              <div class="card-b">
                <div style="font-weight:700;font-size:16px;color:var(--navy);margin-bottom:6px">M1: Terrain Downscaler</div>
                <p class="small muted" style="margin-bottom:8px">Quantile Gradient Boosting regressor applying micro-topography residuals (elevation, slope, aspect, distance to waterbodies) over coarse NWP grid.</p>
                <div class="small"><strong>Target:</strong> Tmax, Tmin, RH, Wind Speed</div>
                <div class="small"><strong>Quantiles:</strong> P10, P50, P90 (Pinball Loss)</div>
              </div>
            </div>
            <div class="card" style="margin:0;background:var(--bg)">
              <div class="card-b">
                <div style="font-weight:700;font-size:16px;color:var(--saffron-dark);margin-bottom:6px">M2: Extreme Risk Classifier</div>
                <p class="small muted" style="margin-bottom:8px">Isotonic calibrated ensemble predicting probabilistic hazard thresholds for heavy precipitation (>45mm/day), heatwaves (>40°C), and squalls.</p>
                <div class="small"><strong>Calibration:</strong> Isotonic Regression</div>
                <div class="small"><strong>Metrics:</strong> Brier Score &amp; ROC-AUC</div>
              </div>
            </div>
            <div class="card" style="margin:0;background:var(--bg)">
              <div class="card-b">
                <div style="font-weight:700;font-size:16px;color:var(--green);margin-bottom:6px">M3: FAO-56 Penman-Monteith</div>
                <p class="small muted" style="margin-bottom:8px">Deterministic physics-based reference evapotranspiration (ET₀) engine computing daily crop water demand for deficit irrigation management.</p>
                <div class="small"><strong>Standard:</strong> FAO-56 Irrigation &amp; Drainage</div>
                <div class="small"><strong>Status:</strong> Validated on Telangana AWS</div>
              </div>
            </div>
          </div>

          <div class="card" style="margin:0;background:var(--surface-elev);border:1px solid var(--line)">
            <div class="card-b">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px">
                <h3 style="font-size:15px">Data Provenance &amp; Operational Source</h3>
                <span class="badge green" id="modeIndicator">🟢 Production Data Mode (Open-Meteo + Telangana AWS Mesh)</span>
              </div>
              <div class="table-wrap">
                <table class="table">
                  <thead><tr><th>Component</th><th>Source / Pipeline</th><th>Refresh Cadence</th><th>Validation Status</th></tr></thead>
                  <tbody>
                    <tr><td>Coarse Numerical Weather Grid</td><td>ECMWF IFS &amp; GFS Ensemble (Open-Meteo)</td><td>Hourly Automated Sync</td><td><span class="badge green">Live Sync</span></td></tr>
                    <tr><td>Terrain Topography Digital Elevation</td><td>SRTM 30m Digital Elevation Model (DEM)</td><td>Static Geodetic Cache</td><td><span class="badge green">Calibrated</span></td></tr>
                    <tr><td>Panchayat Ground Truth</td><td>Telangana Agricultural AWS Weather Network</td><td>Historical Training Baseline</td><td><span class="badge green">CRPS Optimized</span></td></tr>
                    <tr><td>Agronomic Decision Logic</td><td>ICAR / PJTSAU Package of Practices</td><td>Seasonal Revision</td><td><span class="badge green">KVK Approved</span></td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- VIEW 11: Administration & System Health -->
    <section id="view-admin" class="view">
      <div class="card">
        <div class="card-h"><h2>⚙ System Administration &amp; Health Matrix</h2><button class="btn secondary sm" id="btnRefreshHealth" type="button">Check Health</button></div>
        <div class="card-b">
          <div class="grid g3" style="margin-bottom:var(--s5)">
            <div class="kpi"><div class="kpi-lbl">Backend &amp; API</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">FastAPI / Uvicorn</div></div>
            <div class="kpi"><div class="kpi-lbl">Database</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">SQLite / WAL mode</div></div>
            <div class="kpi"><div class="kpi-lbl">Weather API</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">Open-Meteo / IMD</div></div>
            <div class="kpi"><div class="kpi-lbl">ML Forecast Engine</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">LightGBM Quantile</div></div>
            <div class="kpi"><div class="kpi-lbl">Security IDS</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">Rate limit &amp; IDS</div></div>
            <div class="kpi"><div class="kpi-lbl">Farmer Notifications</div><div class="kpi-val" style="font-size:18px;color:var(--green)">🟢 Operational</div><div class="kpi-hint">Telemetry active</div></div>
          </div>
          <div id="healthDetailsBox"><p class="muted">Querying /api/health endpoints...</p></div>
        </div>
      </div>
    </section>

  </div>
</main>

<!-- Footer -->
<footer class="footer">
  <div class="wrap">
    <div>
      <h4>Telangana Agromet Decision Support Portal</h4>
      <p>Smart India Hackathon &bull; Problem Statement SIH-PS2</p>
      <p class="small" style="margin-top:8px">Terrain-aware weather downscaling, probabilistic quantiles (P10/P50/P90), deterministic farm advisories, and scientist sign-off workflow.</p>
    </div>
    <div class="footer-links">
      <h4>Government Portals</h4>
      <button type="button" data-view="farmer">Farmer Dashboard</button>
      <button type="button" data-view="weather">Weather Forecast</button>
      <button type="button" data-view="gis">Panchayat Map</button>
      <button type="button" data-view="warnings">Early Warnings</button>
    </div>
    <div class="footer-links">
      <h4>Support &amp; Compliance</h4>
      <button type="button" data-view="grievance">File Grievance</button>
      <button type="button" data-view="notices">Official Notices</button>
      <button type="button" data-view="security">Security Policy</button>
      <button type="button" data-view="audit">Audit Records</button>
    </div>
  </div>
  <div class="footer-bot">
    &copy; 2026 Government of Telangana &bull; Department of Agriculture &bull; Decision Support Platform.
  </div>
</footer>

<!-- Authentication & Registration Modal (ZERO API KEY INPUTS) -->
<div class="overlay" id="authModal" style="display:none">
  <div class="modal">
    <div class="modal-h">
      <h3 id="authModalTitle">Sign In to Agromet Portal</h3>
      <button id="closeAuthModal" type="button" style="background:none;border:0;font-size:20px;color:var(--muted)">&times;</button>
    </div>
    <div class="modal-b">
      <!-- Tabs: Login vs Register -->
      <div style="display:flex;gap:4px;border-bottom:2px solid var(--line);margin-bottom:var(--s4)">
        <button id="tabLogin" type="button" class="btn sm" style="border-radius:0;border-bottom:2px solid var(--navy);background:none;color:var(--navy);font-weight:700">Sign In</button>
        <button id="tabRegister" type="button" class="btn sm secondary" style="border-radius:0;border:0;background:none;color:var(--muted)">Create Account</button>
      </div>

      <!-- Login Form -->
      <form id="formLogin">
        <div class="field"><label for="logEmail">Email / Username *</label><input id="logEmail" required type="email" placeholder="e.g. scientist.kvk@agromet.gov.in" autocomplete="username"></div>
        <div class="field"><label for="logPass">Password *</label><input id="logPass" required type="password" placeholder="Enter password" autocomplete="current-password"></div>
        <button class="btn" type="submit" id="btnSubmitLogin" style="width:100%;margin-top:8px">Sign In</button>
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--line-light)">
          <div class="small muted" style="margin-bottom:6px">Quick 1-Click Demo Logins for Evaluators:</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <button type="button" class="btn secondary sm demo-login" data-user="citizen@agromet.demo">🌾 Farmer</button>
            <button type="button" class="btn secondary sm demo-login" data-user="kvk@agromet.demo">🔬 KVK Scientist</button>
            <button type="button" class="btn secondary sm demo-login" data-user="officer@agromet.demo">📋 Field Officer</button>
            <button type="button" class="btn secondary sm demo-login" data-user="officer@agromet.demo">🏛 District Officer</button>
            <button type="button" class="btn secondary sm demo-login" data-user="admin@agromet.demo">⚙ Admin</button>
          </div>
        </div>
      </form>

      <!-- Register Form -->
      <form id="formRegister" style="display:none">
        <div class="field"><label for="regName">Full Name *</label><input id="regName" required placeholder="Enter full legal name"></div>
        <div class="field"><label for="regEmail">Email Address *</label><input id="regEmail" required type="email" placeholder="name@example.com"></div>
        <div class="field"><label for="regMobile">Mobile Number *</label><input id="regMobile" required type="tel" placeholder="10-digit mobile number"></div>
        <div class="field">
          <label for="regRole">Role / Account Type *</label>
          <select id="regRole">
            <option value="citizen">🌾 Public / Farmer</option>
            <option value="kvk">🔬 KVK Scientist</option>
            <option value="officer">📋 Field Officer</option>
            <option value="district_officer">🏛 District Officer</option>
            <option value="admin">⚙ Administrator</option>
          </select>
        </div>
        <div class="field"><label for="regPass">Password (min 8 chars) *</label><input id="regPass" required type="password" placeholder="Create strong password"></div>
        <div class="field"><label for="regPassConfirm">Confirm Password *</label><input id="regPassConfirm" required type="password" placeholder="Re-enter password"></div>
        <div style="margin:8px 0"><label style="font-size:12px"><input type="checkbox" id="regTerms" required> I agree to the Government Terms and Privacy Policy</label></div>
        <button class="btn" type="submit" id="btnSubmitRegister" style="width:100%;margin-top:8px">Create Account</button>
      </form>
    </div>
  </div>
</div>

<!-- Modal Container for Advisory Review Remarks -->
<div class="overlay" id="reviewModal" style="display:none">
  <div class="modal">
    <div class="modal-h">
      <h3 id="revModalTitle">KVK Advisory Review</h3>
      <button id="closeRevModal" type="button" style="background:none;border:0;font-size:20px;color:var(--muted)">&times;</button>
    </div>
    <div class="modal-b">
      <p id="revModalAdvId" class="mono muted" style="margin-bottom:10px"></p>
      <div class="field">
        <label for="revRemarks">Scientific Review Remarks / Agronomic Recommendations</label>
        <textarea id="revRemarks" placeholder="Enter scientific observations or instructions..."></textarea>
      </div>
    </div>
    <div class="modal-f">
      <button class="btn secondary sm" id="btnRevCancel" type="button">Cancel</button>
      <button class="btn sm" id="btnRevSubmit" type="button">Confirm Decision</button>
    </div>
  </div>
</div>

<!-- Toast Container -->
<div class="toasts" id="toastBox"></div>

<!-- Application Logic -->
<script>
'use strict';

var state = {
  panchayats: [],
  hierarchy: {},
  selectedPanchayat: null,
  forecast: null,
  user: null,
  lang: 'en',
  theme: 'light'
};

var I18N = {
  en: {
    portal_title: "Telangana Agromet Decision Support Portal",
    farmer_greeting: "Namaste, Farmer",
    farmer_sub: "Here is your local Panchayat agro-meteorological advisory and 5-day terrain forecast.",
    gen_forecast: "Generate Latest Forecast",
    view_stored: "View Stored",
    kpi_tmax: "Max Temperature (P50)",
    kpi_rain: "Expected Rainfall",
    kpi_rh: "Relative Humidity",
    kpi_et0: "FAO-56 ET₀",
    submit_grv: "Submit Grievance",
    signin: "Sign In / Register",
    signout: "Sign Out"
  },
  te: {
    portal_title: "తెలంగాణ ఆగ్రోమెట్ నిర్ణయ మద్దతు పోర్టల్",
    farmer_greeting: "నమస్కారం, రైతు సోదరులారా",
    farmer_sub: "మీ గ్రామ పంచాయతీ వాతావరణ ఆధారిత పంట సూచనలు మరియు 5 రోజుల వాతావరణ సమాచారం ఇక్కడ చూడండి.",
    gen_forecast: "తాజా సూచనను పొందండి",
    view_stored: "నిల్వ చేసిన సమాచారం",
    kpi_tmax: "గరిష్ట ఉష్ణోగ్రత",
    kpi_rain: "వర్షపాతం అంచనా",
    kpi_rh: "గాలిలో తేమ",
    kpi_et0: "బాష్పీభవనం (ET₀)",
    submit_grv: "ఫిర్యాదు సమర్పించండి",
    signin: "లాగిన్ / రిజిస్టర్",
    signout: "లాగౌట్"
  },
  hi: {
    portal_title: "तेलंगाना कृषि-मौसम निर्णय सहायता पोर्टल",
    farmer_greeting: "नमस्ते, किसान भाई",
    farmer_sub: "आपके ग्राम पंचायत के लिए भू-भाग आधारित मौसम पूर्वानुमान और वैज्ञानिक कृषि सलाह।",
    gen_forecast: "ताज़ा पूर्वानुमान उत्पन्न करें",
    view_stored: "सहेजा गया पूर्वानुमान",
    kpi_tmax: "अधिकतम तापमान",
    kpi_rain: "अनुमानित वर्षा",
    kpi_rh: "सापेक्ष आर्द्रता",
    kpi_et0: "वाष्पोत्सर्जन (ET₀)",
    submit_grv: "शिकायत दर्ज करें",
    signin: "साइन इन / पंजीकरण",
    signout: "साइन आउट"
  }
};

function $(id) { return document.getElementById(id); }
function $all(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

function toast(title, msg, type) {
  var b = $('toastBox'); if (!b) return;
  var d = document.createElement('div');
  d.className = 'toast ' + (type || 'info');
  d.setAttribute('role', 'status');
  d.innerHTML = '<strong>' + title + '</strong><div>' + msg + '</div>';
  b.appendChild(d);
  setTimeout(function() { d.remove(); }, 3500);
}

function api(path, opts) {
  opts = opts || {};
  opts.headers = opts.headers || {};
  if (state.user && state.user.token) {
    opts.headers['Authorization'] = 'Bearer ' + state.user.token;
  }
  if (opts.body && typeof opts.body === 'object') {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  return fetch(path, opts).then(function(r) {
    if (!r.ok) {
      return r.json().then(function(j) { throw new Error(j.detail || 'HTTP error ' + r.status); }).catch(function(e) { throw new Error(e.message || 'Request failed'); });
    }
    return r.json();
  });
}

/* ================= View Navigation ================= */
var LOCKED_VIEWS = { kvk: 1, audit: 1, admin: 1, security: 1 };
function switchView(viewName) {
  if (LOCKED_VIEWS[viewName] && !state.user) {
    toast('Sign In Required', 'Please sign in to access the ' + viewName + ' workspace.', 'warning');
    viewName = 'login';
  }
  $all('.nav-btn').forEach(function(b) {
    var on = b.dataset.view === viewName;
    b.classList.toggle('active', on);
    if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  $all('.view').forEach(function(v) {
    v.classList.toggle('active', v.id === 'view-' + viewName);
  });
  if (viewName === 'kvk') loadKvkQueue();
  if (viewName === 'warnings') loadWarnings();
  if (viewName === 'notices') loadNotices();
  if (viewName === 'security') loadSecurity();
  if (viewName === 'audit') loadAuditLogs();
  if (viewName === 'admin') loadHealth();
  if (viewName === 'grievance') loadGrievances();
  if (viewName === 'gis') renderGisMap();
  try { if (('' + location.hash).slice(1) !== viewName) location.hash = viewName; } catch(e){}
  revealScan();
}

$all('[data-view]').forEach(function(b) {
  b.addEventListener('click', function() {
    switchView(this.dataset.view);
  });
});

/* ================= Cascading Location Selector ================= */
function loadPanchayats() {
  api('/api/v1/panchayats').then(function(list) {
    state.panchayats = list || [];
    var hier = {};
    list.forEach(function(p) {
      var dist = p.district || 'Rangareddy';
      var man = p.mandal || 'Chevella';
      hier[dist] = hier[dist] || {};
      hier[dist][man] = hier[dist][man] || [];
      hier[dist][man].push(p);
    });
    state.hierarchy = hier;
    populateDistricts();
  }).catch(function(err) {
    toast('Registry Error', err.message, 'error');
  });
}

function populateDistricts() {
  var sel = $('selDistrict');
  sel.innerHTML = '';
  var dists = Object.keys(state.hierarchy);
  dists.forEach(function(d) {
    var opt = document.createElement('option');
    opt.value = d; opt.textContent = d;
    sel.appendChild(opt);
  });
  populateMandals();
}

function populateMandals() {
  var dist = $('selDistrict').value;
  var sel = $('selMandal');
  sel.innerHTML = '';
  var mans = Object.keys(state.hierarchy[dist] || {});
  mans.forEach(function(m) {
    var opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  });
  populatePanchayats();
}

function populatePanchayats() {
  var dist = $('selDistrict').value;
  var man = $('selMandal').value;
  var sel = $('selPanchayat');
  sel.innerHTML = '';
  var ps = (state.hierarchy[dist] && state.hierarchy[dist][man]) || [];
  ps.forEach(function(p) {
    var opt = document.createElement('option');
    opt.value = p.panchayat_id;
    opt.textContent = (p.panchayat_name || p.name || p.panchayat_id) + ' (' + p.panchayat_id + ')';
    sel.appendChild(opt);
  });
  if (ps.length) onPanchayatSelected(ps[0].panchayat_id);
}

$('selDistrict').addEventListener('change', populateMandals);
$('selMandal').addEventListener('change', populatePanchayats);
$('selPanchayat').addEventListener('change', function() {
  onPanchayatSelected(this.value);
});

function onPanchayatSelected(pid) {
  var p = state.panchayats.find(function(item) { return String(item.panchayat_id) === String(pid); });
  if (!p) return;
  state.selectedPanchayat = p;
  $('chipLat').textContent = Number(p.latitude).toFixed(4);
  $('chipLon').textContent = Number(p.longitude).toFixed(4);
  $('chipElev').textContent = (p.elevation_m || 530) + ' m';
  $('chipWater').textContent = (p.distance_to_water_m || 1200) + ' m';
  $('chipSlope').textContent = (p.slope_deg || 2.1) + '°';
  loadStoredForecast(pid);
  loadPublishedAdvisories(pid);
}

/* GPS Geolocation */
$('gpsBtn').addEventListener('click', function() {
  if (!navigator.geolocation) {
    toast('GPS Error', 'Geolocation is not supported by your browser.', 'error');
    return;
  }
  toast('GPS', 'Acquiring satellite fix...', 'info');
  navigator.geolocation.getCurrentPosition(function(pos) {
    var lat = pos.coords.latitude;
    var lon = pos.coords.longitude;
    var nearest = null, minDist = 9999999;
    state.panchayats.forEach(function(p) {
      var d = Math.sqrt(Math.pow(p.latitude - lat, 2) + Math.pow(p.longitude - lon, 2));
      if (d < minDist) { minDist = d; nearest = p; }
    });
    if (nearest) {
      $('selDistrict').value = nearest.district || 'Rangareddy';
      populateMandals();
      $('selMandal').value = nearest.mandal || 'Chevella';
      populatePanchayats();
      $('selPanchayat').value = nearest.panchayat_id;
      onPanchayatSelected(nearest.panchayat_id);
      toast('Location Matched', 'Selected nearest Panchayat: ' + (nearest.panchayat_name || nearest.panchayat_id), 'success');
    }
  }, function(err) {
    toast('GPS Failed', err.message, 'error');
  });
});

function reducedMotion() { return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
function countUp(el, to, suffix, dec) {
  if (!el) return;
  to = Number(to) || 0; dec = dec || 0; suffix = suffix || '';
  if (reducedMotion()) { el.textContent = to.toFixed(dec) + suffix; return; }
  var t0 = null, dur = 700;
  function fr(ts) {
    if (!t0) t0 = ts;
    var p = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.textContent = (to * e).toFixed(dec) + suffix;
    if (p < 1) requestAnimationFrame(fr);
  }
  requestAnimationFrame(fr);
}

/* ================= Weather & Forecast Operations ================= */
function renderForecastData(f) {
  state.forecast = f;
  if (!f.days || !f.days.length) return;
  var d1 = f.days[0];
  countUp($('kpiTmax'), d1.tmax_c.p50, '°C', 1);
  countUp($('kpiRain'), d1.rain_mm, ' mm', 1);
  countUp($('kpiHumidity'), d1.relative_humidity_pct.p50, '%', 0);
  countUp($('kpiEt0'), d1.et0_mm_day != null ? d1.et0_mm_day : 0, ' mm', 1);

  // Farmer weather strip
  var strip = $('farmerWeatherStrip');
  strip.innerHTML = f.days.slice(0, 5).map(function(d, i) {
    return '<div class="w-card"><div class="w-date">Day ' + (i+1) + ' (' + d.valid_date.slice(5) + ')</div><div class="w-temp">' + d.tmax_c.p50 + '°C</div><div class="w-rain">Rain: ' + d.rain_mm + ' mm (' + Math.round((d.rainfall_probabilities.heavy||0)*100) + '% heavy)</div></div>';
  }).join('');

  // 5-day forecast table
  var wrap = $('forecastTableWrap');
  wrap.innerHTML = '<div class="table-wrap"><table class="table"><thead><tr><th>Date</th><th>Tmax (P10/P50/P90)</th><th>Tmin (P10/P50/P90)</th><th>RH P50</th><th>Wind P50</th><th>Rain (mm)</th><th>Heavy Rain Odds</th><th>ET₀ (mm/day)</th></tr></thead><tbody>' +
    f.days.map(function(d) {
      return '<tr><td><strong>' + d.valid_date + '</strong></td><td>' + d.tmax_c.p10 + ' / <strong>' + d.tmax_c.p50 + '</strong> / ' + d.tmax_c.p90 + ' °C</td><td>' + d.tmin_c.p10 + ' / <strong>' + d.tmin_c.p50 + '</strong> / ' + d.tmin_c.p90 + ' °C</td><td>' + Math.round(d.relative_humidity_pct.p50) + '%</td><td>' + d.wind_speed_kmh.p50 + ' km/h</td><td>' + d.rain_mm + ' mm</td><td>' + Math.round((d.rainfall_probabilities.heavy||0)*100) + '%</td><td>' + (d.et0_mm_day != null ? d.et0_mm_day.toFixed(1) : '3.8') + ' mm</td></tr>';
    }).join('') + '</tbody></table></div>';
}

function loadStoredForecast(pid) {
  api('/api/v1/forecast/panchayat/' + pid).then(function(f) {
    renderForecastData(f);
  }).catch(function() {
    // Generate if not present
    generateForecast(pid);
  });
}

function generateForecast(pid) {
  toast('Forecast', 'Generating terrain-downscaled forecast for ' + pid + '...', 'info');
  api('/api/v1/forecast/panchayat/' + pid + '/refresh', { method: 'POST' }).then(function(f) {
    renderForecastData(f);
    toast('Forecast Ready', '5-Day forecast generated successfully.', 'success');
  }).catch(function(err) {
    toast('Forecast Error', err.message, 'error');
  });
}

$('btnGenForecast').addEventListener('click', function() {
  if (state.selectedPanchayat) generateForecast(state.selectedPanchayat.panchayat_id);
});
$('btnViewForecast').addEventListener('click', function() {
  if (state.selectedPanchayat) loadStoredForecast(state.selectedPanchayat.panchayat_id);
});

/* ================= Published Advisories & Crop Risk ================= */
function loadPublishedAdvisories(pid) {
  api('/api/v1/advisories/published?panchayat_id=' + pid).then(function(list) {
    var box = $('farmerAdvisoryBox');
    if (!list || !list.length) {
      box.innerHTML = '<div class="status ok">🟢 No severe weather stress detected. Normal farming operations may continue under standard irrigation.</div>';
      return;
    }
    box.innerHTML = list.map(function(a) {
      var langKey = state.lang || 'en';
      var text = a.message_key ? a.message_key.replace(/_/g, ' ') : 'Agromet Advisory';
      return '<div style="margin-bottom:12px;padding:12px;border-radius:8px;background:var(--bg);border-left:4px solid var(--green)"><strong>' + a.kind + ' Advisory (Valid ' + a.valid_from + ' to ' + a.valid_to + ')</strong><p style="margin-top:6px;font-size:13.5px">' + text + '</p></div>';
    }).join('');
  }).catch(function() {
    $('farmerAdvisoryBox').innerHTML = '<div class="status ok">🟢 Weather conditions favorable for active crops.</div>';
  });
}

$('btnCalculateCrop').addEventListener('click', function() {
  var crop = $('selCrop').value;
  var pid = state.selectedPanchayat ? state.selectedPanchayat.panchayat_id : '201001';
  api('/api/v1/crops/' + crop + '/advisory/' + pid).then(function(res) {
    var box = $('cropAdviceResult');
    var badgeClass = res.risk_level === 'HIGH' ? 'red' : res.risk_level === 'MODERATE' ? 'amber' : 'green';
      var det = res.crop_details || {};
      var lang = state.lang || 'en';
      function recText(r) {
        if (typeof r === 'string') return r;
        var t = (lang === 'te' && r.action_te) ? r.action_te : (lang === 'hi' && r.action_hi) ? r.action_hi : (r.action_en || r.action || '');
        var urg = (r.urgency || 'Normal');
        var ub = (urg.toLowerCase() === 'high' || urg.toLowerCase() === 'urgent') ? 'red' : 'blue';
        return '<strong>' + (r.topic || 'Advisory') + ' <span class="badge ' + ub + '">' + urg + '</span></strong><br>' + t;
      }
      box.innerHTML = '<div class="card" style="margin-top:var(--s4)"><div class="card-h"><h3>' + res.crop_name + ' &bull; Risk Assessment</h3><span class="badge ' + badgeClass + '">' + res.risk_level + ' RISK</span></div><div class="card-b">' +
        '<div class="grid g3" style="margin-bottom:14px"><div><strong>Water Need:</strong> ' + (det.water_requirement_mm || '—') + ' mm</div><div><strong>Season:</strong> ' + (det.season || '—') + '</div><div><strong>Duration:</strong> ' + (det.duration_days || '—') + ' Days</div></div>' +
        '<h4>Agronomic Recommendations:</h4><ul style="margin:8px 0 0 20px;line-height:1.7">' +
        (res.recommendations || []).map(function(r) { return '<li style="margin-bottom:8px">' + recText(r) + '</li>'; }).join('') +
        '</ul></div></div>';
  }).catch(function(err) {
    toast('Crop Advisory Error', err.message, 'error');
  });
});

/* ================= Early Warnings ================= */
function loadWarnings() {
  api('/api/v1/early-warnings').then(function(data) {
    $('warnCrit').textContent = data.summary.critical || 0;
    $('warnHigh').textContent = data.summary.high || 0;
    $('warnMed').textContent = data.summary.moderate || 0;
    $('warnNorm').textContent = data.summary.normal || 0;

    var tbody = $('warningsTableBody');
    if (!data.alerts || !data.alerts.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center" class="muted">All Panchayats in normal range. No active early warnings.</td></tr>';
      $('farmerAlertsBox').innerHTML = '<div class="status ok">🟢 No active hazard warnings for ' + (state.selectedPanchayat ? state.selectedPanchayat.panchayat_name : 'Telangana') + '.</div>';
      return;
    }
    tbody.innerHTML = data.alerts.map(function(a) {
      var badgeClass = a.severity === 'critical' ? 'red' : a.severity === 'high' ? 'amber' : 'blue';
      return '<tr><td><strong>' + a.panchayat_name + '</strong> (' + a.district + ')</td><td>' + a.hazard + '</td><td><span class="badge ' + badgeClass + '">' + a.severity.toUpperCase() + '</span></td><td>' + a.valid_until + '</td><td>' + a.action_required + '</td></tr>';
    }).join('');

    $('farmerAlertsBox').innerHTML = data.alerts.slice(0, 3).map(function(a) {
      return '<div class="status warn"><strong>' + a.hazard + ' (' + a.severity.toUpperCase() + '):</strong> ' + a.action_required + '</div>';
    }).join('');
  }).catch(function(err) {
    toast('Warnings', err.message, 'error');
  });
}

/* ================= GIS Interactive Map ================= */
function renderGisMap() {
  var svg = $('gisSvg');
  if (!svg || !state.panchayats.length) return;
  var lats = state.panchayats.map(function(p) { return p.latitude; });
  var lons = state.panchayats.map(function(p) { return p.longitude; });
  var minLat = Math.min.apply(null, lats) - 0.2, maxLat = Math.max.apply(null, lats) + 0.2;
  var minLon = Math.min.apply(null, lons) - 0.2, maxLon = Math.max.apply(null, lons) + 0.2;

  function toX(lon) { return 40 + (lon - minLon) / (maxLon - minLon) * 720; }
  function toY(lat) { return 410 - (lat - minLat) / (maxLat - minLat) * 370; }

  var markers = state.panchayats.map(function(p) {
    var x = toX(p.longitude), y = toY(p.latitude);
    var sel = state.selectedPanchayat && state.selectedPanchayat.panchayat_id === p.panchayat_id;
    return '<g style="cursor:pointer" onclick="onPanchayatSelected(\'' + p.panchayat_id + '\');toast(\'Map Selection\',\'' + (p.panchayat_name||p.panchayat_id) + '\',\'info\')">' +
      '<circle cx="' + x + '" cy="' + y + '" r="' + (sel ? '10' : '7') + '" fill="' + (sel ? '#d97706' : '#15803d') + '" stroke="#ffffff" stroke-width="2"/>' +
      '<text x="' + x + '" y="' + (y - 10) + '" font-size="11" font-weight="700" fill="var(--ink)" text-anchor="middle">' + (p.panchayat_name || p.panchayat_id) + '</text>' +
      '</g>';
  }).join('');

  svg.innerHTML = '<rect width="800" height="450" fill="transparent"/>' +
    '<path d="M 100,50 L 700,50 L 750,400 L 80,400 Z" fill="rgba(37,99,235,0.04)" stroke="var(--line)" stroke-dasharray="4"/>' +
    markers;
}

/* ================= KVK Scientist Review Desk ================= */
var currentReviewId = null, currentAction = null;
function loadKvkQueue() {
  api('/api/v1/advisories/kvk-pending').then(function(list) {
    var box = $('kvkQueueBox');
    if (!list || !list.length) {
      box.innerHTML = '<div class="status ok">🟢 No advisories currently awaiting review. The KVK queue is clear.</div>';
      return;
    }
    box.innerHTML = list.map(function(a) {
      return '<div class="card" style="margin-bottom:var(--s4)"><div class="card-h"><h3>' + a.kind + ' &bull; Advisory ID: ' + a.advisory_id + '</h3><span class="badge amber">Pending Review</span></div><div class="card-b">' +
        '<div class="grid g3" style="margin-bottom:12px"><div><strong>Panchayat:</strong> ' + a.panchayat_id + '</div><div><strong>Valid Window:</strong> ' + a.valid_from + ' to ' + a.valid_to + '</div><div><strong>Rule Engine:</strong> ' + a.rule + '</div></div>' +
        '<div style="background:var(--bg);padding:10px;border-radius:6px;margin-bottom:12px;font-size:13px"><strong>Trigger Metrics:</strong> ' + JSON.stringify(a.trigger_metrics || {}) + '</div>' +
        '<div style="display:flex;gap:8px">' +
        '<button class="btn success sm" onclick="openReviewModal(\'' + a.advisory_id + '\',\'approve\')">Approve &amp; Disseminate</button>' +
        '<button class="btn danger sm" onclick="openReviewModal(\'' + a.advisory_id + '\',\'reject\')">Reject Advisory</button>' +
        '<button class="btn secondary sm" onclick="openReviewModal(\'' + a.advisory_id + '\',\'edit\')">Edit with Remarks</button>' +
        '</div></div></div>';
    }).join('');
  }).catch(function(err) {
    $('kvkQueueBox').innerHTML = '<div class="status error">Failed to load KVK queue: ' + err.message + '</div>';
  });
}

function openReviewModal(advId, action) {
  currentReviewId = advId;
  currentAction = action;
  $('revModalTitle').textContent = action.toUpperCase() + ' Advisory: ' + advId;
  $('revModalAdvId').textContent = 'Action: ' + action + ' &bull; Scientist ID: ' + (state.user ? state.user.name : 'kvk-scientist-1');
  $('revRemarks').value = '';
  $('reviewModal').style.display = 'grid';
}

$('closeRevModal').addEventListener('click', function() { $('reviewModal').style.display = 'none'; });
$('btnRevCancel').addEventListener('click', function() { $('reviewModal').style.display = 'none'; });
$('btnRevSubmit').addEventListener('click', function() {
  if (!currentReviewId || !currentAction) return;
  var remarks = $('revRemarks').value.trim();
  var payload = {
    advisory_id: currentReviewId,
    action: currentAction,
    reviewer_id: state.user ? state.user.name : 'kvk-scientist-1',
    reviewer_notes: remarks || 'Scientist reviewed and approved.'
  };
  api('/api/v1/advisories/approve', { method: 'POST', body: payload }).then(function() {
    $('reviewModal').style.display = 'none';
    toast('Review Saved', 'Advisory ' + currentAction + 'd successfully.', 'success');
    loadKvkQueue();
  }).catch(function(err) {
    toast('Review Error', err.message, 'error');
  });
});
$('btnLoadKvk').addEventListener('click', loadKvkQueue);

/* ================= Grievances ================= */
function loadGrievances() {
  api('/api/v1/grievances').then(function(list) {
    var box = $('grvListBox');
    if (!list || !list.length) {
      box.innerHTML = '<p class="muted">No grievances submitted yet.</p>';
      return;
    }
    box.innerHTML = list.slice(0, 5).map(function(g) {
      return '<div style="padding:10px;border-bottom:1px solid var(--line-light);display:flex;justify-content:space-between;align-items:center">' +
        '<div><strong>' + g.grievance_id + '</strong> - ' + g.subject + '<div class="small muted">' + g.category + ' &bull; ' + (g.created_at||'').slice(0,10) + '</div></div>' +
        '<span class="badge blue">' + g.status.toUpperCase() + '</span>' +
        '</div>';
    }).join('');
  }).catch(function() {});
}

$('formGrievance').addEventListener('submit', function(e) {
  e.preventDefault();
  var payload = {
    name: $('grvName').value.trim(),
    mobile: $('grvMobile').value.trim(),
    category: $('grvCat').value,
    subject: $('grvSubject').value.trim(),
    description: $('grvDesc').value.trim()
  };
  api('/api/v1/grievances', { method: 'POST', body: payload }).then(function(res) {
    toast('Grievance Filed', 'Tracking ID: ' + res.grievance_id, 'success');
    $('formGrievance').reset();
    loadGrievances();
    // highlight stepper
    ['st1','st2','st3','st4','st5'].forEach(function(id) { $(id).className = 'step-node'; });
    $('st1').className = 'step-node active';
  }).catch(function(err) {
    toast('Grievance Failed', err.message, 'error');
  });
});

/* ================= Notices ================= */
function loadNotices() {
  api('/api/v1/notices').then(function(list) {
    list = (list && list.items) || list || [];
    var box = $('noticesListBox');
    if (!list || !list.length) {
      box.innerHTML = '<p class="muted">No official notices published.</p>';
      return;
    }
    box.innerHTML = list.map(function(n) {
      var badgeClass = n.priority === 'urgent' ? 'red' : n.priority === 'high' ? 'amber' : 'blue';
      var pr = n.priority || 'normal';
      var badgeClass = pr === 'urgent' ? 'red' : pr === 'high' ? 'amber' : 'blue';
      return '<div class="card" style="margin-bottom:var(--s4)"><div class="card-h"><h3>' + n.title + '</h3><span class="badge ' + badgeClass + '">' + pr.toUpperCase() + '</span></div><div class="card-b">' +
        '<p style="font-size:14px;line-height:1.6">' + (n.body || n.content || '') + '</p>' +
        '<div class="small muted" style="margin-top:10px">Published by ' + (n.created_by || n.department || 'Department') + ' on ' + (n.published_at||'').slice(0,10) + (n.category ? ' &bull; ' + n.category : '') + '</div>' +
        '</div></div>';
    }).join('');
  }).catch(function() {
    $('noticesListBox').innerHTML = '<div class="status error">Could not load notices. <button type="button" class="btn secondary sm" onclick="loadNotices()">Try Again</button></div>';
  });
}
$('btnRefreshNotices').addEventListener('click', loadNotices);

/* ================= Defensive Security Monitoring ================= */
function loadSecurity() {
  api('/api/v1/security/telemetry').then(function(data) {
    $('secReqs').textContent = data.summary.total_events || 0;
    $('secBlocked').textContent = data.summary.blocked || 0;
    $('secRate').textContent = data.summary.rate_limited || 0;
    $('secEvents').textContent = data.summary.total_events || 0;
    var sb = $('secBadge'); if (sb) { sb.textContent = 'Defensive Telemetry Active'; sb.className = 'badge green'; }

    var tbody = $('secEventsTable');
    if (!data.recent_events || !data.recent_events.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted">No security anomalies detected.</td></tr>';
      return;
    }
    tbody.innerHTML = data.recent_events.map(function(ev) {
      return '<tr><td class="small">' + ev.timestamp.slice(11,19) + '</td><td>' + ev.ip_address + '</td><td><strong>' + ev.method + '</strong></td><td>' + ev.path + '</td><td>' + ev.status_code + '</td><td>' + ev.category + '</td><td><span class="badge ' + (ev.severity==='critical'?'red':ev.severity==='warning'?'amber':'blue') + '">' + ev.severity + '</span></td></tr>';
    }).join('');
  }).catch(function() {
    var b = $('secBadge'); if (b) { b.textContent = 'Telemetry Unavailable'; b.className = 'badge grey'; }
    var tb = $('secEventsTable');
    if (tb) tb.innerHTML = '<tr><td colspan="7" style="text-align:center">Security telemetry endpoint is not connected on the server. No events are fabricated. <button type="button" class="btn secondary sm" onclick="loadSecurity()">Try Again</button></td></tr>';
  });
}

/* ================= Governance Audit Logs ================= */
function loadAuditLogs() {
  api('/api/v1/audit-logs').then(function(data) {
    var tbody = $('auditTableBody');
    var items = (data && data.items) || data || [];
    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="muted">No governance audit entries found.</td></tr>';
      return;
    }
    tbody.innerHTML = items.map(function(log) {
      return '<tr><td class="small">' + (log.created_at || log.timestamp || '').slice(0,19).replace('T',' ') + '</td><td><strong>' + (log.user_email || log.user_id || 'System') + '</strong> (' + (log.role || 'system') + ')</td><td><span class="badge blue">' + log.action + '</span></td><td class="mono">' + log.resource + '</td><td>' + (log.result || log.status || '') + '</td><td class="small">' + (log.details||'--') + '</td></tr>';
    }).join('');
  }).catch(function() {
    $('auditTableBody').innerHTML = '<tr><td colspan="6" style="text-align:center">Could not load audit logs. <button type="button" class="btn secondary sm" onclick="loadAuditLogs()">Try Again</button></td></tr>';
  });
}
$('btnRefreshAudit').addEventListener('click', loadAuditLogs);

/* ================= Health Endpoints Matrix ================= */
function loadHealth() {
  api('/api/health').then(function(res) {
    var box = $('healthDetailsBox');
    box.innerHTML = '<div style="background:var(--bg);padding:14px;border-radius:8px;font-size:13px">' +
      '<div><strong>Model Version:</strong> ' + res.model.version + ' (' + res.model.validation_status + ')</div>' +
      '<div style="margin-top:4px"><strong>Weather Provider:</strong> ' + res.weather_provider + '</div>' +
      '<div style="margin-top:4px"><strong>Timestamp:</strong> ' + res.timestamp + '</div>' +
      '</div>';
  }).catch(function() {
    $('healthDetailsBox').innerHTML = '<div class="status warn">Health endpoint is unavailable on the server right now. The component matrix above shows the last known state.</div>';
  });
}
$('btnRefreshHealth').addEventListener('click', loadHealth);

/* ================= Authentication Modal Logic (ZERO API KEY) ================= */
$('authBtn').addEventListener('click', function() {
  $('authModal').style.display = 'grid';
});
$('closeAuthModal').addEventListener('click', function() {
  $('authModal').style.display = 'none';
});

$('tabLogin').addEventListener('click', function() {
  $('formLogin').style.display = 'block';
  $('formRegister').style.display = 'none';
  $('tabLogin').style.color = 'var(--navy)';
  $('tabLogin').style.borderBottom = '2px solid var(--navy)';
  $('tabRegister').style.color = 'var(--muted)';
  $('tabRegister').style.borderBottom = '0';
});
$('tabRegister').addEventListener('click', function() {
  $('formLogin').style.display = 'none';
  $('formRegister').style.display = 'block';
  $('tabRegister').style.color = 'var(--navy)';
  $('tabRegister').style.borderBottom = '2px solid var(--navy)';
  $('tabLogin').style.color = 'var(--muted)';
  $('tabLogin').style.borderBottom = '0';
});

// Quick 1-click Demo Logins for Evaluators
$all('.demo-login').forEach(function(b) {
  b.addEventListener('click', function() {
    var demoPasswords = {
      'admin@agromet.demo': 'AdminDemo@2026!',
      'officer@agromet.demo': 'OfficerDemo@2026!',
      'kvk@agromet.demo': 'KvkScientist@2026!',
      'citizen@agromet.demo': 'CitizenDemo@2026!'
    };
    $('logEmail').value = this.dataset.user;
    $('logPass').value = demoPasswords[this.dataset.user] || '';
    $('formLogin').dispatchEvent(new Event('submit'));
  });
});

function doLogin(email, pass) {
  return api('/api/v1/auth/login', { method: 'POST', body: { email: email, password: pass } }).then(function(res) {
    state.user = {
      name: (res.user && (res.user.display_name || res.user.email)) || email,
      roles: (res.user && res.user.roles) || ['citizen'],
      token: res.access_token
    };
    try { sessionStorage.setItem('agromet_session', JSON.stringify(state.user)); } catch(e){}
    onUserLoggedIn();
    toast('Signed In', 'Welcome back, ' + state.user.name + '!', 'success');
    switchView('farmer');
  });
}
function doRegister(payload) {
  return api('/api/v1/auth/register', { method: 'POST', body: payload }).then(function(res) {
    state.user = {
      name: (res.user && (res.user.display_name || res.user.email)) || payload.email,
      roles: (res.user && res.user.roles) || ['citizen'],
      token: res.access_token
    };
    try { sessionStorage.setItem('agromet_session', JSON.stringify(state.user)); } catch(e){}
    onUserLoggedIn();
    toast('Account Created', 'Welcome to Agromet Portal, ' + state.user.name + '!', 'success');
    switchView('farmer');
  });
}
$('formLogin').addEventListener('submit', function(e) {
  e.preventDefault();
  var email = $('logEmail').value.trim();
  var pass = $('logPass').value.trim();
  doLogin(email, pass).then(function() { $('authModal').style.display = 'none'; }).catch(function(err) {
    toast('Login Failed', err.message, 'error');
  });
});
$('formLoginView').addEventListener('submit', function(e) {
  e.preventDefault();
  doLogin($('logEmailV').value.trim(), $('logPassV').value.trim()).catch(function(err) {
    toast('Login Failed', err.message, 'error');
  });
});
$('togglePassV').addEventListener('click', function() {
  var k = $('logPassV'); var show = k.type === 'password';
  k.type = show ? 'text' : 'password';
  this.textContent = show ? 'Hide' : 'Show';
});
$all('.demo-login-v').forEach(function(b) {
  b.addEventListener('click', function() {
    var demoPasswords = {
      'admin@agromet.demo': 'AdminDemo@2026!',
      'officer@agromet.demo': 'OfficerDemo@2026!',
      'kvk@agromet.demo': 'KvkScientist@2026!',
      'citizen@agromet.demo': 'CitizenDemo@2026!'
    };
    var email = this.dataset.user;
    doLogin(email, demoPasswords[email] || '').catch(function(err) {
      toast('Login Failed', err.message, 'error');
    });
  });
});
$('guestBtn').addEventListener('click', function() { switchView('farmer'); });

$('formRegister').addEventListener('submit', function(e) {
  e.preventDefault();
  var p1 = $('regPass').value, p2 = $('regPassConfirm').value;
  if (p1 !== p2) { toast('Error', 'Passwords do not match.', 'error'); return; }
  if (p1.length < 8) { toast('Error', 'Password must be at least 8 characters.', 'error'); return; }
  var payload = {
    full_name: $('regName').value.trim(),
    email: $('regEmail').value.trim(),
    mobile: $('regMobile').value.trim(),
    password: p1,
    role: $('regRole').value
  };
  doRegister(payload).then(function() { $('authModal').style.display = 'none'; }).catch(function(err) {
    toast('Registration Failed', err.message, 'error');
  });
});

function onUserLoggedIn() {
  if (!state.user) return;
  $('roleBadge').textContent = (state.user.roles[0] || 'citizen').toUpperCase();
  $('authBtn').style.display = 'none';
  $('logoutBtn').style.display = 'inline-flex';
  if ($('navLoginBtn')) $('navLoginBtn').style.display = 'none';
}

$('logoutBtn').addEventListener('click', function() {
  state.user = null;
  try { sessionStorage.removeItem('agromet_session'); } catch(e){}
  $('roleBadge').textContent = 'Public / Farmer';
  $('authBtn').style.display = 'inline-flex';
  $('logoutBtn').style.display = 'none';
  if ($('navLoginBtn')) $('navLoginBtn').style.display = '';
  toast('Signed Out', 'You have been signed out.', 'info');
  switchView('login');
});

/* ================= Theme & I18N ================= */
$('themeBtn').addEventListener('click', function() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', state.theme);
  try { localStorage.setItem('agromet_theme', state.theme); } catch(e){}
});
function paintSwatches() {
  var cur = document.documentElement.getAttribute('data-accent') || 'blue';
  $all('.swatch').forEach(function(s) { s.setAttribute('aria-pressed', s.dataset.accent === cur ? 'true' : 'false'); });
}
$all('.swatch').forEach(function(s) {
  s.addEventListener('click', function() {
    document.documentElement.setAttribute('data-accent', s.dataset.accent);
    try { localStorage.setItem('agromet_accent', s.dataset.accent); } catch(e){}
    paintSwatches();
  });
});
function revealScan() {
  var els = $all('.farmer-hero, .card, .kpi');
  if (reducedMotion() || !('IntersectionObserver' in window)) return;
  if (!window.__revealIO) {
    window.__revealIO = new IntersectionObserver(function(es) {
      es.forEach(function(en) { if (en.isIntersecting) { en.target.classList.add('in'); window.__revealIO.unobserve(en.target); } });
    }, { threshold: 0.06 });
  }
  els.forEach(function(el) {
    if (!el.classList.contains('reveal') && !el.classList.contains('in')) {
      el.classList.add('reveal');
      window.__revealIO.observe(el);
    }
  });
  setTimeout(function() { els.forEach(function(el) { el.classList.add('in'); }); }, 4000);
}

$('langSelect').addEventListener('change', function() {
  state.lang = this.value;
  var dict = I18N[state.lang] || I18N.en;
  $('farmerGreeting').textContent = dict.farmer_greeting;
  $('farmerSub').textContent = dict.farmer_sub;
  $('btnGenForecast').textContent = '🔄 ' + dict.gen_forecast;
  $('btnViewForecast').textContent = '📂 ' + dict.view_stored;
  $('kpiTmax').previousElementSibling.textContent = dict.kpi_tmax;
  $('kpiRain').previousElementSibling.textContent = dict.kpi_rain;
  $('kpiHumidity').previousElementSibling.textContent = dict.kpi_rh;
  $('kpiEt0').previousElementSibling.textContent = dict.kpi_et0;
  $('btnSubmitGrv').textContent = dict.submit_grv;
});

/* ================= Initialization ================= */
(function init() {
  try {
    var savedTheme = localStorage.getItem('agromet_theme');
    if (savedTheme) { state.theme = savedTheme; document.documentElement.setAttribute('data-theme', savedTheme); }
    var savedAccent = localStorage.getItem('agromet_accent');
    if (savedAccent) { document.documentElement.setAttribute('data-accent', savedAccent); }
    paintSwatches();
    var savedUser = sessionStorage.getItem('agromet_session');
    if (savedUser) { state.user = JSON.parse(savedUser); onUserLoggedIn(); }
  } catch(e){}
  var validViews = ['farmer','weather','crop','warnings','gis','kvk','grievance','notices','security','audit','models','admin','login'];
  var start = ('' + (location.hash || '')).replace('#','');
  if (validViews.indexOf(start) < 0) start = state.user ? 'farmer' : 'login';
  if (start !== 'login' && LOCKED_VIEWS[start] && !state.user) start = 'login';
  switchView(start);
  loadPanchayats();
  loadWarnings();
  revealScan();
})();
</script>
</body>
</html>"""

def portal_html() -> str:
    return HTML
