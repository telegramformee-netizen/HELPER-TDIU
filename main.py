"""
HELPER (TDIU) - Asosiy fayl
Railway'da ishlash uchun yagona main.py
"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="HELPER TDIU")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

@app.get("/")
async def root():
    return {"status": "ok", "app": "HELPER TDIU", "message": "Bot ishlayapti!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/app", response_class=HTMLResponse)
async def mini_app():
    return """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HELPER TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: system-ui, sans-serif;
    background: var(--tg-theme-bg-color, #0f0f14);
    color: var(--tg-theme-text-color, #ffffff);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card {
    text-align: center;
    padding: 40px 24px;
  }
  .logo {
    font-size: 64px;
    font-weight: 900;
    margin-bottom: 12px;
    color: #6c63ff;
  }
  .title { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
  .sub { font-size: 14px; opacity: 0.6; margin-bottom: 32px; }
  .status {
    display: inline-block;
    background: rgba(34,197,94,0.15);
    color: #22c55e;
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
  }
</style>
</head>
<body>
<div class="card">
  <div class="logo">H</div>
  <div class="title">HELPER TDIU</div>
  <div class="sub">TDIU Talaba Yordamchisi</div>
  <div class="status">✅ Bot ishlayapti!</div>
</div>
<script>
  window.Telegram?.WebApp?.expand();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
