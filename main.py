"""
main.py - HELPER TDIU v3.0 — Maximum version
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import config
from database import init_db

MINI_APP_HTML = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#000;--bg2:#111114;--bg3:#1c1c1e;--bg4:#2c2c2e;--bg5:#3a3a3c;
  --text:#fff;--t2:rgba(235,235,245,.85);--t3:rgba(235,235,245,.6);--t4:rgba(235,235,245,.35);
  --accent:#0a84ff;--green:#30d158;--orange:#ff9f0a;--red:#ff453a;--purple:#bf5af2;--pink:#ff375f;
  --sep:rgba(255,255,255,.09);
  --nav:83px;--top:60px;
  --safe-b:env(safe-area-inset-bottom,0px);
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  -webkit-font-smoothing:antialiased}

/* BG */
.bg-wrap{position:fixed;inset:0;z-index:0;overflow:hidden}
.blob{position:absolute;border-radius:50%;filter:blur(90px);opacity:.18;animation:blob-move 18s infinite alternate ease-in-out}
.b1{width:380px;height:380px;background:#0a84ff;top:-15%;left:-15%;animation-delay:0s}
.b2{width:460px;height:460px;background:#bf5af2;bottom:-20%;right:-15%;animation-delay:-6s}
.b3{width:300px;height:300px;background:#30d158;top:40%;left:30%;animation-delay:-12s;opacity:.1}
@keyframes blob-move{0%{transform:translate(0,0) scale(1)}100%{transform:translate(30px,25px) scale(1.08)}}

/* TOPBAR */
.topbar{
  position:fixed;top:0;left:0;right:0;height:var(--top);
  background:rgba(0,0,0,.75);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);
  border-bottom:.5px solid var(--sep);
  display:flex;align-items:center;padding:0 18px;z-index:200;
}
.tlogo{
  width:36px;height:36px;border-radius:10px;
  background:linear-gradient(135deg,#0a84ff 0%,#5e5ce6 100%);
  display:flex;align-items:center;justify-content:center;
  font-size:18px;font-weight:900;color:#fff;margin-right:12px;
  box-shadow:0 2px 12px rgba(10,132,255,.45);
  flex-shrink:0;
}
.tname{font-size:16px;font-weight:700;letter-spacing:-.3px}
.tsub{font-size:11px;color:var(--t3);margin-top:1px}
.tright{margin-left:auto;display:flex;align-items:center;gap:8px}
.tbadge{
  font-size:10px;font-weight:700;padding:3px 9px;border-radius:20px;
  letter-spacing:.3px;
}
.pro-badge{background:linear-gradient(135deg,#ff9f0a,#ff6b00);color:#fff}
.demo-badge{background:var(--bg4);color:var(--t3);border:.5px solid var(--sep)}
.tgpa{font-size:15px;font-weight:800;color:var(--accent)}

/* VIEWS */
.view{
  position:fixed;top:var(--top);left:0;right:0;
  bottom:var(--nav);
  overflow-y:auto;overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;
  opacity:0;transform:translateX(28px);
  transition:opacity .28s ease,transform .28s cubic-bezier(.25,.46,.45,.94);
  pointer-events:none;z-index:1;
}
.view::-webkit-scrollbar{display:none}
.view.active{opacity:1;transform:none;pointer-events:auto}
.view.left{transform:translateX(-28px)}
.vpad{padding:14px 16px 24px}

/* NAV */
.bottom-nav{
  position:fixed;bottom:0;left:0;right:0;
  height:calc(var(--nav) + var(--safe-b));
  padding-bottom:var(--safe-b);
  background:rgba(0,0,0,.8);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);
  border-top:.5px solid var(--sep);
  display:flex;align-items:flex-start;padding-top:11px;z-index:200;
}
.ni{
  flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
  background:none;border:none;cursor:pointer;color:var(--t4);
  transition:color .2s;font-family:'Inter',sans-serif;
  position:relative;
}
.ni.active{color:var(--accent)}
.ni.active::before{
  content:'';position:absolute;top:-11px;left:25%;right:25%;
  height:2.5px;background:var(--accent);border-radius:0 0 3px 3px;
}
.ni-icon{font-size:23px;line-height:1}
.ni-lbl{font-size:10px;font-weight:500}

/* CARDS */
.card{
  background:rgba(28,28,30,.65);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border:.5px solid var(--sep);border-radius:18px;
  margin-bottom:12px;overflow:hidden;
}
.cpd{padding:16px}
.ctitle{font-size:12px;font-weight:700;color:var(--t3);
  text-transform:uppercase;letter-spacing:.6px;margin-bottom:14px}
.csep{height:.5px;background:var(--sep)}

/* GPA HERO */
.gpa-hero{
  background:linear-gradient(160deg,rgba(10,132,255,.15) 0%,rgba(94,92,230,.12) 50%,transparent 100%);
  border:.5px solid rgba(10,132,255,.25);border-radius:22px;
  padding:24px 20px;margin-bottom:12px;position:relative;overflow:hidden;
}
.gpa-hero::after{
  content:'';position:absolute;top:-40px;right:-40px;
  width:180px;height:180px;
  background:radial-gradient(circle,rgba(10,132,255,.15) 0%,transparent 70%);
}
.gpa-lbl{font-size:11px;font-weight:700;color:var(--accent);
  text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px}
.gpa-val{
  font-size:68px;font-weight:900;letter-spacing:-3px;line-height:1;
  background:linear-gradient(135deg,#0a84ff,#5e5ce6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:6px;
}
.gpa-meta{font-size:13px;color:var(--t3)}
.gpa-name{font-size:15px;font-weight:600;margin-top:12px;color:var(--text)}

/* STATS */
.stats-row{display:flex;gap:10px;margin-bottom:12px}
.stat-c{
  flex:1;background:rgba(28,28,30,.65);
  backdrop-filter:blur(20px);border:.5px solid var(--sep);
  border-radius:18px;padding:14px 12px;
}
.sv{font-size:30px;font-weight:800;line-height:1;margin-bottom:5px}
.sl{font-size:11px;color:var(--t3);font-weight:500}
.ss{font-size:10px;color:var(--t4);margin-top:2px}

/* ALERTS */
.alert{
  display:flex;align-items:flex-start;gap:10px;
  padding:13px 15px;border-radius:14px;margin-bottom:9px;
  font-size:13px;line-height:1.5;
}
.ai{font-size:18px;flex-shrink:0;margin-top:1px}
.alert.danger{background:rgba(255,69,58,.1);border:.5px solid rgba(255,69,58,.3)}
.alert.warn{background:rgba(255,159,10,.1);border:.5px solid rgba(255,159,10,.3)}
.alert.info{background:rgba(10,132,255,.1);border:.5px solid rgba(10,132,255,.2)}
.alert.success{background:rgba(48,209,88,.1);border:.5px solid rgba(48,209,88,.25)}

/* LESSON CHIPS */
.chips{display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;margin:0 -16px;padding-left:16px;padding-right:16px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{
  flex-shrink:0;background:rgba(44,44,46,.7);
  backdrop-filter:blur(12px);border:.5px solid var(--sep);
  border-radius:16px;padding:13px 15px;min-width:155px;
}
.chip-n{font-size:10px;font-weight:700;color:var(--accent);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}
.chip-t{font-size:12px;color:var(--t3);margin-bottom:7px}
.chip-s{font-size:14px;font-weight:600;line-height:1.3;margin-bottom:5px}
.chip-r{font-size:11px;color:var(--t4)}

/* SECTION */
.sec-hdr{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:11px;margin-top:6px}
.sec-t{font-size:22px;font-weight:800;letter-spacing:-.4px}
.sec-m{font-size:14px;color:var(--accent);font-weight:500;cursor:pointer}

/* GRADE CARD */
.grade-wrap{position:relative;padding:15px 16px}
.g-name{font-size:15px;font-weight:600;line-height:1.3;padding-right:62px;margin-bottom:3px}
.g-meta{font-size:12px;color:var(--t3);margin-bottom:12px}
.g-total{position:absolute;top:15px;right:16px;font-size:24px;font-weight:800}
.bars{display:flex;flex-direction:column;gap:6px}
.bar-r{display:flex;align-items:center;gap:9px}
.bar-l{font-size:11px;color:var(--t4);width:46px;flex-shrink:0;font-weight:500}
.bar-t{flex:1;height:4px;background:var(--bg5);border-radius:99px;overflow:hidden}
.bar-f{height:100%;border-radius:99px;transition:width .8s cubic-bezier(.34,1.56,.64,1)}
.bar-v{font-size:11px;color:var(--t3);width:34px;text-align:right;flex-shrink:0}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:11px}
.tag{font-size:11px;font-weight:600;padding:3px 9px;border-radius:99px}
.t-blue{background:rgba(10,132,255,.15);color:var(--accent)}
.t-green{background:rgba(48,209,88,.15);color:var(--green)}
.t-orange{background:rgba(255,159,10,.15);color:var(--orange)}
.t-red{background:rgba(255,69,58,.15);color:var(--red)}
.t-gray{background:var(--bg4);color:var(--t3)}
.t-purple{background:rgba(191,90,242,.15);color:var(--purple)}
.risk-strip{display:flex;align-items:center;gap:7px;
  background:rgba(255,69,58,.08);border-top:.5px solid rgba(255,69,58,.15);
  padding:9px 16px;font-size:12px;color:#ff6b63}
.nb-strip{display:flex;align-items:center;gap:7px;
  background:rgba(255,159,10,.08);border-top:.5px solid rgba(255,159,10,.15);
  padding:9px 16px;font-size:12px;color:var(--orange)}

/* GPA PROGRESS RING */
.ring-wrap{display:flex;justify-content:center;align-items:center;margin:8px 0}
.ring{transform:rotate(-90deg)}
.ring-bg{fill:none;stroke:var(--bg5);stroke-width:8}
.ring-fg{fill:none;stroke:var(--accent);stroke-width:8;stroke-linecap:round;
  transition:stroke-dashoffset 1.2s cubic-bezier(.34,1.56,.64,1);stroke-dasharray:283;stroke-dashoffset:283}
.ring-text{position:absolute;font-size:26px;font-weight:800;color:var(--accent)}

/* TIMETABLE */
.week-nav{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.wbtn{
  width:38px;height:38px;border-radius:11px;
  background:var(--bg3);border:none;cursor:pointer;color:var(--text);
  font-size:18px;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:background .15s;
}
.wbtn:active{background:var(--bg4)}
.wlbl{flex:1;text-align:center;font-size:13px;font-weight:600;color:var(--t2)}
.dtabs{display:flex;gap:7px;overflow-x:auto;padding-bottom:4px;
  margin-bottom:14px;scrollbar-width:none}
.dtabs::-webkit-scrollbar{display:none}
.dtab{
  flex-shrink:0;padding:8px 15px;
  background:var(--bg3);border:none;border-radius:99px;
  font-size:13px;font-weight:600;color:var(--t3);cursor:pointer;
  transition:all .15s;font-family:'Inter',sans-serif;
  position:relative;
}
.dtab.active{background:var(--accent);color:#fff;box-shadow:0 0 14px rgba(10,132,255,.4)}
.dtab.today:not(.active){border:.5px solid var(--accent);color:var(--accent);background:rgba(10,132,255,.1)}
.dtab .dot{
  position:absolute;top:2px;right:4px;
  width:5px;height:5px;border-radius:50%;background:var(--accent);
}
.dtab.active .dot{background:#fff}
.lrow{display:flex;gap:12px;align-items:flex-start;padding:14px 16px}
.lnum-col{width:38px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:3px}
.lnum{width:34px;height:34px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:700}
.ltmini{font-size:9px;color:var(--t4);text-align:center;line-height:1.4}
.lbody{flex:1}
.lsubj{font-size:14px;font-weight:600;margin-bottom:6px;line-height:1.3}
.lmeta{display:flex;flex-wrap:wrap;gap:8px;font-size:12px;color:var(--t3)}
.lmi{display:flex;align-items:center;gap:3px}
.no-lesson{text-align:center;padding:50px 20px;color:var(--t4)}
.no-lesson-ic{font-size:56px;margin-bottom:14px}
.no-lesson-t{font-size:16px;font-weight:600;color:var(--t3)}
.no-lesson-s{font-size:13px;margin-top:5px}

/* NAVIGATOR */
.nav-segs{display:flex;gap:8px;margin-bottom:14px}
.nseg{
  flex:1;padding:11px;background:var(--bg3);
  border:.5px solid transparent;border-radius:13px;
  font-size:13px;font-weight:600;color:var(--t3);cursor:pointer;
  transition:all .15s;font-family:'Inter',sans-serif;
}
.nseg.active{background:rgba(10,132,255,.12);border-color:var(--accent);color:var(--accent)}
.search-b{
  display:flex;align-items:center;gap:10px;
  background:var(--bg3);border-radius:13px;
  padding:12px 14px;margin-bottom:12px;
  border:.5px solid var(--sep);transition:border-color .2s;
}
.search-b:focus-within{border-color:var(--accent)}
.si{font-size:16px;color:var(--t4)}
.sinput{
  background:none;border:none;outline:none;
  color:var(--text);font-size:14px;flex:1;
  font-family:'Inter',sans-serif;
}
.sinput::placeholder{color:var(--t4)}
.room-r{display:flex;align-items:center;gap:14px;padding:13px 16px}
.rcode{font-size:16px;font-weight:700;color:var(--accent);width:58px;flex-shrink:0}
.rinfo{flex:1}
.rname{font-size:14px;font-weight:500}
.rmeta{font-size:12px;color:var(--t3);margin-top:2px}
.rtag{background:var(--bg4);color:var(--t3);font-size:10px;font-weight:600;padding:3px 8px;border-radius:7px}
.teacher-r{display:flex;align-items:center;gap:14px;padding:13px 16px}
.tav{
  width:44px;height:44px;border-radius:13px;
  background:linear-gradient(135deg,var(--bg3),var(--bg4));
  display:flex;align-items:center;justify-content:center;
  font-size:16px;font-weight:700;flex-shrink:0;color:var(--accent);
}
.tloc-on{color:var(--green);font-size:12px;margin-top:4px;display:flex;align-items:center;gap:4px}
.tloc-off{color:var(--t4);font-size:12px;margin-top:4px}

/* PREMIUM LOCK */
.lock-card{
  background:linear-gradient(160deg,rgba(10,132,255,.12),rgba(94,92,230,.08));
  border:.5px solid rgba(10,132,255,.25);border-radius:20px;
  padding:26px 20px;text-align:center;margin-bottom:12px;
}
.lock-ic{font-size:44px;margin-bottom:14px}
.lock-t{font-size:19px;font-weight:700;margin-bottom:9px}
.lock-d{font-size:13px;color:var(--t3);line-height:1.6;margin-bottom:18px}
.lock-features{display:flex;flex-direction:column;gap:8px;margin-bottom:18px;text-align:left}
.lf-row{display:flex;align-items:center;gap:10px;font-size:13px}
.lf-ic{width:28px;height:28px;border-radius:8px;
  background:rgba(10,132,255,.15);display:flex;align-items:center;
  justify-content:center;font-size:14px;flex-shrink:0}
.btn-primary{
  display:block;width:100%;background:var(--accent);color:#fff;
  font-family:'Inter',sans-serif;font-size:15px;font-weight:700;
  padding:15px;border:none;border-radius:13px;cursor:pointer;
  transition:opacity .15s;letter-spacing:-.1px;
}
.btn-primary:active{opacity:.8}
.btn-outline{
  display:block;width:100%;background:transparent;color:var(--accent);
  font-family:'Inter',sans-serif;font-size:14px;font-weight:600;
  padding:12px;border:.5px solid var(--accent);border-radius:13px;
  cursor:pointer;margin-top:10px;
}

/* PROGRESS CIRCLE */
.pcircle{
  display:inline-flex;position:relative;
  align-items:center;justify-content:center;
  width:100px;height:100px;
}
.pcircle svg{position:absolute;transform:rotate(-90deg)}
.pcircle .pval{font-size:22px;font-weight:800}

/* ATTENDANCE BAR */
.att-row{display:flex;align-items:center;gap:12px;margin-top:4px}
.att-t{width:70px;font-size:11px;color:var(--t4);flex-shrink:0}
.att-bar{flex:1;height:5px;background:var(--bg5);border-radius:99px;overflow:hidden}
.att-fill{height:100%;border-radius:99px}
.att-pct{font-size:11px;color:var(--t3);width:36px;text-align:right;flex-shrink:0}

/* TOAST */
#toasts{
  position:fixed;bottom:calc(var(--nav) + 14px);
  left:16px;right:16px;z-index:999;
  display:flex;flex-direction:column;gap:8px;pointer-events:none;
}
.toast-el{
  background:rgba(44,44,46,.95);
  backdrop-filter:blur(20px);border:.5px solid var(--sep);
  border-radius:14px;padding:13px 16px;
  font-size:13px;display:flex;align-items:center;gap:10px;
  pointer-events:all;
  animation:tIn .3s cubic-bezier(.34,1.56,.64,1);
}
.toast-el.out{animation:tOut .25s ease forwards}
@keyframes tIn{from{opacity:0;transform:translateY(12px) scale(.95)}to{opacity:1;transform:none}}
@keyframes tOut{to{opacity:0;transform:translateY(8px)}}

/* SKEL */
.skel{
  background:linear-gradient(90deg,var(--bg3) 25%,var(--bg4) 50%,var(--bg3) 75%);
  background-size:200% 100%;animation:sk 1.3s infinite;border-radius:12px;
}
@keyframes sk{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
</head>
<body>
<div class="bg-wrap" aria-hidden="true">
  <div class="blob b1"></div>
  <div class="blob b2"></div>
  <div class="blob b3"></div>
</div>

<!-- TOPBAR -->
<header class="topbar">
  <div class="tlogo">H</div>
  <div>
    <div class="tname">HELPER TDIU</div>
    <div class="tsub" id="tsub">Yuklanmoqda…</div>
  </div>
  <div class="tright">
    <div id="tgpa" class="tgpa" style="display:none"></div>
    <div id="badge-pro"  class="tbadge pro-badge"  style="display:none">👑 PRO</div>
    <div id="badge-demo" class="tbadge demo-badge" style="display:none">DEMO</div>
  </div>
</header>

<!-- VIEWS -->
<div id="v-home"      class="view active"><div class="vpad" id="home-inner"></div></div>
<div id="v-grades"    class="view"><div class="vpad" id="grades-inner"></div></div>
<div id="v-timetable" class="view"><div class="vpad" id="tt-inner"></div></div>
<div id="v-navigator" class="view"><div class="vpad" id="nav-inner"></div></div>

<!-- BOTTOM NAV -->
<nav class="bottom-nav">
  <button class="ni active" id="ni-home" onclick="go('home')">
    <span class="ni-icon">🏠</span><span class="ni-lbl">Bosh</span>
  </button>
  <button class="ni" id="ni-grades" onclick="go('grades')">
    <span class="ni-icon">📊</span><span class="ni-lbl">Baholar</span>
  </button>
  <button class="ni" id="ni-timetable" onclick="go('timetable')">
    <span class="ni-icon">📅</span><span class="ni-lbl">Jadval</span>
  </button>
  <button class="ni" id="ni-navigator" onclick="go('navigator')">
    <span class="ni-icon">🗺️</span><span class="ni-lbl">Navigator</span>
  </button>
</nav>

<div id="toasts"></div>

<script>
// ─── Telegram ──────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
tg?.expand();
tg?.disableVerticalSwipes?.();

// ─── State ────────────────────────────────────────────────────
const S = {
  view:'home', prev:'home',
  isPremium:false, isDemo:true,
  weekOff:0,
  dayIdx: new Date().getDay()===0 ? 6 : new Date().getDay()-1,
  navTab:'rooms',
  semIdx:0,  // 0 = joriy semestr
};

// ─── Demo Data ────────────────────────────────────────────────
const D = {
  profile:{name:"Ulug'bek Toshmatov",group:"IQ-22-01",faculty:"Iqtisodiyot",sem:"2024-2",gpa:3.45},
  semesters:[
    {
      id:"2024-2", label:"2024-2 · Bahor", active:true,
      grades:[
        {s:"Mikroiqtisodiyot",      cur:17,mid:24,fin:null,tot:41,hrs:64,miss:4, risk:false,nb:false,need:14},
        {s:"Bank ishi va kredit",   cur:15,mid:22,fin:null,tot:37,hrs:72,miss:15,risk:false,nb:true, need:18},
        {s:"Iqtisodiy siyosat",     cur:18,mid:28,fin:null,tot:46,hrs:80,miss:2, risk:false,nb:false,need:9},
        {s:"Pul va kredit",         cur:12,mid:18,fin:null,tot:30,hrs:64,miss:14,risk:true, nb:true, need:25},
        {s:"Marketing asoslari",    cur:19,mid:26,fin:null,tot:45,hrs:72,miss:0, risk:false,nb:false,need:10},
        {s:"Tadbirkorlik asoslari", cur:16,mid:25,fin:null,tot:41,hrs:56,miss:6, risk:false,nb:false,need:14},
      ]
    },
    {
      id:"2024-1", label:"2024-1 · Kuz", active:false,
      grades:[
        {s:"Makroiqtisodiyot",      cur:19,mid:27,fin:44,tot:90,hrs:64,miss:0, risk:false,nb:false,need:0},
        {s:"Moliya nazariyasi",     cur:16,mid:24,fin:38,tot:78,hrs:72,miss:4, risk:false,nb:false,need:0},
        {s:"Statistika",            cur:18,mid:26,fin:41,tot:85,hrs:80,miss:2, risk:false,nb:false,need:0},
        {s:"Iqtisodiy tahlil",      cur:14,mid:20,fin:30,tot:64,hrs:64,miss:8, risk:false,nb:false,need:0},
        {s:"Informatika",           cur:20,mid:29,fin:48,tot:97,hrs:72,miss:0, risk:false,nb:false,need:0},
        {s:"Ingliz tili",           cur:17,mid:25,fin:35,tot:77,hrs:56,miss:4, risk:false,nb:false,need:0},
      ]
    },
    {
      id:"2023-2", label:"2023-2 · Bahor", active:false,
      grades:[
        {s:"Matematika",            cur:18,mid:26,fin:42,tot:86,hrs:80,miss:2, risk:false,nb:false,need:0},
        {s:"Iqtisodiyot asoslari",  cur:17,mid:25,fin:40,tot:82,hrs:72,miss:0, risk:false,nb:false,need:0},
        {s:"Falsafa",               cur:15,mid:22,fin:35,tot:72,hrs:64,miss:6, risk:false,nb:false,need:0},
        {s:"Tarix",                 cur:16,mid:24,fin:38,tot:78,hrs:56,miss:4, risk:false,nb:false,need:0},
        {s:"Sport",                 cur:20,mid:28,fin:45,tot:93,hrs:48,miss:0, risk:false,nb:false,need:0},
      ]
    },
    {
      id:"2023-1", label:"2023-1 · Kuz", active:false,
      grades:[
        {s:"Matematika (kirish)",   cur:19,mid:27,fin:43,tot:89,hrs:80,miss:0, risk:false,nb:false,need:0},
        {s:"Ona tili",              cur:18,mid:26,fin:40,tot:84,hrs:64,miss:2, risk:false,nb:false,need:0},
        {s:"Iqtisodiyot kirish",    cur:17,mid:25,fin:38,tot:80,hrs:72,miss:4, risk:false,nb:false,need:0},
        {s:"Informatika (kirish)",  cur:20,mid:28,fin:46,tot:94,hrs:56,miss:0, risk:false,nb:false,need:0},
      ]
    },
  ],
  grades:[
    {s:"Mikroiqtisodiyot",       cur:17,mid:24,fin:null,tot:41,hrs:64,miss:4, risk:false,nb:false,need:14},
    {s:"Bank ishi va kredit",    cur:15,mid:22,fin:null,tot:37,hrs:72,miss:15,risk:false,nb:true, need:18},
    {s:"Iqtisodiy siyosat",      cur:18,mid:28,fin:null,tot:46,hrs:80,miss:2, risk:false,nb:false,need:9},
    {s:"Pul va kredit",          cur:12,mid:18,fin:null,tot:30,hrs:64,miss:14,risk:true, nb:true, need:25},
    {s:"Marketing asoslari",     cur:19,mid:26,fin:null,tot:45,hrs:72,miss:0, risk:false,nb:false,need:10},
    {s:"Tadbirkorlik asoslari",  cur:16,mid:25,fin:null,tot:41,hrs:56,miss:6, risk:false,nb:false,need:14},
  ],
  tt:{
    "2025-04-07":[
      {n:1,st:"08:30",en:"09:50",s:"Mikroiqtisodiyot",tp:"Ma'ruza",   tc:"Salimov B.",  r:"A-301",b:"A blok"},
      {n:3,st:"11:30",en:"12:50",s:"Bank ishi",        tp:"Seminar",   tc:"Rahimov N.",  r:"B-204",b:"B blok"},
    ],
    "2025-04-08":[
      {n:2,st:"10:00",en:"11:20",s:"Pul va kredit",    tp:"Ma'ruza",   tc:"Hasanov M.",  r:"A-101",b:"A blok"},
      {n:4,st:"13:30",en:"14:50",s:"Marketing",        tp:"Seminar",   tc:"Yusupov K.",  r:"C-305",b:"C blok"},
    ],
    "2025-04-09":[
      {n:1,st:"08:30",en:"09:50",s:"Iqtisodiy siyosat",tp:"Ma'ruza",  tc:"Toshmatov A.",r:"A-201",b:"A blok"},
      {n:5,st:"15:00",en:"16:20",s:"Tadbirkorlik",     tp:"Seminar",   tc:"Aliyev R.",   r:"B-101",b:"B blok"},
    ],
    "2025-04-10":[
      {n:2,st:"10:00",en:"11:20",s:"Mikroiqtisodiyot", tp:"Seminar",  tc:"Salimov B.",  r:"B-102",b:"B blok"},
    ],
    "2025-04-11":[
      {n:3,st:"11:30",en:"12:50",s:"Marketing",        tp:"Ma'ruza",   tc:"Yusupov K.",  r:"A-301",b:"A blok"},
      {n:6,st:"16:30",en:"17:50",s:"Bank ishi",        tp:"Ma'ruza",   tc:"Rahimov N.",  r:"A-101",b:"A blok"},
    ],
  },
  rooms:[
    {c:"A-101",b:"A blok",f:1,cap:120,t:"Ma'ruza zali"},
    {c:"A-102",b:"A blok",f:1,cap:60, t:"Seminar xona"},
    {c:"A-201",b:"A blok",f:2,cap:80, t:"Ma'ruza zali"},
    {c:"A-301",b:"A blok",f:3,cap:100,t:"Ma'ruza zali"},
    {c:"A-305",b:"A blok",f:3,cap:40, t:"Kompyuter lab"},
    {c:"B-101",b:"B blok",f:1,cap:50, t:"Seminar xona"},
    {c:"B-102",b:"B blok",f:1,cap:50, t:"Seminar xona"},
    {c:"B-204",b:"B blok",f:2,cap:30, t:"Seminar xona"},
    {c:"C-101",b:"C blok",f:1,cap:40, t:"Kompyuter lab"},
    {c:"C-305",b:"C blok",f:3,cap:30, t:"Seminar xona"},
    {c:"AKTOV",b:"Asosiy",f:1,cap:500,t:"Aktov zal"},
  ],
  teachers:[
    {n:"Salimov B.A.",  d:"Mikroiqtisodiyot",  r:"A-301",online:true},
    {n:"Rahimov N.X.",  d:"Bank ishi",         r:"B-204",online:true},
    {n:"Hasanov M.T.",  d:"Pul va kredit",     r:null,   online:false},
    {n:"Yusupov K.O.",  d:"Marketing",         r:"C-305",online:true},
    {n:"Toshmatov A.R.",d:"Iqtisodiy siyosat", r:null,   online:false},
    {n:"Aliyev R.S.",   d:"Tadbirkorlik",      r:"B-101",online:true},
  ],
};

// ─── Helpers ──────────────────────────────────────────────────
const DU = ["Du","Se","Ch","Pa","Ju","Sh","Ya"];
const DF = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"];
const CL = ["#0a84ff","#30d158","#ff9f0a","#bf5af2","#ff453a","#5e5ce6","#32ade6"];

function iso(d){ return d.toISOString().slice(0,10); }
function today(){ return iso(new Date()); }
function monday(off=0){
  const d=new Date(); const wd=d.getDay()===0?6:d.getDay()-1;
  d.setDate(d.getDate()-wd+off*7); d.setHours(0,0,0,0); return d;
}
function fmt(d){ return d.getDate()+'.'+String(d.getMonth()+1).padStart(2,'0'); }

function toast(msg,type='info'){
  const icons={info:'ℹ️',success:'✅',warn:'⚠️',error:'❌'};
  const el=document.createElement('div');
  el.className='toast-el';
  el.innerHTML='<span>'+icons[type]+'</span><span>'+msg+'</span>';
  document.getElementById('toasts').appendChild(el);
  setTimeout(()=>{ el.classList.add('out'); el.addEventListener('animationend',()=>el.remove()); },3000);
}
function haptic(t='light'){ tg?.HapticFeedback?.impactOccurred(t); }

function letter(t){
  if(t===null) return null;
  return t>=86?'A':t>=71?'B':t>=55?'C':'D';
}
function totalColor(t){
  return t>=86?'var(--green)':t>=71?'var(--accent)':t>=55?'var(--orange)':'var(--red)';
}

// ─── Navigation ───────────────────────────────────────────────
const ORDER = ['home','grades','timetable','navigator'];
function go(v){
  if(v===S.view) return;
  const pi = ORDER.indexOf(S.view), ni = ORDER.indexOf(v);
  const going_right = ni > pi;
  document.getElementById('v-'+S.view).classList.toggle('left', going_right);
  document.getElementById('v-'+S.view).classList.remove('active');
  S.prev=S.view; S.view=v;
  const el = document.getElementById('v-'+v);
  el.classList.remove('left');
  el.classList.add('active');
  document.querySelectorAll('.ni').forEach(b => b.classList.toggle('active', b.id==='ni-'+v));
  document.getElementById('v-'+v).querySelector('[id$="-inner"],[id$="inner"]').scrollTop=0;
  render(v);
  haptic('light');
}

function render(v){
  if(v==='home')      renderHome();
  else if(v==='grades')     renderGrades();
  else if(v==='timetable')  renderTimetable();
  else if(v==='navigator')  renderNavigator();
}

// ─── Topbar ───────────────────────────────────────────────────
function initTopbar(){
  const p=D.profile;
  document.getElementById('tsub').textContent=p.group+' · '+p.faculty;
  document.getElementById('tgpa').textContent=p.gpa.toFixed(2);
  document.getElementById('tgpa').style.display='';
  if(S.isPremium) document.getElementById('badge-pro').style.display='';
  if(S.isDemo)    document.getElementById('badge-demo').style.display='';
}

// ══════════════════════════════════════════════════════
// HOME
// ══════════════════════════════════════════════════════
function renderHome(){
  const p=D.profile;
  const risks = D.grades.filter(g=>g.risk).length;
  const nbs   = D.grades.filter(g=>g.nb).length;
  const td    = D.tt[today()]||[];
  const gpaLabel = p.gpa>=3.7?"A'lo":p.gpa>=3.0?"Yaxshi":p.gpa>=2.0?"Qoniqarli":"Past";

  let html = `
  <div class="gpa-hero">
    <div class="gpa-lbl">Umumiy GPA</div>
    <div class="gpa-val">${p.gpa.toFixed(2)}</div>
    <div class="gpa-meta">${p.sem} semester · ${gpaLabel}</div>
    <div class="gpa-name">${p.name} · ${p.group}</div>
  </div>

  <div class="stats-row">
    <div class="stat-c">
      <div class="sv" style="color:${risks>0?'var(--red)':'var(--green)'}">${risks}</div>
      <div class="sl">Xavf ostida</div><div class="ss">fan</div>
    </div>
    <div class="stat-c">
      <div class="sv" style="color:${nbs>0?'var(--orange)':'var(--green)'}">${nbs}</div>
      <div class="sl">NB xavfi</div><div class="ss">fan</div>
    </div>
    <div class="stat-c">
      <div class="sv" style="color:var(--accent)">${td.length}</div>
      <div class="sl">Bugun</div><div class="ss">dars</div>
    </div>
  </div>`;

  if(risks>0) html+=`<div class="alert danger"><span class="ai">🚨</span><div><b>${risks} ta fanda</b> qayta topshirish xavfi bor!</div></div>`;
  if(nbs>0)   html+=`<div class="alert warn"><span class="ai">📍</span><div><b>${nbs} ta fanda</b> davomat chegarasiga yaqin!</div></div>`;
  if(S.isDemo) html+=`<div class="alert info"><span class="ai">👀</span><div>Demo rejim — namunali ma'lumotlar.</div></div>`;

  html += `<div class="sec-hdr"><div class="sec-t">Bugun</div><div class="sec-m" onclick="go('timetable')">Barchasi</div></div>`;

  if(td.length===0){
    html+=`<div class="card"><div class="cpd" style="text-align:center;padding:24px;color:var(--t4)">🎉 Bugun darslar yo'q!</div></div>`;
  } else {
    html+=`<div class="chips">`;
    td.forEach((l,i)=>{
      html+=`<div class="chip">
        <div class="chip-n">${l.n}-dars</div>
        <div class="chip-t">${l.st} – ${l.en}</div>
        <div class="chip-s">${l.s}</div>
        <div class="chip-r">📍 ${l.r} · 👤 ${l.tc}</div>
      </div>`;
    });
    html+=`</div>`;
  }

  const atRisk = D.grades.filter(g=>g.risk||g.nb);
  if(atRisk.length>0){
    html+=`<div class="sec-hdr" style="margin-top:8px"><div class="sec-t">Diqqat</div></div><div class="card">`;
    atRisk.forEach((g,i,a)=>{
      html+=`<div style="padding:13px 16px;${i<a.length-1?'border-bottom:.5px solid var(--sep)':''}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
          <div style="font-size:14px;font-weight:600;flex:1;padding-right:50px">${g.s}</div>
          <div style="font-size:20px;font-weight:800;color:${g.risk?'var(--red)':'var(--orange)'}">${g.tot}</div>
        </div>
        ${g.risk?`<div style="font-size:12px;color:var(--red)">⚠️ O'tish uchun yakuniyda ${g.need}/50 kerak</div>`:''}
        ${g.nb  ?`<div style="font-size:12px;color:var(--orange);margin-top:3px">📍 Davomat 20% chegarasiga yaqin</div>`:''}
      </div>`;
    });
    html+=`</div>`;
  }

  if(!S.isPremium){
    html+=`
    <div class="lock-card" style="margin-top:8px">
      <div class="lock-ic">👑</div>
      <div class="lock-t">Premium ga o'ting</div>
      <div class="lock-features">
        <div class="lf-row"><div class="lf-ic">⚡</div><span>Darhol ball yangilanishi</span></div>
        <div class="lf-row"><div class="lf-ic">🔔</div><span>Jadval o'zgarish ogohlantirishlari</span></div>
        <div class="lf-row"><div class="lf-ic">📈</div><span>To'liq GPA analitika va prognoz</span></div>
        <div class="lf-row"><div class="lf-ic">🗺️</div><span>O'qituvchi real-time tracker</span></div>
      </div>
      <button class="btn-primary" onclick="toast('Tez kunda ulash rejalashtirilgan!','info')">
        👑 5,000 so'm / oy
      </button>
    </div>`;
  }

  document.getElementById('home-inner').innerHTML=html;
}

// ══════════════════════════════════════════════════════
// GRADES
// ══════════════════════════════════════════════════════
function renderGrades(){
  const sem = D.semesters[S.semIdx];
  const grades = sem ? sem.grades : D.grades;
  const isActive = sem ? sem.active : true;
  const total=grades.reduce((s,g)=>s+g.tot,0);
  const gpa=(total/grades.length/25).toFixed(2);

  // Semester tabs
  const semTabs = D.semesters.map((s,i)=>`
    <button onclick="selectSem(${i})" style="
      flex-shrink:0;padding:7px 14px;
      background:${i===S.semIdx?'var(--accent)':'var(--bg3)'};
      border:none;border-radius:99px;
      font-size:13px;font-weight:600;
      color:${i===S.semIdx?'#fff':'var(--t3)'};
      cursor:pointer;font-family:Inter,sans-serif;
      box-shadow:${i===S.semIdx?'0 0 14px rgba(10,132,255,.4)':'none'};
      transition:all .15s;white-space:nowrap;
    ">${s.label}${s.active?' 🔴':''}</button>
  `).join('');

  let html=`
  <!-- Semester Tabs -->
  <div style="display:flex;gap:7px;overflow-x:auto;padding-bottom:4px;
    margin-bottom:14px;scrollbar-width:none;">
    ${semTabs}
  </div>

  <div class="card" style="margin-bottom:14px">
    <div class="cpd" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <div class="ctitle" style="margin-bottom:4px">GPA · ${sem?sem.id:''}</div>
        <div style="font-size:42px;font-weight:900;letter-spacing:-1.5px;
          background:linear-gradient(135deg,#0a84ff,#5e5ce6);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent">${gpa}</div>
      </div>
      <div style="text-align:right">
        <div class="ctitle" style="margin-bottom:4px">Fanlar</div>
        <div style="font-size:42px;font-weight:900">${grades.length}</div>
      </div>
    </div>
    <div class="csep"></div>
    <div style="display:flex;gap:18px;padding:10px 16px;font-size:11px;color:var(--t3)">
      <span><span style="color:var(--accent)">■</span> Joriy /20</span>
      <span><span style="color:var(--purple)">■</span> Oraliq /30</span>
      <span><span style="color:var(--green)">■</span> Yakuniy /50</span>
    </div>
  </div>`;

  grades.forEach((g,i)=>{
    const cp=g.cur!==null?(g.cur/20)*100:0;
    const mp=g.mid!==null?(g.mid/30)*100:0;
    const fp=g.fin!==null?(g.fin/50)*100:0;
    const lt=letter(g.fin!==null?g.tot:null);
    const attPct=g.hrs>0?Math.round((g.hrs-g.miss)/g.hrs*100):100;

    html+=`
    <div class="card" style="border-color:${g.risk?'rgba(255,69,58,.3)':g.nb?'rgba(255,159,10,.2)':'transparent'}">
      <div class="grade-wrap">
        <div class="g-name">${g.s}</div>
        <div class="g-meta">${g.hrs} soat · ${g.miss} o'tkazildi · Davomat ${attPct}%</div>
        <div class="g-total" style="color:${totalColor(g.tot)}">${g.tot}</div>
        <div class="bars">
          <div class="bar-r">
            <div class="bar-l">Joriy</div>
            <div class="bar-t"><div class="bar-f" style="width:${cp}%;background:var(--accent)"></div></div>
            <div class="bar-v">${g.cur??'—'}/20</div>
          </div>
          <div class="bar-r">
            <div class="bar-l">Oraliq</div>
            <div class="bar-t"><div class="bar-f" style="width:${mp}%;background:var(--purple)"></div></div>
            <div class="bar-v">${g.mid??'—'}/30</div>
          </div>
          <div class="bar-r">
            <div class="bar-l">Yakuniy</div>
            <div class="bar-t"><div class="bar-f" style="width:${fp}%;background:var(--green)"></div></div>
            <div class="bar-v">${g.fin??'—'}/50</div>
          </div>
        </div>
        <div class="att-row">
          <div class="att-t">Davomat</div>
          <div class="att-bar"><div class="att-fill" style="width:${attPct}%;background:${attPct>=80?'var(--green)':attPct>=60?'var(--orange)':'var(--red)'}"></div></div>
          <div class="att-pct">${attPct}%</div>
        </div>
        <div class="tags">
          ${lt?`<span class="tag ${lt==='A'?'t-green':lt==='B'?'t-blue':lt==='C'?'t-orange':'t-red'}">${lt}</span>`:''}
          ${g.fin===null?'<span class="tag t-gray">Jarayon</span>':'<span class="tag t-gray">Yakunlangan</span>'}
          ${S.isPremium&&g.need?`<span class="tag t-orange">Yakuniyda ${g.need}/50 kerak</span>`:''}
          ${attPct<80?'<span class="tag t-red">NB xavf</span>':''}
        </div>
      </div>
      ${g.risk?`<div class="risk-strip"><span>⚠️</span><span>O'tish uchun yakuniyda <b>${g.need}/50</b> kerak</span></div>`:''}
      ${g.nb&&!g.risk?`<div class="nb-strip"><span>📍</span><span>Davomat 20% chegarasiga yaqin!</span></div>`:''}
    </div>`;
  });

  if(!S.isPremium){
    html+=`
    <div class="lock-card">
      <div class="lock-ic">🔒</div>
      <div class="lock-t">Premium Analitika</div>
      <div class="lock-d">Maqsad ball hisob-kitobi, GPA prognozi, batafsil tahlil.</div>
      <button class="btn-primary" onclick="toast('Tez kunda!','info')">👑 Premium — 5,000 so'm/oy</button>
    </div>`;
  }

  document.getElementById('grades-inner').innerHTML=html;
}

function selectSem(idx){
  S.semIdx=idx;
  renderGrades();
  tg?.HapticFeedback?.selectionChanged();
  // Scroll to top
  document.getElementById('v-grades').scrollTop=0;
}

// ══════════════════════════════════════════════════════
// TIMETABLE
// ══════════════════════════════════════════════════════
function renderTimetable(){
  const mon=monday(S.weekOff);
  const todayIso=today();
  const days=Array.from({length:6},(_,i)=>{
    const d=new Date(mon); d.setDate(d.getDate()+i);
    const di=iso(d);
    return {i,di,short:DU[i],isToday:di===todayIso,has:!!(D.tt[di]?.length)};
  });
  const endD=new Date(mon); endD.setDate(endD.getDate()+5);
  const wlbl=fmt(mon)+' – '+fmt(endD)+' · '+mon.getFullYear();
  const curDay=days[Math.min(S.dayIdx,days.length-1)];
  const lessons=D.tt[curDay.di]||[];

  let html=`
  <div class="week-nav">
    <button class="wbtn" onclick="changeWeek(-1)">‹</button>
    <div class="wlbl">${wlbl}</div>
    <button class="wbtn" onclick="changeWeek(1)">›</button>
  </div>
  <div class="dtabs">
    ${days.map(d=>`
      <button class="dtab ${d.i===S.dayIdx?'active':''} ${d.isToday&&d.i!==S.dayIdx?'today':''}"
              onclick="selectDay(${d.i},'${d.di}')">
        ${d.short}${d.has&&d.i!==S.dayIdx?'<span class="dot"></span>':''}
      </button>`).join('')}
  </div>
  <div class="card" id="ll-card">`;

  if(lessons.length===0){
    html+=`<div class="no-lesson">
      <div class="no-lesson-ic">🏖️</div>
      <div class="no-lesson-t">Bu kuni darslar yo'q</div>
      <div class="no-lesson-s">Dam oling!</div>
    </div>`;
  } else {
    lessons.forEach((l,i)=>{
      const cl=CL[i%CL.length];
      html+=`<div class="lrow" style="${i>0?'border-top:.5px solid var(--sep)':''}">
        <div class="lnum-col">
          <div class="lnum" style="background:${cl}22;color:${cl}">${l.n}</div>
          <div class="ltmini">${l.st}<br>${l.en}</div>
        </div>
        <div class="lbody">
          <div class="lsubj">${l.s}</div>
          <div class="lmeta">
            <span class="lmi">📍 ${l.r}</span>
            <span class="lmi">👤 ${l.tc}</span>
            <span class="tag t-gray" style="font-size:10px">${l.tp}</span>
          </div>
        </div>
      </div>`;
    });
  }
  html+=`</div>`;

  const total=days.reduce((s,d)=>{const ls=D.tt[d.di];return s+(ls?ls.length:0);},0);
  if(total>0){
    html+=`<div class="card"><div class="cpd">
      <div class="ctitle">Bu hafta</div>
      <div style="display:flex;gap:10px">
        <div class="stat-c" style="background:rgba(10,132,255,.1);border-color:rgba(10,132,255,.2)">
          <div class="sv v-blue">${total}</div>
          <div class="sl">Jami dars</div>
        </div>
        ${days.filter(d=>D.tt[d.di]?.length).map(d=>`
          <div class="stat-c">
            <div class="sv" style="font-size:18px">${D.tt[d.di].length}</div>
            <div class="sl">${d.short}</div>
          </div>`).join('')}
      </div>
    </div></div>`;
  }

  document.getElementById('tt-inner').innerHTML=html;
}

function changeWeek(d){
  S.weekOff+=d;
  S.dayIdx=d>0?0:4;
  renderTimetable();
  haptic('light');
}

function selectDay(idx,di){
  S.dayIdx=idx;
  document.querySelectorAll('.dtab').forEach((b,i)=>{
    b.classList.toggle('active',i===idx);
    b.classList.toggle('today',b.classList.contains('today')&&i!==idx);
  });
  const lessons=D.tt[di]||[];
  const card=document.getElementById('ll-card');
  if(!card) return;
  if(lessons.length===0){
    card.innerHTML=`<div class="no-lesson"><div class="no-lesson-ic">🏖️</div><div class="no-lesson-t">Bu kuni darslar yo'q</div></div>`;
  } else {
    card.innerHTML=lessons.map((l,i)=>{
      const cl=CL[i%CL.length];
      return `<div class="lrow" style="${i>0?'border-top:.5px solid var(--sep)':''}">
        <div class="lnum-col">
          <div class="lnum" style="background:${cl}22;color:${cl}">${l.n}</div>
          <div class="ltmini">${l.st}<br>${l.en}</div>
        </div>
        <div class="lbody">
          <div class="lsubj">${l.s}</div>
          <div class="lmeta">
            <span class="lmi">📍 ${l.r}</span>
            <span class="lmi">👤 ${l.tc}</span>
            <span class="tag t-gray" style="font-size:10px">${l.tp}</span>
          </div>
        </div>
      </div>`;
    }).join('');
  }
  haptic('light');
}

// ══════════════════════════════════════════════════════
// NAVIGATOR
// ══════════════════════════════════════════════════════
function renderNavigator(){
  let html=`
  <div class="nav-segs">
    <button class="nseg ${S.navTab==='rooms'?'active':''}" onclick="switchNavTab('rooms')">🏛️ Xonalar</button>
    <button class="nseg ${S.navTab==='teachers'?'active':''}" onclick="switchNavTab('teachers')">👨‍🏫 O'qituvchilar</button>
  </div>
  <div class="search-b">
    <span class="si">🔍</span>
    <input class="sinput" id="nsearch"
      placeholder="${S.navTab==='rooms'?'A-301, kompyuter lab...':'O\'qituvchi ismi...'}"
      oninput="filterNav(this.value)">
  </div>
  <div id="nlist">${buildNavList('')}</div>`;
  document.getElementById('nav-inner').innerHTML=html;
}

function switchNavTab(tab){
  S.navTab=tab;
  document.querySelectorAll('.nseg').forEach((b,i)=>{
    b.classList.toggle('active',['rooms','teachers'][i]===tab);
  });
  const inp=document.getElementById('nsearch');
  inp.value='';
  inp.placeholder=tab==='rooms'?'A-301, kompyuter lab...':'O\'qituvchi ismi...';
  document.getElementById('nlist').innerHTML=buildNavList('');
  haptic('light');
}

function buildNavList(q){
  if(S.navTab==='rooms'){
    let rooms=D.rooms.filter(r=>!q||
      r.c.toLowerCase().includes(q.toLowerCase())||
      r.t.toLowerCase().includes(q.toLowerCase())||
      r.b.toLowerCase().includes(q.toLowerCase())
    );
    if(!rooms.length) return '<div style="text-align:center;padding:40px;color:var(--t4)">🔍 Topilmadi</div>';
    const byB={};
    rooms.forEach(r=>{ byB[r.b]=byB[r.b]||[]; byB[r.b].push(r); });
    return Object.entries(byB).map(([b,rs])=>`
      <div style="font-size:12px;font-weight:700;color:var(--t3);
        text-transform:uppercase;letter-spacing:.5px;margin:4px 0 8px">${b}</div>
      <div class="card" style="margin-bottom:12px">
        ${rs.map((r,i)=>`
          <div class="room-r" style="${i>0?'border-top:.5px solid var(--sep)':''}">
            <div class="rcode">${r.c}</div>
            <div class="rinfo">
              <div class="rname">${r.t}</div>
              <div class="rmeta">${r.f}-qavat · ${r.cap} o'rin</div>
            </div>
            <div class="rtag">${r.f}Q</div>
          </div>`).join('')}
      </div>`).join('');
  } else {
    if(!S.isPremium) return `
      <div class="lock-card">
        <div class="lock-ic">🔒</div>
        <div class="lock-t">O'qituvchi Tracker</div>
        <div class="lock-d">O'qituvchilar hozir qayerda ekanligini real vaqtda kuzating. Premium bilan mavjud.</div>
        <button class="btn-primary" onclick="toast('Tez kunda!','info')">👑 Premium olish</button>
      </div>`;
    const teachers=D.teachers.filter(t=>!q||t.n.toLowerCase().includes(q.toLowerCase()));
    if(!teachers.length) return '<div style="text-align:center;padding:40px;color:var(--t4)">🔍 Topilmadi</div>';
    return `<div class="card">
      ${teachers.map((t,i)=>`
        <div class="teacher-r" style="${i>0?'border-top:.5px solid var(--sep)':''}">
          <div class="tav">${t.n.split(' ').map(x=>x[0]).slice(0,2).join('')}</div>
          <div>
            <div style="font-size:14px;font-weight:600">${t.n}</div>
            <div style="font-size:12px;color:var(--t3);margin-top:2px">${t.d}</div>
            ${t.online&&t.r
              ?`<div class="tloc-on"><span style="font-size:8px">🟢</span> ${t.r} — hozir shu yerda</div>`
              :`<div class="tloc-off">⚫ Joylashuv noma'lum</div>`}
          </div>
        </div>`).join('')}
    </div>`;
  }
}

function filterNav(q){
  document.getElementById('nlist').innerHTML=buildNavList(q);
}

// ─── Boot ─────────────────────────────────────────────
(function(){
  initTopbar();
  setTimeout(()=>renderHome(), 100);
})();
</script>
</body>
</html>"""

_bot_task = None

async def run_bot_async():
    if not config.BOT_TOKEN:
        print("BOT_TOKEN yo'q!")
        return
    from bot import create_bot, create_dispatcher
    bot = create_bot()
    dp  = create_dispatcher()
    print("Bot polling boshlandi...")
    try:
        await dp.start_polling(bot, allowed_updates=["message","callback_query"])
    except Exception as e:
        print("Bot xatosi: " + str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database tayyor")
    global _bot_task
    if config.BOT_TOKEN:
        _bot_task = asyncio.create_task(run_bot_async())
        print("Bot task boshlandi")
    yield
    if _bot_task:
        _bot_task.cancel()
        try: await _bot_task
        except asyncio.CancelledError: pass

app = FastAPI(title="HELPER TDIU", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status":"ok","app":"HELPER TDIU","version":"3.0.0"}

@app.get("/health")
async def health():
    return {"status":"ok"}

@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    return MINI_APP_HTML


# ════════════════════════════════════════════════════════
# REST API — Mini App uchun
# ════════════════════════════════════════════════════════

from fastapi import Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from database import AsyncSessionFactory, User, SubscriptionTier
from scraper import HemisScraper, HemisAuthError
from analyzer import analyze, risk_text_uz
from crypto import encrypt, decrypt
import json as _json

class HemisConnectRequest(BaseModel):
    hemis_id: str
    password: str
    telegram_id: int

class DemoRequest(BaseModel):
    telegram_id: int


@app.post("/api/connect-hemis")
async def api_connect_hemis(body: HemisConnectRequest):
    """
    Hemis ID va parolni tekshiradi.
    Muvaffaqiyatli bo'lsa DB ga saqlaydi.
    """
    enc_pass = encrypt(body.password)

    try:
        async with HemisScraper(
            user_id=body.telegram_id,
            hemis_id=body.hemis_id,
            enc_password=enc_pass,
            demo=False,
        ) as sc:
            await sc.ensure_login()
            profile = await sc.fetch_profile()
            cookies = await sc.get_cookies_dict()

    except HemisAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Hemis ga ulanib bolmadi: {e}")

    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == body.telegram_id))
        user = res.scalars().first()
        if not user:
            user = User(id=body.telegram_id)
            db.add(user)
        user.hemis_id = body.hemis_id
        user.hemis_password_enc = enc_pass
        user.is_demo = False
        if profile.full_name and profile.full_name != "Noma'lum":
            user.full_name = profile.full_name
        await db.commit()

    return {
        "success": True,
        "profile": {
            "full_name": profile.full_name,
            "group":     profile.group,
            "faculty":   profile.faculty,
            "semester":  profile.semester,
            "gpa":       profile.gpa,
        }
    }


@app.post("/api/demo")
async def api_demo(body: DemoRequest):
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == body.telegram_id))
        user = res.scalars().first()
        if not user:
            user = User(id=body.telegram_id, is_demo=True)
            db.add(user)
        else:
            user.is_demo = True
        await db.commit()
    return {"success": True}


@app.get("/api/grades/{telegram_id}")
async def api_grades(telegram_id: int, semester: str = ""):
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == telegram_id))
        user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    try:
        async with HemisScraper(
            telegram_id, user.hemis_id, user.hemis_password_enc,
            demo=user.is_demo
        ) as sc:
            await sc.ensure_login()
            grades   = await sc.fetch_grades(semester)
            semesters = await sc.fetch_semesters()
    except HemisAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    analyses = [analyze(g.subject, g.current, g.midterm, g.final,
                        g.total_hours, g.missed, g.semester) for g in grades]
    gpa_sum = sum(a.total for a in analyses if a.total) or 0
    gpa_cnt = sum(1 for a in analyses if a.total)

    return {
        "gpa": round(gpa_sum / gpa_cnt / 25, 2) if gpa_cnt else None,
        "semester": semester,
        "semesters": semesters,
        "grades": [
            {
                "subject":      g.subject,
                "current":      g.current,
                "midterm":      g.midterm,
                "final":        g.final,
                "total":        a.total,
                "total_hours":  g.total_hours,
                "missed":       g.missed,
                "fail_risk":    a.fail_risk,
                "nb_warning":   a.nb_warning,
                "needed_final": a.needed_final,
                "attendance":   a.attendance_pct,
                "letter":       a.letter,
            }
            for g, a in zip(grades, analyses)
        ]
    }


@app.get("/api/schedule/{telegram_id}")
async def api_schedule(telegram_id: int, week: str = ""):
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == telegram_id))
        user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    from datetime import date
    target = date.today()
    if week:
        try:
            target = date.fromisoformat(week)
        except Exception:
            pass

    try:
        async with HemisScraper(
            telegram_id, user.hemis_id, user.hemis_password_enc,
            demo=user.is_demo
        ) as sc:
            await sc.ensure_login()
            lessons = await sc.fetch_schedule(target)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    by_date: dict = {}
    for l in lessons:
        by_date.setdefault(l.date, []).append({
            "num": l.num, "start": l.start, "end": l.end,
            "subject": l.subject, "type": l.s_type,
            "teacher": l.teacher, "room": l.room, "building": l.building,
        })

    return {"week": target.isoformat(), "days": by_date}


# ── Login forma inspektori ─────────────────────────────────────
@app.get("/api/inspect-login")
async def inspect_login():
    """
    talaba.tsue.uz login forma tuzilmasini ko'rish.
    Brauzerda: https://your-app.railway.app/api/inspect-login
    """
    from scraper import HemisScraper
    async with HemisScraper(0, "", None, demo=False) as sc:
        info = await sc.inspect_login_form()
    return info


# ── Debug endpoint (faqat development uchun) ──────────────────
@app.get("/api/debug-hemis/{telegram_id}")
async def debug_hemis(telegram_id: int, path: str = "/dashboard"):
    """
    Real Hemis HTML strukturasini ko'rish uchun.
    Browser da: https://your-app.railway.app/api/debug-hemis/YOUR_TG_ID?path=/student/performance
    """
    async with AsyncSessionFactory() as db:
        res = await db.execute(select(User).where(User.id == telegram_id))
        user = res.scalars().first()

    if not user or not user.hemis_id:
        return {"error": "Foydalanuvchi yoki Hemis ID topilmadi"}

    try:
        async with HemisScraper(
            telegram_id, user.hemis_id, user.hemis_password_enc, demo=False
        ) as sc:
            await sc.ensure_login()
            html = await sc.fetch_raw_html(path)

        # HTML ni analiz qilamiz
        soup = BeautifulSoup(html, "html.parser")
        from fastapi.responses import JSONResponse

        tables = []
        for t in soup.find_all("table")[:5]:
            rows = []
            for row in t.find_all("tr")[:5]:
                rows.append([td.get_text(strip=True)[:50] for td in row.find_all(["td","th"])])
            tables.append(rows)

        return JSONResponse({
            "url_fetched": path,
            "title": soup.title.string if soup.title else "",
            "headings": [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3"])[:10]],
            "tables_found": len(soup.find_all("table")),
            "table_preview": tables,
            "forms": [{"action": f.get("action"), "fields": [i.get("name") for i in f.find_all("input")]}
                      for f in soup.find_all("form")[:3]],
            "raw_html_snippet": html[:3000],
        })
    except Exception as e:
        return {"error": str(e)}


from bs4 import BeautifulSoup
