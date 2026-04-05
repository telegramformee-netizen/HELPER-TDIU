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
# MINI APP HTML — iOS 18 Glassmorphism + Full Features
# ══════════════════════════════════════════════════════════════
MINI_APP_HTML = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #000000;
  --bg2:     rgba(28, 28, 30, 0.4);
  --bg3:     rgba(44, 44, 46, 0.5);
  --bg4:     rgba(58, 58, 60, 0.6);
  --text:    #ffffff;
  --text2:   rgba(235, 235, 245, 0.8);
  --text3:   rgba(235, 235, 245, 0.6);
  --text4:   rgba(235, 235, 245, 0.4);
  --accent:  #0a84ff;
  --green:   #30d158;
  --orange:  #ff9f0a;
  --red:     #ff453a;
  --yellow:  #ffd60a;
  --purple:  #bf5af2;
  --sep:     rgba(255,255,255,0.08);
  --card-bg: rgba(28, 28, 30, 0.55);
  --glass-border: rgba(255, 255, 255, 0.1);
  --nav-h:   83px;
  --top-h:   56px;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased}

/* ── Dynamic Blurred Background ── */
.bg-blobs { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; filter: blur(80px); opacity: 0.35; pointer-events: none; }
.blob { position: absolute; border-radius: 50%; animation: float 20s infinite alternate ease-in-out; }
.blob-1 { width: 300px; height: 300px; background: #0a84ff; top: -10%; left: -10%; animation-delay: 0s; }
.blob-2 { width: 400px; height: 400px; background: #bf5af2; bottom: -20%; right: -10%; animation-delay: -5s; }
.blob-3 { width: 250px; height: 250px; background: #30d158; top: 40%; left: 50%; animation-delay: -10s; }
@keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(50px, 50px) scale(1.1); } }

/* ── Scrollable area & Transitions ── */
.view{ position:fixed;top:var(--top-h);left:0;right:0; bottom:var(--nav-h); overflow-y:auto; overscroll-behavior:contain; -webkit-overflow-scrolling:touch; scrollbar-width:none; opacity: 0; transform: translateX(20px); pointer-events: none; transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1); }
.view.active { opacity: 1; transform: translateX(0); pointer-events: auto; }
.view::-webkit-scrollbar{display:none} .view-inner{padding:12px 16px 20px}

/* ── Topbar Glass ── */
.topbar{ position:fixed;top:0;left:0;right:0;height:var(--top-h); background:rgba(0,0,0,0.6); backdrop-filter:blur(25px);-webkit-backdrop-filter:blur(25px); border-bottom:0.5px solid var(--glass-border); display:flex;align-items:center;padding:0 20px; z-index:100; }
.topbar-logo{ width:34px;height:34px;border-radius:9px; background:linear-gradient(135deg,#0a84ff,#5e5ce6); display:flex;align-items:center;justify-content:center; font-size:17px;font-weight:800;color:#fff;margin-right:11px; box-shadow:0 2px 8px rgba(10,132,255,0.4); }
.topbar-name{font-size:16px;font-weight:700;} .topbar-group{font-size:12px;color:var(--text3);margin-top:1px}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.badge-demo{background:var(--bg3);color:var(--text3);font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;border:0.5px solid var(--glass-border);}
.badge-premium{background:linear-gradient(135deg,#ff9f0a,#ff6b00);color:#fff;font-size:10px;font-weight:700;padding:3px 9px;border-radius:20px;}

/* ── Bottom Nav Glass ── */
.bottom-nav{ position:fixed;bottom:0;left:0;right:0; height:var(--nav-h); background:rgba(0,0,0,0.7); backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px); border-top:0.5px solid var(--glass-border); display:flex;align-items:flex-start;padding-top:10px; z-index:100; }
.nav-item{ flex:1;display:flex;flex-direction:column;align-items:center;gap:3px; background:none;border:none;cursor:pointer; color:var(--text4);transition:0.2s; }
.nav-item.active{color:var(--accent)} .nav-icon{font-size:24px; transition: transform 0.2s; } .nav-item:active .nav-icon { transform: scale(0.8); } .nav-label{font-size:10px;font-weight:500;}

/* ── Cards Glass ── */
.card{ background:var(--card-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius:16px; overflow:hidden; margin-bottom:12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }

/* ── Typography & Misc ── */
.gpa-hero{ background:linear-gradient(160deg, rgba(10,132,255,0.1) 0%, rgba(0,0,0,0) 100%); border: 1px solid var(--glass-border); border-radius:20px; padding:24px 20px; margin-bottom:12px; text-align:center; }
.gpa-hero-label{font-size:12px;font-weight:600;color:var(--accent); text-transform:uppercase;margin-bottom:6px}
.gpa-hero-value{ font-size:64px;font-weight:800; background:linear-gradient(135deg,#fff,#a1a1aa); -webkit-background-clip:text;-webkit-text-fill-color:transparent; line-height:1;margin-bottom:8px; }
.gpa-hero-sub{font-size:13px;color:var(--text3)}
.stat-row{display:flex;gap:10px;margin-bottom:12px} .stat-card{flex:1;background:var(--card-bg);border:1px solid var(--glass-border);border-radius:16px;padding:14px 12px;}
.stat-value{font-size:28px;font-weight:800;line-height:1;margin-bottom:4px} .stat-label{font-size:11px;color:var(--text3);font-weight:500}
.v-blue{color:var(--accent)} .v-green{color:var(--green)} .v-orange{color:var(--orange)} .v-red{color:var(--red)}
.alert{display:flex;align-items:flex-start;gap:10px;padding:13px 14px;border-radius:13px;margin-bottom:8px;font-size:13px;line-height:1.5;border: 1px solid var(--glass-border);backdrop-filter: blur(10px);}
.alert-icon{font-size:17px;flex-shrink:0;margin-top:1px} .alert b{font-weight:600}
.alert.danger{background:rgba(255,69,58,0.15);} .alert.warn{background:rgba(255,159,10,0.15);} .alert.info{background:rgba(10,132,255,0.15);}

.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;margin-top:4px;} .section-title{font-size:20px;font-weight:700;} 
.lesson-chip{flex-shrink:0;background:var(--bg3);border-radius:14px;padding:12px 14px;min-width:150px;border:0.5px solid var(--glass-border);margin-bottom:8px;}
.chip-num{font-size:10px;font-weight:700;color:var(--accent);margin-bottom:4px;} .chip-time{font-size:12px;color:var(--text3);margin-bottom:6px} .chip-subj{font-size:13px;font-weight:600;margin-bottom:4px} .chip-room{font-size:11px;color:var(--text4)}

.grade-item{padding:14px 16px;position:relative} .grade-name{font-size:15px;font-weight:600;margin-bottom:3px;} .grade-meta{font-size:12px;color:var(--text3);margin-bottom:10px} .grade-total{position:absolute;top:14px;right:16px;font-size:22px;font-weight:800;}
.grade-bars{display:flex;flex-direction:column;gap:5px} .bar-row{display:flex;align-items:center;gap:8px} .bar-label{font-size:11px;color:var(--text4);width:48px;} .bar-track{flex:1;height:4px;background:var(--bg4);border-radius:99px;} .bar-fill{height:100%;border-radius:99px;} .bar-val{font-size:11px;color:var(--text3);width:32px;text-align:right;}
.risk-strip{display:flex;align-items:center;gap:6px;background:rgba(255,69,58,0.15);padding:8px 16px;font-size:12px;color:#ff6b63;}

.week-nav{display:flex;align-items:center;gap:8px;margin-bottom:14px;} .week-btn{width:36px;height:36px;border-radius:10px;background:var(--bg3);border:1px solid var(--glass-border);color:var(--text);font-size:16px;display:flex;align-items:center;justify-content:center;cursor:pointer;} .week-label{flex:1;text-align:center;font-size:13px;font-weight:600;color:var(--text2)}
.day-tabs{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;margin-bottom:14px;} .day-tab{flex-shrink:0;padding:7px 14px;background:var(--bg3);border:1px solid var(--glass-border);border-radius:99px;font-size:13px;font-weight:600;color:var(--text3);cursor:pointer;} .day-tab.active{background:var(--accent);color:#fff;border-color:var(--accent);}
.lesson-row{display:flex;gap:12px;padding:14px 16px;} .lesson-num-wrap{width:36px;display:flex;flex-direction:column;align-items:center;gap:2px;} .lesson-num-circle{width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;} .lesson-body{flex:1} .lesson-subject{font-size:14px;font-weight:600;margin-bottom:5px;}

.nav-tabs-row{display:flex;gap:8px;margin-bottom:14px} .nav-seg-btn{flex:1;padding:11px;background:var(--bg3);border:1px solid var(--glass-border);border-radius:12px;font-size:13px;font-weight:600;color:var(--text3);cursor:pointer;} .nav-seg-btn.active{background:rgba(10,132,255,0.2);border-color:var(--accent);color:var(--accent);}
.search-wrap{display:flex;align-items:center;gap:10px;background:var(--bg3);border-radius:12px;padding:11px 14px;margin-bottom:12px;border:1px solid var(--glass-border);} .search-input{background:none;border:none;outline:none;color:var(--text);font-size:14px;flex:1;} .room-row{display:flex;align-items:center;gap:14px;padding:13px 16px;}
.teacher-row{display:flex;align-items:center;gap:14px;padding:13px 16px;} .teacher-avatar{width:42px;height:42px;border-radius:13px;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-size:17px;}

/* ── PREMIUM LOCK CARDS ── */
.lock-card{ background:rgba(10, 132, 255, 0.1); backdrop-filter: blur(20px); border: 1px solid var(--accent); border-radius:16px; padding:24px 20px; text-align:center; margin-bottom:12px; }
.lock-icon{font-size:40px;margin-bottom:12px} .lock-title{font-size:17px;font-weight:700;margin-bottom:8px; color: var(--text)}
.lock-desc{font-size:13px;color:var(--text3);line-height:1.6;margin-bottom:16px}
.btn-primary{ display:block;width:100%; background:var(--accent);color:#fff; font-size:15px;font-weight:600; padding:14px;border:none;border-radius:12px; cursor:pointer;}

/* ── TOASTS ── */
#toasts{ position:fixed;bottom:calc(var(--nav-h) + 12px);left:16px;right:16px;z-index:999;display:flex;flex-direction:column;gap:8px;pointer-events:none; }
.toast{ background:rgba(44,44,46,0.95);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:13px;padding:13px 16px;font-size:13px;pointer-events:all; animation:toastIn 0.3s; }
@keyframes toastIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
</style>
</head>
<body>
<div class="bg-blobs"><div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div></div>

<header class="topbar">
  <div class="topbar-logo">H</div>
  <div><div class="topbar-name">HELPER TDIU</div><div class="topbar-group" id="tbar-group">Yuklanmoqda...</div></div>
  <div class="topbar-right">
    <div id="badge-premium" class="badge-premium" style="display:none">PRO</div>
    <div id="badge-demo" class="badge-demo" style="display:none">DEMO</div>
  </div>
</header>

<div class="view-container">
  <div class="view" id="view"><div class="view-inner" id="view-inner"></div></div>
</div>

<nav class="bottom-nav">
  <button class="nav-item active" id="nav-home" onclick="navigate('home')"><span class="nav-icon">🏠</span><span class="nav-label">Bosh</span></button>
  <button class="nav-item" id="nav-grades" onclick="navigate('grades')"><span class="nav-icon">📊</span><span class="nav-label">Baholar</span></button>
  <button class="nav-item" id="nav-timetable" onclick="navigate('timetable')"><span class="nav-icon">📅</span><span class="nav-label">Jadval</span></button>
  <button class="nav-item" id="nav-navigator" onclick="navigate('navigator')"><span class="nav-icon">🗺️</span><span class="nav-label">Navigator</span></button>
</nav>
<div id="toasts"></div>

<script>
const tg = window.Telegram?.WebApp; tg?.expand(); tg?.disableVerticalSwipes?.();
function haptic(type='light') { tg?.HapticFeedback?.impactOccurred(type); }
function toast(msg) { const el = document.createElement('div'); el.className = 'toast'; el.innerHTML = '✅ ' + msg; document.getElementById('toasts').appendChild(el); setTimeout(() => el.remove(), 3000); }

const S = { view: 'home', isPremium: false, isDemo: true, curWeekOff: 0, curDayIdx: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1, navTab: 'rooms' };
const DEMO = {
  profile: { full_name: "Demo Talaba", group: "IQ-22-01", faculty: "Iqtisodiyot", semester: "2024-2", gpa: 3.45 },
  grades: [
    {s:"Mikroiqtisodiyot",cur:17,mid:24,fin:null,tot:41,risk:false,nb:false,needed:14,hrs:64,miss:4},
    {s:"Bank ishi va kredit",cur:15,mid:22,fin:null,tot:37,risk:false,nb:true,needed:18,hrs:72,miss:15},
    {s:"Iqtisodiy siyosat",cur:18,mid:28,fin:null,tot:46,risk:false,nb:false,needed:9,hrs:80,miss:2},
    {s:"Pul va kredit",cur:12,mid:18,fin:null,tot:30,risk:true,nb:true,needed:25,hrs:64,miss:14},
    {s:"Marketing asoslari",cur:19,mid:26,fin:null,tot:45,risk:false,nb:false,needed:10,hrs:72,miss:0},
  ],
  timetable: {
    "2025-04-07":[{num:1,start:"08:30",end:"09:50",s:"Mikroiqtisodiyot",type:"Ma'ruza",teacher:"Salimov B.",room:"A-301"}, {num:3,start:"11:30",end:"12:50",s:"Bank ishi",type:"Seminar",teacher:"Rahimov N.",room:"B-204"}],
    "2025-04-08":[{num:2,start:"10:00",end:"11:20",s:"Pul va kredit",type:"Ma'ruza",teacher:"Hasanov M.",room:"A-101"}],
  },
  rooms: [{code:"A-101",building:"A blok",floor:1,cap:120,type:"Ma'ruza zali"},{code:"B-204",building:"B blok",floor:2,cap:30,type:"Seminar xona"}],
  teachers: [{name:"Salimov B.A.",dept:"Mikroiqtisodiyot",room:"A-301"},{name:"Rahimov N.X.",dept:"Bank ishi",room:null}]
};

const DAYS_UZ = ["Du","Se","Ch","Pa","Ju","Sh","Ya"];
const COLORS = ["#0a84ff","#30d158","#ff9f0a","#bf5af2","#ff453a","#5e5ce6","#32ade6"];
function isoDate(d) { return d.toISOString().slice(0,10); }
function monday(weekOff=0) { const d = new Date(); const off = d.getDay()===0?6:d.getDay()-1; d.setDate(d.getDate()-off+weekOff*7); d.setHours(0,0,0,0); return d; }

function animateValue(id, end, duration) {
    let obj = document.getElementById(id); if (!obj) return;
    let current = 0; let increment = end > 0 ? 0.05 : -0.05; let stepTime = Math.abs(Math.floor(duration / (end / increment)));
    let timer = setInterval(() => { current += increment; obj.innerHTML = current.toFixed(2); if (current >= end) { clearInterval(timer); obj.innerHTML = end.toFixed(2); } }, stepTime);
}

function navigate(view) {
  haptic('light'); S.view = view;
  document.querySelectorAll('.nav-item').forEach(b => b.classList.toggle('active', b.id === 'nav-' + view));
  const v = document.getElementById('view'); v.classList.remove('active');
  
  setTimeout(() => {
    const inner = document.getElementById('view-inner'); inner.innerHTML = ''; v.scrollTop = 0;
    if (view === 'home') renderHome(inner); else if (view === 'grades') renderGrades(inner); else if (view === 'timetable') renderTimetable(inner); else if (view === 'navigator') renderNavigator(inner);
    v.classList.add('active');
  }, 200); 
}

function updateTopbar() {
  document.getElementById('tbar-group').textContent = DEMO.profile.group + ' · ' + DEMO.profile.faculty;
  document.getElementById('badge-demo').style.display = S.isDemo ? '' : 'none';
  document.getElementById('badge-premium').style.display = S.isPremium ? '' : 'none';
}

function renderHome(c) {
  const p = DEMO.profile; const risks = DEMO.grades.filter(g=>g.risk).length; const nbs = DEMO.grades.filter(g=>g.nb).length;
  let html = `
    <div class="gpa-hero"><div class="gpa-hero-label">Umumiy GPA</div><div class="gpa-hero-value" id="gpa-counter">0.00</div><div class="gpa-hero-sub">${p.semester}</div></div>
    <div class="stat-row">
      <div class="stat-card"><div class="stat-value v-${risks>0?'red':'green'}">${risks}</div><div class="stat-label">Xavf</div></div>
      <div class="stat-card"><div class="stat-value v-${nbs>0?'orange':'green'}">${nbs}</div><div class="stat-label">NB</div></div>
    </div>
    ${risks > 0 ? `<div class="alert danger"><span class="alert-icon">🚨</span><div><b>${risks} ta fanda</b> qayta topshirish xavfi mavjud!</div></div>` : ''}
    ${nbs > 0 ? `<div class="alert warn"><span class="alert-icon">📍</span><div><b>${nbs} ta fanda</b> davomat chegarasiga yaqin!</div></div>` : ''}
    <div class="section-header"><div class="section-title">Bugungi darslar</div></div>
    <div class="card">
       <div class="lesson-chip" style="border:none; background:transparent;">
          <div class="chip-num">1-dars</div><div class="chip-subj">Mikroiqtisodiyot</div><div class="chip-room">📍 A-301</div>
       </div>
    </div>
  `;
  if(!S.isPremium) {
    html += `
    <div class="lock-card">
      <div class="lock-icon">👑</div><div class="lock-title">Premium ga o'ting</div>
      <div class="lock-desc">Darhol ball yangilanishi, jadval o'zgarish ogohlantirishlari, to'liq GPA analitika va o'qituvchi tracker.</div>
      <button class="btn-primary" onclick="toast('Tez kunda!')">5,000 so'm / oy</button>
    </div>`;
  }
  c.innerHTML = html;
  setTimeout(() => animateValue("gpa-counter", p.gpa, 800), 250);
}

function renderGrades(c) {
  let html = `
    <div class="card" style="padding: 10px;">
        <h3 style="font-size:12px; color:var(--text3); text-align:center; margin: 10px 0;">O'ZLASHTIRISH GRAFIGI</h3>
        <div style="height:200px; width:100%;"><canvas id="radarChart"></canvas></div>
    </div>
    ${DEMO.grades.map((g,i) => `
    <div class="card" style="${g.risk?'border-color:rgba(255,69,58,0.5);':''}">
      <div class="grade-item">
        <div class="grade-name">${g.s}</div><div class="grade-total" style="color:${g.tot>70?'var(--green)':'var(--orange)'}">${g.tot}</div>
        <div class="grade-bars">
          <div class="bar-row"><div class="bar-label">Joriy</div><div class="bar-track"><div class="bar-fill" style="width:${(g.cur/20)*100}%;background:var(--accent)"></div></div><div class="bar-val">${g.cur}/20</div></div>
          <div class="bar-row"><div class="bar-label">Oraliq</div><div class="bar-track"><div class="bar-fill" style="width:${(g.mid/30)*100}%;background:var(--purple)"></div></div><div class="bar-val">${g.mid}/30</div></div>
        </div>
      </div>
      ${g.risk ? `<div class="risk-strip">⚠️ Yakuniyda ${g.needed}/50 kerak</div>` : ''}
    </div>`).join('')}
  `;
  if(!S.isPremium) {
    html += `
    <div class="lock-card">
      <div class="lock-icon">🔒</div><div class="lock-title">Premium analitika</div>
      <div class="lock-desc">Maqsad ball hisob-kitobi, GPA prognozi va batafsil tahlil Premium bilan mavjud.</div>
      <button class="btn-primary" onclick="toast('Tez kunda!')">👑 Premium — 5,000 so'm/oy</button>
    </div>`;
  }
  c.innerHTML = html;
  setTimeout(() => {
    new Chart(document.getElementById('radarChart').getContext('2d'), {
      type: 'radar',
      data: { labels: DEMO.grades.map(g=>g.s.substring(0,6)+'.'), datasets: [{ data: DEMO.grades.map(g=>g.tot), backgroundColor: 'rgba(10, 132, 255, 0.2)', borderColor: '#0a84ff', borderWidth: 2 }] },
      options: { scales: { r: { angleLines: {color: 'rgba(255,255,255,0.1)'}, grid: {color: 'rgba(255,255,255,0.1)'}, ticks: {display:false, max:50} } }, plugins:{legend:{display:false}} }
    });
  }, 250);
}

function renderTimetable(c) {
  // XATONI TUZATILGAN JOYI: Array length: 7 (Dushanbadan Yakshanbagacha)
  const mon = monday(S.curWeekOff); const days = Array.from({length:7}, (_,i) => { const d=new Date(mon); d.setDate(d.getDate()+i); return {i, iso:isoDate(d), short:DAYS_UZ[i]}; });
  c.innerHTML = `
    <div class="week-nav"><button class="week-btn" id="pw">‹</button><div class="week-label">Jadval · ${mon.getFullYear()}</div><button class="week-btn" id="nw">›</button></div>
    <div class="day-tabs">${days.map(d => `<button class="day-tab ${d.i===S.curDayIdx?'active':''}" onclick="haptic(); S.curDayIdx=${d.i}; navigate('timetable')">${d.short}</button>`).join('')}</div>
    <div class="card">${(DEMO.timetable[days[S.curDayIdx].iso]||[]).map((l,i) => `
      <div class="lesson-row" style="${i>0?'border-top:1px solid var(--glass-border)':''}">
        <div class="lesson-num-wrap"><div class="lesson-num-circle" style="background:${COLORS[i]}22;color:${COLORS[i]}">${l.num}</div></div>
        <div class="lesson-body"><div class="lesson-subject">${l.s}</div><div style="font-size:12px;color:var(--text3)">📍 ${l.room} · 👤 ${l.teacher}</div></div>
      </div>`).join('') || '<div style="text-align:center;padding:40px 10px;color:var(--text4)">🎉 Bu kuni darslar yo\'q!</div>'}
    </div>`;
  document.getElementById('pw').onclick = () => { S.curWeekOff--; navigate('timetable'); }; document.getElementById('nw').onclick = () => { S.curWeekOff++; navigate('timetable'); };
}

function renderNavigator(c) {
  let html = `
    <div class="nav-tabs-row"><button class="nav-seg-btn ${S.navTab==='rooms'?'active':''}" onclick="S.navTab='rooms';navigate('navigator')">🏛️ Xonalar</button><button class="nav-seg-btn ${S.navTab==='teachers'?'active':''}" onclick="S.navTab='teachers';navigate('navigator')">👨‍🏫 O'qituvchi</button></div>
    <div class="search-wrap"><span class="search-icon">🔍</span><input class="search-input" placeholder="Qidirish..."></div>
  `;
  
  if(S.navTab === 'teachers' && !S.isPremium) {
    html += `
    <div class="lock-card">
      <div class="lock-icon">🔒</div><div class="lock-title">O'qituvchi Tracker</div>
      <div class="lock-desc">O'qituvchilar hozir qayerda ekanligini real vaqtda ko'ring. Premium bilan mavjud.</div>
      <button class="btn-primary" onclick="toast('Tez kunda!')">👑 Premium olish</button>
    </div>`;
  } else {
    html += `
    <div class="card">
      ${(S.navTab==='rooms'?DEMO.rooms:DEMO.teachers).map((item, i) => `
        <div class="room-row" style="${i>0?'border-top:1px solid var(--glass-border)':''}">
           <div><div style="font-size:15px;font-weight:600">${item.code || item.name}</div><div style="font-size:12px;color:var(--text3)">${item.type || item.dept}</div></div>
        </div>`).join('')}
    </div>`;
  }
  c.innerHTML = html;
}

// ── Boot ──
setTimeout(() => { updateTopbar(); navigate('home'); }, 100);
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
async def root(): return {"status":"ok","app":"HELPER TDIU"}

@app.get("/health")
async def health(): return {"status":"ok"}

@app.get("/app", response_class=HTMLResponse)
async def mini_app(): return MINI_APP_HTML
