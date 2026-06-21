"""
Application configuration via environment variables.
Updated for Meta WhatsApp Cloud API (replacing Twilio).
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Meta WhatsApp Cloud API (replaces Twilio) ──
    WHATSAPP_TOKEN: str = ""           # Permanent access token from Meta App Dashboard
    WHATSAPP_PHONE_NUMBER_ID: str = "" # Phone number ID from WhatsApp → Getting Started
    WHATSAPP_VERIFY_TOKEN: str = ""    # Custom string for webhook verification
    META_API_VERSION: str = "v25.0"    # Graph API version

    # ── OpenRouter (LLM) ──
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-sonnet-4"
    OPENROUTER_MAX_TOKENS: int = 300   # FIX #3: Hard cap per response (WhatsApp replies are short)
    OPENROUTER_TIMEOUT: int = 15       # Seconds before LLM call is considered failed

    # ── App ──
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_SECRET: str = "change-me-in-production"
    APP_URL: str = "http://localhost:8000"

    # ── Database ──
    # SQLite default (zero-cost). Set to Supabase Postgres URL for cloud DB.
    # Format: postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/whatsapp_agent.db"

    # ── Rate limiting ──
    RATE_LIMIT_PER_PHONE_PER_MIN: int = 20  # Max messages per phone per minute

    # ── Conversation ──
    CONVERSATION_TTL_HOURS: int = 6  # Reset booking flow after N hours of inactivity

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
