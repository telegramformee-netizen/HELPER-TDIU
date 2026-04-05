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
# MINI APP HTML — iOS 18 PRO VERSION (Soddalashtirilgan Bosh Sahifa)
# ══════════════════════════════════════════════════════════════
MINI_APP_HTML = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #000000; --text: #ffffff; --text2: rgba(235,235,245,0.8); --text3: rgba(235,235,245,0.6); --text4: rgba(235,235,245,0.4);
  --accent: #0a84ff; --green: #30d158; --orange: #ff9f0a; --red: #ff453a; --purple: #bf5af2;
  --card-bg: rgba(28, 28, 30, 0.6); --glass-border: rgba(255, 255, 255, 0.1);
  --nav-h: 83px; --top-h: 60px;
}
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); overflow:hidden; height:100vh; }

.bg-blobs { position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; filter:blur(80px); opacity:0.3; }
.blob { position:absolute; border-radius:50%; animation:float 20s infinite alternate ease-in-out; }
.blob-1 { width:300px; height:300px; background:#0a84ff; top:-10%; left:-10%; }
.blob-2 { width:400px; height:400px; background:#bf5af2; bottom:-20%; right:-10%; }
@keyframes float { 0% { transform:translate(0,0); } 100% { transform:translate(40px,40px); } }

.topbar { position:fixed; top:0; width:100%; height:var(--top-h); background:rgba(0,0,0,0.7); backdrop-filter:blur(25px); border-bottom:1px solid var(--glass-border); display:flex; align-items:center; padding:0 20px; z-index:100; }
.topbar-logo { width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,#0a84ff,#5e5ce6); display:flex; align-items:center; justify-content:center; font-weight:800; margin-right:12px; }

.view { position:fixed; top:var(--top-h); bottom:var(--nav-h); width:100%; overflow-y:auto; padding:15px; opacity:0; transform:translateX(20px); transition:0.3s cubic-bezier(0.2,1,0.3,1); pointer-events:none; }
.view.active { opacity:1; transform:translateX(0); pointer-events:auto; }

.card { background:var(--card-bg); backdrop-filter:blur(20px); border:1px solid var(--glass-border); border-radius:18px; padding:18px; margin-bottom:12px; }

.day-tabs { display:flex; gap:8px; overflow-x:auto; padding-bottom:15px; scrollbar-width:none; }
.day-tab { flex-shrink:0; width:52px; height:70px; background:var(--card-bg); border:1px solid var(--glass-border); border-radius:16px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text3); cursor:pointer; }
.day-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); box-shadow:0 0 15px rgba(10,132,255,0.4); }
.day-name { font-size:11px; font-weight:500; text-transform:uppercase; margin-bottom:4px; }
.day-num { font-size:18px; font-weight:700; }

.bottom-nav { position:fixed; bottom:0; width:100%; height:var(--nav-h); background:rgba(0,0,0,0.8); backdrop-filter:blur(30px); border-top:1px solid var(--glass-border); display:flex; padding-top:10px; }
.nav-item { flex:1; display:flex; flex-direction:column; align-items:center; color:var(--text4); cursor:pointer; transition:0.2s; }
.nav-item.active { color:var(--accent); }
.nav-icon { font-size:24px; margin-bottom:4px; }
.nav-label { font-size:10px; font-weight:500; }

.lock-card { background:rgba(10,132,255,0.1); border:1px solid var(--accent); border-radius:18px; padding:20px; text-align:center; margin-bottom:12px; }
.btn-pro { width:100%; background:var(--accent); color:#fff; border:none; padding:14px; border-radius:12px; font-weight:600; margin-top:12px; }

#toasts { position:fixed; bottom:100px; left:20px; right:20px; z-index:1000; }
.toast { background:rgba(40,40,40,0.9); padding:12px 20px; border-radius:12px; font-size:14px; margin-top:8px; animation:slideUp 0.3s; }
@keyframes slideUp { from { transform:translateY(20px); opacity:0; } to { transform:translateY(0); opacity:1; } }
</style>
</head>
<body>
<div class="bg-blobs"><div class="blob blob-1"></div><div class="blob blob-2"></div></div>

<header class="topbar">
  <div class="topbar-logo">H</div>
  <div><div style="font-weight:700; font-size:15px;">HELPER TDIU</div><div id="top-sub" style="font-size:11px; color:var(--text3);">Yuklanmoqda...</div></div>
  <div style="margin-left:auto;"><div class="badge-demo" style="background:var(--bg4); font-size:10px; padding:3px 8px; border-radius:20px; color:var(--text3); border:1px solid var(--glass-border);">DEMO</div></div>
</header>

<div id="view-container">
  <div id="home" class="view"></div>
  <div id="grades" class="view"></div>
  <div id="timetable" class="view"></div>
  <div id="navigator" class="view"></div>
</div>

<nav class="bottom-nav">
  <div class="nav-item active" onclick="show('home')"><div class="nav-icon">🏠</div><div class="nav-label">Bosh</div></div>
  <div class="nav-item" onclick="show('grades')"><div class="nav-icon">📊</div><div class="nav-label">Baholar</div></div>
  <div class="nav-item" onclick="show('timetable')"><div class="nav-icon">📅</div><div class="nav-label">Jadval</div></div>
  <div class="nav-item" onclick="show('navigator')"><div class="nav-icon">🗺️</div><div class="nav-label">Navi</div></div>
</nav>

<div id="toasts"></div>

<script>
const tg = window.Telegram?.WebApp; tg?.expand();
const DATA = {
  profile: { gpa: 3.45, group: "IQ-22-01", sem: "2024-2" },
  grades: [
    {s:"Mikroiqtisodiyot", tot:41, cur:17, mid:24, r:false, nb:false},
    {s:"Pul va kredit", tot:30, cur:12, mid:18, r:true, nb:true, need:25},
    {s:"Bank ishi va kredit", tot:37, cur:15, mid:22, r:false, nb:true}
  ],
  timetable: { "2025-04-07": [{n:1, t:"08:30", s:"Matematika", r:"A-301"}] }
};

function toast(m) { const t=document.getElementById('toasts'); const e=document.createElement('div'); e.className='toast'; e.innerHTML="✅ "+m; t.appendChild(e); setTimeout(()=>e.remove(),3000); }

function show(v) {
  tg?.HapticFeedback?.impactOccurred('light');
  document.querySelectorAll('.view').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach((e,i) => e.classList.toggle('active', ['home','grades','timetable','navigator'][i]===v));
  const el = document.getElementById(v); el.classList.add('active');
  if(v==='home') renderHome(); if(v==='grades') renderGrades(); if(v==='timetable') renderTable(); if(v==='navigator') renderNav();
}

function renderHome() {
  const p = DATA.profile;
  const risks = DATA.grades.filter(g => g.r).length;
  const nbs = DATA.grades.filter(g => g.nb).length;

  let html = `
    <div style="background:linear-gradient(135deg, rgba(10,132,255,0.15), transparent); border:1px solid rgba(10,132,255,0.2); border-radius:18px; padding:20px; display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
       <div>
          <div style="font-size:12px; color:var(--accent); font-weight:700; margin-bottom:4px; text-transform:uppercase;">Umumiy GPA</div>
          <div style="font-size:42px; font-weight:800; line-height:1;">${p.gpa.toFixed(2)}</div>
       </div>
       <div style="font-size:14px; color:var(--text3); font-weight:500;">
          ${p.sem}
       </div>
    </div>
  `;

  // Soddalashtirilgan Xavf va NB (takrorlanishlarsiz)
  if (risks > 0 || nbs > 0) {
     html += `<div style="display:flex; gap:10px; margin-bottom:12px;">`;
     if (risks > 0) {
        html += `
          <div style="flex:1; background:rgba(255,69,58,0.15); border:1px solid rgba(255,69,58,0.3); border-radius:16px; padding:14px; display:flex; align-items:center; gap:12px;">
             <div style="font-size:24px;">🚨</div>
             <div>
                <div style="color:var(--red); font-size:18px; font-weight:800; line-height:1;">${risks} ta</div>
                <div style="color:var(--text2); font-size:12px; font-weight:500; margin-top:4px;">Qayta topshirish</div>
             </div>
          </div>`;
     }
     if (nbs > 0) {
        html += `
          <div style="flex:1; background:rgba(255,159,10,0.15); border:1px solid rgba(255,159,10,0.3); border-radius:16px; padding:14px; display:flex; align-items:center; gap:12px;">
             <div style="font-size:24px;">📍</div>
             <div>
                <div style="color:var(--orange); font-size:18px; font-weight:800; line-height:1;">${nbs} ta</div>
                <div style="color:var(--text2); font-size:12px; font-weight:500; margin-top:4px;">Davomat xavfi</div>
             </div>
          </div>`;
     }
     html += `</div>`;
  }

  html += `
    <div class="card" style="margin-bottom:12px;">
      <div style="font-size:14px; font-weight:700; margin-bottom:12px; color:var(--text2);">BUGUNGI DARSLAR</div>
      <div style="color:var(--text4); font-size:13px; text-align:center; padding:10px;">Bugun dam olish kuni ✨</div>
    </div>
    <div class="lock-card">
      <div style="font-size:32px;">👑</div>
      <div style="font-weight:700; margin-top:8px;">Premium Tracker</div>
      <div style="font-size:12px; color:var(--text3); margin-top:5px;">O'qituvchilar qayerdaligini real-vaqtda ko'ring.</div>
      <button class="btn-pro" onclick="toast('Tez kunda!')">PRO — 5,000 so'm</button>
    </div>
  `;
  document.getElementById('home').innerHTML = html;
}

function renderGrades() {
  document.getElementById('grades').innerHTML = `
    <div class="card" style="padding:10px;"><canvas id="chart" style="height:180px;"></canvas></div>
    ${DATA.grades.map(g => `<div class="card"><div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:600;">${g.s}</div><div style="font-size:11px; color:var(--text3);">J: ${g.cur} | O: ${g.mid}</div></div><div style="font-size:22px; font-weight:800; color:${g.r?'var(--red)':'var(--green)'}">${g.tot}</div></div>${g.r?`<div style="font-size:11px; color:var(--red); margin-top:8px; padding-top:8px; border-top:1px solid rgba(255,69,58,0.2);">⚠️ Yakuniyda ${g.need}/50 ball kerak</div>`:''}</div>`).join('')}
  `;
  new Chart(document.getElementById('chart'), { type:'radar', data:{ labels:['M','P','B','S','I'], datasets:[{data:[41,30,45,38,42], backgroundColor:'rgba(10,132,255,0.2)', borderColor:'#0a84ff', borderWidth:2}] }, options:{ scales:{ r:{ ticks:{display:false}, grid:{color:'rgba(255,255,255,0.1)'} } }, plugins:{legend:{display:false}} } });
}

function renderTable() {
  const d = new Date(); const start = new Date(d); start.setDate(d.getDate() - (d.getDay()===0?6:d.getDay()-1));
  const days = Array.from({length:7}, (_,i) => { const curr=new Date(start); curr.setDate(start.getDate()+i); return {n:["Du","Se","Ch","Pa","Ju","Sh","Ya"][i], d:curr.getDate(), iso:curr.toISOString().split('T')[0]}; });
  document.getElementById('timetable').innerHTML = `
    <div style="text-align:center; margin-bottom:15px; font-size:13px; font-weight:600; color:var(--text2);">${start.getDate()}.${start.getMonth()+1} - ${days[6].d}.${days[6].iso.split('-')[1]} · 2026</div>
    <div class="day-tabs">${days.map((x,i) => `<div class="day-tab ${i===d.getDay()-1||(d.getDay()===0&&i===6)?'active':''}" onclick="toast('${x.n} kuni tanlandi')"><div class="day-name">${x.n}</div><div class="day-num">${x.d}</div></div>`).join('')}</div>
    <div class="card" style="text-align:center; padding:40px 20px;"><div style="font-size:40px; margin-bottom:10px;">🎉</div><div style="font-weight:600;">Darslar yo'q!</div><div style="font-size:12px; color:var(--text3); margin-top:5px;">Mazaza qilib dam oling.</div></div>
  `;
}

function renderNav() {
  document.getElementById('navigator').innerHTML = `
    <div style="display:flex; gap:10px; margin-bottom:15px;"><div style="flex:1; background:var(--accent); color:#fff; padding:12px; border-radius:12px; text-align:center; font-weight:600; font-size:13px;">🏛️ Xonalar</div><div style="flex:1; background:var(--bg3); padding:12px; border-radius:12px; text-align:center; font-size:13px;" onclick="toast('PRO funksiya')">👨‍🏫 Ustozlar</div></div>
    <div class="card" style="padding:12px 16px; color:var(--text4);">🔍 Qidiruv...</div>
    <div class="card"><div style="font-weight:600; color:var(--accent);">A-301</div><div style="font-size:12px; color:var(--text3);">A blok, 3-qavat (Ma'ruza)</div></div>
  `;
}

window.onload = () => { document.getElementById('top-sub').innerHTML = DATA.profile.group; show('home'); };
</script>
</body>
</html>"""

# ── Server sozlamalari ───────────────────────────────────────
app = FastAPI(lifespan=lifespan)
@app.get("/")
async def root(): return {"status":"ok"}
@app.get("/app", response_class=HTMLResponse)
async def mini_app(): return MINI_APP_HTML
