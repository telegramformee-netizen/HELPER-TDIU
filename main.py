"""
main.py - HELPER TDIU
FastAPI + aiogram bot (to'g'ri async arxitektura)
"""
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import config
from database import init_db

# ── Mini App HTML ─────────────────────────────────────────────────────────────
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>HELPER · TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:var(--tg-theme-bg-color,#0f0f14);
color:var(--tg-theme-text-color,#fff);min-height:100vh}
.topbar{position:fixed;top:0;left:0;right:0;height:56px;
background:var(--tg-theme-secondary-bg-color,#1a1a24);
display:flex;align-items:center;padding:0 16px;gap:12px;
border-bottom:1px solid rgba(255,255,255,0.08);z-index:50}
.logo{width:32px;height:32px;border-radius:8px;background:#6c63ff;color:#fff;
font-size:16px;font-weight:900;display:flex;align-items:center;justify-content:center}
.topbar-title{font-size:15px;font-weight:700}
.topbar-sub{font-size:11px;opacity:0.5}
.content{padding:72px 16px 80px;display:flex;flex-direction:column;gap:12px}
.card{background:var(--tg-theme-secondary-bg-color,#1a1a24);
border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px}
.card-title{font-size:12px;font-weight:600;opacity:0.5;
text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px}
.gpa-big{font-size:52px;font-weight:900;color:#a78bfa;text-align:center;padding:12px 0}
.stat-row{display:flex;gap:10px}
.stat{flex:1;background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;text-align:center}
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
.bottom-nav{position:fixed;bottom:0;left:0;right:0;height:64px;
background:var(--tg-theme-secondary-bg-color,#1a1a24);
border-top:1px solid rgba(255,255,255,0.08);
display:flex;align-items:center;z-index:50}
.nav-btn{flex:1;display:flex;flex-direction:column;align-items:center;
gap:3px;padding:8px 4px;background:none;border:none;
cursor:pointer;color:rgba(255,255,255,0.35);font-size:10px;font-weight:600}
.nav-btn.active{color:#6c63ff}
.nav-icon{font-size:22px;line-height:1}
</style>
</head>
<body>
<div class="topbar">
  <div class="logo">H</div>
  <div>
    <div class="topbar-title">HELPER</div>
    <div class="topbar-sub">TDIU</div>
  </div>
</div>
<div class="content" id="content">
  <div style="text-align:center;padding:40px;opacity:0.4">Yuklanmoqda...</div>
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
const D = {
  profile:{name:"Demo Talaba",group:"IM-22-01",faculty:"Iqtisodiyot",gpa:3.45},
  grades:[
    {s:"Mikroiqtisodiyot",cur:17,mid:24,fin:null,tot:41,risk:false,nb:false},
    {s:"Bank ishi",cur:15,mid:22,fin:null,tot:37,risk:false,nb:true},
    {s:"Iqtisodiy siyosat",cur:18,mid:28,fin:null,tot:46,risk:false,nb:false},
    {s:"Pul va kredit",cur:12,mid:18,fin:null,tot:30,risk:true,nb:true},
    {s:"Marketing",cur:19,mid:26,fin:null,tot:45,risk:false,nb:false},
  ],
  schedule:[
    {num:1,start:"08:30",end:"09:50",s:"Mikroiqtisodiyot",type:"Ma'ruza",teacher:"Salimov B.",room:"A-301"},
    {num:3,start:"11:30",end:"12:50",s:"Bank ishi",type:"Seminar",teacher:"Rahimov N.",room:"B-204"},
  ]
};
function showTab(tab) {
  document.querySelectorAll('.nav-btn').forEach((b,i)=>{
    b.classList.toggle('active',['home','grades','schedule','navigator'][i]===tab);
  });
  const c=document.getElementById('content');
  if(tab==='home') renderHome(c);
  else if(tab==='grades') renderGrades(c);
  else if(tab==='schedule') renderSchedule(c);
  else renderNavigator(c);
}
function renderHome(c) {
  const risks=D.grades.filter(g=>g.risk).length;
  const nbs=D.grades.filter(g=>g.nb).length;
  c.innerHTML=`
    <div class="card">
      <div class="card-title">Umumiy GPA</div>
      <div class="gpa-big">${D.profile.gpa}</div>
      <div style="text-align:center;opacity:0.5;font-size:13px">${D.profile.group}</div>
    </div>
    <div class="stat-row">
      <div class="stat"><div class="stat-val" style="color:${risks>0?'#ef4444':'#22c55e'}">${risks}</div><div class="stat-lbl">Xavf</div></div>
      <div class="stat"><div class="stat-val" style="color:${nbs>0?'#f97316':'#22c55e'}">${nbs}</div><div class="stat-lbl">NB</div></div>
      <div class="stat"><div class="stat-val">${D.schedule.length}</div><div class="stat-lbl">Dars</div></div>
    </div>
    ${risks>0?'<div class="alert danger"><span>🚨</span><div>'+risks+' ta fanda qayta topshirish xavfi!</div></div>':''}
    ${nbs>0?'<div class="alert warn"><span>📍</span><div>'+nbs+' ta fanda davomat chegarasiga yaqin!</div></div>':''}
    <div class="alert info"><span>👀</span><div>Demo rejim — namunali maʼlumotlar.</div></div>
  `;
}
function renderGrades(c) {
  const gpa=(D.grades.reduce((s,g)=>s+g.tot,0)/D.grades.length/25).toFixed(2);
  c.innerHTML='<div class="card"><div style="display:flex;justify-content:space-between"><div><div class="card-title">GPA</div><div style="font-size:32px;font-weight:800;color:#a78bfa">'+gpa+'</div></div><div style="text-align:right"><div class="card-title">Fanlar</div><div style="font-size:32px;font-weight:800">'+D.grades.length+'</div></div></div></div>'
    +D.grades.map(g=>{
      const c2=g.tot>=86?'#22c55e':g.tot>=71?'#a78bfa':g.tot>=55?'#f97316':'#ef4444';
      const l=g.tot>=86?'A':g.tot>=71?'B':g.tot>=55?'C':'D';
      return '<div class="card" style="margin-bottom:0;border-color:'+(g.risk?'rgba(239,68,68,.4)':g.nb?'rgba(249,115,22,.3)':'rgba(255,255,255,.08)')+'"><div style="display:flex;justify-content:space-between;margin-bottom:10px"><div style="font-size:14px;font-weight:600;flex:1">'+g.s+'</div><div style="font-size:22px;font-weight:800;color:'+c2+';margin-left:8px">'+g.tot+'</div></div><div style="height:6px;background:rgba(255,255,255,.1);border-radius:99px;margin-bottom:10px"><div style="width:'+g.tot+'%;height:100%;background:'+c2+';border-radius:99px"></div></div><div style="font-size:11px;opacity:.5">Joriy: '+g.cur+'/20 · Oraliq: '+g.mid+'/30 · Yakuniy: '+(g.fin||'—')+'/50</div><div style="margin-top:8px"><span style="background:rgba(255,255,255,.08);padding:2px 8px;border-radius:99px;font-size:11px">'+l+'</span>'+(g.risk?' <span style="background:rgba(239,68,68,.15);color:#fca5a5;padding:2px 8px;border-radius:99px;font-size:11px">⚠️ Xavf</span>':'')+(g.nb?' <span style="background:rgba(249,115,22,.15);color:#fdba74;padding:2px 8px;border-radius:99px;font-size:11px">📍 NB</span>':'')+'</div></div>';
    }).join('');
}
function renderSchedule(c) {
  const days=['Dushanba','Seshanba','Chorshanba','Payshanba','Juma','Shanba','Yakshanba'];
  const today=days[new Date().getDay()===0?6:new Date().getDay()-1];
  c.innerHTML='<div class="card"><div class="card-title">📅 '+today+' — Bugungi jadval</div>'
    +D.schedule.map(l=>'<div class="lesson"><div class="lesson-time">'+l.num+'-dars · '+l.start+' – '+l.end+'</div><div class="lesson-name">'+l.s+'</div><div class="lesson-meta">📍 '+l.room+' · 👤 '+l.teacher+'</div></div>').join('')
    +'</div>';
}
function renderNavigator(c) {
  const rooms=[
    {code:"A-101",b:"A blok",f:1,t:"Ma'ruza zali"},
    {code:"A-201",b:"A blok",f:2,t:"Ma'ruza zali"},
    {code:"A-301",b:"A blok",f:3,t:"Ma'ruza zali"},
    {code:"B-101",b:"B blok",f:1,t:"Seminar xona"},
    {code:"B-204",b:"B blok",f:2,t:"Seminar xona"},
    {code:"C-101",b:"C blok",f:1,t:"Kompyuter lab"},
  ];
  c.innerHTML='<div style="background:rgba(255,255,255,.05);border-radius:12px;display:flex;align-items:center;gap:10px;padding:12px 14px;margin-bottom:12px"><span>🔍</span><input id="rs" placeholder="Auditoriya qidirish..." style="background:none;border:none;outline:none;color:inherit;font-size:14px;flex:1" oninput="fr(this.value)"></div><div id="rl">'
    +rooms.map(r=>'<div class="card" style="display:flex;align-items:center;gap:14px;padding:12px;margin-bottom:8px"><div style="font-size:16px;font-weight:700;color:#a78bfa;width:56px">'+r.code+'</div><div><div style="font-size:13px;font-weight:500">'+r.t+'</div><div style="font-size:11px;opacity:.5">'+r.b+' · '+r.f+'-qavat</div></div></div>').join('')
    +'</div>';
}
function fr(q){document.querySelectorAll('#rl .card').forEach(el=>{el.style.display=el.textContent.toLowerCase().includes(q.toLowerCase())?'':'none'});}
renderHome(document.getElementById('content'));
</script>
</body>
</html>"""


# ── Bot background task ───────────────────────────────────────────────────────
_bot_task = None

async def run_bot_async():
    """Bot polling - to'g'ri async, main thread'da"""
    if not config.BOT_TOKEN:
        print("BOT_TOKEN yo'q!")
        return
    from bot import create_bot, create_dispatcher
    bot = create_bot()
    dp  = create_dispatcher()
    print("Bot polling boshlandi...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        print("Bot xatosi: " + str(e))


# ── FastAPI lifespan ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("Database tayyor")

    # Bot ni asyncio task sifatida ishga tushirish (thread emas!)
    global _bot_task
    if config.BOT_TOKEN:
        _bot_task = asyncio.create_task(run_bot_async())
        print("Bot task boshlandi")

    yield

    # Shutdown
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="HELPER TDIU", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "app": "HELPER TDIU"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    return MINI_APP_HTML
