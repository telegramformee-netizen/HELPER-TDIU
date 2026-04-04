"""
config.py — Barcha sozlamalar .env yoki Railway Variables'dan olinadi
"""
import os

BOT_TOKEN        = os.getenv("BOT_TOKEN", "")
DATABASE_URL     = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./helper.db")
AES_KEY          = os.getenv("AES_KEY", "01234567890123456789012345678901")  # 32 bayt
HEMIS_BASE_URL   = os.getenv("HEMIS_BASE_URL", "https://hemis.tdiu.uz")
PREMIUM_PRICE    = int(os.getenv("PREMIUM_PRICE", "5000"))
APP_URL          = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
MINI_APP_URL     = f"https://{APP_URL}/app"

# Scheduler
EVENING_HOUR     = int(os.getenv("EVENING_HOUR", "20"))
EVENING_MINUTE   = int(os.getenv("EVENING_MINUTE", "0"))
SCRAPE_INTERVAL  = int(os.getenv("SCRAPE_INTERVAL", "15"))  # daqiqa
