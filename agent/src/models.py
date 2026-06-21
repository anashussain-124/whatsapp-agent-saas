"""
Database models and connection for WhatsApp Agent SaaS.
Uses SQLAlchemy 2.0 with async support.
Updated: Meta Cloud API fields, Meta message ID, opt-out support.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def generate_id() -> str:
    return str(uuid.uuid4())


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    phone = Column(String)
    industry = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    timezone = Column(String, default="Asia/Kolkata")

    # WhatsApp (Meta Cloud API)
    whatsapp_number = Column(String)  # Display number (e.g., "919876543210")
    whatsapp_phone_number_id = Column(String)  # Meta phone number ID
    whatsapp_token = Column(String, default="")  # Business-specific token (optional, uses default if empty)

    # LLM
    openrouter_key = Column(String)
    system_prompt = Column(Text)

    is_active = Column(Boolean, default=True)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    services = relationship("Service", back_populates="business", lazy="selectin")
    conversations = relationship("Conversation", back_populates="business", lazy="selectin")
    bookings = relationship("Booking", back_populates="business", lazy="selectin")


class Service(Base):
    __tablename__ = "services"

    id = Column(String, primary_key=True, default=generate_id)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    price_inr = Column(Integer)
    is_active = Column(Boolean, default=True)

    business = relationship("Business", back_populates="services")


class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(String, primary_key=True, default=generate_id)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    open_time = Column(String)  # "09:00"
    close_time = Column(String)  # "18:00"
    is_closed = Column(Boolean, default=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_id)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String)
    status = Column(String, default="active")
    current_intent = Column(String)
    context_json = Column(Text, default="{}")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", lazy="selectin")
    bookings = relationship("Booking", back_populates="conversation", lazy="selectin")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_id)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    direction = Column(String, nullable=False)  # inbound, outbound
    message_type = Column(String, default="text")
    content = Column(Text)
    meta_message_id = Column(String, default="")  # Meta message ID (replaces twilio_sid)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_id)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    service_id = Column(String, ForeignKey("services.id"))
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(String, nullable=False)
    status = Column(String, default="confirmed")
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="bookings")
    conversation = relationship("Conversation", back_populates="bookings")


class DailyAnalytics(Base):
    __tablename__ = "daily_analytics"
    __table_args__ = (UniqueConstraint("business_id", "date"),)

    id = Column(String, primary_key=True, default=generate_id)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_conversations = Column(Integer, default=0)
    new_conversations = Column(Integer, default=0)
    bookings_made = Column(Integer, default=0)
    bookings_cancelled = Column(Integer, default=0)
    avg_response_time_seconds = Column(Integer)
    top_intent = Column(String)


# ─── Database engine ────────────────────────────────────────────────
# Supports both SQLite (default, zero-cost) and PostgreSQL (Supabase free tier)
# Switch via DATABASE_URL env var — no code changes needed.

_db_url = settings.DATABASE_URL

# If using bare sqlite:/// path, add aiosqlite driver
if _db_url.startswith("sqlite:///"):
    _db_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
# If using postgres without async driver, add +asyncpg
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_db_url, echo=settings.APP_ENV == "development")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency: get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
