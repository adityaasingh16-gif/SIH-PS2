"""Premium government-style web portal for SIH26074 — UI/UX upgraded (v2).

Single-file, dependency-free frontend. All data comes from the real backend
API; unconnected integrations render honest empty/locked states.
"""

from __future__ import annotations

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#431407">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%237c2d12'/%3E%3Ctext x='32' y='42' font-family='Arial' font-size='24' font-weight='bold' fill='white' text-anchor='middle'%3ETS%3C/text%3E%3C/svg%3E">
<title>Telangana Panchayat Agromet Portal</title>
<style>
/* ================= Design tokens ================= */
:root{
  --navy:#7c2d12;--navy-light:#c2410c;--navy-dark:#431407;
  --blue:#c2410c;--blue-light:#fdeee3;
  --saffron:#c96a00;--saffron-light:#fef3e2;
  --green:#137333;--green-light:#edf8ef;
  --red:#b42318;--red-light:#fff0ef;
  --amber:#8a5d00;--amber-light:#fff7e0;
  --info:#0e5a8a;--info-light:#edf5fb;
  --ink:#17212b;--muted:#55606b;--line:#d7dee5;--line-light:#e8edf1;
  --bg:#f8f5f1;--surface:#ffffff;--surface-elev:#ffffff;
  --focus:#1a73e8;
  --font:'Segoe UI',system-ui,-apple-system,Roboto,'Noto Sans',sans-serif;
  --mono:'Cascadia Code','SF Mono',Consolas,monospace;
  --s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:20px;--s6:24px;--s8:32px;--s10:40px;
  --r-sm:4px;--r-md:6px;--r-lg:10px;--r-xl:14px;--r-pill:999px;
  --sh-sm:0 1px 3px rgba(16,32,48,.07);
  --sh-md:0 2px 10px rgba(16,32,48,.09);
  --sh-lg:0 8px 28px rgba(16,32,48,.13);
  --ease:cubic-bezier(.25,.46,.45,.94);
  --fast:120ms;--norm:220ms;--slow:380ms;
  --gov-h:34px;--head-h:64px;--nav-h:46px;
  --side-w:264px;--side-c:68px;--max:1280px;
}
[data-theme="dark"]{
  --navy:#e8823c;--navy-light:#f0955a;--navy-dark:#241107;
  --blue:#f0955a;--blue-light:#2a1a10;
  --saffron:#e8932b;--saffron-light:#2b2010;
  --green:#4caf6d;--green-light:#0f2a1a;
  --red:#f26d5f;--red-light:#2b1512;
  --amber:#e8b93e;--amber-light:#2b2208;
  --info:#5ec8a5;--info-light:#14291f;
  --ink:#e9eef3;--muted:#a7b2bd;--line:#2b3d4f;--line-light:#20303f;
  --bg:#0e1721;--surface:#15212e;--surface-elev:#1a2836;
  --sh-sm:0 1px 3px rgba(0,0,0,.4);--sh-md:0 2px 10px rgba(0,0,0,.45);--sh-lg:0 8px 28px rgba(0,0,0,.55);
}
/* ================= Base ================= */
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:var(--font);color:var(--ink);background:var(--bg);line-height:1.55;-webkit-font-smoothing:antialiased}
h1,h2,h3,h4{margin:0;line-height:1.25;letter-spacing:-.01em}
p{margin:0}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
button,input,select,textarea{font:inherit;color:inherit}
button{cursor:pointer;min-height:44px}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:var(--r-sm)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-9999px;top:0;background:var(--navy-dark);color:#fff;padding:10px 16px;z-index:2000;font-weight:600;border-radius:0 0 var(--r-md) 0}
.skip:focus{left:0}
.muted{color:var(--muted)}.small{font-size:12px}.mono{font-family:var(--mono);font-size:12px}
.wrap{max-width:var(--max);margin:0 auto;width:100%;padding:0 var(--s5)}
/* ================= Gov bar / header / nav ================= */
.govbar{background:var(--navy-dark);color:rgba(255,255,255,.88);font-size:12px;min-height:var(--gov-h);display:flex;align-items:center}
.govbar .wrap{display:flex;justify-content:space-between;align-items:center;gap:var(--s4);padding-top:5px;padding-bottom:5px}
.govbar a{color:rgba(255,255,255,.88)}
.govbar .tools{display:flex;gap:var(--s2);align-items:center;flex-wrap:wrap}
.govbar .tools button{background:transparent;border:1px solid rgba(255,255,255,.25);color:#fff;padding:2px 9px;border-radius:var(--r-sm);font-size:11px;min-height:28px}
.govbar .tools button:hover{background:rgba(255,255,255,.12)}
.header{background:var(--surface);border-bottom:3px solid var(--saffron);position:sticky;top:0;z-index:200;box-shadow:var(--sh-sm)}
.header .wrap{display:flex;align-items:center;gap:var(--s4);min-height:var(--head-h);padding-top:8px;padding-bottom:8px}
.emblem{width:48px;height:48px;border:2px solid var(--navy);border-radius:50%;display:grid;place-items:center;color:var(--navy);font-weight:800;font-size:16px;flex-shrink:0;background:var(--surface)}
.brand{flex:1;min-width:0}
.brand h1{font-size:20px;color:var(--navy);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
[data-theme="dark"] .brand h1{color:var(--ink)}
.brand p{color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.header-actions{display:flex;align-items:center;gap:var(--s2);flex-shrink:0}
.pilot{background:var(--blue-light);color:var(--navy);border:1px solid var(--line);padding:4px 10px;border-radius:var(--r-sm);font-size:11px;font-weight:700;white-space:nowrap}
[data-theme="dark"] .pilot{color:var(--ink)}
.iconbtn{width:40px;height:40px;min-height:40px;border:1px solid var(--line);background:var(--surface);border-radius:var(--r-md);display:grid;place-items:center;color:var(--muted)}
.iconbtn:hover{border-color:var(--navy);color:var(--navy);background:var(--blue-light)}
.iconbtn svg{width:18px;height:18px}
.nav{background:var(--navy);color:#fff;position:sticky;top:var(--head-h);z-index:190}
.nav .wrap{display:flex;align-items:stretch;min-height:var(--nav-h);padding:0 var(--s5)}
.nav-links{display:flex;align-items:stretch;overflow-x:auto;scrollbar-width:none;flex:1}
.nav-links::-webkit-scrollbar{display:none}
.nav-btn{background:transparent;color:rgba(255,255,255,.85);border:0;border-bottom:3px solid transparent;padding:10px var(--s4);font-weight:600;font-size:13px;white-space:nowrap;min-height:var(--nav-h)}
.nav-btn:hover{color:#fff;background:rgba(255,255,255,.08)}
.nav-btn.active{color:#fff;border-bottom-color:var(--saffron);background:rgba(255,255,255,.06)}
.nav-toggle{display:none;background:transparent;border:0;color:#fff;padding:8px 10px;margin-left:auto}
/* ================= Page ================= */
.page{padding:var(--s5) 0 var(--s10)}
.crumb{font-size:12px;color:var(--muted);margin-bottom:var(--s3);display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.crumb a{color:var(--muted)}.crumb a:hover{color:var(--navy)}
.crumb .sep{opacity:.45}
.view{display:none}.view.active{display:block;animation:pageIn var(--norm) var(--ease)}
@keyframes pageIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.pagehead{margin:2px 0 var(--s5)}
.eyebrow{font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--saffron);margin-bottom:4px}
.pagehead h2{font-size:24px;margin-bottom:4px}
.pagehead p{color:var(--muted);font-size:14px;max-width:70ch}
.notice{background:var(--saffron-light);border:1px solid #ecc88f;border-left:4px solid var(--saffron);padding:var(--s4) var(--s5);margin-bottom:var(--s5);border-radius:var(--r-md);display:flex;gap:var(--s3);align-items:flex-start}
[data-theme="dark"] .notice{border-color:#4a3a1a}
.notice svg{width:20px;height:20px;color:var(--saffron);flex-shrink:0;margin-top:2px}
.notice p{font-size:13px}
/* ================= Hero / cards / grid ================= */
.hero{background:linear-gradient(135deg,var(--navy-dark) 0%,var(--navy) 55%,var(--navy-light) 100%);color:#fff;padding:var(--s8) var(--s6);border-radius:var(--r-lg);margin-bottom:var(--s5);position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;top:-60px;right:-40px;width:340px;height:340px;background:radial-gradient(circle,rgba(255,255,255,.09),transparent 70%);border-radius:50%}
.hero h2{margin:0 0 var(--s3);font-size:27px;position:relative}
.hero p{max-width:78ch;margin:0 0 var(--s5);color:rgba(255,255,255,.87);font-size:14.5px;position:relative}
.hero .actions{display:flex;gap:var(--s3);flex-wrap:wrap;position:relative}
.grid{display:grid;gap:var(--s4)}
.g4{grid-template-columns:repeat(4,1fr)}.g3{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);box-shadow:var(--sh-sm);margin-bottom:var(--s5);overflow:hidden}
.card-h{padding:var(--s4) var(--s5);border-bottom:1px solid var(--line-light);display:flex;align-items:center;justify-content:space-between;gap:var(--s3);flex-wrap:wrap}
.card-h h2,.card-h h3{font-size:16px;color:var(--navy)}
[data-theme="dark"] .card-h h2,[data-theme="dark"] .card-h h3{color:var(--ink)}
.card-b{padding:var(--s5)}
.kpi{padding:var(--s5)}
.kpi .label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.kpi .value{font-size:28px;font-weight:800;margin-top:4px;line-height:1.15;font-variant-numeric:tabular-nums}
.kpi .hint{font-size:12px;color:var(--muted);margin-top:2px}
.kpi{position:relative}
.kpi-ic{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;margin-bottom:10px}
.kpi-ic svg{width:20px;height:20px}
.tint-navy{background:var(--blue-light);color:var(--navy)}
.tint-green{background:var(--green-light);color:var(--green)}
.tint-amber{background:var(--amber-light);color:var(--amber)}
.tint-saffron{background:var(--saffron-light);color:var(--saffron)}
[data-theme="dark"] .tint-navy{color:var(--ink)}
.card.kpi{transition:transform var(--fast) var(--ease),box-shadow var(--norm) var(--ease)}
.card.kpi:hover{transform:translateY(-2px);box-shadow:var(--sh-md)}
.hero h2,.hero p,.hero .actions,.hero-stats{animation:heroUp var(--slow) var(--ease) backwards}
.hero p{animation-delay:90ms}.hero .actions{animation-delay:180ms}.hero-stats{animation-delay:260ms}
@keyframes heroUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.hero-stats{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px;position:relative}
.hchip{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#fff;font-size:12px;font-weight:600;padding:6px 12px;border-radius:var(--r-pill);font-variant-numeric:tabular-nums}
.hchip .dot{width:7px;height:7px;border-radius:50%;background:#4ade80}
.hero-split{display:grid;grid-template-columns:1.12fr .88fr;gap:var(--s8);align-items:center;background-image:radial-gradient(rgba(255,255,255,.09) 1px,transparent 1.4px),linear-gradient(135deg,var(--navy-dark) 0%,var(--navy) 55%,var(--navy-light) 100%);background-size:22px 22px,cover}
.hero-visual{display:flex;justify-content:center}
.hero-visual svg{width:100%;max-width:340px;height:auto;filter:drop-shadow(0 10px 24px rgba(0,0,0,.25))}
.hero-visual .ping{fill:none;stroke:rgba(255,255,255,.65);stroke-width:1.5;transform-box:fill-box;transform-origin:center;animation:ping 2.6s ease-out infinite}
@keyframes ping{from{transform:scale(.55);opacity:.9}to{transform:scale(2.3);opacity:0}}
.hero-visual .spark{fill:none;stroke:#ffcf87;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:400;stroke-dashoffset:400;animation:draw 1.2s var(--ease) .3s forwards}
.pipe{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--s4);position:relative;margin-top:var(--s4)}
.pipe::before{content:"";position:absolute;top:17px;left:11%;right:11%;height:2px;background:var(--line)}
.pstep{position:relative;text-align:center;padding:0 var(--s2)}
.pnum{width:36px;height:36px;border-radius:50%;background:var(--surface);border:2px solid var(--navy);color:var(--navy);font-weight:800;font-size:14px;display:grid;place-items:center;margin:0 auto var(--s2);position:relative;z-index:1}
.pstep b{display:block;font-size:13px;margin-bottom:2px}
.pstep span.d{font-size:11.5px;color:var(--muted);display:block;line-height:1.45}
.qlink{display:flex;gap:var(--s3);align-items:flex-start;text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:14px;min-height:72px;transition:border-color var(--fast) var(--ease),transform var(--fast) var(--ease),box-shadow var(--fast) var(--ease)}
.qlink:hover{border-color:var(--navy);transform:translateY(-1px);box-shadow:var(--sh-md);text-decoration:none}
.qic{width:36px;height:36px;border-radius:9px;display:grid;place-items:center;flex-shrink:0}
.qic svg{width:18px;height:18px}
.qlink b{display:block;font-size:13.5px;color:var(--navy)}
[data-theme="dark"] .qlink b{color:var(--ink)}
.qlink .qd{font-size:12px;color:var(--muted)}
@media(max-width:920px){.hero-split{grid-template-columns:1fr}.hero-visual{display:none}.pipe{grid-template-columns:1fr;gap:var(--s4)}.pipe::before{top:6%;bottom:6%;left:17px;right:auto;width:2px;height:auto}.pstep{text-align:left;display:flex;gap:var(--s3)}.pnum{margin:0;flex-shrink:0}}
@media(prefers-reduced-motion:reduce){.hero-visual .ping,.hero-visual .spark{animation:none}}
/* ================= Buttons ================= */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:var(--s2);border:1px solid var(--navy);background:var(--navy);color:#fff;padding:10px 18px;border-radius:var(--r-md);font-weight:650;font-size:13.5px;line-height:1.3;transition:transform var(--fast) var(--ease),box-shadow var(--fast) var(--ease),filter var(--fast) var(--ease)}
.btn:hover{filter:brightness(1.08);transform:translateY(-1px);box-shadow:var(--sh-md);text-decoration:none}
.btn:active{transform:none}
.btn.secondary{background:var(--surface);color:var(--navy);border-color:var(--line)}
[data-theme="dark"] .btn.secondary{color:var(--ink)}
.btn.secondary:hover{border-color:var(--navy);background:var(--blue-light)}
.btn.success{background:var(--green);border-color:var(--green)}
.btn.danger{background:var(--red);border-color:var(--red)}
.btn.ghost{background:transparent;border-color:transparent;color:var(--blue)}
.btn.sm{padding:7px 12px;font-size:12.5px;min-height:36px}
.btn:disabled{opacity:.55;cursor:not-allowed;transform:none!important;box-shadow:none!important}
.btn .spin{width:15px;height:15px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;animation:spin .65s linear infinite}
.btn.secondary .spin{border-color:rgba(11,61,98,.3);border-top-color:var(--navy)}
@keyframes spin{to{transform:rotate(360deg)}}
/* ================= Status / badges ================= */
.status{display:flex;align-items:flex-start;gap:8px;padding:10px 12px;border-radius:var(--r-md);font-size:13px;border:1px solid transparent}
.status svg{width:17px;height:17px;flex-shrink:0;margin-top:2px}
.status.ok{background:var(--green-light);color:var(--green);border-color:#bfe0c7}
.status.error{background:var(--red-light);color:var(--red);border-color:#efc4c0}
.status.warn{background:var(--amber-light);color:var(--amber);border-color:#ecd9a8}
.status.info{background:var(--info-light);color:var(--info);border-color:#bfd7e8}
[data-theme="dark"] .status{border-color:var(--line)}
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:var(--r-pill);font-size:11px;font-weight:750;letter-spacing:.02em;border:1px solid transparent;white-space:nowrap}
.badge .dot{width:7px;height:7px;border-radius:50%;background:currentColor}
.badge.green{color:var(--green);background:var(--green-light)}
.badge.red{color:var(--red);background:var(--red-light)}
.badge.amber{color:var(--amber);background:var(--amber-light)}
.badge.blue{color:var(--info);background:var(--info-light)}
.badge.grey{color:var(--muted);background:var(--bg);border-color:var(--line)}
.pulse{position:relative}
.pulse .dot::after{content:"";position:absolute;left:10px;top:50%;width:7px;height:7px;margin-top:-3.5px;border-radius:50%;background:currentColor;opacity:.5;animation:pulse 1.8s var(--ease) infinite}
@keyframes pulse{0%{transform:scale(1);opacity:.55}70%{transform:scale(2.1);opacity:0}100%{opacity:0}}
/* ================= Forms / tables / tabs ================= */
.field label{display:block;font-weight:650;font-size:13px;margin-bottom:6px}
.field label .req{color:var(--red)}
.field input,.field select,.field textarea{width:100%;border:1px solid var(--line);border-radius:var(--r-md);padding:10px 12px;background:var(--surface);transition:border-color var(--fast) var(--ease),box-shadow var(--fast) var(--ease)}
.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-color:var(--navy);box-shadow:0 0 0 3px rgba(11,61,98,.14)}
.field textarea{min-height:120px;resize:vertical}
.field .msg{font-size:12px;margin-top:5px;display:flex;gap:5px;align-items:flex-start}
.field .err{color:var(--red)}.field .okm{color:var(--green)}
.field.bad input,.field.bad select,.field.bad textarea{border-color:var(--red)}
.field.good input,.field.good select,.field.good textarea{border-color:var(--green)}
.charcount{font-size:11px;color:var(--muted);text-align:right;margin-top:3px}
.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s4)}
.form-grid .full{grid-column:1/-1}
.toolbar{display:flex;gap:var(--s3);align-items:flex-end;flex-wrap:wrap}
.toolbar .field{min-width:200px;flex:1}
.table-wrap{overflow-x:auto;border:1px solid var(--line-light);border-radius:var(--r-md)}
.table{width:100%;border-collapse:collapse;font-size:13px;min-width:640px}
.table caption{text-align:left;font-size:12px;color:var(--muted);padding:8px 12px;background:var(--bg)}
.table th{background:var(--bg);color:var(--muted);text-align:left;font-weight:750;font-size:11px;text-transform:uppercase;letter-spacing:.045em;padding:10px 12px;border-bottom:2px solid var(--line);white-space:nowrap;position:sticky;top:0}
.table td{border-bottom:1px solid var(--line-light);padding:10px 12px;vertical-align:top}
.table tbody tr{transition:background var(--fast) var(--ease)}
.table tbody tr:hover td{background:var(--blue-light)}
.table tbody tr:last-child td{border-bottom:0}
.tabs{display:flex;gap:2px;border-bottom:2px solid var(--line);overflow-x:auto}
.tab-btn{border:0;background:transparent;padding:11px 16px;color:var(--muted);font-weight:650;font-size:13px;white-space:nowrap;border-bottom:3px solid transparent;margin-bottom:-2px;min-height:44px}
.tab-btn:hover{color:var(--navy)}
.tab-btn.active{color:var(--navy);border-bottom-color:var(--saffron)}
[data-theme="dark"] .tab-btn.active,[data-theme="dark"] .tab-btn:hover{color:var(--ink)}
/* ================= Charts (SVG) ================= */
.chart{padding:var(--s5)}
.chart svg{width:100%;height:auto;display:block}
.chart .axis{font-size:10px;fill:var(--muted)}
.chart .gridln{stroke:var(--line-light);stroke-width:1}
.chart .band{fill:rgba(194,65,12,.14)}
.chart .pline{fill:none;stroke:var(--blue);stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:600;stroke-dashoffset:600;animation:draw 1s var(--ease) forwards}
.chart .pdot{fill:var(--navy)}
.chart .rbar{fill:var(--blue);rx:3}
.chart .rbar:hover{filter:brightness(1.12)}
@keyframes draw{to{stroke-dashoffset:0}}
/* ================= Timeline / empty / skeleton ================= */
.timeline{border-left:3px solid var(--line);padding-left:var(--s5);margin:4px 0}
.step{position:relative;margin-bottom:18px}.step:last-child{margin-bottom:0}
.step::before{content:"";position:absolute;left:calc(-1 * var(--s5) - 7px);top:4px;width:12px;height:12px;border-radius:50%;background:var(--navy);border:3px solid var(--surface);box-shadow:0 0 0 2px var(--navy)}
.step b{display:block;font-size:14px;margin-bottom:2px}
.empty{text-align:center;padding:var(--s10) var(--s5);color:var(--muted)}
.empty-ic{width:56px;height:56px;margin:0 auto var(--s4);border-radius:50%;background:var(--bg);border:1px solid var(--line-light);display:grid;place-items:center;color:var(--muted)}
.empty-ic svg{width:26px;height:26px}
.empty h3{font-size:15.5px;color:var(--ink);margin-bottom:6px}
.empty p{font-size:13px;max-width:46ch;margin:0 auto var(--s4)}
.skel{border-radius:var(--r-sm);background:linear-gradient(90deg,var(--bg) 25%,var(--line-light) 50%,var(--bg) 75%);background-size:200% 100%;animation:shim 1.4s linear infinite;min-height:14px}
@keyframes shim{to{background-position:-200% 0}}
/* ================= Toast / modal / search ================= */
.toasts{position:fixed;top:calc(var(--gov-h) + var(--head-h) + var(--nav-h) + 10px);right:var(--s5);z-index:3000;display:flex;flex-direction:column;gap:var(--s3);max-width:min(400px,calc(100vw - 24px))}
.toast{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--info);border-radius:var(--r-md);padding:var(--s4) var(--s4);box-shadow:var(--sh-lg);display:flex;gap:var(--s3);align-items:flex-start;animation:tin var(--norm) var(--ease);font-size:13px}
.toast.success{border-left-color:var(--green)}.toast.error{border-left-color:var(--red)}.toast.warning{border-left-color:var(--saffron)}
.toast svg{width:18px;height:18px;flex-shrink:0;margin-top:1px}
.toast.success svg{color:var(--green)}.toast.error svg{color:var(--red)}.toast.warning svg{color:var(--saffron)}.toast.info svg{color:var(--info)}
.toast b{display:block;margin-bottom:1px}.toast .tm{color:var(--muted);font-size:12px}
.toast button{background:transparent;border:0;color:var(--muted);font-size:18px;line-height:1;padding:2px 6px;min-height:32px}
.toast.out{animation:tout var(--fast) ease-in forwards}
@keyframes tin{from{opacity:0;transform:translateX(32px)}to{opacity:1;transform:none}}
@keyframes tout{to{opacity:0;transform:translateX(32px)}}
.overlay{position:fixed;inset:0;background:rgba(8,20,32,.5);z-index:2500;display:grid;place-items:center;padding:var(--s5);animation:fin var(--norm) var(--ease)}
@keyframes fin{from{opacity:0}to{opacity:1}}
.modal{background:var(--surface);border-radius:var(--r-xl);box-shadow:var(--sh-lg);max-width:580px;width:100%;max-height:90vh;overflow:auto;animation:min var(--norm) var(--ease)}
@keyframes min{from{opacity:0;transform:translateY(16px) scale(.98)}to{opacity:1;transform:none}}
.modal-h{padding:var(--s5) var(--s6);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:var(--s3)}
.modal-h h3{font-size:17px}.modal-b{padding:var(--s6)}.modal-f{padding:var(--s4) var(--s6);border-top:1px solid var(--line);display:flex;justify-content:flex-end;gap:var(--s3);flex-wrap:wrap}
.search-ov{position:fixed;inset:0;background:rgba(8,20,32,.45);z-index:2500;display:flex;align-items:flex-start;justify-content:center;padding:12vh var(--s4) var(--s4)}
.search-pal{background:var(--surface);border-radius:var(--r-xl);box-shadow:var(--sh-lg);max-width:620px;width:100%;overflow:hidden;animation:min var(--norm) var(--ease)}
.search-bar{display:flex;align-items:center;gap:var(--s3);padding:var(--s4) var(--s5);border-bottom:1px solid var(--line)}
.search-bar svg{width:19px;height:19px;color:var(--muted);flex-shrink:0}
.search-bar input{flex:1;border:0;outline:none;font-size:15.5px;background:transparent;min-height:40px}
.search-res{max-height:380px;overflow:auto;padding:var(--s2)}
.search-it{display:flex;gap:var(--s3);align-items:flex-start;padding:10px 12px;border-radius:var(--r-md);cursor:pointer;border:0;background:transparent;width:100%;text-align:left}
.search-it:hover,.search-it.sel{background:var(--blue-light)}
.search-it svg{width:16px;height:16px;color:var(--muted);flex-shrink:0;margin-top:3px}
.search-it .t{font-size:13.5px;font-weight:600}.search-it .d{font-size:12px;color:var(--muted)}
.search-it mark{background:var(--saffron-light);color:inherit;border-radius:2px;padding:0 1px}
.authwrap{max-width:1020px;margin:0 auto}
.authgrid{display:grid;grid-template-columns:1fr 1fr;gap:var(--s5);align-items:start}
.role{display:flex;gap:var(--s3);width:100%;text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:14px;margin-bottom:10px;align-items:flex-start;min-height:72px}
.role:hover{border-color:var(--navy)}
.role.sel{border-color:var(--navy);box-shadow:0 0 0 3px rgba(194,65,12,.18)}
.role b{display:block;font-size:13.5px;color:var(--navy)}
[data-theme="dark"] .role b{color:var(--ink)}
.role .qd{font-size:12px;color:var(--muted)}
.keyrow{display:flex;gap:8px}.keyrow input{flex:1}
.mapsvg{width:100%;height:auto;display:block}
.mk{cursor:pointer}.mk circle{stroke:#fff;stroke-width:2}
.mk .ok{fill:var(--green)}.mk .cfg{fill:var(--blue)}
.mk:hover circle,.mk:focus circle{stroke:var(--saffron);stroke-width:3}
.mk text{font-size:11px;fill:var(--muted)}
.table th.sortable{cursor:pointer;user-select:none}
.table th.sortable:hover{color:var(--navy)}
.table th .arr{font-size:10px;margin-left:4px}
.pager{display:flex;align-items:center;gap:12px;justify-content:flex-end;margin-top:12px;font-size:12.5px;color:var(--muted)}
tr.detail{display:none}tr.detail.open{display:table-row}tr.detail td{background:var(--bg);font-size:12.5px}
.expbtn{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-sm);width:28px;height:28px;min-height:28px;line-height:1;color:var(--muted);padding:0}
.expbtn:hover{border-color:var(--navy);color:var(--navy)}
.bellbadge{position:absolute;top:4px;right:4px;min-width:18px;height:18px;border-radius:9px;background:var(--red);color:#fff;font-size:10.5px;font-weight:800;display:grid;place-items:center;padding:0 5px}
.notif{display:flex;gap:12px;padding:12px 14px;border:1px solid var(--line);border-radius:var(--r-md);margin-bottom:10px;align-items:flex-start}
.notif.unread{border-color:var(--navy)}
.notif .ndot{width:9px;height:9px;border-radius:50%;background:var(--navy);flex-shrink:0;margin-top:6px}
.notif.read .ndot{background:var(--line)}
.notif .nt{flex:1;min-width:0}.notif .nh{font-weight:650;font-size:13.5px}.notif .nm{font-size:12px;color:var(--muted);margin-top:2px}
.reveal{opacity:0;transform:translateY(10px);transition:opacity var(--slow) var(--ease),transform var(--slow) var(--ease)}
.reveal.in{opacity:1;transform:none}
.setrow{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0;border-bottom:1px solid var(--line-light);flex-wrap:wrap}
.setrow:last-child{border-bottom:0}
.setrow .sl b{display:block;font-size:14px}.setrow .sl span{font-size:12.5px;color:var(--muted)}
.seg{display:flex;border:1px solid var(--line);border-radius:var(--r-md);overflow:hidden}
.seg button{border:0;background:var(--surface);padding:9px 16px;font-weight:650;font-size:13px;min-height:40px;color:var(--muted)}
.seg button.on{background:var(--navy);color:#fff}
.switch{position:relative;width:46px;height:26px;flex-shrink:0;display:inline-block}
.switch input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer}
.switch .tr{position:absolute;inset:0;background:var(--line);border-radius:13px;transition:background var(--fast) var(--ease)}
.switch .tr::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:var(--sh-sm);transition:transform var(--fast) var(--ease)}
.switch input:checked+.tr{background:var(--green)}
.switch input:checked+.tr::after{transform:translateX(20px)}
.switch input:focus-visible+.tr{outline:3px solid var(--focus);outline-offset:2px}
.metricbar{height:9px;background:var(--line-light);border-radius:6px;overflow:hidden;flex:1}
.metricbar span{display:block;height:100%;background:var(--navy)}
.mapleg{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px}
.mapleg .sw{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}
@media(max-width:880px){.authgrid{grid-template-columns:1fr}}
/* ================= Alerts / review cards ================= */
.alert{display:flex;gap:var(--s3);padding:var(--s4);border:1px solid var(--line);border-radius:var(--r-md);margin-bottom:var(--s3)}
.alert:hover{border-color:var(--navy)}
.alert .sev{width:4px;border-radius:2px;flex-shrink:0}
.sev.critical{background:var(--red)}.sev.high{background:#d35400}.sev.medium{background:var(--saffron)}.sev.low{background:var(--info)}.sev.info{background:var(--green)}
.alert .at{flex:1;min-width:0}.alert .ah{font-weight:700;font-size:13.5px;margin-bottom:2px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.alert .am{font-size:12px;color:var(--muted)}
.kv{border:1px solid var(--line);border-radius:var(--r-md);padding:var(--s4) var(--s5);margin-bottom:var(--s4)}
.kv .kh{display:flex;gap:var(--s2);align-items:center;flex-wrap:wrap;margin-bottom:6px}
.kv .kh b{font-size:14px}
.kv dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:6px 16px;margin:10px 0;font-size:12.5px}
.kv dt{color:var(--muted)}.kv dd{margin:0;font-weight:600;font-variant-numeric:tabular-nums}
/* ================= Sidebar layout ================= */
.lay{display:flex;gap:var(--s5);align-items:flex-start}
.side{width:var(--side-w);flex-shrink:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden;position:sticky;top:calc(var(--gov-h) + var(--head-h) + var(--nav-h) + var(--s5));transition:width var(--norm) var(--ease)}
.side.min{width:var(--side-c)}
.side nav{padding:var(--s3)}
.ssec{padding:10px 12px 4px;font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.slink{display:flex;align-items:center;gap:var(--s3);padding:10px 12px;border-radius:var(--r-md);color:var(--muted);font-size:13px;font-weight:550;white-space:nowrap;min-height:44px}
.slink:hover{background:var(--bg);color:var(--navy);text-decoration:none}
.slink.active{background:var(--blue-light);color:var(--navy);font-weight:700}
[data-theme="dark"] .slink:hover,[data-theme="dark"] .slink.active{color:var(--ink)}
.slink svg{width:18px;height:18px;flex-shrink:0}
.side.min .slink span,.side.min .ssec{display:none}
.side.min .slink{justify-content:center}
.stoggle{width:100%;border:0;border-top:1px solid var(--line);background:var(--bg);padding:10px;display:flex;align-items:center;justify-content:center;gap:6px;font-size:11.5px;font-weight:700;color:var(--muted);min-height:44px}
.stoggle:hover{color:var(--navy)}
.maincol{flex:1;min-width:0}
/* ================= Footer / mobile nav ================= */
.footer{background:var(--navy-dark);color:rgba(255,255,255,.72);margin-top:var(--s10);border-top:3px solid var(--saffron)}
.footer .wrap{padding-top:var(--s8);padding-bottom:var(--s8);display:grid;grid-template-columns:2fr 1fr 1fr;gap:var(--s8);font-size:13px}
.footer h3{color:#fff;font-size:14px;margin-bottom:var(--s3)}
.footer button.linklike{display:block;background:none;border:0;color:rgba(255,255,255,.72);padding:4px 0;font-size:13px;min-height:32px;text-align:left}
.footer button.linklike:hover{color:#fff;text-decoration:underline}
.footer-bot{border-top:1px solid rgba(255,255,255,.15);padding:12px var(--s5);font-size:11px;text-align:center}
.mnav{display:none;position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-top:1px solid var(--line);z-index:400;padding-bottom:env(safe-area-inset-bottom)}
.mnav .row{display:flex;justify-content:space-around}
.mnav a{display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 10px;color:var(--muted);font-size:10px;font-weight:700;min-width:60px;min-height:52px}
.mnav a.active{color:var(--navy)}[data-theme="dark"] .mnav a.active{color:var(--ink)}
.mnav svg{width:20px;height:20px}
/* ================= Responsive ================= */
@media(max-width:1180px){.g4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:1020px){
  .g3{grid-template-columns:repeat(2,1fr)}
  .footer .wrap{grid-template-columns:1fr 1fr}
  .lay{flex-direction:column}.side{width:100%!important;position:static}
  .side nav{display:flex;flex-wrap:wrap;gap:2px;align-items:center}
  .ssec{width:100%}
}
@media(max-width:760px){
  .govbar .wrap{flex-direction:column;align-items:flex-start;gap:6px}
  .header .wrap{flex-wrap:wrap}.brand h1{font-size:17px;white-space:normal}.brand p{white-space:normal}
  .pilot{display:none}
  .nav-toggle{display:block}
  .nav-links{display:none;flex-direction:column;width:100%}
  .nav-links.open{display:flex}
  .nav-btn{text-align:left;border-bottom:1px solid rgba(255,255,255,.08);border-left:3px solid transparent}
  .nav-btn.active{border-left-color:var(--saffron);border-bottom-color:transparent}
  .g4,.g3,.g2,.form-grid{grid-template-columns:1fr}
  .hero{padding:var(--s6) var(--s4)}.hero h2{font-size:22px}.pagehead h2{font-size:21px}
  .wrap,.nav .wrap{padding-left:var(--s4);padding-right:var(--s4)}
  .page{padding:var(--s4) 0 var(--s10)}
  .footer .wrap{grid-template-columns:1fr;gap:var(--s5)}
  .mnav{display:block}body{padding-bottom:64px}
  .toasts{left:12px;right:12px;max-width:none}
  .hero .actions .btn,.toolbar .btn{width:100%}
  .table{min-width:560px}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
  html{scroll-behavior:auto}
}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:5px}::-webkit-scrollbar-thumb:hover{background:var(--muted)}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<div class="govbar"><div class="wrap"><div>Government of Telangana &bull; Agriculture &amp; Agrometeorological Decision Support</div><div class="tools"><button data-goto="help" type="button">Accessibility</button><button data-goto="help" type="button">Help</button><button id="fontDown" type="button" aria-label="Decrease text size">A&minus;</button><button id="fontUp" type="button" aria-label="Increase text size">A+</button><button id="langBtn" type="button">English &#9662;</button><button id="themeToggle" type="button" aria-label="Toggle dark mode" aria-pressed="false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg></button></div></div></div>
<header class="header"><div class="wrap"><div class="emblem" aria-hidden="true">TS</div><div class="brand"><h1>Telangana Panchayat Agromet Portal</h1><p>Panchayat-level weather downscaling and agro-meteorological advisory decision support</p></div><div class="header-actions"><span class="pilot">SIH26074 &bull; PILOT</span><button class="btn sm" id="loginBtn" data-view="login" type="button">Sign in</button><span class="pilot" id="userChip" style="display:none"></span><button class="btn secondary sm" id="logoutBtn" type="button" style="display:none">Sign out</button><button class="iconbtn" id="notifBtn" data-view="notifications" type="button" aria-label="Notifications" style="position:relative"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg><span class="bellbadge" id="notifBadge" hidden></span></button><button class="iconbtn" id="searchBtn" type="button" aria-label="Search pages and panchayats"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></button></div></div></header>
<nav class="nav" aria-label="Main navigation"><div class="wrap"><div class="nav-links" id="navLinks"><button class="nav-btn active" data-view="home" type="button" aria-current="page">Home</button><button class="nav-btn" data-view="projects" type="button">Projects</button><button class="nav-btn" data-view="dashboard" type="button">Dashboard</button><button class="nav-btn" data-view="reports" type="button">Reports</button><button class="nav-btn" data-view="notices" type="button">Notices</button><button class="nav-btn" data-view="services" type="button">Services</button><button class="nav-btn" data-view="citizen" type="button">Citizen</button><button class="nav-btn" data-view="officer" type="button">Officer</button><button class="nav-btn" data-view="admin" type="button">Administration</button><button class="nav-btn" data-view="settings" type="button">Settings</button></div><button class="nav-toggle" id="navToggle" type="button" aria-label="Toggle navigation menu" aria-expanded="false"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 12h18M3 6h18M3 18h18"/></svg></button></div></nav>
<main id="main" class="page"><div class="wrap">
<div id="crumb" class="crumb" aria-label="Breadcrumb">Home</div>
<div class="notice" role="note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg><p><strong>Important:</strong> This pilot presents analytical decision-support. The bundled <strong>M1 model uses synthetic development data</strong>; it is not a production Telangana accuracy claim. Connect approved IMD/TGDPS/AWS historical data before operational deployment.</p></div>

<section id="login" class="view" aria-label="Sign in">
<div class="authwrap">
<div class="pagehead"><div class="eyebrow">Secure access</div><h2>Sign in to the portal</h2><p>Public pages stay open to everyone. Sign in to enter the officer, scientist and administrator workspaces. This pilot uses workspace roles plus the server API key; production must use the department identity provider.</p></div>
<div class="authgrid">
<div class="card"><div class="card-h"><h2>1 · Choose your workspace</h2></div><div class="card-b" id="roleList" role="radiogroup" aria-label="Workspace role">
<button type="button" class="role sel" data-role="citizen" role="radio" aria-checked="true"><span class="qic tint-green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span><span><b>Citizen</b><span class="qd">Grievances, public forecasts and help</span></span></button>
<button type="button" class="role" data-role="officer" role="radio" aria-checked="false"><span class="qic tint-navy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg></span><span><b>Officer</b><span class="qd">Forecasts, early warnings and monitoring</span></span></button>
<button type="button" class="role" data-role="kvk" role="radio" aria-checked="false"><span class="qic tint-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4a2 2 0 014 0M9 13l2 2 4-4"/></svg></span><span><b>KVK Scientist</b><span class="qd">Advisory review and audit trail</span></span></button>
<button type="button" class="role" data-role="admin" role="radio" aria-checked="false"><span class="qic tint-saffron"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span><span><b>Administrator</b><span class="qd">Governance, audit events and security</span></span></button>
</div></div>
<div class="card"><div class="card-h"><h2>2 · Identify yourself</h2></div><div class="card-b">
<div class="field"><label for="loginReviewer">Email / Reviewer ID</label><input id="loginReviewer" value="" autocomplete="username" maxlength="254"></div>
<div class="field" style="margin-top:12px"><label for="loginPassword">Password</label><input id="loginPassword" type="password" autocomplete="current-password" minlength="12" placeholder="Enter account password"></div>
<div class="field" style="margin-top:12px"><label for="loginKey">API key <span class="small muted">(legacy pilot fallback, if enabled)</span></label><div class="keyrow"><input id="loginKey" type="password" placeholder="Enter API key" autocomplete="current-password"><button type="button" class="btn secondary sm" id="loginKeyToggle" aria-label="Show API key">Show</button></div></div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px"><button type="button" class="btn secondary" id="loginVerify">Verify key</button><button type="button" class="btn" id="loginContinue">Continue</button></div>
<div id="loginMsg" style="margin-top:12px" role="status"></div>
</div></div>
</div></div>
</section>

<section id="home" class="view active" aria-label="Home">
<div class="hero hero-split"><div class="hero-text"><h2>AI-enabled Panchayat-level Agrometeorological Decision Support</h2><p>Terrain-aware five-day weather forecasts, calibrated uncertainty, deterministic farm advisories and KVK scientist review &mdash; presented through a public-sector monitoring portal.</p><div class="actions"><button class="btn" data-view="dashboard" type="button">Open Forecast Dashboard</button><button class="btn secondary" data-view="projects" type="button" style="background:#fff">View Projects &amp; Coverage</button><button class="btn secondary" data-view="reports" type="button" style="background:#fff">Reports &amp; Evaluation</button></div><div class="hero-stats" aria-label="Live pilot figures"><span class="hchip"><span class="dot" aria-hidden="true"></span><span id="heroStatP">Loading registry…</span></span><span class="hchip" id="heroStatM">Model: —</span><span class="hchip" id="heroStatF">Forecasts: —</span></div></div><div class="hero-visual" aria-hidden="true"><svg viewBox="0 0 320 250"><circle cx="252" cy="52" r="18" fill="none" stroke="rgba(255,255,255,.28)"/><circle cx="252" cy="52" r="34" fill="none" stroke="rgba(255,255,255,.2)"/><circle cx="252" cy="52" r="50" fill="none" stroke="rgba(255,255,255,.13)"/><circle class="ping" cx="252" cy="52" r="18"/><circle cx="252" cy="52" r="7" fill="#e8932b"/><circle cx="252" cy="52" r="2.6" fill="#fff"/><rect x="16" y="96" width="252" height="138" rx="10" fill="rgba(255,255,255,.1)" stroke="rgba(255,255,255,.32)"/><text x="32" y="120" font-family="Segoe UI,sans-serif" font-size="10.5" font-weight="700" letter-spacing="1.5" fill="rgba(255,255,255,.75)">PANCHAYAT 201001 &middot; 5-DAY</text><circle cx="52" cy="152" r="13" fill="#ffcf87"/><text x="76" y="164" font-family="Segoe UI,sans-serif" font-size="34" font-weight="800" fill="#fff">32&deg;</text><text x="150" y="164" font-family="Segoe UI,sans-serif" font-size="11" fill="rgba(255,255,255,.8)">P50 max &middot; RH 64%</text><path class="spark" d="M32,206 L78,194 L124,200 L170,182 L216,188 L252,176"/><circle cx="32" cy="206" r="3" fill="#ffcf87"/><circle cx="170" cy="182" r="3" fill="#ffcf87"/><circle cx="252" cy="176" r="3" fill="#ffcf87"/></svg></div></div>
<div class="pagehead"><div class="eyebrow">Pilot at a glance</div><h2>System overview</h2><p>Live counts below come from the portal summary API. Figures animate once when loaded.</p></div>
<div id="summaryGrid" class="grid g4">
<div class="card kpi"><div class="kpi-ic tint-navy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg></div><div class="label">Panchayats configured</div><div class="value" id="kpiPanchayats">&mdash;</div><div class="hint">Registered in the Panchayat registry</div></div>
<div class="card kpi"><div class="kpi-ic tint-green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 20h18"/><path d="M6 20v-6M11 20V6M16 20v-9M21 20V11"/></svg></div><div class="label">Forecasts available</div><div class="value" id="kpiForecasts">&mdash;</div><div class="hint">Stored five-day forecasts</div></div>
<div class="card kpi"><div class="kpi-ic tint-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4a2 2 0 014 0M9 13l2 2 4-4"/></svg></div><div class="label">Pending KVK review</div><div class="value" id="kpiPending">&mdash;</div><div class="hint">Advisories awaiting scientist sign-off</div></div>
<div class="card kpi"><div class="kpi-ic tint-saffron"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div><div class="label">System status</div><div class="value" id="kpiHealth" style="font-size:20px">&mdash;</div><div class="hint" id="kpiModelHint">Active model version</div></div>
</div>
<div id="summaryError" style="margin-bottom:var(--s5)"></div>
<div class="grid g2"><div class="card"><div class="card-h"><h2>About the pilot</h2></div><div class="card-b"><p class="muted" style="margin-bottom:var(--s5)">The system downscales coarse forecast information toward Panchayat locations using terrain features, lapse-rate physics, station residual corrections and a versioned probabilistic model.</p><div class="pipe"><div class="pstep"><span class="pnum">1</span><div><b>Coarse forecast</b><span class="d">Open-Meteo / approved IMD upstream</span></div></div><div class="pstep"><span class="pnum">2</span><div><b>Terrain-aware features</b><span class="d">Elevation, slope, aspect and water-distance</span></div></div><div class="pstep"><span class="pnum">3</span><div><b>M1 probabilistic forecast</b><span class="d">Quantile estimates and calibrated rainfall odds</span></div></div><div class="pstep"><span class="pnum">4</span><div><b>KVK review</b><span class="d">Scientist sign-off and auditable changes</span></div></div></div></div></div>
<div class="card"><div class="card-h"><h2>Public information</h2></div><div class="card-b"><div class="grid g2"><button class="qlink" data-view="notices" type="button"><span class="qic tint-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg></span><span><b>Notices &amp; announcements</b><span class="qd">Official announcements and alerts</span></span></button><button class="qlink" data-view="reports" type="button"><span class="qic tint-navy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg></span><span><b>Reports &amp; publications</b><span class="qd">Evaluation records and methodology</span></span></button><button class="qlink" data-view="services" type="button"><span class="qic tint-green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span><span><b>Citizen services</b><span class="qd">Grievance support and tracking</span></span></button><button class="qlink" data-view="help" type="button"><span class="qic tint-saffron"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg></span><span><b>FAQ &amp; help</b><span class="qd">Usage guide and accessibility</span></span></button></div></div></div></div>
</section>

<section id="dashboard" class="view" aria-label="Forecast dashboard">
<div class="pagehead"><div class="eyebrow">Forecast</div><h2>Forecast Dashboard</h2><p>Select a Panchayat, generate the latest terrain-aware forecast, or open a stored one. Charts show median values with the P10&ndash;P90 uncertainty band.</p></div>
<div class="card"><div class="card-h"><h2>Generate forecast</h2><span class="badge grey"><span class="dot"></span>5-day horizon</span></div><div class="card-b"><div class="toolbar"><div class="field"><label for="panchayat">Panchayat</label><select id="panchayat" aria-describedby="panchayatHint"></select><div class="small muted" id="panchayatHint">Registry loads from the backend on page open.</div></div><button id="refreshBtn" class="btn" type="button">Generate latest forecast</button><button id="viewBtn" class="btn secondary" type="button">View stored forecast</button></div><div id="status" class="status info" role="status" style="margin-top:var(--s4)">Loading Panchayat registry&hellip;</div></div></div>
<div class="grid g4">
<div class="card kpi"><div class="label">Selected Panchayat</div><div class="value" id="kpiPanchayat" style="font-size:20px">&mdash;</div><div class="hint">Currently displayed forecast</div></div>
<div class="card kpi"><div class="label">Model version</div><div class="value" id="kpiModel" style="font-size:15px">&mdash;</div><div class="hint">Exposed by the forecast API</div></div>
<div class="card kpi"><div class="label">Forecast horizon</div><div class="value">5 days</div><div class="hint">Daily steps, UTC</div></div>
<div class="card kpi"><div class="label">ET&#8320;, Day 1</div><div class="value" id="kpiEt0">&mdash;</div><div class="hint">FAO-56 reference evapotranspiration</div></div>
</div>
<div class="grid g2">
<div class="card"><div class="card-h"><h2>Temperature outlook</h2><span class="small muted">P10 / P50 / P90, &deg;C</span></div><div id="tempChart" class="chart" role="img" aria-label="Temperature outlook chart"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z"/></svg></div><p>Generate a forecast to display P10/P50/P90.</p></div></div></div>
<div class="card"><div class="card-h"><h2>Rainfall outlook</h2><span class="small muted">Expected mm + heavy-rain probability</span></div><div id="rainChart" class="chart" role="img" aria-label="Rainfall outlook chart"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 16.58A5 5 0 0018 7h-1.26A8 8 0 104 15.25"/></svg></div><p>Generate a forecast to display rainfall.</p></div></div></div>
</div>
<div class="card"><div class="card-h"><h2>Five-day forecast</h2><span class="small muted">Quantile values with calibrated probabilities</span></div><div class="card-b" id="forecastTable"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg></div><h3>No forecast loaded</h3><p>Select a Panchayat above and choose &ldquo;Generate latest forecast&rdquo;.</p></div></div></div>
</section>

<section id="projects" class="view" aria-label="Projects and coverage">
<div class="hero"><h2>Projects &amp; Geographic Coverage</h2><p>Public transparency view for the configured Panchayat pilot. Project-management records appear only when a project data source is connected &mdash; nothing is fabricated.</p></div>
<div class="card"><div class="card-h"><h2>Panchayat location map</h2><span class="small muted">Schematic plot from registry coordinates</span></div><div class="card-b"><div id="coverMap" role="img" aria-label="Schematic panchayat location map"></div><div class="mapleg small muted"><span><span class="sw" style="background:var(--green)"></span>Forecast available</span><span><span class="sw" style="background:var(--blue)"></span>Configured</span></div><p class="small muted" style="margin-top:8px">Marker color shows stored-forecast availability. Activate a marker to open that Panchayat.</p></div></div>
<div class="card"><div class="card-h"><h2>Configured Panchayat coverage</h2><div class="toolbar" style="align-items:center"><div class="field" style="min-width:220px"><label for="coverageSearch" class="sr">Filter panchayats</label><input id="coverageSearch" type="search" placeholder="Filter by Panchayat ID&hellip;" autocomplete="off"></div></div></div><div class="card-b"><div id="coverageTable"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><p>Loading coverage&hellip;</p></div></div></div></div>
<div class="card"><div class="card-h"><h2>Project transparency</h2></div><div class="card-b"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg></div><h3>No project dataset connected</h3><p>No government infrastructure project dataset is connected to this Agromet pilot. No fabricated project records are displayed.</p></div></div></div>
</section>

<section id="reports" class="view" aria-label="Reports">
<div class="pagehead"><div class="eyebrow">Evidence</div><h2>Reports, Publications &amp; Model Evaluation</h2><p>Evaluation records come from the persisted scorecard file when supplied. Method and limitations are stated explicitly.</p></div>
<div class="card"><div class="card-h"><h2>Model evaluation</h2></div><div class="card-b"><div class="tabs" role="tablist" id="reportTabs"><button class="tab-btn active" data-tab="score" type="button" role="tab" aria-selected="true">Model evaluation</button><button class="tab-btn" data-tab="method" type="button" role="tab" aria-selected="false">Method</button><button class="tab-btn" data-tab="limitations" type="button" role="tab" aria-selected="false">Data &amp; limitations</button></div>
<div id="reportScore" style="padding-top:var(--s5)"></div>
<div id="reportMethod" style="display:none;padding-top:var(--s5)"><div class="grid g2"><div><h3 style="margin-bottom:var(--s3);font-size:15px">Evaluation framework</h3><p class="muted">Continuous metrics include MAE, RMSE and bias. Rainfall evaluation includes POD, FAR, CSI, Brier Score and Brier Skill Score against the defined baselines.</p></div><div><h3 style="margin-bottom:var(--s3);font-size:15px">Model lineage</h3><p class="muted">Physics baseline &rarr; lapse-rate/IDW correction &rarr; calibrated LightGBM M1. The active model version is always exposed by the forecast API.</p></div></div></div>
<div id="reportLimitations" style="display:none;padding-top:var(--s5)"><div class="status warn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg><span>The bundled M1 artifact was trained on synthetic development data. Production validation requires historical AWS/TGDPS observations, matched coarse forecasts, terrain data and time-based evaluation.</span></div></div>
</div></div>
</section>

<section id="notices" class="view" aria-label="Notices">
<div class="pagehead"><div class="eyebrow">Public information</div><h2>Notices &amp; Announcements</h2><p>Official notices appear here when connected. Empty states never invent announcements.</p></div>
<div class="card"><div class="card-h"><h2>All notices</h2></div><div class="card-b"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg></div><h3>No notices published</h3><p>No official notices have been connected to this pilot. This page intentionally avoids fabricated government announcements.</p></div></div></div>
</section>

<section id="services" class="view" aria-label="Services">
<div class="pagehead"><div class="eyebrow">Citizen</div><h2>Citizen Services</h2><p>Entry points for grievance submission, tracking and help.</p></div>
<div class="card"><div class="card-h"><h2>Available services</h2></div><div class="card-b"><div class="grid g3"><button class="btn secondary" data-view="citizen" type="button">Citizen dashboard</button><button class="btn secondary" data-view="grievance" type="button">Submit grievance</button><button class="btn secondary" data-view="help" type="button">Help &amp; accessibility</button></div></div></div>
<div class="card"><div class="card-h"><h2>Service status</h2></div><div class="card-b"><div id="serviceStatus" class="status ok" role="status">Agromet forecast API is available when the local service is running.</div></div></div>
</section>

<section id="citizen" class="view" aria-label="Citizen services">
<div class="hero"><h2>Citizen Services</h2><p>Submit and track pilot grievances and access public forecast information. Citizen identity verification is not enabled by this local pilot.</p></div>
<div class="grid g2">
<div class="card"><div class="card-h"><h2>Submit a grievance</h2></div><div class="card-b">
<form id="grievanceForm" novalidate>
<div id="grievanceErrors" class="status error" style="display:none;margin-bottom:var(--s4)" role="alert"></div>
<div class="form-grid">
<div class="field" data-field="name"><label for="gName">Name <span class="req" aria-hidden="true">*</span></label><input id="gName" name="name" required minlength="2" maxlength="120" placeholder="Enter your full name" autocomplete="name"><div class="msg" hidden></div></div>
<div class="field" data-field="mobile"><label for="gMobile">Mobile <span class="req" aria-hidden="true">*</span></label><input id="gMobile" name="mobile" required minlength="10" maxlength="20" inputmode="tel" placeholder="10-digit mobile number" autocomplete="tel"><div class="msg" hidden></div></div>
<div class="field" data-field="category"><label for="gCategory">Category <span class="req" aria-hidden="true">*</span></label><select id="gCategory" name="category" required><option value="">Select category</option><option>Forecast service</option><option>Advisory</option><option>Data quality</option><option>Portal access</option><option>Other</option></select><div class="msg" hidden></div></div>
<div class="field" data-field="subject"><label for="gSubject">Subject <span class="req" aria-hidden="true">*</span></label><input id="gSubject" name="subject" required minlength="3" maxlength="160" placeholder="Brief subject"><div class="msg" hidden></div></div>
<div class="field full" data-field="description"><label for="gDesc">Description <span class="req" aria-hidden="true">*</span></label><textarea id="gDesc" name="description" required minlength="10" maxlength="4000" placeholder="Describe your grievance in detail"></textarea><div class="charcount"><span id="gDescCount">0</span> / 4000</div><div class="msg" hidden></div></div>
</div>
<div style="margin-top:var(--s4)"><button class="btn" type="submit" id="grievanceSubmit">Submit grievance</button></div>
<div id="grievanceResult" style="margin-top:var(--s3)"></div>
</form>
</div></div>
<div class="card"><div class="card-h"><h2>Track submitted grievances</h2><button id="loadGrievances" class="btn secondary sm" type="button">Refresh list</button></div><div class="card-b"><div id="grievanceList"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div><h3>No grievances loaded</h3><p>Choose &ldquo;Refresh list&rdquo; to load grievances from the backend.</p></div></div></div></div>
</div>
</section>

<section id="officer" class="view" aria-label="Officer workspace">
<div class="lay">
<aside class="side" id="officerSidebar"><nav aria-label="Officer section navigation"><div class="ssec">Overview</div><a class="slink active" data-view="officer" href="#officer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg><span>Dashboard</span></a><div class="ssec">Forecast</div><a class="slink" data-view="dashboard" href="#dashboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg><span>Forecast dashboard</span></a><a class="slink" data-view="projects" href="#projects"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Projects</span></a><div class="ssec">Review</div><a class="slink" data-view="kvk" href="#kvk"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3z"/><path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/></svg><span>KVK review</span></a><div class="ssec">Governance</div><a class="slink" data-view="admin" href="#admin"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Administration</span></a><a class="slink" data-view="security" href="#security"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg><span>Security centre</span></a></nav><button class="stoggle" id="sidebarToggle" type="button" aria-expanded="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg><span>Collapse</span></button></aside>
<div class="maincol">
<div class="hero"><h2>Officer Monitoring Workspace</h2><p>Operational view for forecast generation, early warnings and KVK review. Authentication must be connected to the department identity provider before production use.</p></div>
<div class="grid g4"><div class="card kpi"><div class="label">Panchayats</div><div class="value" id="offPanch">&mdash;</div></div><div class="card kpi"><div class="label">Forecasts available</div><div class="value" id="offForecasts">&mdash;</div></div><div class="card kpi"><div class="label">Pending review</div><div class="value" id="offPending">&mdash;</div></div><div class="card kpi"><div class="label">System health</div><div class="value" id="offHealth" style="font-size:20px">&mdash;</div></div></div>
<div class="grid g2">
<div class="card"><div class="card-h"><h2>Early warning centre</h2><button class="btn secondary sm" id="reloadAlerts" type="button">Refresh</button></div><div class="card-b" id="alerts" role="status"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg></div><p>Loading alerts&hellip;</p></div></div></div>
<div class="card"><div class="card-h"><h2>KVK review queue</h2></div><div class="card-b"><p class="muted" style="margin-bottom:var(--s4)">Pending advisories need scientist sign-off before dissemination. Every decision is written to the audit log.</p><button class="btn" data-view="kvk" type="button">Open KVK review</button><p class="small muted" style="margin-top:var(--s3)">All approval/rejection actions are audited in SQLite.</p></div></div>
</div>
</div>
</div>
</section>

<section id="kvk" class="view" aria-label="KVK review">
<div class="pagehead"><div class="eyebrow">Scientist review</div><h2>KVK / AMFU Scientist Review</h2><p>Approve or reject deterministic advisories. Notes are optional but recommended for the audit trail.</p></div>
<div class="card"><div class="card-h"><h2>Review queue</h2><span class="badge grey"><span class="dot"></span>Audited in SQLite</span></div><div class="card-b"><div class="grid g3"><div class="field"><label for="reviewer">Reviewer ID</label><input id="reviewer" value="kvk-scientist-1" autocomplete="username"></div><div class="field"><label for="apiKey">API key, if configured</label><input id="apiKey" type="password" placeholder="Enter API key" autocomplete="current-password"></div><div style="display:flex;align-items:flex-end"><button id="loadPending" class="btn" type="button">Load pending advisories</button></div></div><div id="pendingList" style="margin-top:var(--s5)" role="status"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3z"/><path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/></svg></div><h3>Review queue is empty</h3><p>Choose &ldquo;Load pending advisories&rdquo; to fetch items awaiting sign-off.</p></div></div></div></div>
</section>

<section id="admin" class="view" aria-label="Administration">
<div class="lay">
<aside class="side" id="adminSidebar"><nav aria-label="Administration section navigation"><div class="ssec">Overview</div><a class="slink active" data-view="admin" href="#admin"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg><span>Dashboard</span></a><div class="ssec">Management</div><a class="slink" data-view="projects" href="#projects"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Projects</span></a><a class="slink" data-view="kvk" href="#kvk"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3z"/><path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/></svg><span>KVK review</span></a><div class="ssec">Security</div><a class="slink" data-view="security" href="#security"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Security centre</span></a><a class="slink" data-view="officer" href="#officer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg><span>Audit logs</span></a></nav><button class="stoggle" id="adminSidebarToggle" type="button" aria-expanded="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg><span>Collapse</span></button></aside>
<div class="maincol">
<div class="hero"><h2>Administration & Governance</h2><p>Administrative controls are shown as a governance workspace. Production identity, RBAC and departmental directory integration must be connected before enabling privileged actions.</p></div>
<div class="grid g3"><div class="card kpi"><div class="label">Users</div><div class="value">&mdash;</div><div class="hint">External identity provider required</div></div><div class="card kpi"><div class="label">Roles &amp; permissions</div><div class="value">RBAC</div><div class="hint">Backend enforcement required</div></div><div class="card kpi"><div class="label">Audit events</div><div class="value" id="auditCount">&mdash;</div><div class="hint">KVK review events</div></div></div>
<div class="card"><div class="card-h"><h2>Audit &amp; Security</h2></div><div class="card-b"><div class="toolbar"><button class="btn secondary" id="loadAudit" type="button">Load audit events</button><button class="btn secondary" data-view="security" type="button">Security centre</button></div><div id="auditList" style="margin-top:var(--s4)" role="status"><div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><h3>Audit events need credentials</h3><p>Enter the configured API key in the KVK section, then load audit events.</p></div></div></div></div>
</div>
</div>
</section>

<section id="security" class="view" aria-label="Security centre">
<div class="pagehead"><div class="eyebrow">Trust &amp; safety</div><h2>Defensive Security Monitoring</h2><p>This pilot exposes no offensive functions. Telemetry appears here only when an endpoint is connected.</p></div>
<div class="card"><div class="card-h"><h2>Security overview</h2><span class="badge grey"><span class="dot"></span>No telemetry connected</span></div><div class="card-b"><div class="status ok" style="margin-bottom:var(--s5)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>This pilot exposes no offensive security functions. Integrate the existing defensive IDS/rate-limiting telemetry here when connected.</span></div>
<div class="grid g4" style="margin-bottom:var(--s2)"><div class="card kpi"><div class="label">Requests</div><div class="value">&mdash;</div></div><div class="card kpi"><div class="label">Blocked</div><div class="value">&mdash;</div></div><div class="card kpi"><div class="label">Suspicious</div><div class="value">&mdash;</div></div><div class="card kpi"><div class="label">Critical</div><div class="value">&mdash;</div></div></div>
<div class="empty"><div class="empty-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><h3>No security telemetry</h3><p>No security telemetry endpoint is connected in the Agromet backend. The UI does not fabricate security events.</p></div></div></div>
</section>

<section id="grievance" class="view" aria-label="Grievance">
<div class="pagehead"><div class="eyebrow">Support</div><h2>Grievance</h2><p>Use the Citizen service to submit a grievance and receive a tracking ID.</p></div>
<div class="card"><div class="card-h"><h2>Open grievance service</h2></div><div class="card-b"><button class="btn" data-view="citizen" type="button">Open Citizen grievance service</button></div></div>
</section>

<section id="notifications" class="view" aria-label="Notifications">
<div class="pagehead"><div class="eyebrow">Alerts</div><h2>Notifications</h2><p>Advisory queue items, forecast-derived warnings and grievance updates. Read state lives on this device only; the server stays the source of truth, and no timestamp is ever invented.</p></div>
<div class="card"><div class="card-h"><h2>All notifications</h2><div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn secondary sm" id="notifRefresh" type="button">Refresh</button><button class="btn secondary sm" id="notifReadAll" type="button">Mark all read</button></div></div><div class="card-b"><div id="notifList" role="status"><div class="empty"><p>Loading…</p></div></div></div></div>
</section>
<section id="settings" class="view" aria-label="Settings">
<div class="pagehead"><div class="eyebrow">Preferences</div><h2>Settings</h2><p>Profile, appearance and notification preferences. Stored on this device; nothing leaves the browser except real API calls.</p></div>
<div class="grid g2">
<div class="card"><div class="card-h"><h2>Profile</h2></div><div class="card-b">
<div class="field"><label for="setName">Display name / Reviewer ID</label><input id="setName" maxlength="80" autocomplete="username"></div>
<div id="setDirty" style="display:none;gap:8px;margin-top:12px"><button class="btn sm" id="setSave" type="button">Save changes</button><button class="btn secondary sm" id="setDiscard" type="button">Discard</button></div>
<div style="margin-top:14px" id="setSession"></div>
<div style="margin-top:12px"><button class="btn secondary sm" id="setLogout" type="button">Sign out</button></div>
</div></div>
<div class="card"><div class="card-h"><h2>Appearance</h2></div><div class="card-b">
<div class="setrow"><div class="sl"><b>Theme</b><span>Dark mode keeps charts and branding readable.</span></div><div class="seg" id="themeSeg" role="group" aria-label="Theme"><button type="button" data-ts="light">Light</button><button type="button" data-ts="dark">Dark</button></div></div>
<div class="setrow"><div class="sl"><b>Text size</b><span>Scales the whole interface (<span id="setFontVal">100%</span>).</span></div><div style="display:flex;gap:8px"><button class="btn secondary sm" id="setFontDown" type="button" aria-label="Decrease text size">A−</button><button class="btn secondary sm" id="setFontUp" type="button" aria-label="Increase text size">A+</button></div></div>
</div></div>
</div>
<div class="grid g2">
<div class="card"><div class="card-h"><h2>Notifications</h2></div><div class="card-b">
<div class="setrow"><div class="sl"><b>Toast notifications</b><span>Pop-up feedback for actions. Errors always show.</span></div><label class="switch"><input type="checkbox" id="setToasts" checked><span class="tr" aria-hidden="true"></span><span class="sr">Toast notifications</span></label></div>
<div class="setrow"><div class="sl"><b>Language</b><span>English is active. Advisory templates also ship in Telugu and Hindi.</span></div><button class="btn secondary sm" data-view="help" type="button">Help &amp; accessibility</button></div>
</div></div>
<div class="card"><div class="card-h"><h2>Data on this device</h2></div><div class="card-b">
<p class="muted small" style="margin-bottom:12px">Read/dismissed notification history and preferences. Forecasts, advisories and grievances live on the server.</p>
<button class="btn secondary sm" id="wipePrefs" type="button">Clear local preferences</button>
</div></div>
</div>
</section>
<section id="help" class="view" aria-label="Help">
<div class="pagehead"><div class="eyebrow">Support</div><h2>Help, FAQ &amp; Accessibility</h2><p>Usage guidance and accessibility options for all users.</p></div>
<div class="card"><div class="card-h"><h2>Frequently asked questions</h2></div><div class="card-b"><div class="grid g2"><div><h3 style="margin-bottom:var(--s3);font-size:15px">How do I generate a forecast?</h3><p class="muted" style="margin-bottom:var(--s5)">Select a Panchayat in the Forecast Dashboard and choose <strong>Generate latest forecast</strong>.</p><h3 style="margin-bottom:var(--s3);font-size:15px">What does P10/P50/P90 mean?</h3><p class="muted">They represent lower, median and upper forecast quantiles. They communicate uncertainty and are not guarantees.</p></div><div id="accessibility"><h3 style="margin-bottom:var(--s3);font-size:15px">Accessibility</h3><p class="muted" style="margin-bottom:var(--s4)">Use keyboard navigation, browser zoom and the A&minus;/A+ controls above. Statuses use text and icons, never color alone. Enable dark mode from the header for low-light environments.</p><h3 style="margin-bottom:var(--s3);font-size:15px">Official-use warning</h3><p class="muted">The pilot must be connected to approved data, identity, monitoring and a validated production model before operational use.</p></div></div></div></div>
</section>
</div></main>
<footer class="footer"><div class="wrap"><div><h3>Telangana Panchayat Agromet Portal</h3><div>Smart India Hackathon &bull; SIH26074</div><div class="small" style="margin-top:var(--s2)">Panchayat-level weather downscaling and agrometeorological advisory decision support.</div></div><div><h3>Public information</h3><button class="linklike" data-view="reports" type="button">Reports</button><button class="linklike" data-view="help" type="button">Accessibility / Help</button><button class="linklike" data-placeholder="About this pilot" type="button">About</button></div><div><h3>Legal</h3><button class="linklike" data-placeholder="Privacy notice" type="button">Privacy</button><button class="linklike" data-placeholder="Terms of use" type="button">Terms</button><button class="linklike" data-placeholder="Sitemap" type="button">Sitemap</button></div></div><div class="footer-bot">Pilot environment &bull; Do not use synthetic model metrics as operational performance claims.</div></footer>
<nav class="mnav" aria-label="Mobile navigation"><div class="row"><a data-view="home" href="#home"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg><span>Home</span></a><a data-view="dashboard" href="#dashboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg><span>Dashboard</span></a><a data-view="projects" href="#projects"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg><span>Projects</span></a><a data-view="citizen" href="#citizen"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>Citizen</span></a><a data-view="officer" href="#officer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg><span>Officer</span></a></div></nav>
<div class="toasts" id="toastContainer" aria-live="polite" aria-atomic="false"></div>
<div id="searchPalette" style="display:none"></div>
<div id="modalContainer"></div>
<script>
'use strict';
var state={panchayats:[],forecast:null,summary:null,font:1,theme:'light',route:'home',syncing:false,animatedKPIs:{},availCache:{}};
function $(id){return document.getElementById(id)}
function $all(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function num(v,d){if(v==null||v===''||isNaN(Number(v)))return '—';return Number(v).toFixed(d==null?1:d)}
function pct(v){if(v==null||isNaN(Number(v)))return '—';return Math.round(Number(v)*100)+'%'}
function reduced(){return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches}
function debounce(fn,ms){var t;return function(){var a=arguments,c=this;clearTimeout(t);t=setTimeout(function(){fn.apply(c,a)},ms)}}
var ICON={
ok:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>',
err:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
warn:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
info:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>'};
/* ---------- toast ---------- */
function toast(title,message,type,duration){
  type=type||'info';var box=$('toastContainer');if(!box)return;
  try{if(localStorage.getItem('agromet-toasts')==='0'&&type!=='error')return}catch(e){}
  var el=document.createElement('div');el.className='toast '+type;el.setAttribute('role','status');
  el.innerHTML=(ICON[type==='success'?'ok':type]||ICON.info)+'<div style="flex:1"><b>'+esc(title)+'</b>'+(message?'<div class="tm">'+esc(message)+'</div>':'')+'</div><button type="button" aria-label="Dismiss notification">&times;</button>';
  box.appendChild(el);
  var dead=false;function bye(){if(dead)return;dead=true;el.classList.add('out');setTimeout(function(){el.remove()},180)}
  el.querySelector('button').onclick=bye;
  el.addEventListener('mouseenter',function(){clearTimeout(tm)}); 
  var tm=setTimeout(bye,duration==null?4200:duration);
}
/* ---------- modal with focus trap ---------- */
var lastFocus=null;
function openModal(title,bodyHTML,footHTML){
  lastFocus=document.activeElement;
  var wrap=$('modalContainer');
  var ov=document.createElement('div');ov.className='overlay';
  ov.innerHTML='<div class="modal" role="dialog" aria-modal="true" aria-label="'+esc(title)+'"><div class="modal-h"><h3>'+esc(title)+'</h3><button type="button" class="iconbtn" data-x aria-label="Close dialog">&times;</button></div><div class="modal-b">'+bodyHTML+'</div>'+(footHTML?'<div class="modal-f">'+footHTML+'</div>':'')+'</div>';
  wrap.appendChild(ov);
  var modal=ov.querySelector('.modal');
  function focusables(){return $all('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])',modal).filter(function(e){return !e.disabled})}
  function close(){ov.remove();document.removeEventListener('keydown',onKey,true);if(lastFocus&&lastFocus.focus)lastFocus.focus()}
  function onKey(e){
    if(e.key==='Escape'){e.stopPropagation();close();return}
    if(e.key!=='Tab')return;
    var f=focusables();if(!f.length)return;
    var first=f[0],last=f[f.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  }
  document.addEventListener('keydown',onKey,true);
  ov.addEventListener('mousedown',function(e){if(e.target===ov)close()});
  ov.querySelector('[data-x]').onclick=close;
  var f=focusables();if(f.length)f[0].focus();
  return{close:close,root:ov};
}
/* ---------- api ---------- */
function headers(){
  var k=$('apiKey'),v=k&&k.value?k.value.trim():'';
  var s=null;try{s=JSON.parse(sessionStorage.getItem('agromet-session')||'null')}catch(e){}
  var h=v?{'X-API-Key':v}:{};
  if(s&&s.token)h['Authorization']='Bearer '+s.token;
  return h;
}
function api(path,opt){
  opt=opt||{};
  var init={method:opt.method||'GET',headers:Object.assign({'Content-Type':'application/json'},headers(),opt.headers||{})};
  if(opt.body)init.body=opt.body;
  return fetch(path,init).then(function(r){return r.json().catch(function(){return null}).then(function(d){if(!r.ok)throw new Error((d&&d.detail)||('HTTP '+r.status));return d})});
}
/* ---------- router ---------- */
var VIEWS={home:['Home'],dashboard:['Home','Dashboard'],projects:['Home','Projects'],reports:['Home','Reports'],notices:['Home','Notices'],services:['Home','Services'],citizen:['Home','Citizen Services'],officer:['Home','Officer Workspace'],kvk:['Home','KVK Review'],admin:['Home','Administration'],security:['Home','Security Centre'],grievance:['Home','Grievance'],help:['Home','Help & FAQ'],login:['Sign in'],settings:['Settings'],notifications:['Notifications']};
function setActive(sel,view){$all(sel).forEach(function(b){var on=b.dataset.view===view;b.classList.toggle('active',!!on);if(b.classList.contains('nav-btn')){if(on)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')}})}
function nav(id,opts){
  opts=opts||{};
  if(!VIEWS[id]){toast('Page not available','That link is not part of this pilot.','warning');id='home'}
  var LOCKED={officer:1,kvk:1,admin:1};
  if(LOCKED[id]&&!session()){id='login';if(!opts.silent)toast('Sign in required','Choose a workspace to continue.','warning')}
  state.route=id;
  $all('.view').forEach(function(v){v.classList.toggle('active',v.id===id)});
  setActive('.nav-btn',id);setActive('.mnav a',id);setActive('.slink',id);
  var parts=VIEWS[id];
  $('crumb').innerHTML=parts.map(function(p,i){return i<parts.length-1?'<a href="#home" data-view="home">'+esc(p)+'</a><span class="sep">/</span>':'<span aria-current="page">'+esc(p)+'</span>'}).join('');
  if(location.hash.slice(1)!==id){state.syncing=true;location.hash=id;setTimeout(function(){state.syncing=false},60)}
  if(!opts.silent){
    if(id==='reports')loadScorecard();
    if(id==='officer'){loadSummary();loadAlerts()}
    if(id==='admin')loadAudit();
    if(id==='projects')renderCoverage();
    if(id==='citizen'&&!$('grievanceList').dataset.loaded)loadGrievances();
    if(id==='notifications')renderNotifs();
    if(id==='settings')paintSettings();
  }
  var sec=$(id);if(sec&&!opts.keepScroll)window.scrollTo({top:0,behavior:reduced()?'auto':'smooth'});
}
document.addEventListener('click',function(e){
  var ph=e.target.closest('[data-placeholder]');
  if(ph){e.preventDefault();openModal(ph.dataset.placeholder,'<p class="muted">'+esc(ph.dataset.placeholder)+' is not connected in this pilot. The interface intentionally avoids placeholder government content.</p>','<button type="button" class="btn secondary" data-x2>Close</button>');var b=$('modalContainer').querySelector('[data-x2]');if(b)b.onclick=function(){$('modalContainer').innerHTML=''};return}
  var g=e.target.closest('[data-goto]');
  if(g){e.preventDefault();nav(g.dataset.goto);return}
  var v=e.target.closest('[data-view]');
  if(v){e.preventDefault();if(window.innerWidth<=760)$('navLinks').classList.remove('open');nav(v.dataset.view);return}
});
window.addEventListener('hashchange',function(){if(state.syncing)return;var h=location.hash.slice(1)||'home';if(h!==state.route)nav(h)});
/* ---------- theme + font + lang ---------- */
function paintTheme(){document.documentElement.setAttribute('data-theme',state.theme);try{localStorage.setItem('agromet-theme',state.theme)}catch(e){}var t=$('themeToggle');t.setAttribute('aria-pressed',state.theme==='dark'?'true':'false');t.innerHTML=state.theme==='dark'?'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>':'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'}
function paintFont(){document.documentElement.style.fontSize=(state.font*16)+'px';try{localStorage.setItem('agromet-font',String(state.font))}catch(e){}}
$('themeToggle').onclick=function(){state.theme=state.theme==='light'?'dark':'light';paintTheme();toast('Theme changed','Switched to '+state.theme+' mode.','info',2200)};
$('fontUp').onclick=function(){state.font=Math.min(1.15,state.font+.05);paintFont()};
$('fontDown').onclick=function(){state.font=Math.max(.9,state.font-.05);paintFont()};
$('langBtn').onclick=function(){toast('Language','English is active. Telugu and Hindi advisory templates are available in the advisory engine.','info')};
$('searchBtn').onclick=function(){openSearch()};
$('navToggle').onclick=function(){var l=$('navLinks');var open=l.classList.toggle('open');$('navToggle').setAttribute('aria-expanded',open?'true':'false')};
/* ---------- sidebar ---------- */
function wireSide(toggleId,sideId,key){
  var t=$(toggleId),s=$(sideId);if(!t||!s)return;
  function paint(min){s.classList.toggle('min',min);t.setAttribute('aria-expanded',min?'false':'true');t.querySelector('span').textContent=min?'Expand':'Collapse';$all('.slink',s).forEach(function(a){var lbl=a.querySelector('span');a.title=min&&lbl?lbl.textContent:'';a.setAttribute('aria-label',lbl?lbl.textContent:'Section link')})}
  var min=false;try{min=localStorage.getItem(key)==='1'}catch(e){}
  if(window.innerWidth<=1180)min=true;
  paint(min);
  t.onclick=function(){min=!min;paint(min);try{localStorage.setItem(key,min?'1':'0')}catch(e){}};
}
wireSide('sidebarToggle','officerSidebar','agromet-side-officer');
wireSide('adminSidebarToggle','adminSidebar','agromet-side-admin');
/* ---------- search palette ---------- */
var PAGES=[['Home','Portal overview and pilot information','home'],['Dashboard','Forecast dashboard with five-day outlook','dashboard'],['Projects','Geographic coverage and transparency','projects'],['Reports','Model evaluation and methodology','reports'],['Notices','Official announcements','notices'],['Services','Citizen service entry points','services'],['Citizen Services','Submit and track grievances','citizen'],['Officer Workspace','Monitoring and early warnings','officer'],['KVK Review','Scientist advisory review queue','kvk'],['Administration','Governance and audit events','admin'],['Security Centre','Defensive security monitoring','security'],['Help & FAQ','Accessibility and usage guide','help'],['Sign in','Role-based workspace access','login'],['Settings','Profile, appearance and preferences','settings'],['Notifications','Advisory, forecast and grievance alerts','notifications']];
function hi(text,q){if(!q)return esc(text);var i=text.toLowerCase().indexOf(q.toLowerCase());if(i<0)return esc(text);return esc(text.slice(0,i))+'<mark>'+esc(text.slice(i,i+q.length))+'</mark>'+esc(text.slice(i+q.length))}
function openSearch(){
  var host=$('searchPalette');host.style.display='block';
  host.innerHTML='<div class="search-ov"><div class="search-pal" role="dialog" aria-modal="true" aria-label="Search"><div class="search-bar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input id="q" placeholder="Search pages and panchayats&hellip;" aria-label="Search pages and panchayats" autocomplete="off"><button type="button" class="btn ghost sm" id="qx">Close</button></div><div class="search-res" id="qr" role="listbox" aria-label="Results"></div></div></div>';
  var input=host.querySelector('#q'),res=host.querySelector('#qr');
  function close(){host.style.display='none';host.innerHTML='';$('searchBtn').focus()}
  host.querySelector('#qx').onclick=close;
  host.querySelector('.search-ov').addEventListener('mousedown',function(e){if(e.target.classList.contains('search-ov'))close()});
  function items(q){
    q=(q||'').trim().toLowerCase();
    var out=[];
    PAGES.forEach(function(p){if(!q||p[0].toLowerCase().indexOf(q)>=0||p[1].toLowerCase().indexOf(q)>=0)out.push({kind:'Page',title:p[0],desc:p[1],view:p[2]})});
    state.panchayats.forEach(function(p){var id=String(p.panchayat_id);if(!q||id.toLowerCase().indexOf(q)>=0)out.push({kind:'Panchayat',title:'Panchayat '+id,desc:'Open forecast dashboard for '+id,view:'dashboard',pid:id})});
    return out.slice(0,14);
  }
  function draw(){
    var q=input.value;var list=items(q);
    if(!list.length){res.innerHTML='<div class="empty"><p>No results for &ldquo;'+esc(q)+'&rdquo;.</p></div>';return}
    res.innerHTML=list.map(function(it,i){return '<button type="button" class="search-it'+(i===0?' sel':'')+'" role="option" data-i="'+i+'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><span><span class="t">'+hi(it.title,input.value.trim())+' <span class="small muted">'+esc(it.kind)+'</span></span><br><span class="d">'+esc(it.desc)+'</span></span></button>'}).join('');
    $all('.search-it',res).forEach(function(b){
      b.onclick=function(){var it=list[Number(b.dataset.i)];close();if(it.pid&&$('panchayat'))$('panchayat').value=it.pid;nav(it.view,{keepScroll:!!it.pid});if(it.pid)toast('Panchayat selected',it.pid+' selected in the forecast dashboard.','info',2500)};
    });
  }
  input.addEventListener('input',debounce(draw,120));
  input.addEventListener('keydown',function(e){
    if(e.key==='Escape'){close();return}
    var all=$all('.search-it',res);if(!all.length)return;
    var idx=all.indexOf(res.querySelector('.sel'));
    if(e.key==='Enter'){(all[Math.max(0,idx)]||all[0]).click();return}
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(idx>=0)all[idx].classList.remove('sel');idx=e.key==='ArrowDown'?Math.min(all.length-1,idx+1):Math.max(0,idx-1);all[idx].classList.add('sel');all[idx].scrollIntoView({block:'nearest'})}
  });
  input.focus();draw();
}
/* ---------- status ---------- */
function setStatus(t,kind){var s=$('status');if(!s)return;s.className='status '+(kind||'info');s.setAttribute('role','status');s.innerHTML=(kind==='ok'?ICON.ok:kind==='error'?ICON.err:kind==='warn'?ICON.warn:ICON.info)+'<span>'+esc(t)+'</span>'}
/* ---------- animated numbers (once, reduced-motion aware) ---------- */
function countUp(el,target,key){
  if(!el)return;
  if(reduced()){el.textContent=Number(target).toLocaleString('en-IN');return}
  if(state.animatedKPIs[key]===target){el.textContent=Number(target).toLocaleString('en-IN');return}
  state.animatedKPIs[key]=target;
  var t0=performance.now(),dur=750;
  function fr(now){var p=Math.min(1,(now-t0)/dur);var e=1-Math.pow(1-p,3);el.textContent=Math.round(target*e).toLocaleString('en-IN');if(p<1)requestAnimationFrame(fr)}
  requestAnimationFrame(fr);
}
/* ---------- summary ---------- */
function skelKPIs(){return '<div class="card kpi"><div class="label">Loading</div><div class="skel" style="height:30px;margin-top:8px"></div></div>'.repeat(4)}
function loadSummary(){
  return api('/api/v1/portal/summary').then(function(s){
    state.summary=s;
    countUp($('kpiPanchayats'),s.total_panchayats,'tp');
    countUp($('kpiForecasts'),s.forecasts_available,'fa');
    countUp($('kpiPending'),s.pending_advisories,'pa');
    $('kpiHealth').textContent=s.health||'—';
    $('kpiModelHint').textContent='Model: '+(s.model_version||'—');
    if($('heroStatP'))$('heroStatP').textContent=s.total_panchayats+' panchayats connected';
    if($('heroStatM'))$('heroStatM').textContent='Model: '+(s.model_version||'—');
    if($('heroStatF'))$('heroStatF').textContent=s.forecasts_available+' stored forecasts';
    $('offPanch').textContent=s.total_panchayats;
    $('offForecasts').textContent=s.forecasts_available;
    $('offPending').textContent=s.pending_advisories;
    $('offHealth').textContent=s.health||'—';
    $('summaryError').innerHTML='';
  }).catch(function(e){
    $('summaryError').innerHTML='<div class="status error">'+ICON.err+'<span>Summary failed to load: '+esc(e.message)+'. <button type="button" class="btn secondary sm" id="sumRetry">Try again</button></span></div>';
    var b=$('sumRetry');if(b)b.onclick=loadSummary;
  });
}
/* ---------- registry + coverage ---------- */
function loadRegistry(){
  setStatus('Loading Panchayat registry…','info');
  return api('/api/v1/panchayats').then(function(list){
    state.panchayats=list||[];
    $('panchayat').innerHTML=state.panchayats.map(function(p){return '<option value="'+esc(p.panchayat_id)+'">'+esc(p.panchayat_id)+'</option>'}).join('');
    setStatus('Panchayat registry loaded ('+state.panchayats.length+'). Generate the latest forecast.','ok');
    renderCoverage();
  }).catch(function(e){setStatus('Unable to load registry: '+e.message+'. ','error');var s=$('status');var b=document.createElement('button');b.type='button';b.className='btn secondary sm';b.textContent='Try again';b.style.marginLeft='8px';b.onclick=loadRegistry;s.appendChild(b)});
}
function availBadge(pid){
  if(state.availCache[pid])return state.availCache[pid];
  return '<span class="badge grey"><span class="dot"></span>Checking…</span>';
}
function refreshAvail(){
  var ids=state.panchayats.map(function(p){return p.panchayat_id});
  Promise.allSettled(ids.map(function(id){return api('/api/v1/forecast/panchayat/'+encodeURIComponent(id))})).then(function(rs){
    rs.forEach(function(r,i){state.availCache[ids[i]]=r.status==='fulfilled'?'<span class="badge green"><span class="dot"></span>Forecast available</span>':'<span class="badge blue"><span class="dot"></span>Configured</span>';state.avail=state.avail||{};state.avail[ids[i]]=r.status==='fulfilled'});
    renderCoverage(true);
  });
}
var coverageLoaded=false;
function renderCoverage(keep){
  var el=$('coverageTable');if(!el)return;
  var q=($('coverageSearch')&&$('coverageSearch').value||'').trim().toLowerCase();
  if(!state.panchayats.length){el.innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>No Panchayat registry</h3><p>No Panchayat registry is configured on the backend.</p></div>';return}
  var rows=state.panchayats.filter(function(p){return !q||String(p.panchayat_id).toLowerCase().indexOf(q)>=0});
  var sk=state.covSort&&state.covSort.key;
  if(sk){var dir=state.covSort.dir||1;rows=rows.slice().sort(function(a,b){var x=a[sk],y=b[sk];if(x==null)x='';if(y==null)y='';return (x>y?1:x<y?-1:0)*dir})}
  var PS=5,pages=Math.max(1,Math.ceil(rows.length/PS));state.covPage=Math.min(state.covPage||1,pages);
  var rp=rows.slice((state.covPage-1)*PS,state.covPage*PS);
  if(!rows.length){el.innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>No matches</h3><p>No panchayats match &ldquo;'+esc(q)+'&rdquo;.</p><button type="button" class="btn secondary" id="clearCov">Clear filter</button></div>';$('clearCov').onclick=function(){$('coverageSearch').value='';renderCoverage()};return}
  el.innerHTML='<div class="table-wrap"><table class="table"><caption>'+rows.length+' of '+state.panchayats.length+' panchayats</caption><thead><tr>'+covHead()+'</tr></thead><tbody>'+rp.map(function(p){return '<tr><td><strong>'+esc(p.panchayat_id)+'</strong></td><td>'+num(p.latitude,4)+'</td><td>'+num(p.longitude,4)+'</td><td>'+num(p.elevation_m,0)+' m</td><td>'+availBadge(p.panchayat_id)+'</td><td><button type="button" class="btn secondary sm" data-openfc="'+esc(p.panchayat_id)+'">Open</button></td></tr>'}).join('')+'</tbody></table></div>';
  $all('[data-openfc]',el).forEach(function(b){b.onclick=function(){if($('panchayat'))$('panchayat').value=b.dataset.openfc;nav('dashboard',{keepScroll:true});storedForecast()}});
  $all('th.sortable',el).forEach(function(th){function go(){var k=th.dataset.sk;if(state.covSort&&state.covSort.key===k){state.covSort.dir*=-1}else{state.covSort={key:k,dir:1}}renderCoverage(true)}th.onclick=go;th.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}}});
  {var pg=document.createElement('div');pg.innerHTML=pagerHTML(state.covPage,pages,rp.length,rows.length);el.appendChild(pg.firstChild);wirePager(el,function(d){state.covPage+=d;renderCoverage(true)})}
  renderMap();
  if(!keep&&!coverageLoaded){coverageLoaded=true;refreshAvail()}
}
/* ---------- forecast + SVG charts ---------- */
function svgTemp(f){
  var W=560,H=220,pl=34,pr=10,pt=12,pb=24;
  var all=[];f.days.forEach(function(d){all.push(d.tmax_c.p10,d.tmax_c.p90)});
  var lo=Math.min.apply(null,all),hi=Math.max.apply(null,all);if(hi-lo<2){hi+=1;lo-=1}
  function X(i){return pl+(W-pl-pr)*(i/(f.days.length-1||1))}
  function Y(v){return pt+(H-pt-pb)*(1-(v-lo)/(hi-lo))}
  var band='',line='';
  f.days.forEach(function(d,i){band+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(d.tmax_c.p90).toFixed(1)+' '});
  for(var i=f.days.length-1;i>=0;i--){var d=f.days[i];band+='L'+X(i).toFixed(1)+' '+Y(d.tmax_c.p10).toFixed(1)+' '}
  band+='Z';
  f.days.forEach(function(d,i){line+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(d.tmax_c.p50).toFixed(1)+' '});
  var dots=f.days.map(function(d,i){return '<circle class="pdot" cx="'+X(i).toFixed(1)+'" cy="'+Y(d.tmax_c.p50).toFixed(1)+'" r="4"><title>'+esc(d.valid_date)+' P50 '+num(d.tmax_c.p50)+' °C (P10 '+num(d.tmax_c.p10)+', P90 '+num(d.tmax_c.p90)+')</title></circle>'}).join('');
  var xl=f.days.map(function(d,i){return '<text class="axis" x="'+X(i).toFixed(1)+'" y="'+(H-8)+'" text-anchor="middle">'+esc(String(d.valid_date).slice(5))+'</text>'}).join('');
  var grid=[0.25,0.5,0.75].map(function(fr){var y=pt+(H-pt-pb)*fr;return '<line class="gridln" x1="'+pl+'" y1="'+y+'" x2="'+(W-pr)+'" y2="'+y+'"/>'}).join('');
  return '<svg viewBox="0 0 '+W+' '+H+'" role="presentation"><text class="axis" x="4" y="'+(pt+8)+'">'+num(hi,0)+'°</text><text class="axis" x="4" y="'+(H-pb)+'">'+num(lo,0)+'°</text>'+grid+'<path class="band" d="'+band+'"/><path class="pline" d="'+line+'"/>'+dots+xl+'</svg><div class="legend small muted" style="display:flex;gap:14px;margin-top:8px"><span><span style="display:inline-block;width:22px;height:8px;background:rgba(194,65,12,.25);border-radius:2px;vertical-align:middle"></span> P10–P90 band</span><span><span style="display:inline-block;width:22px;height:3px;background:var(--blue);vertical-align:middle"></span> P50 median</span></div>';
}
function svgRain(f){
  var W=560,H=220,pl=34,pr=10,pt=12,pb=44;
  var mx=Math.max.apply(null,f.days.map(function(d){return d.rain_mm}).concat([1]));
  var bw=(W-pl-pr)/f.days.length;
  var bars=f.days.map(function(d,i){
    var h=(H-pt-pb)*(d.rain_mm/mx);var x=pl+bw*i+bw*0.2;var y=H-pb-h;var w=bw*0.6;
    var hp=d.rainfall_probabilities&&d.rainfall_probabilities.heavy!=null?Math.round(d.rainfall_probabilities.heavy*100):null;
    return '<rect class="rbar" x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" width="'+w.toFixed(1)+'" height="'+Math.max(3,h).toFixed(1)+'"><title>'+esc(d.valid_date)+': '+num(d.rain_mm)+' mm'+(hp==null?'':' — heavy-rain probability '+hp+'%')+'</title></rect><text class="axis" x="'+(x+w/2).toFixed(1)+'" y="'+(y-5).toFixed(1)+'" text-anchor="middle">'+num(d.rain_mm,0)+'</text>'+(hp==null?'':'<text class="axis" x="'+(x+w/2).toFixed(1)+'" y="'+(H-pb+14).toFixed(1)+'" text-anchor="middle">'+hp+'%</text>')+'<text class="axis" x="'+(x+w/2).toFixed(1)+'" y="'+(H-8)+'" text-anchor="middle">'+esc(String(d.valid_date).slice(5))+'</text>';
  }).join('');
  return '<svg viewBox="0 0 '+W+' '+H+'" role="presentation">'+bars+'</svg><div class="small muted" style="margin-top:8px">Bar labels show expected millimetres; percentages show heavy-threshold probability.</div>';
}
function renderForecast(f){
  state.forecast=f;
  $('kpiPanchayat').textContent=f.panchayat_id;
  $('kpiModel').textContent=f.model_version;
  $('kpiEt0').textContent=f.days[0]&&f.days[0].et0_mm_day!=null?num(f.days[0].et0_mm_day)+' mm/day':'—';
  $('tempChart').innerHTML=svgTemp(f);
  $('rainChart').innerHTML=svgRain(f);
  $('forecastTable').innerHTML='<div class="table-wrap"><table class="table"><caption>Five-day quantile forecast for '+esc(f.panchayat_id)+' · model '+esc(f.model_version)+'</caption><thead><tr><th scope="col">Date</th><th scope="col">Tmax P10/P50/P90</th><th scope="col">Tmin P10/P50/P90</th><th scope="col">RH P50</th><th scope="col">Wind P50</th><th scope="col">Rain</th><th scope="col">Heavy prob.</th><th scope="col">ET₀</th></tr></thead><tbody>'+f.days.map(function(d,i){var probs=Object.keys(d.rainfall_probabilities||{}).map(function(k){return esc(k)+': '+pct(d.rainfall_probabilities[k])}).join(' · ')||'—';return '<tr><td><button type="button" class="expbtn" data-exp="'+i+'" aria-expanded="false" aria-label="Show full quantiles for '+esc(d.valid_date)+'">+</button> <strong>'+esc(d.valid_date)+'</strong></td><td>'+num(d.tmax_c.p10)+' / '+num(d.tmax_c.p50)+' / '+num(d.tmax_c.p90)+' °C</td><td>'+num(d.tmin_c.p10)+' / '+num(d.tmin_c.p50)+' / '+num(d.tmin_c.p90)+' °C</td><td>'+num(d.relative_humidity_pct.p50,0)+'%</td><td>'+num(d.wind_speed_kmh.p50)+' km/h</td><td>'+num(d.rain_mm)+' mm</td><td>'+pct(d.rainfall_probabilities.heavy)+'</td><td>'+(d.et0_mm_day==null?'—':num(d.et0_mm_day)+' mm')+'</td></tr><tr class="detail" id="fcDetail'+i+'"><td colspan="8"><strong>Full quantiles — '+esc(d.valid_date)+':</strong> RH '+num(d.relative_humidity_pct.p10,0)+' / '+num(d.relative_humidity_pct.p50,0)+' / '+num(d.relative_humidity_pct.p90,0)+'% · Wind '+num(d.wind_speed_kmh.p10)+' / '+num(d.wind_speed_kmh.p50)+' / '+num(d.wind_speed_kmh.p90)+' km/h · Rain probabilities: '+probs+'</td></tr>'}).join('')+'</tbody></table></div>';
  wireForecastExpand();
  loadSummary();updateNotifBadge();
}
function withBtn(btn,fn){
  var label=btn.innerHTML;btn.disabled=true;btn.innerHTML='<span class="spin" aria-hidden="true"></span> Working…';
  return fn().finally(function(){btn.disabled=false;btn.innerHTML=label});
}
function refreshForecast(){
  var id=$('panchayat').value;if(!id){setStatus('Select a Panchayat first.','warn');return}
  setStatus('Fetching upstream forecast and constructing terrain-aware prediction…','warn');
  withBtn($('refreshBtn'),function(){return api('/api/v1/forecast/panchayat/'+encodeURIComponent(id)+'/refresh',{method:'POST'})}).then(function(f){renderForecast(f);setStatus('Forecast generated and persisted successfully.','ok');toast('Forecast generated','Latest forecast for '+id+' is ready.','success');loadAlerts()}).catch(function(e){setStatus('Forecast generation failed: '+e.message,'error');toast('Generation failed',e.message,'error')});
}
function storedForecast(){
  var id=$('panchayat').value;if(!id){setStatus('Select a Panchayat first.','warn');return}
  setStatus('Loading stored forecast…','info');
  withBtn($('viewBtn'),function(){return api('/api/v1/forecast/panchayat/'+encodeURIComponent(id))}).then(function(f){renderForecast(f);setStatus('Stored forecast loaded.','ok')}).catch(function(){setStatus('No stored forecast. Generate a latest forecast first.','error')});
}
$('refreshBtn').onclick=refreshForecast;$('viewBtn').onclick=storedForecast;
/* ---------- early warnings (real data only) ---------- */
function sevOf(a){
  if(a.kind==='rice_blast')return['high','High'];
  if(a.kind==='urea_topdressing')return['medium','Medium'];
  if(a.kind==='spraying_window')return['low','Low'];
  return['info','Info'];
}
function loadAlerts(){
  var el=$('alerts');if(!el)return;
  function derived(){
    var out=[];
    if(state.forecast){state.forecast.days.forEach(function(d){
      var hp=d.rainfall_probabilities?d.rainfall_probabilities.heavy:0;
      if(hp>=0.8)out.push({sev:'critical',label:'Critical',title:'Heavy rainfall likely — '+d.valid_date,text:'Heavy-threshold probability '+Math.round(hp*100)+'% for '+state.forecast.panchayat_id+'.',src:'Derived on-device from the loaded forecast'});
      else if(hp>=0.6)out.push({sev:'high',label:'High',title:'Heavy rainfall possible — '+d.valid_date,text:'Heavy-threshold probability '+Math.round(hp*100)+'% for '+state.forecast.panchayat_id+'.',src:'Derived on-device from the loaded forecast'});
      if(d.tmax_c.p50>=42)out.push({sev:'high',label:'High',title:'Extreme heat — '+d.valid_date,text:'Median maximum '+num(d.tmax_c.p50)+' °C for '+state.forecast.panchayat_id+'.',src:'Derived on-device from the loaded forecast'});
    })}
    return out.slice(0,6);
  }
  return api('/api/v1/advisories/kvk-pending').then(function(list){
    var items=(list||[]).map(function(a){var s=sevOf(a);return{sev:s[0],label:s[1],title:String(a.message_key).replace(/_/g,' '),text:'Panchayat '+a.panchayat_id+' · '+a.valid_from+' → '+a.valid_to,src:'Stored advisory · status '+a.status,view:'kvk'}});
    var d=derived();var all=items.concat(d);
    if(!all.length){el.innerHTML='<div class="status ok">'+ICON.ok+'<span>No active warnings. Stored advisories and derived forecast checks are both clear.</span></div>';return}
    var order={critical:0,high:1,medium:2,low:3,info:4};
    all.sort(function(a,b){return order[a.sev]-order[b.sev]});
    el.innerHTML=all.map(function(a){return '<div class="alert"><div class="sev '+a.sev+'" aria-hidden="true"></div><div class="at"><div class="ah"><span class="badge '+(a.sev==='critical'?'red pulse':a.sev==='high'?'red':a.sev==='medium'?'amber':a.sev==='low'?'blue':'green')+'"><span class="dot"></span>'+esc(a.label)+'</span>'+esc(a.title)+'</div><div class="am">'+esc(a.text)+'<br>'+esc(a.src)+'</div></div>'+(a.view?'<button type="button" class="btn secondary sm" data-view="'+a.view+'">Review</button>':'')+'</div>'}).join('');
  }).catch(function(e){
    var d=derived();
    if(/401|HTTP 401/.test(e.message)){el.innerHTML=(d.length?d.map(function(a){return '<div class="alert"><div class="sev '+a.sev+'"></div><div class="at"><div class="ah"><span class="badge '+(a.sev==='critical'?'red pulse':'amber')+'"><span class="dot"></span>'+esc(a.label)+'</span>'+esc(a.title)+'</div><div class="am">'+esc(a.text)+'<br>'+esc(a.src)+'</div></div></div>'}).join(''):'')+'<div class="status warn">'+ICON.warn+'<span>Stored advisory queue needs an API key (enter it in KVK Review). Forecast-derived checks are shown above when available.</span></div>';return}
    el.innerHTML='<div class="status error">'+ICON.err+'<span>Alerts failed to load: '+esc(e.message)+'. <button type="button" class="btn secondary sm" id="alRetry">Try again</button></span></div>';
    var b=$('alRetry');if(b)b.onclick=loadAlerts;
  });
}
$('reloadAlerts').onclick=loadAlerts;
/* ---------- scorecard ---------- */
var scoreLoaded=false;
function loadScorecard(){
  if(scoreLoaded)return;scoreLoaded=true;
  $('reportScore').innerHTML='<div class="skel" style="height:18px;margin-bottom:10px"></div><div class="skel" style="height:120px"></div>';
  api('/api/v1/scorecard').then(function(d){
    if(!d.models||!d.models.length){scoreLoaded=false;$('reportScore').innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>No scorecard supplied</h3><p>No persisted production scorecard has been supplied yet. Run the evaluation pipeline to populate this section.</p><button type="button" class="btn secondary" id="scRetry">Try again</button></div>';$('scRetry').onclick=function(){scoreLoaded=false;loadScorecard()};return}
    $('reportScore').innerHTML=d.models.map(function(m){var keys=Object.keys(m||{});return '<div class="kv"><div class="kh"><b>'+esc(m.model||m.name||'Model')+'</b><span class="badge blue">Evaluation record</span></div><dl>'+keys.filter(function(k){return k!=='model'&&k!=='name'}).slice(0,8).map(function(k){var v=m[k];return '<div><dt>'+esc(k)+'</dt><dd>'+esc(typeof v==='object'?JSON.stringify(v):String(v)).slice(0,120)+'</dd></div>'}).join('')+'</dl><details><summary class="small">Full record (JSON)</summary><pre class="mono" style="white-space:pre-wrap">'+esc(JSON.stringify(m,null,1))+'</pre></details></div>'}).join('');
  }).catch(function(e){scoreLoaded=false;$('reportScore').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(e.message)+'. <button type="button" class="btn secondary sm" id="scRetry">Try again</button></span></div>';$('scRetry').onclick=loadScorecard});
}
/* ---------- KVK review (modal notes, no prompt()) ---------- */
function metricDL(m){
  var ks=Object.keys(m||{});if(!ks.length)return '<p class="small muted">No trigger metrics.</p>';
  return '<dl>'+ks.map(function(k){var v=m[k];return '<div><dt>'+esc(k)+'</dt><dd>'+esc(typeof v==='number'?(Math.abs(v)<1?Math.round(v*100)+'%':num(v,2)):String(v))+'</dd></div>'}).join('')+'</dl>';
}
function loadPending(){
  var btn=$('loadPending');
  withBtn(btn,function(){return api('/api/v1/advisories/kvk-pending')}).then(function(list){
    state.pendingCache=list||[];updateNotifBadge();
    if(!list.length){$('pendingList').innerHTML='<div class="status ok">'+ICON.ok+'<span>No advisories are awaiting KVK review.</span></div>';return}
    $('pendingList').innerHTML=list.map(function(a){var s=sevOf(a);return '<div class="kv" data-adv="'+esc(a.advisory_id)+'"><div class="kh"><b>'+esc(String(a.message_key).replace(/_/g,' '))+'</b><span class="badge '+(s[0]==='high'?'red':s[0]==='medium'?'amber':s[0]==='low'?'blue':'green')+'"><span class="dot"></span>'+esc(s[1])+'</span><span class="badge grey">'+esc(a.status)+'</span></div><div class="small muted">Panchayat '+esc(a.panchayat_id)+' · '+esc(a.valid_from)+' → '+esc(a.valid_to)+' · rule '+esc(a.rule)+'</div>'+metricDL(a.trigger_metrics)+factorBars(a.trigger_metrics)+'<div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" class="btn success sm" data-act="approve">Approve</button><button type="button" class="btn danger sm" data-act="reject">Reject</button></div></div>'}).join('');
  }).catch(function(e){$('pendingList').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(e.message)+'. If API-key protection is enabled, enter the key above and retry.</span></div>'});
}
$('pendingList').addEventListener('click',function(e){
  var b=e.target.closest('[data-act]');if(!b)return;
  var card=e.target.closest('[data-adv]');var id=card.dataset.adv;var action=b.dataset.act;
  var m=openModal((action==='approve'?'Approve':'Reject')+' advisory','<p class="muted" style="margin-bottom:12px">'+esc(id)+'</p><div class="field"><label for="revNotes">Reviewer notes (optional)</label><textarea id="revNotes" maxlength="2000" placeholder="Reviewed in pilot portal."></textarea><div class="charcount"><span id="revCount">0</span> / 2000</div></div>','<button type="button" class="btn secondary" data-c>Cancel</button><button type="button" class="btn '+(action==='approve'?'success':'danger')+'" data-ok>'+(action==='approve'?'Approve':'Reject')+'</button>');
  var ta=m.root.querySelector('#revNotes');ta.focus();
  ta.addEventListener('input',function(){m.root.querySelector('#revCount').textContent=ta.value.length});
  m.root.querySelector('[data-c]').onclick=m.close;
  m.root.querySelector('[data-ok]').onclick=function(){
    var okBtn=m.root.querySelector('[data-ok]');okBtn.disabled=true;okBtn.innerHTML='<span class="spin"></span> Saving…';
    api('/api/v1/advisories/approve',{method:'POST',body:JSON.stringify({advisory_id:id,action:action,reviewer_id:($('reviewer').value||'').trim()||'kvk-scientist-1',reviewer_notes:ta.value||null})}).then(function(){m.close();toast('Review recorded','Advisory '+action+'d successfully.','success');loadPending();loadSummary();loadAlerts()}).catch(function(err){okBtn.disabled=false;okBtn.textContent=action==='approve'?'Approve':'Reject';toast('Review failed',err.message,'error')});
  };
});
$('loadPending').onclick=loadPending;
/* ---------- audit ---------- */
function loadAudit(){
  var btn=$('loadAudit');
  withBtn(btn,function(){return api('/api/v1/portal/audit-events')}).then(function(d){
    $('auditCount').textContent=d.length;
    state.auditCache=d||[];state.auditPage=1;renderAuditPage();
  }).catch(function(e){$('auditList').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(e.message)+'. Enter the configured API key in the KVK section, then retry.</span></div>'});
}
$('loadAudit').onclick=loadAudit;
/* ---------- grievances: list + validated form ---------- */
function loadGrievances(){
  return api('/api/v1/grievances').then(function(d){
    state.grievCache=d||[];state.grievPage=1;renderGrievPage();updateNotifBadge();
  }).catch(function(e){$('grievanceList').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(e.message)+'</span></div>'});
}
$('loadGrievances').onclick=loadGrievances;
function setField(name,ok,msg){
  var f=document.querySelector('.field[data-field="'+name+'"]');if(!f)return;
  var m=f.querySelector('.msg');f.classList.toggle('bad',!ok);f.classList.toggle('good',ok&&msg==='valid');
  if(!msg||msg==='valid'){m.hidden=true;m.textContent='';m.className='msg';return}
  m.hidden=false;m.className='msg';m.innerHTML='<span class="'+(ok?'okm':'err')+'">'+esc(msg)+'</span>';
}
function validGrievance(show){
  var v={name:$('gName').value.trim(),mobile:$('gMobile').value.replace(/[\s\-+]/g,''),category:$('gCategory').value,subject:$('gSubject').value.trim(),description:$('gDesc').value.trim()};
  var errs=[];
  function chk(name,ok,msg){if(show)setField(name,ok,ok?'valid':msg);if(!ok)errs.push(msg);return ok}
  chk('name',v.name.length>=2,'Name must be at least 2 characters.');
  chk('mobile',/^[0-9]{10,13}$/.test(v.mobile),'Mobile must be 10–13 digits.');
  chk('category',v.category.length>=2,'Choose a category.');
  chk('subject',v.subject.length>=3,'Subject must be at least 3 characters.');
  chk('description',v.description.length>=10,'Description must be at least 10 characters.');
  var box=$('grievanceErrors');
  if(errs.length&&show){box.style.display='flex';box.innerHTML=ICON.err+'<span><strong>Please fix '+errs.length+' field'+(errs.length>1?'s':'')+':</strong> '+esc(errs[0])+'</span>'}
  else{box.style.display='none';box.innerHTML=''}
  return errs;
}
['gName','gMobile','gCategory','gSubject','gDesc'].forEach(function(id){$(id).addEventListener('input',debounce(function(){validGrievance(false);$('gDescCount').textContent=$('gDesc').value.length},200))});
$('grievanceForm').addEventListener('submit',function(e){
  e.preventDefault();
  var errs=validGrievance(true);
  if(errs.length){var bad=document.querySelector('.field.bad input,.field.bad select,.field.bad textarea');if(bad)bad.focus();return}
  var data={name:$('gName').value.trim(),mobile:$('gMobile').value.trim(),category:$('gCategory').value,subject:$('gSubject').value.trim(),description:$('gDesc').value.trim()};
  var btn=$('grievanceSubmit');
  withBtn(btn,function(){return api('/api/v1/grievances',{method:'POST',body:JSON.stringify(data)})}).then(function(r){
    $('grievanceResult').innerHTML='<div class="status ok">'+ICON.ok+'<span>Grievance submitted. Tracking ID: <strong class="mono">'+esc(r.grievance_id)+'</strong> <button type="button" class="btn secondary sm" id="copyGrv">Copy ID</button></span></div>';
    $('copyGrv').onclick=function(){if(navigator.clipboard)navigator.clipboard.writeText(r.grievance_id);toast('Copied','Tracking ID copied to clipboard.','info',2200)};
    $('grievanceForm').reset();$('gDescCount').textContent='0';
    $all('.field[data-field] .msg').forEach(function(m){m.hidden=true});
    $all('.field[data-field]').forEach(function(f){f.classList.remove('bad','good')});
    loadGrievances();toast('Grievance submitted','Tracking ID: '+r.grievance_id,'success');
  }).catch(function(err){$('grievanceResult').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(err.message)+'</span></div>';toast('Submission failed',err.message,'error')});
});
/* ---------- report tabs ---------- */
$all('.tab-btn').forEach(function(t){t.onclick=function(){
  $all('.tab-btn').forEach(function(x){x.classList.remove('active');x.setAttribute('aria-selected','false')});
  t.classList.add('active');t.setAttribute('aria-selected','true');
  ['score','method','limitations'].forEach(function(k){$('report'+k[0].toUpperCase()+k.slice(1)).style.display=t.dataset.tab===k?'block':'none'});
  if(t.dataset.tab==='score')loadScorecard();
}});
/* ---------- coverage filter ---------- */
$('coverageSearch').addEventListener('input',debounce(function(){renderCoverage(true)},150));
/* ---------- tables: sort / pager / expand ---------- */
function covHead(){
  function th(label,key){var on=state.covSort&&state.covSort.key===key;var arr=on?(state.covSort.dir===1?'▲':'▼'):'';return '<th scope="col" class="sortable" data-sk="'+key+'" tabindex="0" title="Sort by '+label+'" aria-sort="'+(on?(state.covSort.dir===1?'ascending':'descending'):'none')+'">'+label+'<span class="arr" aria-hidden="true">'+arr+'</span></th>'}
  return th('Panchayat','panchayat_id')+th('Latitude','latitude')+th('Longitude','longitude')+th('Elevation','elevation_m')+'<th scope="col">Forecast status</th><th scope="col">Action</th>';
}
function pagerHTML(page,pages,shown,total){
  return '<div class="pager"><span>Page '+page+' of '+pages+' · '+shown+' of '+total+' records</span><button type="button" class="btn secondary sm" data-pg="-1"'+(page<=1||pages<=1?' disabled':'')+'>‹ Prev</button><button type="button" class="btn secondary sm" data-pg="1"'+(page>=pages||pages<=1?' disabled':'')+'>Next ›</button></div>';
}
function wirePager(el,go){$all('[data-pg]',el).forEach(function(b){b.onclick=function(){go(Number(b.dataset.pg))}})}
function wireForecastExpand(){
  var t=$('forecastTable');if(!t||t.dataset.wired)return;t.dataset.wired='1';
  t.addEventListener('click',function(e){var b=e.target.closest('[data-exp]');if(!b)return;var row=$('fcDetail'+b.dataset.exp);if(!row)return;var open=row.classList.toggle('open');b.setAttribute('aria-expanded',open?'true':'false');b.textContent=open?'–':'+';b.setAttribute('aria-label',(open?'Hide':'Show')+' full quantiles for '+row.id)});
}
function renderGrievPage(){
  var el=$('grievanceList');if(!el)return;el.dataset.loaded='1';
  var d=state.grievCache||[];
  if(!d.length){el.innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>No submitted grievances</h3><p>Submit the form to receive a tracking ID.</p></div>';return}
  var PS=5,pages=Math.max(1,Math.ceil(d.length/PS));state.grievPage=Math.min(state.grievPage||1,pages);
  var slice=d.slice((state.grievPage-1)*PS,state.grievPage*PS);
  el.innerHTML='<div class="table-wrap"><table class="table"><caption>'+d.length+' submitted grievances</caption><thead><tr><th scope="col">Tracking ID</th><th scope="col">Category</th><th scope="col">Subject</th><th scope="col">Status</th><th scope="col">Created</th></tr></thead><tbody>'+slice.map(function(x){return '<tr><td><strong class="mono">'+esc(x.grievance_id)+'</strong></td><td>'+esc(x.category)+'</td><td>'+esc(x.subject)+'</td><td><span class="badge blue"><span class="dot"></span>'+esc(x.status)+'</span></td><td class="small">'+esc(x.created_at)+'</td></tr>'}).join('')+'</tbody></table></div>'+pagerHTML(state.grievPage,pages,slice.length,d.length);
  wirePager(el,function(pg){state.grievPage+=pg;renderGrievPage()});
}
function renderAuditPage(){
  var el=$('auditList');if(!el)return;
  var d=state.auditCache||[];
  if(!d.length){el.innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>No audit events</h3><p>No review decisions have been recorded yet.</p></div>';return}
  var PS=6,pages=Math.max(1,Math.ceil(d.length/PS));state.auditPage=Math.min(state.auditPage||1,pages);
  var slice=d.slice((state.auditPage-1)*PS,state.auditPage*PS);
  el.innerHTML='<div class="table-wrap"><table class="table"><caption>'+d.length+' audit events (newest first)</caption><thead><tr><th scope="col">Time</th><th scope="col">Reviewer</th><th scope="col">Action</th><th scope="col">Advisory</th><th scope="col">Notes</th></tr></thead><tbody>'+slice.map(function(x){return '<tr><td class="small">'+esc(x.created_at)+'</td><td>'+esc(x.reviewer_id)+'</td><td><span class="badge '+(x.action==='approve'?'green':x.action==='reject'?'red':'amber')+'">'+esc(x.action)+'</span></td><td class="mono">'+esc(x.advisory_id)+'</td><td>'+esc(x.notes||'—')+'</td></tr>'}).join('')+'</tbody></table></div>'+pagerHTML(state.auditPage,pages,slice.length,d.length);
  wirePager(el,function(pg){state.auditPage+=pg;renderAuditPage()});
}
/* ---------- risk-factor explainability (real rule metrics) ---------- */
function factorBars(m){
  var ks=Object.keys(m||{}).filter(function(k){return typeof m[k]==='number'&&m[k]>=0&&m[k]<=1});
  if(!ks.length)return '';
  return '<div style="margin:10px 0 4px"><div class="small" style="font-weight:700;margin-bottom:6px">Why this triggered — probability factors</div>'+ks.map(function(k){var v=Math.round(m[k]*100);return '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px"><span class="small" style="width:230px;flex-shrink:0">'+esc(k.replace(/_/g,' '))+'</span><div class="metricbar"><span style="width:'+v+'%"></span></div><strong class="small" style="width:42px;text-align:right">'+v+'%</strong></div>'}).join('')+'<p class="small muted">Rule-derived from live advisory data — an analytical cue for the reviewer, not a government decision.</p></div>';
}
/* ---------- notifications (real sources only) ---------- */
function lsGet(k){try{return JSON.parse(localStorage.getItem(k)||'[]')}catch(e){return[]}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
function derivedWarnings(){
  var out=[];
  if(state.forecast){state.forecast.days.forEach(function(d){
    var hp=d.rainfall_probabilities?d.rainfall_probabilities.heavy:0;
    if(hp>=0.8)out.push({sev:'critical',label:'Critical',title:'Heavy rainfall likely — '+d.valid_date,text:'Heavy-threshold probability '+Math.round(hp*100)+'% for '+state.forecast.panchayat_id+'.'});
    else if(hp>=0.6)out.push({sev:'high',label:'High',title:'Heavy rainfall possible — '+d.valid_date,text:'Heavy-threshold probability '+Math.round(hp*100)+'% for '+state.forecast.panchayat_id+'.'});
    if(d.tmax_c.p50>=42)out.push({sev:'high',label:'High',title:'Extreme heat — '+d.valid_date,text:'Median maximum '+num(d.tmax_c.p50)+' °C for '+state.forecast.panchayat_id+'.'});
  })}
  return out.slice(0,6);
}
function notifItems(){
  var out=[];
  (state.pendingCache||[]).forEach(function(a){var s=sevOf(a);out.push({id:'adv:'+a.advisory_id,sev:s[0],label:s[1],title:String(a.message_key).replace(/_/g,' '),text:'Panchayat '+a.panchayat_id+' · '+a.valid_from+' → '+a.valid_to+' · '+a.status,sub:'KVK review queue · stored advisory',time:null,view:'kvk'})});
  derivedWarnings().forEach(function(w,i){out.push({id:'drv:'+(state.forecast?state.forecast.panchayat_id:'-')+':'+w.title,sev:w.sev,label:w.label,title:w.title,text:w.text,sub:'Derived on-device from the loaded forecast',time:null,view:'dashboard'})});
  (state.grievCache||[]).forEach(function(x){out.push({id:'grv:'+x.grievance_id,sev:'info',label:'Info',title:'Grievance '+x.status+': '+x.subject,text:x.category+' · '+x.grievance_id,sub:'Citizen grievance',time:x.created_at,view:'citizen'})});
  var read=lsGet('agromet-read'),dis=lsGet('agromet-dismissed');
  out=out.filter(function(n){return dis.indexOf(n.id)<0});
  out.forEach(function(n){n.unread=read.indexOf(n.id)<0});
  out.sort(function(a,b){if(a.time&&b.time)return b.time<a.time?-1:1;if(a.time)return -1;if(b.time)return 1;return 0});
  return out;
}
function fmtTime(t){if(!t)return 'Active now';try{var d=new Date(t);return isNaN(d)?t:d.toLocaleString()}catch(e){return t}}
function updateNotifBadge(){var b=$('notifBadge');if(!b)return;var n=notifItems().filter(function(x){return x.unread}).length;if(!n){b.hidden=true;return}b.hidden=false;b.textContent=n>9?'9+':String(n)}
function renderNotifs(){
  var el=$('notifList');if(!el)return;
  var items=notifItems();
  if(!items.length){el.innerHTML='<div class="empty"><div class="empty-ic">'+ICON.info+'</div><h3>All caught up</h3><p>No advisories, forecast warnings or grievance updates right now.</p></div>';return}
  el.innerHTML=items.map(function(n){return '<div class="notif '+(n.unread?'unread':'read')+'"><span class="ndot" aria-hidden="true"></span><div class="sev '+n.sev+'" aria-hidden="true" style="align-self:stretch"></div><div class="nt"><div class="nh"><span class="badge '+(n.sev==='critical'?'red pulse':n.sev==='high'?'red':n.sev==='medium'?'amber':n.sev==='low'?'blue':'green')+'"><span class="dot"></span>'+esc(n.label)+'</span> '+esc(n.title)+'</div><div class="nm">'+esc(n.text)+'<br>'+esc(n.sub)+' · '+esc(fmtTime(n.time))+'</div></div><div style="display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap"><button type="button" class="btn secondary sm" data-nview="'+n.view+'" data-nid="'+esc(n.id)+'">View</button><button type="button" class="btn ghost sm" data-ndis="'+esc(n.id)+'">Dismiss</button></div></div>'}).join('');
}
$('notifList').addEventListener('click',function(e){
  var v=e.target.closest('[data-nview]');
  if(v){var r=lsGet('agromet-read');if(r.indexOf(v.dataset.nid)<0){r.push(v.dataset.nid);lsSet('agromet-read',r)}nav(v.dataset.nview);renderNotifs();updateNotifBadge();return}
  var d=e.target.closest('[data-ndis]');
  if(d){var x=lsGet('agromet-dismissed');if(x.indexOf(d.dataset.ndis)<0){x.push(d.dataset.ndis);lsSet('agromet-dismissed',x)}renderNotifs();updateNotifBadge()}
});
$('notifReadAll').onclick=function(){lsSet('agromet-read',notifItems().map(function(n){return n.id}));renderNotifs();updateNotifBadge();toast('Notifications','All marked as read on this device.','info',2500)};
$('notifRefresh').onclick=function(){renderNotifs();updateNotifBadge();toast('Notifications refreshed','Built from advisories, forecasts and grievances.','info',2500)};
/* ---------- settings ---------- */
function paintSettings(){
  var s=session();
  if($('setName')&&document.activeElement!==$('setName'))$('setName').value=s?s.reviewer:($('reviewer')?$('reviewer').value:'');
  if($('setDirty'))$('setDirty').style.display='none';
  paintSeg();paintFontLabel();paintSetSession();
  var t=true;try{t=localStorage.getItem('agromet-toasts')!=='0'}catch(e){}
  if($('setToasts'))$('setToasts').checked=t;
}
function paintSeg(){$all('#themeSeg button').forEach(function(b){b.classList.toggle('on',b.dataset.ts===state.theme)})}
function paintFontLabel(){if($('setFontVal'))$('setFontVal').textContent=Math.round(state.font*100)+'%'}
function paintSetSession(){var s=session();if(!$('setSession'))return;$('setSession').innerHTML=s?'<div class="status ok">'+ICON.ok+'<span>Signed in as <strong>'+esc(s.reviewer)+'</strong> ('+esc(s.roleLabel)+')'+(s.authed?' · API key verified':s.open?' · open pilot mode':'')+'.</span></div>':'<div class="status warn">'+ICON.warn+'<span>Not signed in. Public browsing only.</span></div>'}
$('setName').addEventListener('input',function(){$('setDirty').style.display='flex'});
$('setDiscard').onclick=paintSettings;
$('setSave').onclick=function(){
  var v=$('setName').value.trim()||'guest';var s=session();
  if(s){s.reviewer=v;try{sessionStorage.setItem('agromet-session',JSON.stringify(s))}catch(e){}}
  if($('reviewer'))$('reviewer').value=v;if($('loginReviewer'))$('loginReviewer').value=v;
  paintSession();paintSettings();toast('Profile saved','Display name updated.','success');
};
$all('#themeSeg button').forEach(function(b){b.onclick=function(){state.theme=b.dataset.ts;paintTheme();paintSeg();toast('Theme changed','Switched to '+state.theme+' mode.','info',2200)}});
$('setFontDown').onclick=function(){state.font=Math.max(.9,state.font-.05);paintFont();paintFontLabel()};
$('setFontUp').onclick=function(){state.font=Math.min(1.15,state.font+.05);paintFont();paintFontLabel()};
$('setToasts').onchange=function(){try{localStorage.setItem('agromet-toasts',this.checked?'1':'0')}catch(e){}toast('Preferences saved','Toast notifications '+(this.checked?'enabled':'muted (errors still show)')+'.','info',2500)};
$('setLogout').onclick=function(){$('logoutBtn').click()};
$('wipePrefs').onclick=function(){['agromet-read','agromet-dismissed','agromet-toasts'].forEach(function(k){try{localStorage.removeItem(k)}catch(e){}});paintSettings();updateNotifBadge();toast('Preferences cleared','Notification history and toast preference were reset.','info')};
/* ---------- session + login gate ---------- */
var ROLE_VIEW={citizen:'citizen',officer:'officer',kvk:'kvk',admin:'admin'};
var ROLE_LABEL={citizen:'Citizen',officer:'Officer',kvk:'KVK Scientist',admin:'Administrator'};
var selectedRole='citizen',verifiedKey=null,verifiedOpen=false;
function session(){try{return JSON.parse(sessionStorage.getItem('agromet-session')||'null')}catch(e){return null}}
function paintSession(){var s=session();var on=!!s;if(!$('loginBtn'))return;$('loginBtn').style.display=on?'none':'';$('userChip').style.display=on?'':'none';$('logoutBtn').style.display=on?'':'none';if(on){$('userChip').textContent=s.roleLabel+' · '+s.reviewer;if(s.reviewer&&$('reviewer'))$('reviewer').value=s.reviewer;if(s.key&&$('apiKey'))$('apiKey').value=s.key}}
$('roleList').addEventListener('click',function(e){var b=e.target.closest('.role');if(!b)return;selectedRole=b.dataset.role;$all('.role').forEach(function(r){var on=r===b;r.classList.toggle('sel',on);r.setAttribute('aria-checked',on?'true':'false')})});
$('loginKeyToggle').onclick=function(){var k=$('loginKey');var show=k.type==='password';k.type=show?'text':'password';this.textContent=show?'Hide':'Show';this.setAttribute('aria-label',show?'Hide API key':'Show API key')};
$('loginVerify').onclick=function(){
  var btn=this;var key=$('loginKey').value.trim();var label=btn.innerHTML;btn.disabled=true;btn.innerHTML='<span class="spin" aria-hidden="true"></span> Verifying…';$('loginMsg').innerHTML='';
  var field=$('apiKey');var prev=field?field.value:'';
  if(field)field.value=key;
  api('/api/v1/advisories/kvk-pending').then(function(){
    verifiedKey=key;verifiedOpen=!key;
    $('loginMsg').innerHTML='<div class="status ok">'+ICON.ok+'<span>'+(key?'Key verified. Privileged actions are unlocked for this session.':'Server runs in open pilot mode — no key protection is configured.')+'</span></div>';
  }).catch(function(err){
    verifiedKey=null;verifiedOpen=false;
    if(field)field.value=prev;
    $('loginMsg').innerHTML='<div class="status error">'+ICON.err+'<span>'+(/401/.test(err.message)?'Invalid API key. Check the key and try again.':esc(err.message))+'</span></div>';
  }).finally(function(){btn.disabled=false;btn.innerHTML=label});
};
$('loginContinue').onclick=function(){
  var reviewer=($('loginReviewer').value||'').trim();
  var password=($('loginPassword')?$('loginPassword').value:'').trim();
  if(reviewer && password){
    var btn=this;btn.disabled=true;
    api('/api/v1/auth/login',{method:'POST',body:JSON.stringify({email:reviewer,password:password})}).then(function(r){
      var roles=r.user&&r.user.roles||[];
      var role=roles.indexOf('admin')>=0?'admin':roles.indexOf('kvk')>=0?'kvk':roles.indexOf('officer')>=0?'officer':'citizen';
      var s={role:role,roleLabel:ROLE_LABEL[role],reviewer:r.user.display_name||r.user.email,key:'',token:r.access_token,authed:true,open:false};
      try{sessionStorage.setItem('agromet-session',JSON.stringify(s))}catch(e){}
      paintSession();updateNotifBadge();toast('Signed in','Welcome, '+s.reviewer+' ('+s.roleLabel+').','success');nav(ROLE_VIEW[role]);
    }).catch(function(err){
      $('loginMsg').innerHTML='<div class="status error">'+ICON.err+'<span>'+esc(err.message)+'</span></div>';
      if(verifiedKey){toast('Login failed','Check account credentials or use the configured API key.','error')}
    }).finally(function(){btn.disabled=false});
    return;
  }
  var reviewer=reviewer||'guest';
  var s={role:selectedRole,roleLabel:ROLE_LABEL[selectedRole],reviewer:reviewer,key:verifiedKey||'',authed:!!verifiedKey,open:verifiedOpen&&!verifiedKey};
  try{sessionStorage.setItem('agromet-session',JSON.stringify(s))}catch(e){}
  paintSession();updateNotifBadge();toast('Signed in','Legacy pilot session opened.','success');nav(ROLE_VIEW[selectedRole]);
};
$('logoutBtn').onclick=function(){try{sessionStorage.removeItem('agromet-session')}catch(e){}verifiedKey=null;verifiedOpen=false;paintSession();toast('Signed out','Your workspace session ended.','info');nav('login')};
/* ---------- schematic panchayat map (registry coordinates) ---------- */
function openPid(pid){if($('panchayat'))$('panchayat').value=pid;nav('dashboard',{keepScroll:true});storedForecast()}
function renderMap(){
  var el=$('coverMap');if(!el)return;
  if(!state.panchayats.length){el.innerHTML='<div class="empty"><p>No registry configured.</p></div>';return}
  var W=620,H=330,pad=42;
  var lats=state.panchayats.map(function(p){return p.latitude}),lons=state.panchayats.map(function(p){return p.longitude});
  var mna=Math.min.apply(null,lats),mxa=Math.max.apply(null,lats),mno=Math.min.apply(null,lons),mxo=Math.max.apply(null,lons);
  if(mxa-mna<0.01){mxa+=0.005;mna-=0.005}if(mxo-mno<0.01){mxo+=0.005;mno-=0.005}
  function X(lon){return pad+(lon-mno)/(mxo-mno)*(W-2*pad)}
  function Y(lat){return H-pad-(lat-mna)/(mxa-mna)*(H-2*pad)}
  el.innerHTML='<svg class="mapsvg" viewBox="0 0 '+W+' '+H+'"><rect x="0" y="0" width="'+W+'" height="'+H+'" rx="8" fill="var(--bg)"/>'+state.panchayats.map(function(p){
    var ok=state.avail&&state.avail[p.panchayat_id];
    return '<g class="mk" data-pid="'+esc(p.panchayat_id)+'" tabindex="0" role="button" aria-label="Open forecast for Panchayat '+esc(p.panchayat_id)+'"><circle class="'+(ok?'ok':'cfg')+'" cx="'+X(p.longitude).toFixed(1)+'" cy="'+Y(p.latitude).toFixed(1)+'" r="9"><title>'+esc(p.panchayat_id)+(ok?' — forecast available':' — configured')+'</title></circle><text x="'+X(p.longitude).toFixed(1)+'" y="'+(Y(p.latitude)+24).toFixed(1)+'" text-anchor="middle">'+esc(p.panchayat_id)+'</text></g>'
  }).join('')+'</svg>';
}
$('coverMap').addEventListener('click',function(e){var g=e.target.closest('.mk');if(g)openPid(g.dataset.pid)});
$('coverMap').addEventListener('keydown',function(e){if(e.key!=='Enter'&&e.key!==' ')return;var g=e.target.closest('.mk');if(g){e.preventDefault();openPid(g.dataset.pid)}});
/* ---------- init ---------- */
(function init(){
  try{var th=localStorage.getItem('agromet-theme');if(th==='dark'||th==='light')state.theme=th;var f=parseFloat(localStorage.getItem('agromet-font'));if(f>=.9&&f<=1.15)state.font=f}catch(e){}
  paintTheme();paintFont();paintSession();updateNotifBadge();
  var start=(location.hash||'').slice(1);
  nav(session()?(VIEWS[start]?start:'home'):'login',{silent:true});
  loadRegistry();loadSummary();
  (function(){var R=$all('#home .card, .pagehead');R.forEach(function(el){el.classList.add('reveal')});if(reduced()||!('IntersectionObserver' in window)){R.forEach(function(el){el.classList.add('in')});return}var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}})},{threshold:.06});R.forEach(function(el){io.observe(el)});setTimeout(function(){R.forEach(function(el){el.classList.add('in')})},4000)})();
})();
</script>
</body>
</html>"""

def portal_html() -> str:
    return HTML
