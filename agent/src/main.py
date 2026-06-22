"""
WhatsApp Agent SaaS — Main FastAPI Application.
Updated for Meta WhatsApp Cloud API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .models import init_db
from .handlers.webhook import router as webhook_router
from .handlers.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"Starting WhatsApp Agent SaaS in {settings.APP_ENV} mode")
    
    # Use absolute path for data directory (works on Render too)
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Override DATABASE_URL with absolute path if using SQLite
    if "sqlite" in settings.DATABASE_URL and "./data" in settings.DATABASE_URL:
        abs_db_path = data_dir / "whatsapp_agent.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{abs_db_path}"
    
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="WhatsApp Agent SaaS",
    description="AI-powered WhatsApp booking & support agent for local Indian businesses",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(webhook_router, prefix="/webhook")
app.include_router(dashboard_router)  # Router already has prefix="/api"


@app.get("/")
async def root():
    return {
        "name": "WhatsApp Agent SaaS",
        "version": "0.2.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint. Use with free uptime monitors."""
    return {"status": "healthy", "version": "0.2.0"}
