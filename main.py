from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    database_url: str = ""
    aes_master_key: str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa="
    jwt_secret: str = "changeme_secret_key"
    hemis_base_url: str = "https://student.hemis.uz"
    mini_app_url: str = "https://example.com/app"
    port: int = 8000
    debug: bool = False
    premium_price_uzs: int = 5000
    scrape_interval_minutes: int = 15
    evening_notify_hour: int = 20
    evening_notify_minute: int = 0

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
