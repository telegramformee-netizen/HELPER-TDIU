import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB bor bo'lsa init qilamiz
    if settings.database_url:
        try:
            from app.db.base import init_db
            await init_db()
        except Exception as e:
            print(f"DB xato: {e}")
    yield

app = FastAPI(title="HELPER TDIU API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static fayllar
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "HELPER TDIU"}


@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    # Fayl mavjud bo'lsa o'qiymiz
    if os.path.exists("frontend/templates/index.html"):
        with open("frontend/templates/index.html", encoding="utf-8") as f:
            return f.read()
    return """<!DOCTYPE html>
<html lang="uz"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HELPER TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0f0f14;color:#fff;
min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{text-align:center;padding:40px 24px}
.logo{font-size:72px;font-weight:900;color:#6c63ff;margin-bottom:16px}
.title{font-size:28px;font-weight:700;margin-bottom:8px}
.sub{font-size:14px;color:#888;margin-bottom:32px}
.badge{background:rgba(34,197,94,.15);color:#22c55e;
border:1px solid rgba(34,197,94,.3);padding:10px 24px;border-radius:999px;
display:inline-block;font-size:14px;font-weight:600}
</style></head>
<body><div class="card">
<div class="logo">H</div>
<div class="title">HELPER TDIU</div>
<div class="sub">TDIU Talaba Yordamchisi</div>
<div class="badge">✅ Bot ishlayapti!</div>
</div>
<script>window.Telegram?.WebApp?.expand();</script>
</body></html>"""
