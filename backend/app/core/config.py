"""
Application configuration.

All configuration is sourced from environment variables (see .env.example).
Never hard-code secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "Construction Site Store & Tool Accountability System"
    ENVIRONMENT: str = "development"  # development | test | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Database ---
    # Prefer a full DATABASE_URL. Falls back to building one from parts.
    DATABASE_URL: str = "postgresql+psycopg://csuser:devpassword@localhost:5432/construction_store"

    # --- Security / JWT ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_this_is_a_dev_only_default_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hour shift-length session
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- Timezone ---
    # All timestamps are stored in UTC. This is the display timezone only.
    DISPLAY_TIMEZONE: str = "Africa/Nairobi"

    # --- Rate limiting ---
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "120/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
