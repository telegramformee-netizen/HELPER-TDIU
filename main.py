"""
main.py - HELPER TDIU — FastAPI + aiogram bot
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import config
from database import init_db

# ══════════════════════════════════════════════════════════════
# MINI APP HTML — Apple-style dizayn
# ══════════════════════════════════════════════════════════════
MINI_APP_HTML = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #000000;
  --bg2:     #1c1c1e;
  --bg3:     #2c2c2e;
  --bg4:     #3a3a3c;
  --text:    #ffffff;
  --text2:   #ebebf5cc;
  --text3:   #ebebf599;
  --text4:   #ebebf560;
  --accent:  #0a84ff;
  --green:   #30d158;
  --orange:  #ff9f0a;
  --red:     #ff453a;
  --yellow:  #ffd60a;
  --purple:  #bf5af2;
  --sep:     rgba(255,255,255,0.08);
  --card-bg: #1c1c1e;
  --nav-h:   83px;
  --top-h:   56px;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'SF Pro Display',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}

/* ── Scrollable area ── */
.view{
  position:fixed;top:var(--top-h);left:0;right:0;
  bottom:var(--nav-h);
  overflow-y:auto;
  overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;
}
.view::-webkit-scrollbar{display:none}
.view-inner{padding:12px 16px 20px}

/* ── Topbar ── */
.topbar{
  position:fixed;top:0;left:0;right:0;height:var(--top-h);
  background:rgba(0,0,0,0.85);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:0.5px solid var(--sep);
  display:flex;align-items:center;padding:0 20px;
  z-index:100;
}
.topbar-logo{
  width:34px;height:34px;border-radius:9px;
  background:linear-gradient(135deg,#0a84ff,#5e5ce6);
  display:flex;align-items:center;justify-content:center;
  font-size:17px;font-weight:800;color:#fff;margin-right:11px;
  box-shadow:0 2px 8px rgba(10,132,255,0.4);
}
.topbar-name{font-size:16px;font-weight:700;letter-spacing:-0.3px}
.topbar-group{font-size:12px;color:var(--text3);margin-top:1px}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.badge-premium{
  background:linear-gradient(135deg,#ff9f0a,#ff6b00);
  color:#fff;font-size:10px;font-weight:700;
  padding:3px 9px;border-radius:20px;letter-spacing:0.3px;
}
.badge-demo{
  background:var(--bg3);color:var(--text3);
  font-size:10px;font-weight:600;
  padding:3px 9px;border-radius:20px;
  border:0.5px solid var(--sep);
}
.badge-gpa{
  font-family:'Inter',sans-serif;
  font-size:14px;font-weight:700;color:var(--accent);
}

/* ── Bottom Nav ── */
.bottom-nav{
  position:fixed;bottom:0;left:0;right:0;
  height:var(--nav-h);
  background:rgba(0,0,0,0.85);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-top:0.5px solid var(--sep);
  display:flex;align-items:flex-start;padding-top:10px;
  z-index:100;
}
.nav-item{
  flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
  background:none;border:none;cursor:pointer;
  color:var(--text4);transition:color 0.2s;
  padding:0 4px;position:relative;
}
.nav-item.active{color:var(--accent)}
.nav-icon{font-size:24px;line-height:1}
.nav-label{font-size:10px;font-weight:500;letter-spacing:0.1px}

/* ── Cards ── */
.card{
  background:var(--card-bg);
  border-radius:16px;
  overflow:hidden;
  margin-bottom:12px;
}
.card-section{padding:16px}
.card-title{
  font-size:13px;font-weight:600;color:var(--text3);
  text-transform:uppercase;letter-spacing:0.5px;
  margin-bottom:14px;
}
.sep-line{height:0.5px;background:var(--sep);margin:0 16px}

/* ── GPA Hero ── */
.gpa-hero{
  background:linear-gradient(160deg,#0a1628 0%,#001429 50%,#000d1f 100%);
  border-radius:20px;
  padding:24px 20px;
  margin-bottom:12px;
  position:relative;overflow:hidden;
  border:0.5px solid rgba(10,132,255,0.2);
}
.gpa-hero::before{
  content:'';position:absolute;top:-60px;right:-60px;
  width:200px;height:200px;
  background:radial-gradient(circle,rgba(10,132,255,0.12),transparent 70%);
}
.gpa-hero-label{font-size:12px;font-weight:600;color:rgba(10,132,255,0.8);
  text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.gpa-hero-value{
  font-size:64px;font-weight:800;
  background:linear-gradient(135deg,#0a84ff,#5e5ce6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  line-height:1;letter-spacing:-2px;margin-bottom:8px;
}
.gpa-hero-sub{font-size:13px;color:var(--text3)}
.gpa-hero-name{font-size:15px;font-weight:600;color:var(--text);margin-top:10px}

/* ── Stat Row ── */
.stat-row{display:flex;gap:10px;margin-bottom:12px}
.stat-card{
  flex:1;background:var(--card-bg);border-radius:16px;
  padding:14px 12px;
}
.stat-value{font-size:28px;font-weight:800;line-height:1;margin-bottom:4px}
.stat-label{font-size:11px;color:var(--text3);font-weight:500}
.stat-sub{font-size:10px;color:var(--text4);margin-top:2px}
.v-blue{color:var(--accent)}
.v-green{color:var(--green)}
.v-orange{color:var(--orange)}
.v-red{color:var(--red)}
.v-purple{color:var(--purple)}

/* ── Alert ── */
.alert{
  display:flex;align-items:flex-start;gap:10px;
  padding:13px 14px;border-radius:13px;
  margin-bottom:8px;font-size:13px;line-height:1.5;
}
.alert-icon{font-size:17px;flex-shrink:0;margin-top:1px}
.alert b{font-weight:600}
.alert.danger{background:rgba(255,69,58,0.1);border:0.5px solid rgba(255,69,58,0.25)}
.alert.warn{background:rgba(255,159,10,0.1);border:0.5px solid rgba(255,159,10,0.25)}
.alert.info{background:rgba(10,132,255,0.1);border:0.5px solid rgba(10,132,255,0.2)}
.alert.success{background:rgba(48,209,88,0.1);border:0.5px solid rgba(48,209,88,0.2)}

/* ── Today Strip ── */
.today-scroll{
  display:flex;gap:10px;
  overflow-x:auto;padding-bottom:4px;
  margin:-4px -16px;padding:4px 16px 10px;
  scrollbar-width:none;
}
.today-scroll::-webkit-scrollbar{display:none}
.lesson-chip{
  flex-shrink:0;
  background:var(--bg3);border-radius:14px;
  padding:12px 14px;min-width:150px;
  border:0.5px solid var(--sep);
}
.chip-num{
  font-size:10px;font-weight:700;color:var(--accent);
  text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;
}
.chip-time{font-size:12px;color:var(--text3);margin-bottom:6px}
.chip-subj{font-size:13px;font-weight:600;line-height:1.3;margin-bottom:4px}
.chip-room{font-size:11px;color:var(--text4)}

/* ── Section header ── */
.section-header{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:10px;margin-top:4px;
}
.section-title{font-size:20px;font-weight:700;letter-spacing:-0.3px}
.section-more{font-size:14px;color:var(--accent);font-weight:500;cursor:pointer}

/* ── Grade Card ── */
.grade-item{padding:14px 16px;position:relative}
.grade-name{font-size:15px;font-weight:600;margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:60px}
.grade-meta{font-size:12px;color:var(--text3);margin-bottom:10px}
.grade-total{
  position:absolute;top:14px;right:16px;
  font-size:22px;font-weight:800;
}
.grade-bars{display:flex;flex-direction:column;gap:5px}
.bar-row{display:flex;align-items:center;gap:8px}
.bar-label{font-size:11px;color:var(--text4);width:48px;flex-shrink:0;font-weight:500}
.bar-track{flex:1;height:4px;background:var(--bg4);border-radius:99px;overflow:hidden}
.bar-fill{height:100%;border-radius:99px;transition:width 0.7s cubic-bezier(.34,1.56,.64,1)}
.bar-val{font-size:11px;color:var(--text3);width:32px;text-align:right;flex-shrink:0}
.grade-tags{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.tag{
  font-size:11px;font-weight:600;padding:3px 9px;border-radius:99px;
}
.tag-blue{background:rgba(10,132,255,0.15);color:var(--accent)}
.tag-green{background:rgba(48,209,88,0.15);color:var(--green)}
.tag-orange{background:rgba(255,159,10,0.15);color:var(--orange)}
.tag-red{background:rgba(255,69,58,0.15);color:var(--red)}
.tag-gray{background:var(--bg3);color:var(--text3)}
.tag-purple{background:rgba(191,90,242,0.15);color:var(--purple)}
.risk-strip{
  display:flex;align-items:center;gap:6px;
  background:rgba(255,69,58,0.08);
  border-top:0.5px solid rgba(255,69,58,0.15);
  padding:8px 16px;
  font-size:12px;color:#ff6b63;
}
.nb-strip{
  display:flex;align-items:center;gap:6px;
  background:rgba(255,159,10,0.08);
  border-top:0.5px solid rgba(255,159,10,0.15);
  padding:8px 16px;
  font-size:12px;color:#ff9f0a;
}

/* ── Timetable ── */
.week-nav{
  display:flex;align-items:center;gap:8px;margin-bottom:14px;
}
.week-btn{
  width:36px;height:36px;border-radius:10px;
  background:var(--bg3);border:none;cursor:pointer;
  color:var(--text);font-size:16px;
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;
}
.week-label{flex:1;text-align:center;font-size:13px;font-weight:600;color:var(--text2)}
.day-tabs{
  display:flex;gap:6px;overflow-x:auto;
  padding-bottom:2px;margin-bottom:14px;
  scrollbar-width:none;
}
.day-tabs::-webkit-scrollbar{display:none}
.day-tab{
  flex-shrink:0;padding:7px 14px;
  background:var(--bg3);border:none;border-radius:99px;
  font-size:13px;font-weight:600;color:var(--text3);
  cursor:pointer;transition:all 0.15s;
  font-family:'Inter',sans-serif;
}
.day-tab.active{background:var(--accent);color:#fff}
.day-tab.today{border:1.5px solid var(--accent);color:var(--accent);background:rgba(10,132,255,0.1)}
.lesson-row{
  display:flex;gap:12px;align-items:flex-start;
  padding:14px 16px;
}
.lesson-num-wrap{
  width:36px;flex-shrink:0;
  display:flex;flex-direction:column;align-items:center;gap:2px;
}
.lesson-num-circle{
  width:32px;height:32px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:700;
}
.lesson-time-mini{font-size:9px;color:var(--text4);text-align:center;line-height:1.3}
.lesson-body{flex:1}
.lesson-subject{font-size:14px;font-weight:600;margin-bottom:5px;line-height:1.3}
.lesson-details{display:flex;flex-wrap:wrap;gap:8px;font-size:12px;color:var(--text3)}
.lesson-detail{display:flex;align-items:center;gap:3px}
.no-lessons{
  text-align:center;padding:48px 20px;
  color:var(--text4);
}
.no-lessons-icon{font-size:52px;margin-bottom:12px}
.no-lessons-text{font-size:15px;font-weight:500}
.no-lessons-sub{font-size:13px;margin-top:4px}

/* ── Navigator ── */
.nav-tabs-row{display:flex;gap:8px;margin-bottom:14px}
.nav-seg-btn{
  flex:1;padding:11px;
  background:var(--bg3);
  border:1.5px solid transparent;
  border-radius:12px;font-size:13px;font-weight:600;
  color:var(--text3);cursor:pointer;transition:all 0.15s;
  font-family:'Inter',sans-serif;
}
.nav-seg-btn.active{
  background:rgba(10,132,255,0.1);
  border-color:var(--accent);color:var(--accent);
}
.search-wrap{
  display:flex;align-items:center;gap:10px;
  background:var(--bg3);border-radius:12px;
  padding:11px 14px;margin-bottom:12px;
  border:0.5px solid var(--sep);
}
.search-icon{font-size:16px;color:var(--text4)}
.search-input{
  background:none;border:none;outline:none;
  color:var(--text);font-size:14px;flex:1;
  font-family:'Inter',sans-serif;
}
.search-input::placeholder{color:var(--text4)}
.room-row{
  display:flex;align-items:center;gap:14px;
  padding:13px 16px;
}
.room-code{
  font-size:16px;font-weight:700;color:var(--accent);
  width:56px;flex-shrink:0;
}
.room-info{flex:1}
.room-name{font-size:14px;font-weight:500}
.room-meta{font-size:12px;color:var(--text3);margin-top:2px}
.room-tag{
  background:var(--bg3);color:var(--text3);
  font-size:10px;font-weight:600;
  padding:3px 8px;border-radius:6px;
}
.teacher-row{
  display:flex;align-items:center;gap:14px;
  padding:13px 16px;
}
.teacher-avatar{
  width:42px;height:42px;border-radius:13px;
  background:linear-gradient(135deg,var(--bg3),var(--bg4));
  display:flex;align-items:center;justify-content:center;
  font-size:17px;flex-shrink:0;
}
.teacher-name{font-size:14px;font-weight:600}
.teacher-dept{font-size:12px;color:var(--text3);margin-top:2px}
.teacher-loc{display:flex;align-items:center;gap:4px;font-size:12px;margin-top:4px}
.loc-online{color:var(--green)}
.loc-offline{color:var(--text4)}

/* ── Lock premium ── */
.lock-card{
  background:linear-gradient(135deg,#0a1628,#001429);
  border:0.5px solid rgba(10,132,255,0.2);
  border-radius:16px;padding:24px 20px;text-align:center;margin-bottom:12px;
}
.lock-icon{font-size:40px;margin-bottom:12px}
.lock-title{font-size:17px;font-weight:700;margin-bottom:8px}
.lock-desc{font-size:13px;color:var(--text3);line-height:1.6;margin-bottom:16px}
.btn-primary{
  display:block;width:100%;
  background:var(--accent);color:#fff;
  font-family:'Inter',sans-serif;
  font-size:15px;font-weight:600;
  padding:14px;border:none;border-radius:12px;
  cursor:pointer;transition:opacity 0.15s;
}
.btn-primary:active{opacity:0.8}

/* ── Skeleton ── */
.skel{
  background:linear-gradient(90deg,var(--bg3) 25%,var(--bg4) 50%,var(--bg3) 75%);
  background-size:200% 100%;
  animation:shimmer 1.3s infinite;
  border-radius:10px;
}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ── Toast ── */
#toasts{
  position:fixed;bottom:calc(var(--nav-h) + 12px);
  left:16px;right:16px;z-index:999;
  display:flex;flex-direction:column;gap:8px;pointer-events:none;
}
.toast{
  background:rgba(44,44,46,0.95);
  backdrop-filter:blur(20px);
  border:0.5px solid var(--sep);
  border-radius:13px;padding:13px 16px;
  font-size:13px;display:flex;align-items:center;gap:10px;
  pointer-events:all;
  animation:toastIn 0.3s cubic-bezier(.34,1.56,.64,1);
}
.toast.hide{animation:toastOut 0.25s ease forwards}
@keyframes toastIn{from{opacity:0;transform:translateY(10px) scale(.96)}to{opacity:1;transform:none}}
@keyframes toastOut{to{opacity:0;transform:translateY(6px)}}
</style>
</head>
<body>

<!-- Topbar -->
<header class="topbar">
  <div class="topbar-logo">H</div>
  <div>
    <div class="topbar-name">HELPER TDIU</div>
    <div class="topbar-group" id="tbar-group">Yuklanmoqda...</div>
  </div>
  <div class="topbar-right">
    <div id="tbar-gpa" class="badge-gpa" style="display:none"></div>
    <div id="badge-premium" class="badge-premium" style="display:none">PRO</div>
    <div id="badge-demo" class="badge-demo" style="display:none">DEMO</div>
  </div>
</header>

<!-- Views -->
<div class="view" id="view">
  <div class="view-inner" id="view-inner">
    <div style="display:flex;flex-direction:column;gap:12px;padding-top:8px">
      <div class="skel" style="height:140px;border-radius:20px"></div>
      <div style="display:flex;gap:10px">
        <div class="skel" style="height:80px;flex:1;border-radius:16px"></div>
        <div class="skel" style="height:80px;flex:1;border-radius:16px"></div>
        <div class="skel" style="height:80px;flex:1;border-radius:16px"></div>
      </div>
      <div class="skel" style="height:200px;border-radius:16px"></div>
    </div>
  </div>
</div>

<!-- Bottom Nav -->
<nav class="bottom-nav">
  <button class="nav-item active" id="nav-home" onclick="navigate('home')">
    <span class="nav-icon">🏠</span>
    <span class="nav-label">Bosh</span>
  </button>
  <button class="nav-item" id="nav-grades" onclick="navigate('grades')">
    <span class="nav-icon">📊</span>
    <span class="nav-label">Baholar</span>
  </button>
  <button class="nav-item" id="nav-timetable" onclick="navigate('timetable')">
    <span class="nav-icon">📅</span>
    <span class="nav-label">Jadval</span>
  </button>
  <button class="nav-item" id="nav-navigator" onclick="navigate('navigator')">
    <span class="nav-icon">🗺️</span>
    <span class="nav-label">Navigator</span>
  </button>
</nav>

<!-- Toasts -->
<div id="toasts"></div>

<script>
// ── Telegram WebApp ──────────────────────────────────────────
const tg = window.Telegram?.WebApp;
tg?.expand();
tg?.disableVerticalSwipes?.();

// ── State ────────────────────────────────────────────────────
const S = {
  view: 'home',
  isPremium: false,
  isDemo: true,
  profile: null,
  grades: null,
  timetable: null,
  curWeekOff: 0,
  curDayIdx: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1,
  navTab: 'rooms',
};

// ── Demo Data ────────────────────────────────────────────────
const DEMO = {
  profile: {
    full_name: "Demo Talaba",
    group: "IQ-22-01",
    faculty: "Iqtisodiyot",
    semester: "2024-2",
    gpa: 3.45
  },
  grades: [
    {s:"Mikroiqtisodiyot",cur:17,mid:24,fin:null,tot:41,risk:false,nb:false,needed:14,hrs:64,miss:4},
    {s:"Bank ishi va kredit",cur:15,mid:22,fin:null,tot:37,risk:false,nb:true,needed:18,hrs:72,miss:15},
    {s:"Iqtisodiy siyosat",cur:18,mid:28,fin:null,tot:46,risk:false,nb:false,needed:9,hrs:80,miss:2},
    {s:"Pul va kredit",cur:12,mid:18,fin:null,tot:30,risk:true,nb:true,needed:25,hrs:64,miss:14},
    {s:"Marketing asoslari",cur:19,mid:26,fin:null,tot:45,risk:false,nb:false,needed:10,hrs:72,miss:0},
  ],
  timetable: {
    "2025-04-07":[
      {num:1,start:"08:30",end:"09:50",s:"Mikroiqtisodiyot",type:"Ma'ruza",teacher:"Salimov B.",room:"A-301",building:"A blok"},
      {num:3,start:"11:30",end:"12:50",s:"Bank ishi",type:"Seminar",teacher:"Rahimov N.",room:"B-204",building:"B blok"},
    ],
    "2025-04-08":[
      {num:2,start:"10:00",end:"11:20",s:"Pul va kredit",type:"Ma'ruza",teacher:"Hasanov M.",room:"A-101",building:"A blok"},
      {num:4,start:"13:30",end:"14:50",s:"Marketing",type:"Seminar",teacher:"Yusupov K.",room:"C-305",building:"C blok"},
    ],
    "2025-04-09":[
      {num:1,start:"08:30",end:"09:50",s:"Iqtisodiy siyosat",type:"Ma'ruza",teacher:"Toshmatov A.",room:"A-201",building:"A blok"},
    ],
    "2025-04-10":[
      {num:2,start:"10:00",end:"11:20",s:"Mikroiqtisodiyot",type:"Seminar",teacher:"Salimov B.",room:"B-102",building:"B blok"},
      {num:5,start:"15:00",end:"16:20",s:"Bank ishi",type:"Ma'ruza",teacher:"Rahimov N.",room:"A-301",building:"A blok"},
    ],
    "2025-04-11":[
      {num:3,start:"11:30",end:"12:50",s:"Marketing",type:"Ma'ruza",teacher:"Yusupov K.",room:"A-101",building:"A blok"},
    ],
  },
  rooms: [
    {code:"A-101",building:"A blok",floor:1,cap:120,type:"Ma'ruza zali"},
    {code:"A-201",building:"A blok",floor:2,cap:80,type:"Ma'ruza zali"},
    {code:"A-301",building:"A blok",floor:3,cap:100,type:"Ma'ruza zali"},
    {code:"A-305",building:"A blok",floor:3,cap:40,type:"Kompyuter lab"},
    {code:"B-101",building:"B blok",floor:1,cap:50,type:"Seminar xona"},
    {code:"B-102",building:"B blok",floor:1,cap:50,type:"Seminar xona"},
    {code:"B-204",building:"B blok",floor:2,cap:30,type:"Seminar xona"},
    {code:"C-101",building:"C blok",floor:1,cap:40,type:"Kompyuter lab"},
    {code:"C-305",building:"C blok",floor:3,cap:30,type:"Seminar xona"},
    {code:"AKTOV",building:"Asosiy",floor:1,cap:500,type:"Aktov zal"},
  ],
  teachers: [
    {name:"Salimov B.A.",dept:"Mikroiqtisodiyot",room:"A-301"},
    {name:"Rahimov N.X.",dept:"Bank ishi",room:"B-204"},
    {name:"Hasanov M.T.",dept:"Pul va kredit",room:null},
    {name:"Yusupov K.O.",dept:"Marketing",room:"C-305"},
    {name:"Toshmatov A.R.",dept:"Iqtisodiy siyosat",room:null},
  ]
};

// ── Helpers ──────────────────────────────────────────────────
const DAYS_UZ = ["Du","Se","Ch","Pa","Ju","Sh","Ya"];
const DAYS_FULL = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"];
const COLORS = ["#0a84ff","#30d158","#ff9f0a","#bf5af2","#ff453a","#5e5ce6","#32ade6"];

function isoDate(d) { return d.toISOString().slice(0,10); }

function monday(weekOff=0) {
  const d = new Date();
  const off = d.getDay() === 0 ? 6 : d.getDay()-1;
  d.setDate(d.getDate() - off + weekOff*7);
  d.setHours(0,0,0,0);
  return d;
}

function toast(msg, type='info') {
  const icons = {info:'ℹ️',success:'✅',warn:'⚠️',error:'❌'};
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = '<span>' + icons[type] + '</span><span>' + msg + '</span>';
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => {
    el.classList.add('hide');
    el.addEventListener('animationend', () => el.remove());
  }, 3000);
}

function haptic(type='light') {
  tg?.HapticFeedback?.impactOccurred(type);
}

// ── Navigation ───────────────────────────────────────────────
function navigate(view) {
  S.view = view;
  document.querySelectorAll('.nav-item').forEach(b => {
    b.classList.toggle('active', b.id === 'nav-' + view);
  });
  document.getElementById('view').scrollTop = 0;
  const inner = document.getElementById('view-inner');
  inner.innerHTML = '';

  if (view === 'home')      renderHome(inner);
  else if (view === 'grades')     renderGrades(inner);
  else if (view === 'timetable')  renderTimetable(inner);
  else if (view === 'navigator')  renderNavigator(inner);

  haptic('light');
}

// ── TOPBAR UPDATE ────────────────────────────────────────────
function updateTopbar(profile, isPremium, isDemo) {
  if (profile) {
    document.getElementById('tbar-group').textContent = profile.group + ' · ' + profile.faculty;
    if (profile.gpa) {
      const el = document.getElementById('tbar-gpa');
      el.textContent = profile.gpa.toFixed(2);
      el.style.display = '';
    }
  }
  if (isPremium) document.getElementById('badge-premium').style.display = '';
  if (isDemo)    document.getElementById('badge-demo').style.display = '';
}

// ══════════════════════════════════════════════════════════════
// HOME VIEW
// ══════════════════════════════════════════════════════════════
function renderHome(c) {
  const p = DEMO.profile;
  const grades = DEMO.grades;
  const risks = grades.filter(g => g.risk).length;
  const nbs   = grades.filter(g => g.nb).length;

  // Today's lessons
  const todayIso = isoDate(new Date());
  const todayLessons = DEMO.timetable[todayIso] || [];

  const gpaVal = p.gpa ? p.gpa.toFixed(2) : '—';
  const gpaOf  = p.gpa ? (p.gpa >= 3.5 ? 'A'xcel' : p.gpa >= 3.0 ? 'Yaxshi' : 'Qoniqarli') : '';

  c.innerHTML = `
    <!-- GPA Hero -->
    <div class="gpa-hero">
      <div class="gpa-hero-label">Umumiy GPA</div>
      <div class="gpa-hero-value">${gpaVal}</div>
      <div class="gpa-hero-sub">${p.semester} · ${gpaOf}</div>
      <div class="gpa-hero-name">${p.full_name} · ${p.group}</div>
    </div>

    <!-- Stats -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-value v-${risks>0?'red':'green'}">${risks}</div>
        <div class="stat-label">Xavf</div>
        <div class="stat-sub">ta fan</div>
      </div>
      <div class="stat-card">
        <div class="stat-value v-${nbs>0?'orange':'green'}">${nbs}</div>
        <div class="stat-label">NB</div>
        <div class="stat-sub">ogohlantirish</div>
      </div>
      <div class="stat-card">
        <div class="stat-value v-blue">${todayLessons.length}</div>
        <div class="stat-label">Bugun</div>
        <div class="stat-sub">dars</div>
      </div>
    </div>

    ${risks > 0 ? `
    <div class="alert danger">
      <span class="alert-icon">🚨</span>
      <div><b>${risks} ta fanda</b> qayta topshirish xavfi mavjud!</div>
    </div>` : ''}

    ${nbs > 0 ? `
    <div class="alert warn">
      <span class="alert-icon">📍</span>
      <div><b>${nbs} ta fanda</b> davomat chegarasiga yaqin!</div>
    </div>` : ''}

    ${S.isDemo ? `
    <div class="alert info">
      <span class="alert-icon">👀</span>
      <div>Demo rejim — namunali ma'lumotlar ko'rsatilmoqda.</div>
    </div>` : ''}

    <!-- Today's schedule -->
    <div class="section-header" style="margin-top:8px">
      <div class="section-title">Bugungi darslar</div>
      <div class="section-more" onclick="navigate('timetable')">Barchasi</div>
    </div>

    ${todayLessons.length === 0 ? `
    <div class="card">
      <div style="text-align:center;padding:24px;color:var(--text4)">
        🎉 Bugun darslar yo'q!
      </div>
    </div>` : `
    <div class="today-scroll">
      ${todayLessons.map((l,i) => `
        <div class="lesson-chip">
          <div class="chip-num">${l.num}-dars</div>
          <div class="chip-time">${l.start} – ${l.end}</div>
          <div class="chip-subj">${l.s}</div>
          <div class="chip-room">📍 ${l.room}</div>
        </div>`).join('')}
    </div>`}

    <!-- Risk subjects -->
    ${grades.filter(g=>g.risk||g.nb).length > 0 ? `
    <div class="section-header" style="margin-top:4px">
      <div class="section-title">Diqqat talab fanlar</div>
    </div>
    <div class="card">
      ${grades.filter(g=>g.risk||g.nb).map((g,i,arr) => `
        <div style="padding:13px 16px;${i<arr.length-1?'border-bottom:0.5px solid var(--sep)':''}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <div style="font-size:14px;font-weight:600">${g.s}</div>
            <div style="font-size:18px;font-weight:700;color:${g.risk?'var(--red)':'var(--orange)'}">${g.tot}</div>
          </div>
          ${g.risk ? `<div style="font-size:12px;color:var(--red)">⚠️ O'tish uchun yakuniyda ${g.needed}/50 kerak</div>` : ''}
          ${g.nb   ? `<div style="font-size:12px;color:var(--orange);margin-top:2px">📍 Davomat chegarasiga yaqin</div>` : ''}
        </div>`).join('')}
    </div>` : ''}

    <!-- Premium upsell -->
    ${!S.isPremium ? `
    <div class="lock-card" style="margin-top:4px">
      <div class="lock-icon">👑</div>
      <div class="lock-title">Premium ga o'ting</div>
      <div class="lock-desc">
        Darhol ball yangilanishi, jadval o'zgarish ogohlantirishlari,
        to'liq GPA analitika va o'qituvchi tracker.
      </div>
      <button class="btn-primary" onclick="toast('Tez kunda ulash rejalashtirilgan!','info')">
        5,000 so'm / oy
      </button>
    </div>` : ''}
  `;

  updateTopbar(DEMO.profile, S.isPremium, S.isDemo);
}

// ══════════════════════════════════════════════════════════════
// GRADES VIEW
// ══════════════════════════════════════════════════════════════
function renderGrades(c) {
  const grades = DEMO.grades;
  const totalSum = grades.reduce((s,g) => s+(g.tot||0), 0);
  const gpa = (totalSum / grades.length / 25).toFixed(2);

  function letter(t) {
    if(t===null) return null;
    return t>=86?'A':t>=71?'B':t>=55?'C':'D';
  }
  function barColor(pct) {
    return pct>=80?'var(--green)':pct>=55?'var(--accent)':pct>=30?'var(--orange)':'var(--red)';
  }
  function totalColor(t) {
    return t>=86?'var(--green)':t>=71?'var(--accent)':t>=55?'var(--orange)':'var(--red)';
  }

  c.innerHTML = `
    <!-- GPA Strip -->
    <div class="card" style="margin-bottom:14px">
      <div class="card-section" style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px">
        <div>
          <div style="font-size:12px;color:var(--text3);font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">GPA</div>
          <div style="font-size:38px;font-weight:800;background:linear-gradient(135deg,#0a84ff,#5e5ce6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${gpa}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:12px;color:var(--text3);font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Fanlar</div>
          <div style="font-size:38px;font-weight:800">${grades.length}</div>
        </div>
      </div>
      <!-- Legend -->
      <div class="sep-line"></div>
      <div style="display:flex;gap:16px;padding:10px 16px;font-size:11px;color:var(--text3)">
        <span><span style="color:var(--accent)">■</span> Joriy /20</span>
        <span><span style="color:var(--purple)">■</span> Oraliq /30</span>
        <span><span style="color:var(--green)">■</span> Yakuniy /50</span>
      </div>
    </div>

    <!-- Grade Cards -->
    ${grades.map((g,i) => {
      const curPct = g.cur !== null ? (g.cur/20)*100 : 0;
      const midPct = g.mid !== null ? (g.mid/30)*100 : 0;
      const finPct = g.fin !== null ? (g.fin/50)*100 : 0;
      const lt = letter(g.fin !== null ? g.tot : null);
      const isRisk = g.risk;
      const isNb   = g.nb;

      return `
      <div class="card" style="border:0.5px solid ${isRisk?'rgba(255,69,58,0.3)':isNb?'rgba(255,159,10,0.2)':'transparent'}">
        <div class="grade-item">
          <div class="grade-name">${g.s}</div>
          <div class="grade-meta">${g.hrs ? g.hrs+' soat' : ''}${g.miss ? ' · '+g.miss+' soat o\'tkazilgan' : ''}</div>
          <div class="grade-total" style="color:${totalColor(g.tot)}">${g.tot}</div>
          <div class="grade-bars">
            <div class="bar-row">
              <div class="bar-label">Joriy</div>
              <div class="bar-track"><div class="bar-fill" style="width:${curPct}%;background:var(--accent)"></div></div>
              <div class="bar-val">${g.cur??'—'}/20</div>
            </div>
            <div class="bar-row">
              <div class="bar-label">Oraliq</div>
              <div class="bar-track"><div class="bar-fill" style="width:${midPct}%;background:var(--purple)"></div></div>
              <div class="bar-val">${g.mid??'—'}/30</div>
            </div>
            <div class="bar-row">
              <div class="bar-label">Yakuniy</div>
              <div class="bar-track"><div class="bar-fill" style="width:${finPct}%;background:var(--green)"></div></div>
              <div class="bar-val">${g.fin??'—'}/50</div>
            </div>
          </div>
          <div class="grade-tags">
            ${lt ? `<span class="tag ${lt==='A'?'tag-green':lt==='B'?'tag-blue':lt==='C'?'tag-orange':'tag-red'}">${lt}</span>` : ''}
            ${g.fin===null ? '<span class="tag tag-gray">Jarayon</span>' : '<span class="tag tag-gray">Yakunlangan</span>'}
            ${S.isPremium && g.needed ? `<span class="tag tag-orange">Yakuniyda ${g.needed}/50 kerak</span>` : ''}
          </div>
        </div>
        ${isRisk ? `<div class="risk-strip"><span>⚠️</span><span>Maksimal ball uchun yakuniyda <b>${g.needed}/50</b> kerak</span></div>` : ''}
        ${isNb   ? `<div class="nb-strip"><span>📍</span><span>Davomat 20% chegarasiga yaqin!</span></div>` : ''}
      </div>`;
    }).join('')}

    ${!S.isPremium ? `
    <div class="lock-card">
      <div class="lock-icon">🔒</div>
      <div class="lock-title">Premium analitika</div>
      <div class="lock-desc">Maqsad ball hisob-kitobi, GPA prognozi va batafsil tahlil Premium bilan mavjud.</div>
      <button class="btn-primary" onclick="toast('Tez kunda!','info')">👑 Premium — 5,000 so'm/oy</button>
    </div>` : ''}
  `;
}

// ══════════════════════════════════════════════════════════════
// TIMETABLE VIEW
// ══════════════════════════════════════════════════════════════
function renderTimetable(c) {
  const mon = monday(S.curWeekOff);
  const todayIso = isoDate(new Date());

  const days = Array.from({length:6}, (_,i) => {
    const d = new Date(mon);
    d.setDate(d.getDate() + i);
    const iso = isoDate(d);
    return {
      i, iso,
      short: DAYS_UZ[i],
      isToday: iso === todayIso,
      hasLessons: !!(DEMO.timetable[iso]?.length),
    };
  });

  const curDay = days[S.curDayIdx] || days[0];
  const lessons = DEMO.timetable[curDay.iso] || [];

  // Week label
  const endD = new Date(mon);
  endD.setDate(endD.getDate() + 5);
  const fmt = d => d.getDate() + '.' + String(d.getMonth()+1).padStart(2,'0');
  const weekLabel = fmt(mon) + ' – ' + fmt(endD) + ' · ' + mon.getFullYear();

  c.innerHTML = `
    <div class="week-nav">
      <button class="week-btn" id="prevWeek">‹</button>
      <div class="week-label">${weekLabel}</div>
      <button class="week-btn" id="nextWeek">›</button>
    </div>

    <div class="day-tabs" id="dayTabs">
      ${days.map(d => `
        <button class="day-tab ${d.i===S.curDayIdx?'active':''} ${d.isToday&&d.i!==S.curDayIdx?'today':''}"
                onclick="selectDay(${d.i},'${d.iso}')">
          ${d.short}${d.hasLessons?'<span style="color:var(--accent);font-size:8px;vertical-align:super">●</span>':''}
        </button>`).join('')}
    </div>

    <div class="card" id="lessonsCard">
      ${lessons.length === 0 ? `
        <div class="no-lessons">
          <div class="no-lessons-icon">🏖️</div>
          <div class="no-lessons-text">Bu kuni darslar yo'q</div>
          <div class="no-lessons-sub">Dam oling!</div>
        </div>` :
        lessons.map((l,i) => {
          const color = COLORS[i % COLORS.length];
          return `
          <div class="lesson-row" style="${i>0?'border-top:0.5px solid var(--sep)':''}">
            <div class="lesson-num-wrap">
              <div class="lesson-num-circle" style="background:${color}22;color:${color}">${l.num}</div>
              <div class="lesson-time-mini">${l.start}<br>${l.end}</div>
            </div>
            <div class="lesson-body">
              <div class="lesson-subject">${l.s}</div>
              <div class="lesson-details">
                <span class="lesson-detail">📍 ${l.room}</span>
                <span class="lesson-detail">👤 ${l.teacher}</span>
                <span class="tag tag-gray" style="font-size:10px">${l.type}</span>
              </div>
            </div>
          </div>`;
        }).join('')}
    </div>
  `;

  document.getElementById('prevWeek').onclick = () => {
    S.curWeekOff--;
    S.curDayIdx = 4;
    navigate('timetable');
  };
  document.getElementById('nextWeek').onclick = () => {
    S.curWeekOff++;
    S.curDayIdx = 0;
    navigate('timetable');
  };
}

function selectDay(idx, iso) {
  S.curDayIdx = idx;
  document.querySelectorAll('.day-tab').forEach((b,i) => {
    b.classList.toggle('active', i === idx);
  });
  const lessons = DEMO.timetable[iso] || [];
  const card = document.getElementById('lessonsCard');
  if(!card) return;
  card.innerHTML = lessons.length === 0 ?
    '<div class="no-lessons"><div class="no-lessons-icon">🏖️</div><div class="no-lessons-text">Bu kuni darslar yo\'q</div></div>' :
    lessons.map((l,i) => {
      const color = COLORS[i%COLORS.length];
      return `<div class="lesson-row" style="${i>0?'border-top:0.5px solid var(--sep)':''}">
        <div class="lesson-num-wrap">
          <div class="lesson-num-circle" style="background:${color}22;color:${color}">${l.num}</div>
          <div class="lesson-time-mini">${l.start}<br>${l.end}</div>
        </div>
        <div class="lesson-body">
          <div class="lesson-subject">${l.s}</div>
          <div class="lesson-details">
            <span class="lesson-detail">📍 ${l.room}</span>
            <span class="lesson-detail">👤 ${l.teacher}</span>
            <span class="tag tag-gray" style="font-size:10px">${l.type}</span>
          </div>
        </div>
      </div>`;
    }).join('');
  haptic('light');
}

// ══════════════════════════════════════════════════════════════
// NAVIGATOR VIEW
// ══════════════════════════════════════════════════════════════
function renderNavigator(c) {
  c.innerHTML = `
    <div class="nav-tabs-row">
      <button class="nav-seg-btn ${S.navTab==='rooms'?'active':''}" onclick="switchNavTab('rooms')">🏛️ Xonalar</button>
      <button class="nav-seg-btn ${S.navTab==='teachers'?'active':''}" onclick="switchNavTab('teachers')">👨‍🏫 O'qituvchilar</button>
    </div>
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input class="search-input" id="navSearch"
        placeholder="${S.navTab==='rooms'?'A-301, B-102...':'Ism bo\'yicha...'}"
        oninput="filterNav(this.value)">
    </div>
    <div id="navList">${buildNavList('')}</div>
  `;
}

function switchNavTab(tab) {
  S.navTab = tab;
  document.querySelectorAll('.nav-seg-btn').forEach((b,i) => {
    b.classList.toggle('active', ['rooms','teachers'][i] === tab);
  });
  document.getElementById('navSearch').value = '';
  document.getElementById('navSearch').placeholder = tab==='rooms'?'A-301, B-102...':'Ism bo\'yicha...';
  document.getElementById('navList').innerHTML = buildNavList('');
  haptic('light');
}

function buildNavList(q) {
  if(S.navTab === 'rooms') {
    const rooms = DEMO.rooms.filter(r =>
      !q || r.code.toLowerCase().includes(q.toLowerCase()) ||
      r.building.toLowerCase().includes(q.toLowerCase())
    );
    if(!rooms.length) return '<div style="text-align:center;padding:40px;color:var(--text4)">Topilmadi</div>';

    const byBuilding = {};
    rooms.forEach(r => { byBuilding[r.building] = byBuilding[r.building]||[]; byBuilding[r.building].push(r); });

    return Object.entries(byBuilding).map(([building, rs]) => `
      <div style="font-size:12px;font-weight:700;color:var(--text3);
        text-transform:uppercase;letter-spacing:0.5px;
        margin-bottom:8px;margin-top:4px">${building}</div>
      <div class="card" style="margin-bottom:12px">
        ${rs.map((r,i) => `
          <div class="room-row" style="${i>0?'border-top:0.5px solid var(--sep)':''}">
            <div class="room-code">${r.code}</div>
            <div class="room-info">
              <div class="room-name">${r.type}</div>
              <div class="room-meta">${r.floor}-qavat · ${r.cap} o'rin</div>
            </div>
            <div class="room-tag">${r.floor}Q</div>
          </div>`).join('')}
      </div>`).join('');
  } else {
    if(!S.isPremium) {
      return `<div class="lock-card">
        <div class="lock-icon">🔒</div>
        <div class="lock-title">O'qituvchi Tracker</div>
        <div class="lock-desc">O'qituvchilar hozir qayerda ekanligini real vaqtda ko'ring. Premium bilan mavjud.</div>
        <button class="btn-primary" onclick="toast('Tez kunda!','info')">👑 Premium olish</button>
      </div>`;
    }
    const teachers = DEMO.teachers.filter(t =>
      !q || t.name.toLowerCase().includes(q.toLowerCase())
    );
    return '<div class="card">' + teachers.map((t,i) => `
      <div class="teacher-row" style="${i>0?'border-top:0.5px solid var(--sep)':''}">
        <div class="teacher-avatar">${t.name.split(' ').map(n=>n[0]).slice(0,2).join('')}</div>
        <div>
          <div class="teacher-name">${t.name}</div>
          <div class="teacher-dept">${t.dept}</div>
          <div class="teacher-loc ${t.room?'loc-online':'loc-offline'}">
            ${t.room ? '🟢 ' + t.room + ' — hozir shu yerda' : '⚫ Joylashuv noma\'lum'}
          </div>
        </div>
      </div>`).join('') + '</div>';
  }
}

function filterNav(q) {
  document.getElementById('navList').innerHTML = buildNavList(q);
}

// ── Boot ─────────────────────────────────────────────────────
(function boot() {
  setTimeout(() => {
    updateTopbar(DEMO.profile, S.isPremium, S.isDemo);
    navigate('home');
  }, 400);
})();
</script>
</body>
</html>"""

# ── Bot background task ───────────────────────────────────────
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
    return {"status":"ok","app":"HELPER TDIU","version":"2.0.0"}

@app.get("/health")
async def health():
    return {"status":"ok"}

@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    return MINI_APP_HTML
