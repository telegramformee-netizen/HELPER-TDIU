"""
main.py — HELPER TDIU
FastAPI (web server) + aiogram bot (background thread)
"""
import asyncio
import threading
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import config
from database import init_db

app = FastAPI(title="HELPER TDIU")

# ── HTML Mini App ─────────────────────────────────────────────────────────────
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:system-ui,sans-serif;
  background:var(--tg-theme-bg-color,#0f0f14);
  color:var(--tg-theme-text-color,#fff);
  min-height:100vh;
}
.topbar{
  position:fixed;top:0;left:0;right:0;height:56px;
  background:var(--tg-theme-secondary-bg-color,#1a1a24);
  display:flex;align-items:center;padding:0 16px;gap:12px;
  border-bottom:1px solid rgba(255,255,255,0.08);z-index:50;
}
.logo{
  width:32px;height:32px;border-radius:8px;
  background:#6c63ff;color:#fff;
  font-size:16px;font-weight:900;
  display:flex;align-items:center;justify-content:center;
}
.topbar-title{font-size:15px;font-weight:700}
.topbar-sub{font-size:11px;opacity:0.5}
.content{
  padding:72px 16px 90px;
  display:flex;flex-direction:column;gap:12px;
}
.card{
  background:var(--tg-theme-secondary-bg-color,#1a1a24);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:16px;padding:16px;
}
.card-title{font-size:12px;font-weight:600;opacity:0.5;
  text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px}
.gpa-big{
  font-size:52px;font-weight:900;color:#a78bfa;
  text-align:center;padding:12px 0;
}
.stat-row{display:flex;gap:10px}
.stat{flex:1;background:rgba(255,255,255,0.04);border-radius:12px;
  padding:12px;text-align:center}
.stat-val{font-size:24px;font-weight:800;color:#a78bfa}
.stat-lbl{font-size:11px;opacity:0.5;margin-top:4px}
.alert{display:flex;gap:10px;padding:12px;border-radius:12px;
  font-size:13px;line-height:1.5;margin-bottom:6px}
.alert.warn{background:rgba(249,115,22,.1);border:1px solid rgba(249,115,22,.25);color:#fdba74}
.alert.danger{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);color:#fca5a5}
.alert.info{background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.25);color:#c4b5fd}
.lesson{padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06)}
.lesson:last-child{border-bottom:none}
.lesson-time{font-size:11px;opacity:0.5;font-weight:600}
.lesson-name{font-size:14px;font-weight:600;margin:3px 0}
.lesson-meta{font-size:12px;opacity:0.5}
.bottom-nav{
  position:fixed;bottom:0;left:0;right:0;height:64px;
  background:var(--tg-theme-secondary-bg-color,#1a1a24);
  border-top:1px solid rgba(255,255,255,0.08);
  display:flex;align-items:center;z-index:50;
}
.nav-btn{
  flex:1;display:flex;flex-direction:column;align-items:center;
  gap:3px;padding:8px 4px;background:none;border:none;
  cursor:pointer;color:rgba(255,255,255,0.35);font-size:10px;font-weight:600;
  transition:color 0.2s;
}
.nav-btn.active{color:#6c63ff}
.nav-icon{font-size:22px;line-height:1}
.loading{text-align:center;padding:40px;opacity:0.4;font-size:14px}
.hidden{display:none}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">H</div>
  <div>
    <div class="topbar-title">HELPER</div>
    <div class="topbar-sub" id="user-group">TDIU</div>
  </div>
</div>

<div class="content" id="content">
  <div class="loading">⏳ Yuklanmoqda...</div>
</div>

<nav class="bottom-nav">
  <button class="nav-btn active" onclick="showTab('home')">
    <span class="nav-icon">🏠</span>Bosh
  </button>
  <button class="nav-btn" onclick="showTab('grades')">
    <span class="nav-icon">📊</span>Baholar
  </button>
  <button class="nav-btn" onclick="showTab('schedule')">
    <span class="nav-icon">📅</span>Jadval
  </button>
  <button class="nav-btn" onclick="showTab('navigator')">
    <span class="nav-icon">🗺️</span>Navigator
  </button>
</nav>

<script>
const tg = window.Telegram?.WebApp;
tg?.expand();
tg?.disableVerticalSwipes?.();

// Demo ma'lumotlar
const DEMO = {
  profile: {name:"Demo Talaba", group:"IM-22-01", faculty:"Iqtisodiyot", gpa:3.45},
  grades:[
    {s:"Mikroiqtisodiyot",cur:17,mid:24,fin:null,tot:41,risk:false,nb:false},
    {s:"Bank ishi",       cur:15,mid:22,fin:null,tot:37,risk:false,nb:true},
    {s:"Iqtisodiy siyosat",cur:18,mid:28,fin:null,tot:46,risk:false,nb:false},
    {s:"Pul va kredit",   cur:12,mid:18,fin:null,tot:30,risk:true,nb:true},
    {s:"Marketing",       cur:19,mid:26,fin:null,tot:45,risk:false,nb:false},
  ],
  schedule:[
    {num:1,start:"08:30",end:"09:50",s:"Mikroiqtisodiyot",type:"Ma'ruza",teacher:"Salimov B.",room:"A-301"},
    {num:3,start:"11:30",end:"12:50",s:"Bank ishi",type:"Seminar",teacher:"Rahimov N.",room:"B-204"},
  ]
};

function showTab(tab) {
  document.querySelectorAll('.nav-btn').forEach((b,i)=>{
    b.classList.toggle('active', ['home','grades','schedule','navigator'][i]===tab);
  });
  const c = document.getElementById('content');
  if(tab==='home')      renderHome(c);
  else if(tab==='grades')    renderGrades(c);
  else if(tab==='schedule')  renderSchedule(c);
  else if(tab==='navigator') renderNavigator(c);
}

function renderHome(c) {
  const p = DEMO.profile;
  const risks = DEMO.grades.filter(g=>g.risk).length;
  const nbs   = DEMO.grades.filter(g=>g.nb).length;
  c.innerHTML = `
    <div class="card">
      <div class="card-title">Umumiy GPA</div>
      <div class="gpa-big">${p.gpa}</div>
      <div style="text-align:center;opacity:0.5;font-size:13px">${p.group} · ${p.faculty}</div>
    </div>
    <div class="stat-row">
      <div class="stat">
        <div class="stat-val" style="color:${risks>0?'#ef4444':'#22c55e'}">${risks}</div>
        <div class="stat-lbl">Xavf ostida</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="color:${nbs>0?'#f97316':'#22c55e'}">${nbs}</div>
        <div class="stat-lbl">NB ogohlantirish</div>
      </div>
      <div class="stat">
        <div class="stat-val">${DEMO.schedule.length}</div>
        <div class="stat-lbl">Bugungi dars</div>
      </div>
    </div>
    ${risks>0?`<div class="alert danger"><span>🚨</span><div>${risks} ta fanda qayta topshirish xavfi bor!</div></div>`:''}
    ${nbs>0?`<div class="alert warn"><span>📍</span><div>${nbs} ta fanda davomat chegarasiga yaqin!</div></div>`:''}
    <div class="alert info"><span>👀</span><div>Demo rejim — namunali ma'lumotlar ko'rsatilmoqda.</div></div>
  `;
}

function renderGrades(c) {
  const gpa = (DEMO.grades.reduce((s,g)=>s+g.tot,0)/DEMO.grades.length/25).toFixed(2);
  c.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div class="card-title">GPA</div>
          <div style="font-size:32px;font-weight:800;color:#a78bfa">${gpa}</div>
        </div>
        <div style="text-align:right">
          <div class="card-title">Fanlar</div>
          <div style="font-size:32px;font-weight:800">${DEMO.grades.length}</div>
        </div>
      </div>
    </div>
    ${DEMO.grades.map(g=>{
      const pct = Math.min(g.tot/100*100,100);
      const clr = g.tot>=86?'#22c55e':g.tot>=71?'#a78bfa':g.tot>=55?'#f97316':'#ef4444';
      const ltr = g.tot>=86?'A':g.tot>=71?'B':g.tot>=55?'C':'D';
      return `
      <div class="card" style="border-color:${g.risk?'rgba(239,68,68,.4)':g.nb?'rgba(249,115,22,.3)':'rgba(255,255,255,0.08)'}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
          <div style="font-size:14px;font-weight:600;flex:1">${g.s}</div>
          <div style="font-size:22px;font-weight:800;color:${clr};margin-left:8px">${g.tot}</div>
        </div>
        <div style="height:6px;background:rgba(255,255,255,.1);border-radius:99px;margin-bottom:10px">
          <div style="width:${pct}%;height:100%;background:${clr};border-radius:99px;transition:width .6s"></div>
        </div>
        <div style="display:flex;gap:6px;font-size:11px;color:rgba(255,255,255,.5)">
          <span>Joriy: ${g.cur}/20</span>·
          <span>Oraliq: ${g.mid}/30</span>·
          <span>Yakuniy: ${g.fin??'—'}/50</span>
        </div>
        <div style="display:flex;gap:6px;margin-top:8px">
          <span style="background:rgba(255,255,255,.08);padding:2px 8px;border-radius:99px;font-size:11px">${ltr}</span>
          ${g.risk?'<span style="background:rgba(239,68,68,.15);color:#fca5a5;padding:2px 8px;border-radius:99px;font-size:11px">⚠️ Xavf</span>':''}
          ${g.nb?'<span style="background:rgba(249,115,22,.15);color:#fdba74;padding:2px 8px;border-radius:99px;font-size:11px">📍 NB</span>':''}
        </div>
      </div>`;
    }).join('')}
  `;
}

function renderSchedule(c) {
  const days = ['Dushanba','Seshanba','Chorshanba','Payshanba','Juma','Shanba','Yakshanba'];
  const today = days[new Date().getDay()===0?6:new Date().getDay()-1];
  c.innerHTML = `
    <div class="card">
      <div class="card-title">📅 ${today} — Bugungi jadval</div>
      ${DEMO.schedule.length===0
        ?'<div style="text-align:center;padding:20px;opacity:.5">🎉 Bugun darslar yo\'q!</div>'
        :DEMO.schedule.map(l=>`
        <div class="lesson">
          <div class="lesson-time">${l.num}-dars · ${l.start} – ${l.end}</div>
          <div class="lesson-name">${l.s}</div>
          <div class="lesson-meta">📍 ${l.room} · 👤 ${l.teacher} · ${l.type}</div>
        </div>`).join('')}
    </div>
  `;
}

function renderNavigator(c) {
  const rooms=[
    {code:"A-101",building:"A blok",floor:1,type:"Ma'ruza zali",cap:120},
    {code:"A-201",building:"A blok",floor:2,type:"Ma'ruza zali",cap:80},
    {code:"A-301",building:"A blok",floor:3,type:"Ma'ruza zali",cap:100},
    {code:"B-101",building:"B blok",floor:1,type:"Seminar xona",cap:50},
    {code:"B-204",building:"B blok",floor:2,type:"Seminar xona",cap:30},
    {code:"C-101",building:"C blok",floor:1,type:"Kompyuter lab",cap:40},
  ];
  c.innerHTML = `
    <div style="background:rgba(255,255,255,.05);border-radius:12px;
      display:flex;align-items:center;gap:10px;padding:12px 14px;margin-bottom:12px">
      <span>🔍</span>
      <input id="room-search" placeholder="Auditoriya qidirish..."
        style="background:none;border:none;outline:none;color:inherit;font-size:14px;flex:1"
        oninput="filterRooms(this.value)">
    </div>
    <div id="rooms-list">
      ${rooms.map(r=>`
        <div class="card" style="display:flex;align-items:center;gap:14px;padding:12px 14px;margin-bottom:8px">
          <div style="font-size:16px;font-weight:700;color:#a78bfa;width:56px">${r.code}</div>
          <div style="flex:1">
            <div style="font-size:13px;font-weight:500">${r.type}</div>
            <div style="font-size:11px;opacity:.5">${r.building} · ${r.floor}-qavat · ${r.cap} o'rin</div>
          </div>
        </div>`).join('')}
    </div>
  `;
}

function filterRooms(q) {
  document.querySelectorAll('#rooms-list .card').forEach(el=>{
    el.style.display = el.textContent.toLowerCase().includes(q.toLowerCase())?'':'none';
  });
}

// Boshlash
renderHome(document.getElementById('content'));
</script>
</body>
</html>"""


# ── FastAPI Endpoints ──────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "app": "HELPER TDIU", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    return MINI_APP_HTML


# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    # Ma'lumotlar bazasini yaratish
    await init_db()
    print("✅ Database tayyor")

    # Botni alohida thread'da ishga tushirish
    if config.BOT_TOKEN:
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from bot import start_bot
            loop.run_until_complete(start_bot())

        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        print("🤖 Bot thread boshlandi")
    else:
        print("⚠️  BOT_TOKEN yo'q — Railway Variables'ga qo'shing!")
