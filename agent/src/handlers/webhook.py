"""
Webhook handler for incoming WhatsApp messages via Meta Cloud API.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Business, Conversation, Message, get_db
from ..config import settings
from ..agents.orchestrator import OrchestratorAgent
from ..services.whatsapp import WhatsAppService, parse_meta_webhook, _strip_whatsapp_prefix

router = APIRouter()

# ─── In-memory rate limiter ──────────────────────────────────────────
_rate_limit_store: dict[str, list[float]] = {}


def is_rate_limited(phone: str) -> bool:
    """Check if phone number exceeded rate limit."""
    now = time.time()
    window = 60.0
    max_msgs = settings.RATE_LIMIT_PER_PHONE_PER_MIN

    if phone not in _rate_limit_store:
        _rate_limit_store[phone] = []

    _rate_limit_store[phone] = [
        ts for ts in _rate_limit_store[phone] if now - ts < window
    ]

    if len(_rate_limit_store[phone]) >= max_msgs:
        return True

    _rate_limit_store[phone].append(now)
    return False


# ─── Webhook verification (Meta GET challenge) ──────────────────────

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta sends this to verify the webhook URL during setup."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified by Meta")
        return PlainTextResponse(hub_challenge or "")
    logger.warning(f"Webhook verification failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


# ─── Incoming messages (Meta POST) ──────────────────────────────────

@router.post("/whatsapp")
async def handle_incoming_whatsapp(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle incoming WhatsApp message from Meta Cloud API webhook."""
    try:
        payload = await request.json()
    except Exception:
        logger.error("Invalid JSON in webhook body")
        return PlainTextResponse("", status_code=400)

    parsed = parse_meta_webhook(payload)
    if not parsed:
        return PlainTextResponse("")

    from_number = parsed.get("from_number", "")
    to_number = parsed.get("to_number", "")
    body = parsed.get("body", "").strip()
    message_id = parsed.get("message_id", "")
    profile_name = parsed.get("profile_name", "")
    msg_type = parsed.get("message_type", "text")

    if msg_type == "status":
        logger.info(f"Message {message_id} status: {parsed.get('status', '')}")
        return PlainTextResponse("")

    if not body or not from_number:
        return PlainTextResponse("")

    logger.info(f"Meta msg {message_id} from {from_number} to {to_number}: {body[:100]}")

    # Deduplication
    if message_id:
        existing = await db.execute(
            select(Message).where(Message.meta_message_id == message_id)
        )
        if existing.scalar_one_or_none():
            logger.info(f"Duplicate message {message_id}, skipping")
            return PlainTextResponse("")

    # Rate limiting
    if is_rate_limited(from_number):
        logger.warning(f"Rate limited: {from_number}")
        return PlainTextResponse("")

    # Look up business
    business = await _get_business_by_phone_id(db, parsed.get("phone_number_id", ""), to_number)
    if not business:
        logger.warning(f"No business found for phone: {to_number}")
        return PlainTextResponse("")

    # Get or create conversation
    conversation = await _get_or_create_conversation(db, business.id, from_number)

    if profile_name and not conversation.customer_name:
        conversation.customer_name = profile_name

    # Handle opt-out
    if body.strip().upper() == "STOP":
        ctx_data = json.loads(conversation.context_json or "{}")
        ctx_data["opted_out"] = True
        conversation.context_json = json.dumps(ctx_data)
        await db.commit()
        logger.info(f"Opt-out: {from_number}")
        return PlainTextResponse("")

    # Re-enable if previously opted out
    ctx_data = json.loads(conversation.context_json or "{}")
    if ctx_data.get("opted_out"):
        ctx_data["opted_out"] = False
        conversation.context_json = json.dumps(ctx_data)
        logger.info(f"Opt-in (re-engaged): {from_number}")

    # Check conversation TTL
    conversation = await _check_conversation_ttl(db, conversation)

    # Process through orchestrator
    try:
        orchestrator = OrchestratorAgent(business, db)
        response_text = await orchestrator.process_message(
            conversation=conversation,
            customer_phone=from_number,
            message_body=body,
        )

        inbound_msg = Message(
            conversation_id=conversation.id,
            direction="inbound",
            content=body,
            meta_message_id=message_id,
            message_type=msg_type,
        )
        db.add(inbound_msg)

        if response_text:
            wa = _get_whatsapp_service(business)
            sent_id = wa.send_text(from_number, response_text)

            out_msg = Message(
                conversation_id=conversation.id,
                direction="outbound",
                content=response_text,
                meta_message_id=sent_id or "",
                message_type="text",
            )
            db.add(out_msg)

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await db.rollback()

    return PlainTextResponse("")


# ─── Helper functions ──────────────────────────────────────────────

async def _get_business_by_phone_id(
    db: AsyncSession, phone_number_id: str, display_number: str
) -> Optional[Business]:
    """Look up business by phone number ID or display number."""
    if phone_number_id:
        result = await db.execute(
            select(Business).where(
                Business.whatsapp_phone_number_id == phone_number_id,
                Business.is_active == True,
            )
        )
        business = result.scalars().first()
        if business:
            return business

    clean_number = _strip_whatsapp_prefix(display_number)
    if clean_number:
        result = await db.execute(
            select(Business).where(
                Business.whatsapp_number == clean_number,
                Business.is_active == True,
            )
        )
        return result.scalars().first()

    return None


async def _get_or_create_conversation(
    db: AsyncSession, business_id: str, customer_phone: str
) -> Conversation:
    """Get active conversation or create new one."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == business_id,
            Conversation.customer_phone == customer_phone,
            Conversation.status == "active",
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            business_id=business_id,
            customer_phone=customer_phone,
            status="active",
        )
        db.add(conversation)
        await db.flush()
        logger.info(f"New conversation: {conversation.id} for {customer_phone}")

    return conversation


async def _check_conversation_ttl(
    db: AsyncSession, conversation: Conversation
) -> Conversation:
    """Reset conversation state if inactive for too long."""
    ttl_hours = settings.CONVERSATION_TTL_HOURS
    last_msg = conversation.last_message_at

    if last_msg:
        if last_msg.tzinfo is None:
            last_msg = last_msg.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now - last_msg > timedelta(hours=ttl_hours):
            ctx_data = json.loads(conversation.context_json or "{}")
            ctx_data["state"] = "greeting"
            ctx_data.pop("selected_service", None)
            ctx_data.pop("selected_date", None)
            ctx_data.pop("selected_time", None)
            conversation.context_json = json.dumps(ctx_data)
            logger.info(f"Conversation {conversation.id} TTL reset ({ttl_hours}h)")

    return conversation


def _get_whatsapp_service(business: Business) -> WhatsAppService:
    """Create WhatsAppService for a business."""
    if business.whatsapp_token and business.whatsapp_phone_number_id:
        return WhatsAppService(
            access_token=business.whatsapp_token,
            phone_number_id=business.whatsapp_phone_number_id,
        )
    return WhatsAppService()
