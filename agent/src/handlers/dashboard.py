"""
Business owner dashboard API.
Updated: removed Twilio fields, added Meta WhatsApp fields.
Task 6: Added today's bookings + stats endpoints for owner dashboard.
"""
from typing import Optional
from datetime import datetime, date, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Business, Service, Conversation, Message, Booking, get_db
)

router = APIRouter(prefix="/api")


# ─── Pydantic Schemas ──────────────────────────────────────────────

class BusinessCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    industry: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    whatsapp_number: str
    whatsapp_phone_number_id: Optional[str] = None  # Meta phone number ID
    openrouter_key: Optional[str] = None
    system_prompt: Optional[str] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price_inr: Optional[int] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price_inr: Optional[int] = None
    is_active: Optional[bool] = None


# ─── Business Endpoints ─────────────────────────────────────────────

@router.post("/business")
async def create_business(data: BusinessCreate, db: AsyncSession = Depends(get_db)):
    """Create a new business (onboarding)."""
    business = Business(**data.model_dump())
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return {"id": business.id, "name": business.name, "status": "created"}


@router.get("/business/{business_id}")
async def get_business(business_id: str, db: AsyncSession = Depends(get_db)):
    """Get business configuration."""
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return {
        "id": business.id,
        "name": business.name,
        "industry": business.industry,
        "city": business.city,
        "whatsapp_number": business.whatsapp_number,
        "whatsapp_phone_number_id": business.whatsapp_phone_number_id,
        "is_active": business.is_active,
        "plan": business.plan,
        "created_at": business.created_at.isoformat() if business.created_at else None,
    }


@router.put("/business/{business_id}")
async def update_business(
    business_id: str, data: BusinessUpdate, db: AsyncSession = Depends(get_db)
):
    """Update business configuration."""
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(business, key, value)

    business.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "updated"}


# ─── Services Endpoints ─────────────────────────────────────────────

@router.get("/business/{business_id}/services")
async def list_services(business_id: str, db: AsyncSession = Depends(get_db)):
    """List all services for a business."""
    result = await db.execute(
        select(Service).where(Service.business_id == business_id)
    )
    services = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "duration_minutes": s.duration_minutes,
            "price_inr": s.price_inr,
            "is_active": s.is_active,
        }
        for s in services
    ]


@router.post("/business/{business_id}/services")
async def add_service(
    business_id: str, data: ServiceCreate, db: AsyncSession = Depends(get_db)
):
    """Add a new service."""
    service = Service(business_id=business_id, **data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return {"id": service.id, "name": service.name, "status": "created"}


@router.put("/business/{business_id}/services/{service_id}")
async def update_service(
    business_id: str,
    service_id: str,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a service."""
    result = await db.execute(
        select(Service).where(
            Service.id == service_id, Service.business_id == business_id
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)

    await db.commit()
    return {"status": "updated"}


# ─── Conversations Endpoints ────────────────────────────────────────

@router.get("/business/{business_id}/conversations")
async def list_conversations(
    business_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for a business."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.business_id == business_id)
        .order_by(Conversation.last_message_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "customer_phone": c.customer_phone,
            "customer_name": c.customer_name,
            "status": c.status,
            "current_intent": c.current_intent,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        }
        for c in conversations
    ]


@router.get("/business/{business_id}/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    business_id: str,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "content": m.content,
            "message_type": m.message_type,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


# ─── Bookings Endpoints ─────────────────────────────────────────────

@router.get("/business/{business_id}/bookings")
async def list_bookings(
    business_id: str,
    status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """List bookings for a business."""
    query = select(Booking).where(Booking.business_id == business_id)
    if status:
        query = query.where(Booking.status == status)
    if from_date:
        query = query.where(Booking.booking_date >= from_date)
    if to_date:
        query = query.where(Booking.booking_date <= to_date)

    result = await db.execute(query.order_by(Booking.booking_date.desc()))
    bookings = result.scalars().all()
    return [
        {
            "id": b.id,
            "customer_name": b.customer_name,
            "customer_phone": b.customer_phone,
            "booking_date": b.booking_date.isoformat(),
            "booking_time": b.booking_time,
            "status": b.status,
            "notes": b.notes,
        }
        for b in bookings
    ]


# ─── Task 6: Owner Dashboard — Today's Bookings & Stats ─────────────

@router.get("/business/{business_id}/dashboard")
async def get_dashboard(business_id: str, db: AsyncSession = Depends(get_db)):
    """Minimal owner dashboard: today's bookings, this week's stats."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    # Today's bookings
    today_result = await db.execute(
        select(Booking).where(
            Booking.business_id == business_id,
            Booking.booking_date == today,
        ).order_by(Booking.booking_time.asc())
    )
    today_bookings = today_result.scalars().all()

    # This week's bookings count
    week_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.business_id == business_id,
            Booking.booking_date >= week_start,
            Booking.booking_date <= today,
        )
    )
    week_bookings = week_result.scalar() or 0

    # This month's bookings count
    month_start = today.replace(day=1)
    month_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.business_id == business_id,
            Booking.booking_date >= month_start,
            Booking.booking_date <= today,
        )
    )
    month_bookings = month_result.scalar() or 0

    # Total conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.business_id == business_id,
        )
    )
    total_conversations = conv_result.scalar() or 0

    # Active conversations today
    active_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.business_id == business_id,
            Conversation.status == "active",
        )
    )
    active_conversations = active_result.scalar() or 0

    return {
        "today": {
            "date": today.isoformat(),
            "bookings": [
                {
                    "id": b.id,
                    "customer_name": b.customer_name,
                    "customer_phone": b.customer_phone,
                    "booking_time": b.booking_time,
                    "status": b.status,
                }
                for b in today_bookings
            ],
            "total_bookings": len(today_bookings),
        },
        "this_week": {
            "bookings_count": week_bookings,
        },
        "this_month": {
            "bookings_count": month_bookings,
        },
        "conversations": {
            "total": total_conversations,
            "active": active_conversations,
        },
    }


# ─── Analytics Endpoints ────────────────────────────────────────────

@router.get("/business/{business_id}/analytics")
async def get_analytics(
    business_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for a business."""
    from_date = date.today() - timedelta(days=days)

    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.business_id == business_id,
            Conversation.started_at >= from_date,
        )
    )
    total_conversations = conv_result.scalar() or 0

    book_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.business_id == business_id,
            Booking.created_at >= from_date,
        )
    )
    total_bookings = book_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.business_id == business_id,
            Conversation.status == "active",
        )
    )
    active_conversations = active_result.scalar() or 0

    status_result = await db.execute(
        select(Booking.status, func.count(Booking.id))
        .where(Booking.business_id == business_id)
        .group_by(Booking.status)
    )
    bookings_by_status = dict(status_result.all())

    return {
        "period_days": days,
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "total_bookings": total_bookings,
        "bookings_by_status": bookings_by_status,
    }
