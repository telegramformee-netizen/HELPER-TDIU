"""
config.py - HELPER TDIU sozlamalari
"""
import os

BOT_TOKEN       = os.getenv("BOT_TOKEN", "")
DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./helper.db")
AES_KEY         = os.getenv("AES_KEY", "helper_tdiu_secret_key_32chars!!")
PREMIUM_PRICE   = int(os.getenv("PREMIUM_PRICE", "5000"))
EVENING_HOUR    = int(os.getenv("EVENING_HOUR", "20"))
EVENING_MINUTE  = int(os.getenv("EVENING_MINUTE", "0"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))

# ── TSUE Hemis URL ─────────────────────────────────────────────
# TSUE uchun to'g'ri URL: https://talaba.tsue.uz
HEMIS_BASE_URL = os.getenv("HEMIS_BASE_URL", "https://talaba.tsue.uz")

# ── Mini App URL ───────────────────────────────────────────────
def _build_mini_app_url():
    direct = os.getenv("MINI_APP_URL", "").strip()
    if direct:
        if not direct.startswith("https://"):
            direct = "https://" + direct.lstrip("http://").lstrip("https://")
        return direct.rstrip("/")
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if domain:
        clean = domain.replace("https://","").replace("http://","").rstrip("/")
        return "https://" + clean + "/app"
    return ""

MINI_APP_URL = _build_mini_app_url()

if MINI_APP_URL:
    print("Mini App URL:", MINI_APP_URL)
else:
    print("Mini App URL sozlanmagan")
