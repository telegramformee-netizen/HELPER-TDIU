"""
config.py - Barcha sozlamalar
"""
import os

BOT_TOKEN       = os.getenv("BOT_TOKEN", "")
DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./helper.db")
AES_KEY         = os.getenv("AES_KEY", "helper_tdiu_secret_key_32chars!!")
HEMIS_BASE_URL  = os.getenv("HEMIS_BASE_URL", "https://hemis.tdiu.uz")
PREMIUM_PRICE   = int(os.getenv("PREMIUM_PRICE", "5000"))
EVENING_HOUR    = int(os.getenv("EVENING_HOUR", "20"))
EVENING_MINUTE  = int(os.getenv("EVENING_MINUTE", "0"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))

# Railway public URL - to'g'ri o'qish
_domain = os.getenv("MINI_APP_URL", "")
if not _domain:
    _railway = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    if _railway:
        # Railway ba'zan https:// bilan beradi, ba'zan bermaydi
        if _railway.startswith("http"):
            _domain = _railway.rstrip("/") + "/app"
        else:
            _domain = "https://" + _railway.rstrip("/") + "/app"
    else:
        _domain = ""   # bo'sh - bot tugmasiz ishlaydi

MINI_APP_URL = _domain
