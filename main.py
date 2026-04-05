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
# MINI APP HTML — iOS 18 Glassmorphism UI
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #000000;
  --text: #ffffff;
  --text-sec: rgba(235, 235, 245, 0.6);
  --accent: #0a84ff;
  --green: #30d158;
  --red: #ff453a;
  --orange: #ff9f0a;
  --card-bg: rgba(28, 28, 30, 0.6);
  --glass-border: rgba(255, 255, 255, 0.1);
  --nav-h: 85px;
  --top-h: 60px;
}

* { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
body {
  font-family: 'Inter', -apple-system, sans-serif;
  background-color: var(--bg);
  color: var(--text);
  overflow: hidden;
  height: 100vh;
  position: relative;
}

/* ── Dynamic Blurred Background ── */
.bg-blobs {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
  overflow: hidden; filter: blur(80px); opacity: 0.4;
}
.blob {
  position: absolute; border-radius: 50%;
  animation: float 20s infinite alternate ease-in-out;
}
.blob-1 { width: 300px; height: 300px; background: #0a84ff; top: -10%; left: -10%; animation-delay: 0s; }
.blob-2 { width: 400px; height: 400px; background: #bf5af2; bottom: -20%; right: -10%; animation-delay: -5s; }
.blob-3 { width: 250px; height: 250px; background: #30d158; top: 40%; left: 50%; animation-delay: -10s; }

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(50px, 50px) scale(1.1); }
}

/* ── Layout ── */
.topbar {
  position: fixed; top: 0; width: 100%; height: var(--top-h);
  background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
  display: flex; align-items: center; justify-content: space-between; padding: 0 20px;
  z-index: 100; border-bottom: 1px solid var(--glass-border);
}
.top-title { font-weight: 700; font-size: 17px; }
.top-subtitle { font-size: 12px; color: var(--text-sec); }

.view-container {
  position: relative; width: 100%; height: 100%; overflow: hidden;
}
.view {
  position: absolute; top: var(--top-h); left: 0; width: 100%; height: calc(100% - var(--top-h) - var(--nav-h));
  overflow-y: auto; padding: 15px 15px 30px;
  opacity: 0; transform: translateX(20px); pointer-events: none;
  transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}
.view.active {
  opacity: 1; transform: translateX(0); pointer-events: auto;
}

/* ── Glass Cards ── */
.card {
  background: var(--card-bg);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 20px; padding: 20px; margin-bottom: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

/* ── Typography & Numbers ── */
.hero-gpa {
  font-size: 72px; font-weight: 800; line-height: 1;
  background: linear-gradient(135deg, #fff, #a1a1aa);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 10px 0; text-align: center;
}
.gpa-label { text-align: center; font-size: 14px; color: var(--text-sec); font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}

/* ── Grid Stats ── */
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
.stat-box {
  background: var(--card-bg); border: 1px solid var(--glass-border);
  border-radius: 16px; padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.stat-val { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.stat-title { font-size: 11px; color: var(--text-sec); text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Chart Container ── */
.chart-container { position: relative; height: 200px; width: 100%; margin-top: 10px; }

/* ── List Items ── */
.list-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.list-item:last-child { border-bottom: none; padding-bottom: 0; }
.li-title { font-size: 15px; font-weight: 600; }
.li-sub { font-size: 12px; color: var(--text-sec); margin-top: 4px; }
.li-right { font-size: 18px; font-weight: 700; }

/* ── Bottom Nav ── */
.bottom-nav {
  position: fixed; bottom: 0; width: 100%; height: var(--nav-h);
  background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
  border-top: 1px solid var(--glass-border); display: flex; padding-bottom: 15px; z-index: 100;
}
.nav-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: var(--text-sec); cursor: pointer; transition: 0.2s;
}
.nav-btn.active { color: var(--accent); }
.nav-icon { font-size: 24px; margin-bottom: 4px; transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.nav-btn:active .nav-icon { transform: scale(0.8); }
.nav-label { font-size: 10px; font-weight: 500; }

</style>
</head>
<body>

<div class="bg-blobs">
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>
  <div class="blob blob-3"></div>
</div>

<header class="topbar">
  <div>
    <div class="top-title">HELPER TDIU</div>
    <div class="top-subtitle">IQ-22-01 · Iqtisodiyot</div>
  </div>
  <div style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">
    DEMO
  </div>
</header>

<div class="view-container">
  
  <div id="view-home" class="view active">
    <div class="card" style="margin-top: 10px; padding-top: 30px; padding-bottom: 30px;">
      <div class="gpa-label">Umumiy GPA</div>
      <div class="hero-gpa" id="gpa-counter">0.00</div>
    </div>

    <div class="stats-grid">
      <div class="stat-box">
        <div class="stat-val" style="color: var(--red);">2</div>
        <div class="stat-title">Xavf</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" style="color: var(--orange);">1</div>
        <div class="stat-title">NB Ogohlantirish</div>
      </div>
    </div>

    <div class="card">
      <h3 style="font-size: 14px; margin-bottom: 15px; color: var(--text-sec);">BUGUNGI DARSLAR</h3>
      <div class="list-item">
        <div>
          <div class="li-title">Mikroiqtisodiyot</div>
          <div class="li-sub">08:30 - 09:50 · Ma'ruza</div>
        </div>
        <div class="li-right" style="font-size:14px; color: var(--accent);">A-301</div>
      </div>
      <div class="list-item">
        <div>
          <div class="li-title">Bank ishi va kredit</div>
          <div class="li-sub">11:30 - 12:50 · Seminar</div>
        </div>
        <div class="li-right" style="font-size:14px; color: var(--accent);">B-204</div>
      </div>
    </div>
  </div>

  <div id="view-grades" class="view">
    <div class="card">
      <h3 style="font-size: 14px; margin-bottom: 5px; color: var(--text-sec); text-align: center;">O'ZLASHTIRISH GRAFIGI</h3>
      <div class="chart-container">
        <canvas id="radarChart"></canvas>
      </div>
    </div>

    <div class="card">
      <h3 style="font-size: 14px; margin-bottom: 15px; color: var(--text-sec);">BARCHA FANLAR</h3>
      
      <div class="list-item">
        <div>
          <div class="li-title">Iqtisodiy siyosat</div>
          <div class="li-sub">J: 18 · O: 28</div>
        </div>
        <div class="li-right" style="color: var(--green);">46</div>
      </div>
      
      <div class="list-item">
        <div>
          <div class="li-title">Marketing asoslari</div>
          <div class="li-sub">J: 19 · O: 26</div>
        </div>
        <div class="li-right" style="color: var(--green);">45</div>
      </div>
      
      <div class="list-item">
        <div>
          <div class="li-title">Mikroiqtisodiyot</div>
          <div class="li-sub">J: 17 · O: 24</div>
        </div>
        <div class="li-right" style="color: var(--accent);">41</div>
      </div>

      <div class="list-item">
        <div>
          <div class="li-title">Pul va kredit</div>
          <div class="li-sub" style="color: var(--red);">Yakuniyda 25 kerak</div>
        </div>
        <div class="li-right" style="color: var(--red);">30</div>
      </div>
    </div>
  </div>

  <div id="view-timetable" class="view">
     <div class="card">
        <div style="text-align: center; padding: 40px 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">🚧</div>
            <div style="font-size: 18px; font-weight: 600;">Jadval tayyorlanmoqda</div>
            <div style="font-size: 13px; color: var(--text-sec); margin-top: 5px;">Tez kunda yangi dizaynda ishga tushadi.</div>
        </div>
     </div>
  </div>

</div>

<nav class="bottom-nav">
  <div class="nav-btn active" id="nav-home" onclick="nav('home')">
    <div class="nav-icon">🏠</div>
    <div class="nav-label">Bosh</div>
  </div>
  <div class="nav-btn" id="nav-grades" onclick="nav('grades')">
    <div class="nav-icon">📊</div>
    <div class="nav-label">Baholar</div>
  </div>
  <div class="nav-btn" id="nav-timetable" onclick="nav('timetable')">
    <div class="nav-icon">📅</div>
    <div class="nav-label">Jadval</div>
  </div>
</nav>

<script>
const tg = window.Telegram?.WebApp;
tg?.expand();
tg?.disableVerticalSwipes?.();

function haptic() { tg?.HapticFeedback?.impactOccurred('light'); }

// Navigation logic with animations
function nav(viewId) {
  haptic();
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('nav-' + viewId).classList.add('active');

  document.querySelectorAll('.view').forEach(v => {
    v.style.opacity = '0';
    v.style.transform = 'translateX(-20px)';
    v.classList.remove('active');
  });

  const activeView = document.getElementById('view-' + viewId);
  activeView.classList.add('active');
  activeView.style.transform = 'translateX(20px)';
  
  setTimeout(() => {
    activeView.style.opacity = '1';
    activeView.style.transform = 'translateX(0)';
  }, 50);
  
  if(viewId === 'grades') renderChart();
}

// Number Counter Animation
function animateValue(id, start, end, duration) {
    if (start === end) return;
    var range = end - start;
    var current = start;
    var increment = end > start? 0.05 : -0.05;
    var stepTime = Math.abs(Math.floor(duration / (range / increment)));
    var obj = document.getElementById(id);
    var timer = setInterval(function() {
        current += increment;
        obj.innerHTML = current.toFixed(2);
        if (current >= end) {
            clearInterval(timer);
            obj.innerHTML = end.toFixed(2);
        }
    }, stepTime);
}

// Chart.js Setup
let myChart = null;
function renderChart() {
    if(myChart) return; // Prevent recreation
    const ctx = document.getElementById('radarChart').getContext('2d');
    
    Chart.defaults.color = 'rgba(235, 235, 245, 0.6)';
    Chart.defaults.font.family = 'Inter';
    
    myChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Mikroiq.', 'Bank ishi', 'Siyosat', 'Pul-kredit', 'Marketing'],
            datasets: [{
                label: 'Ball',
                data: [41, 37, 46, 30, 45],
                backgroundColor: 'rgba(10, 132, 255, 0.2)',
                borderColor: 'rgba(10, 132, 255, 1)',
                pointBackgroundColor: '#fff',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: { font: { size: 10 } },
                    ticks: { display: false, max: 50, min: 0 }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// Init
window.onload = () => {
    setTimeout(() => {
        animateValue("gpa-counter", 0.00, 3.45, 1200);
    }, 300);
};
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
