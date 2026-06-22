"""
Main Orchestrator Agent — the brain of the WhatsApp bot.
Coordinates sub-agents, manages conversation flow, generates responses.

Follows Anthropic's "orchestrator-workers" pattern:
1. Receive message
2. Classify intent (Intent Classifier sub-agent)
3. Route to appropriate handler (Booking, Pricing, Service, etc.)
4. Generate response (Response Generator sub-agent)
5. Return response text (webhook handler sends via Twilio)
"""
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loguru import logger
from typing import Optional

# IST timezone for all date parsing — regardless of server timezone
IST = ZoneInfo("Asia/Kolkata")

from ..models import Business, Conversation, Message, Service, Booking
from ..services.llm import LLMClient, FALLBACK_REPLY


# ─── Conversation States ────────────────────────────────────────────
STATE_GREETING = "greeting"
STATE_INTENT_COLLECTION = "intent_collection"
STATE_SERVICE_SELECTION = "service_selection"
STATE_DATE_SELECTION = "date_selection"
STATE_TIME_SELECTION = "time_selection"
STATE_CONFIRMATION = "confirmation"
STATE_COMPLETED = "completed"
STATE_GENERAL_QUERY = "general_query"


# ─── WhatsApp Formatting Utility ───────────────────────────────────

def format_for_whatsapp(text: str) -> str:
    """Convert LLM output to WhatsApp-safe formatting.

    - **bold** → *bold* (WhatsApp uses asterisks)
    - ## headings → CAPS
    - Strip markdown links → keep text
    - Limit to 4096 chars (WhatsApp max)
    - Collapse 3+ newlines to 2
    """
    if not text:
        return text

    # Convert markdown bold **text** to WhatsApp *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

    # Convert markdown italic _text_ to WhatsApp _text_ (already compatible)
    # But handle __text__ → _text_
    text = re.sub(r'__(.+?)__', r'_\1_', text)

    # Convert ## Heading → *HEADING*
    text = re.sub(r'^#{1,3}\s+(.+)$', lambda m: f'*{m.group(1).upper()}*', text, flags=re.MULTILINE)

    # Strip markdown links [text](url) → text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # WhatsApp message limit
    if len(text) > 4096:
        text = text[:4093] + '...'

    return text.strip()


# ─── Conversation Context ───────────────────────────────────────────

class ConversationContext:
    """Manages conversation state for a single customer dialog."""

    def __init__(self, raw_json: str = "{}"):
        self.data = json.loads(raw_json) if raw_json else {}

    @property
    def state(self) -> str:
        return self.data.get("state", STATE_GREETING)

    @state.setter
    def state(self, value: str):
        self.data["state"] = value

    @property
    def intent(self) -> str:
        return self.data.get("intent", "")

    @intent.setter
    def intent(self, value: str):
        self.data["intent"] = value

    @property
    def selected_service(self) -> Optional[dict]:
        return self.data.get("selected_service")

    @selected_service.setter
    def selected_service(self, value: dict):
        self.data["selected_service"] = value

    @property
    def selected_date(self) -> str:
        return self.data.get("selected_date", "")

    @selected_date.setter
    def selected_date(self, value: str):
        self.data["selected_date"] = value

    @property
    def selected_time(self) -> str:
        return self.data.get("selected_time", "")

    @selected_time.setter
    def selected_time(self, value: str):
        self.data["selected_time"] = value

    @property
    def customer_name(self) -> str:
        return self.data.get("customer_name", "")

    @customer_name.setter
    def customer_name(self, value: str):
        self.data["customer_name"] = value

    @property
    def history(self) -> list:
        return self.data.get("history", [])

    def add_to_history(self, role: str, content: str):
        self.data.setdefault("history", []).append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(IST).isoformat(),
        })
        # Keep last 20 messages
        self.data["history"] = self.data["history"][-20:]

    def to_json(self) -> str:
        return json.dumps(self.data)


# ─── Orchestrator Agent ─────────────────────────────────────────────

class OrchestratorAgent:
    """
    Main orchestrator that processes incoming WhatsApp messages
    and coordinates sub-agents to generate responses.

    IMPORTANT: This class returns response text only. The webhook handler
    is responsible for sending the message via Twilio. This keeps the
    agent testable and decoupled from the transport layer.
    """

    def __init__(self, business: Business, db_session):
        self.business = business
        self.db = db_session
        # Use business-specific key or fall back to settings default
        api_key = business.openrouter_key or settings.OPENROUTER_API_KEY
        if not api_key:
            logger.warning(f"No OpenRouter API key for business {business.name}")
        self.llm = LLMClient(api_key=api_key)

    async def process_message(
        self,
        conversation: Conversation,
        customer_phone: str,
        message_body: str,
    ) -> str:
        """
        Main entry point: process an incoming message and return response text.
        The webhook handler sends the response via Twilio.
        """
        # Load context
        ctx = ConversationContext(conversation.context_json)
        ctx.add_to_history("customer", message_body)

        # Save inbound message
        msg = Message(
            conversation_id=conversation.id,
            direction="inbound",
            content=message_body,
        )
        self.db.add(msg)

        # ── Step 1: Classify Intent ──
        intent_data = await self._classify_intent(message_body, ctx)
        intent = intent_data.get("intent", "other")
        entities = intent_data.get("entities", {})

        logger.info(
            f"Intent: {intent} | Entities: {entities} | State: {ctx.state} | "
            f"Business: {self.business.name}"
        )

        # ── Step 2: Route to appropriate handler ──
        response = await self._route_intent(intent, entities, ctx, message_body, customer_phone)

        # ── Step 3: Format for WhatsApp ──
        response = format_for_whatsapp(response)

        # ── Step 4: Update conversation ──
        ctx.add_to_history("assistant", response)
        conversation.context_json = ctx.to_json()
        conversation.current_intent = intent
        conversation.last_message_at = datetime.now(IST)

        # Save outbound message
        out_msg = Message(
            conversation_id=conversation.id,
            direction="outbound",
            content=response,
        )
        self.db.add(out_msg)

        await self.db.flush()
        return response

    async def _classify_intent(self, message: str, ctx: ConversationContext) -> dict:
        """Classify customer intent using LLM."""
        business_context = {
            "name": self.business.name,
            "industry": self.business.industry,
            "city": self.business.city or "",
        }
        return await self.llm.classify_intent(message, business_context)

    async def _route_intent(
        self, intent: str, entities: dict, ctx: ConversationContext,
        raw_message: str, customer_phone: str,
    ) -> str:
        """Route to the appropriate handler based on intent + current state."""

        # Handle confirm/deny based on state first
        if intent == "confirm":
            # FIX #3: Guard — only handle confirm if we're in a confirmation state
            if ctx.state == STATE_CONFIRMATION:
                return await self._handle_confirmation(ctx, customer_phone)
            # If not in confirmation state, treat as general positive response
            ctx.state = STATE_INTENT_COLLECTION
            return await self._handle_general_query(raw_message, ctx)

        if intent == "deny":
            # FIX #3: Guard — only handle denial if we're in a multi-step flow
            if ctx.state in (STATE_CONFIRMATION, STATE_SERVICE_SELECTION,
                             STATE_DATE_SELECTION, STATE_TIME_SELECTION):
                return await self._handle_denial(ctx)
            # If not in a flow, treat as general response
            ctx.state = STATE_INTENT_COLLECTION
            return "No problem! Is there anything else I can help you with? 😊"

        # State-based routing
        if ctx.state == STATE_GREETING:
            if intent == "greeting":
                ctx.state = STATE_INTENT_COLLECTION
                return await self._generate_greeting()
            else:
                # Skip greeting, go straight to intent
                ctx.state = STATE_INTENT_COLLECTION
                return await self._route_by_intent(intent, entities, ctx, raw_message)

        if ctx.state == STATE_INTENT_COLLECTION:
            return await self._route_by_intent(intent, entities, ctx, raw_message)

        if ctx.state == STATE_SERVICE_SELECTION:
            return await self._handle_service_selection(raw_message, ctx)

        if ctx.state == STATE_DATE_SELECTION:
            return await self._handle_date_selection(raw_message, ctx)

        if ctx.state == STATE_TIME_SELECTION:
            return await self._handle_time_selection(raw_message, ctx)

        if ctx.state == STATE_CONFIRMATION:
            # If not confirm/deny, treat as new query
            ctx.state = STATE_INTENT_COLLECTION
            return await self._route_by_intent(intent, entities, ctx, raw_message)

        # Default: treat as general query
        return await self._handle_general_query(raw_message, ctx)

    async def _route_by_intent(
        self, intent: str, entities: dict, ctx: ConversationContext, raw_message: str
    ) -> str:
        """Route to handler based on classified intent."""

        if intent == "greeting":
            return await self._generate_greeting()

        if intent == "book_appointment":
            ctx.state = STATE_SERVICE_SELECTION
            ctx.intent = "book_appointment"
            return await self._prompt_service_selection()

        if intent == "reschedule":
            return await self._handle_reschedule_request(raw_message, ctx)

        if intent == "cancel":
            return await self._handle_cancellation_request(raw_message, ctx)

        if intent == "check_availability":
            return await self._handle_availability_query(raw_message, ctx)

        if intent == "pricing_query":
            return await self._handle_pricing_query(raw_message, ctx)

        if intent == "service_info":
            return await self._handle_service_info(raw_message, ctx)

        if intent == "location_query":
            return self._handle_location_query()

        if intent == "hours_query":
            return self._handle_hours_query()

        if intent == "small_talk":
            return await self._handle_small_talk(raw_message, ctx)

        # Fallback: general query
        return await self._handle_general_query(raw_message, ctx)

    # ─── Handlers ─────────────────────────────────────────────────────

    async def _generate_greeting(self) -> str:
        """Generate a personalized greeting."""
        services = [s.name for s in self.business.services if s.is_active][:3]
        services_text = ", ".join(services) if services else "various services"

        prompt = f"""You are a friendly WhatsApp assistant for {self.business.name}, a {self.business.industry} business in {self.business.city or 'the area'}.

Generate a warm, brief greeting (2-3 sentences) that:
1. Greets the customer
2. Mentions the business name
3. Lists a few services: {services_text}
4. Asks how you can help today

Keep it conversational and friendly. Use emojis sparingly (1-2 max).
Do NOT use bullet points. Keep under 100 words."""

        return await self.llm.chat(prompt, "Generate greeting.", max_tokens=200)

    async def _prompt_service_selection(self) -> str:
        """Show available services for booking."""
        services = [s for s in self.business.services if s.is_active]
        if not services:
            return (
                f"We'd love to help you book an appointment! "
                f"Please call us at {self.business.phone or 'our office'} to schedule."
            )

        service_list = "\n".join(
            [
                f"*{i+1}.* {s.name}"
                + (f" — ₹{s.price_inr}" if s.price_inr else "")
                + (f" ({s.duration_minutes} min)" if s.duration_minutes else "")
                for i, s in enumerate(services)
            ]
        )

        return (
            f"Great! Here are our services:\n\n{service_list}\n\n"
            f"Which service would you like? Reply with the number or name. 😊"
        )

    async def _handle_service_selection(self, message: str, ctx: ConversationContext) -> str:
        """Parse service selection and move to date selection."""
        services = [s for s in self.business.services if s.is_active]

        # Try to match by number
        try:
            idx = int(message.strip()) - 1
            if 0 <= idx < len(services):
                selected = services[idx]
                ctx.selected_service = {
                    "id": selected.id,
                    "name": selected.name,
                    "price_inr": selected.price_inr,
                    "duration_minutes": selected.duration_minutes,
                }
                ctx.state = STATE_DATE_SELECTION
                return (
                    f"Perfect! *{selected.name}* selected. "
                    + (f"(₹{selected.price_inr})\n\n" if selected.price_inr else "\n")
                    + "Which date would you prefer? (e.g., tomorrow, Monday, or 25-06-2026)"
                )
        except ValueError:
            pass

        # Try to match by name
        for s in services:
            if s.name.lower() in message.lower():
                ctx.selected_service = {
                    "id": s.id,
                    "name": s.name,
                    "price_inr": s.price_inr,
                    "duration_minutes": s.duration_minutes,
                }
                ctx.state = STATE_DATE_SELECTION
                return (
                    f"Perfect! *{s.name}* selected. "
                    + (f"(₹{s.price_inr})\n\n" if s.price_inr else "\n")
                    + "Which date would you prefer? (e.g., tomorrow, Monday, or 25-06-2026)"
                )

        # Couldn't match — ask again
        service_names = ", ".join([s.name for s in services[:5]])
        return (
            f"I couldn't find that service. Please choose from:\n{service_names}\n\n"
            f"Reply with the number or name."
        )

    async def _handle_date_selection(self, message: str, ctx: ConversationContext) -> str:
        """Parse date selection and move to time selection. Uses IST."""
        today = datetime.now(IST).strftime("%Y-%m-%d")
        prompt = f"""Today is {today} (Indian Standard Time, IST). Parse the following date expression and return ONLY the date in YYYY-MM-DD format. If unclear, return the most likely date. Always interpret relative dates (tomorrow, next Monday) in IST.

Examples:
- "tomorrow" → {(datetime.now(IST) + timedelta(days=1)).strftime('%Y-%m-%d')}
- "Monday" → next Monday's date (IST)
- "25-06-2026" → 2026-06-25
- "next week" → the Monday of next week

Input: "{message}"

Return ONLY the date in YYYY-MM-DD format:"""

        parsed_date = await self.llm.chat(prompt, message, temperature=0.1, max_tokens=20)
        parsed_date = parsed_date.strip()

        try:
            date_obj = datetime.strptime(parsed_date[:10], "%Y-%m-%d")
            ctx.selected_date = parsed_date[:10]
            ctx.state = STATE_TIME_SELECTION
            service_name = ctx.selected_service.get("name", "your appointment") if ctx.selected_service else "your appointment"
            return (
                f"Got it! *{parsed_date[:10]}* for {service_name}.\n\n"
                f"What time would you prefer? (e.g., 10:30 AM, 2 PM, 14:30)"
            )
        except ValueError:
            return (
                "I didn't understand that date. Please try again with a clear date like:\n"
                "• tomorrow\n"
                "• Monday\n"
                "• 25-06-2026"
            )

    async def _handle_time_selection(self, message: str, ctx: ConversationContext) -> str:
        """Parse time selection and move to confirmation. Uses IST."""
        prompt = f"""Parse the following time expression and return ONLY the time in 24-hour HH:MM format. All times are in Indian Standard Time (IST, UTC+5:30).

Examples:
- "10:30 AM" → 10:30
- "2 PM" → 14:00
- "14:30" → 14:30
- "morning" → 10:00
- "afternoon" → 14:00
- "evening" → 17:00

Input: "{message}"

Return ONLY the time in HH:MM format:"""

        parsed_time = await self.llm.chat(prompt, message, temperature=0.1, max_tokens=10)
        parsed_time = parsed_time.strip()

        try:
            time_obj = datetime.strptime(parsed_time[:5], "%H:%M")
            ctx.selected_time = parsed_time[:5]
            ctx.state = STATE_CONFIRMATION

            service = ctx.selected_service.get("name", "your appointment") if ctx.selected_service else "your appointment"
            price = ctx.selected_service.get("price_inr") if ctx.selected_service else None
            date_str = ctx.selected_date
            time_str = parsed_time[:5]

            confirm_msg = (
                f"Please confirm your booking:\n\n"
                f"📅 *Date:* {date_str}\n"
                f"⏰ *Time:* {time_str}\n"
                f"💇 *Service:* {service}\n"
            )
            if price:
                confirm_msg += f"💰 *Price:* ₹{price}\n"
            confirm_msg += f"\nReply *YES* to confirm or *NO* to start over."

            return confirm_msg
        except ValueError:
            return (
                "I didn't understand that time. Please try again like:\n"
                "• 10:30 AM\n"
                "• 2 PM\n"
                "• 14:30"
            )

    async def _handle_confirmation(self, ctx: ConversationContext, customer_phone: str) -> str:
        """Handle booking confirmation. FIX #2: customer_phone is now passed in."""
        if ctx.state == STATE_CONFIRMATION and ctx.selected_service:
            booking = Booking(
                business_id=self.business.id,
                service_id=ctx.selected_service.get("id"),
                customer_phone=customer_phone,  # FIX #2: was empty string
                customer_name=ctx.customer_name,
                booking_date=datetime.strptime(ctx.selected_date, "%Y-%m-%d").date(),
                booking_time=ctx.selected_time,
                status="confirmed",
            )
            self.db.add(booking)

            ctx.state = STATE_COMPLETED
            service_name = ctx.selected_service.get("name", "your appointment")
            return (
                f"✅ *Booking Confirmed!*\n\n"
                f"📅 {ctx.selected_date}\n"
                f"⏰ {ctx.selected_time}\n"
                f"💇 {service_name}\n\n"
                f"We'll see you then! Send us a message if you need to reschedule. 😊"
            )

        ctx.state = STATE_INTENT_COLLECTION
        return "How can I help you today?"

    async def _handle_denial(self, ctx: ConversationContext) -> str:
        """Handle denial/cancellation of current flow."""
        ctx.state = STATE_INTENT_COLLECTION
        ctx.selected_service = None
        ctx.selected_date = ""
        ctx.selected_time = ""
        return "No problem! Let's start over. How can I help you? 😊"

    async def _handle_reschedule_request(self, message: str, ctx: ConversationContext) -> str:
        """Handle reschedule request."""
        return (
            "I'd be happy to help you reschedule! 📅\n\n"
            "Could you tell me:\n"
            "1. Your current booking date & time\n"
            "2. Your preferred new date & time\n\n"
            "Or call us directly at " + (self.business.phone or "our office") + "."
        )

    async def _handle_cancellation_request(self, message: str, ctx: ConversationContext) -> str:
        """Handle cancellation request."""
        return (
            "I'm sorry you need to cancel. 😔\n\n"
            "Please share your booking date and time, and I'll help you cancel. "
            "Or call us at " + (self.business.phone or "our office") + "."
        )

    async def _handle_availability_query(self, message: str, ctx: ConversationContext) -> str:
        """Handle availability queries."""
        prompt = f"""You are an assistant for {self.business.name}. The customer is asking about availability.

Business info:
- Industry: {self.business.industry}
- City: {self.business.city or 'N/A'}
- Phone: {self.business.phone or 'N/A'}

Generate a helpful response (2-3 sentences) about checking availability.
Mention they can book directly through this chat by saying "I want to book" or similar.
Keep it brief and friendly."""

        return await self.llm.chat(prompt, message, max_tokens=150)

    async def _handle_pricing_query(self, message: str, ctx: ConversationContext) -> str:
        """Handle pricing queries. Prices always from DB, never from LLM."""
        services = [s for s in self.business.services if s.is_active]

        # Check if asking about specific service
        for s in services:
            if s.name.lower() in message.lower():
                price_text = f"₹{s.price_inr}" if s.price_inr else "Please contact us for pricing"
                duration_text = f" ({s.duration_minutes} min)" if s.duration_minutes else ""
                return f"*{s.name}*{duration_text}: {price_text}\n\nWould you like to book this service?"

        # General pricing — list all from DB
        if services:
            price_list = "\n".join(
                [
                    f"• {s.name}: "
                    + (f"₹{s.price_inr}" if s.price_inr else "Contact for pricing")
                    for s in services
                ]
            )
            return f"Here are our prices:\n\n{price_list}\n\nWould you like to book any of these?"

        return (
            "For pricing information, please call us at "
            + (self.business.phone or "our office")
            + " or visit us at " + (self.business.address or "our location") + "."
        )

    async def _handle_service_info(self, message: str, ctx: ConversationContext) -> str:
        """Handle service information queries."""
        services = [s for s in self.business.services if s.is_active]
        if not services:
            return f"We offer various {self.business.industry} services. Call us at {self.business.phone or 'our office'} for details."

        service_list = "\n".join(
            [
                f"*{s.name}*"
                + (f"\n  {s.description}" if s.description else "")
                + (f"\n  Duration: {s.duration_minutes} min" if s.duration_minutes else "")
                + (f" | Price: ₹{s.price_inr}" if s.price_inr else "")
                for s in services
            ]
        )

        return (
            f"Here's what we offer:\n\n{service_list}\n\n"
            f"Want to book any of these? Just say 'I want to book'! 😊"
        )

    def _handle_location_query(self) -> str:
        """Handle location/address queries."""
        if self.business.address:
            return (
                f"📍 *Our Address:*\n{self.business.address}"
                + (f", {self.business.city}" if self.business.city else "")
                + (f", {self.business.state}" if self.business.state else "")
                + (f" - {self.business.pincode}" if self.business.pincode else "")
                + "\n\nWe look forward to seeing you! 😊"
            )
        return (
            f"We're located in {self.business.city or 'the area'}. "
            f"Call us at {self.business.phone or 'our office'} for directions."
        )

    def _handle_hours_query(self) -> str:
        """Handle business hours queries."""
        return (
            f"🕐 *Our Hours:*\n"
            f"Monday - Friday: 9:00 AM - 7:00 PM\n"
            f"Saturday: 9:00 AM - 5:00 PM\n"
            f"Sunday: Closed\n\n"
            f"(Hours may vary. Call {self.business.phone or 'us'} to confirm.)"
        )

    async def _handle_small_talk(self, message: str, ctx: ConversationContext) -> str:
        """Handle casual conversation."""
        prompt = f"""You are a friendly WhatsApp assistant for {self.business.name}, a {self.business.industry} business.

The customer said: "{message}"

Respond in a warm, brief way (1-2 sentences). Then gently steer the conversation toward how you can help them (booking, services, etc.).

Keep it under 50 words. Use 1 emoji max."""

        return await self.llm.chat(prompt, message, max_tokens=100)

    async def _handle_general_query(self, message: str, ctx: ConversationContext) -> str:
        """Handle any query that doesn't match specific intents."""
        services = [s.name for s in self.business.services if s.is_active]
        business_info = f"""Business: {self.business.name}
Industry: {self.business.industry}
Location: {self.business.city or 'N/A'}
Phone: {self.business.phone or 'N/A'}
Address: {self.business.address or 'N/A'}
Services: {', '.join(services) if services else 'Various services'}
"""

        system = f"""You are a helpful WhatsApp assistant for {self.business.name}, a {self.business.industry} business in {self.business.city or 'the area'}.

Business Info:
{business_info}

The customer sent: "{message}"

Provide a helpful, concise response (2-3 sentences). If you don't know the answer, suggest they call the business. Keep it friendly and professional. Use emojis sparingly."""

        return await self.llm.chat(system, message, max_tokens=200)
