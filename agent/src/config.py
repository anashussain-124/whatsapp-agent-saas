"""
Application configuration via environment variables.
Updated for Meta WhatsApp Cloud API (replacing Twilio).
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # ── Meta WhatsApp Cloud API (replaces Twilio) ──
    WHATSAPP_TOKEN: str = Field(default="", description="Permanent access token from Meta App Dashboard")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="", description="Phone number ID from WhatsApp → Getting Started")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="", description="Custom string for webhook verification")
    META_API_VERSION: str = Field(default="v25.0", description="Graph API version")

    # ── OpenRouter (LLM) ──
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    OPENROUTER_MODEL: str = Field(default="openrouter/owl-alpha", description="OpenRouter model ID")
    OPENROUTER_MAX_TOKENS: int = Field(default=300, ge=1, le=4096, description="Hard cap per response")
    OPENROUTER_TIMEOUT: int = Field(default=15, ge=1, le=60, description="Seconds before LLM call timeout")

    # ── App ──
    APP_ENV: str = Field(default="development", pattern="^(development|production|testing)$")
    APP_PORT: int = Field(default=8000, ge=1, le=65535)
    APP_SECRET: str = Field(default="change-me-in-production-32chars-long!!", min_length=32)
    APP_URL: str = Field(default="http://localhost:8000", description="Public URL for webhooks")

    # ── Database ──
    # SQLite default (zero-cost). Set to Supabase Postgres URL for cloud DB.
    # Format: postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/whatsapp_agent.db")

    # ── Rate limiting ──
    RATE_LIMIT_PER_PHONE_PER_MIN: int = Field(default=20, ge=1, le=1000)

    # ── Conversation ──
    CONVERSATION_TTL_HOURS: int = Field(default=6, ge=1, le=168)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


def get_settings() -> Settings:
    """Get settings instance. Not cached to allow env reload."""
    return Settings()


settings = get_settings()