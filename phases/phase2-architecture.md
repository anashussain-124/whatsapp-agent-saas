# Phase 2: Architecture & System Design
**Date:** 2026-06-19
**Status:** Complete

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Business Platform                │
│                    (via Twilio / Meta Cloud API)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Webhook (incoming messages)
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Webhook     │  │  Conversation │  │  Business Owner   │  │
│  │  Handler     │  │  Manager      │  │  Dashboard API    │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────────────┘  │
│         │                │                                    │
│         ▼                ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Main Orchestrator Agent                   │   │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │  Intent     │ │  Context    │ │  Response       │  │   │
│  │  │  Classifier │ │  Manager    │ │  Generator      │  │   │
│  │  └──────┬─────┘ └──────┬──────┘ └────────┬────────┘  │   │
│  └─────────┼──────────────┼─────────────────┼────────────┘   │
│            │              │                 │                 │
│            ▼              ▼                 ▼                 │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐     │
│  │  Booking      │ │  Pricing   │ │  Service Menu      │     │
│  │  Agent        │ │  Agent     │ │  Agent             │     │
│  └──────────────┘ └────────────┘ └────────────────────┘     │
│            │              │                 │                 │
│            ▼              ▼                 ▼                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Business Config (per tenant)              │   │
│  │  • Services & Pricing  • Availability  • Location     │   │
│  │  • Business Hours      • Owner Info   • Custom FAQs   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    SQLite / PostgreSQL                        │
│  • Conversations  • Bookings  • Business Config  • Analytics │
└──────────────────────────────────────────────────────────────┘
```

## Agent Architecture: Main Orchestrator Pattern

Following Anthropic's "orchestrator-workers" pattern:

### Main Orchestrator
- Receives customer message
- Classifies intent (booking, query, support, small talk)
- Routes to appropriate sub-agent
- Manages conversation context (memory)
- Generates final response

### Sub-Agents
1. **Intent Classifier:** Classifies message intent + extracts entities
2. **Booking Agent:** Handles appointment scheduling, rescheduling, cancellation
3. **Pricing Agent:** Answers price queries from business config
4. **Service Menu Agent:** Lists services, descriptions, duration
5. **Context Manager:** Maintains conversation state, handles multi-turn dialogs
6. **Response Generator:** Formats response with WhatsApp-friendly formatting

### Conversation State Machine
```
GREETING → INTENT_COLLECTION → DETAIL_GATHERING → CONFIRMATION → COMPLETED
    ↑              │                    │                │
    └──────────────┴────────────────────┴────────────────┘
                    (clarification loops)
```

## Tech Stack

### Backend
- **Runtime:** Python 3.12 + FastAPI
- **WhatsApp:** Twilio Python SDK (`twilio`)
- **LLM:** OpenRouter API (access to Claude, GPT-4, etc.)
- **Database:** SQLite (MVP) → PostgreSQL (scale)
- **ORM:** SQLAlchemy 2.0
- **Task Queue:** Celery + Redis (for async tasks like reminders)
- **Hosting:** Railway.app (free tier → $5/mo)

### Frontend (Landing Page)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Hosting:** Vercel (free tier)
- **CMS:** Google Sheets (for programmatic SEO content)

### DevOps
- **Version Control:** GitHub
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (free tier)
- **Logging:** Loguru

## Database Schema

```sql
-- Business configuration (one per tenant)
CREATE TABLE businesses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    industry TEXT NOT NULL,  -- salon, clinic, tutor, repair, restaurant, retail
    address TEXT,
    city TEXT,
    state TEXT,
    pincode TEXT,
    timezone TEXT DEFAULT 'Asia/Kolkata',
    whatsapp_number TEXT UNIQUE,
    twilio_sid TEXT,
    twilio_auth_token TEXT,
    openrouter_key TEXT,
    system_prompt TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    plan TEXT DEFAULT 'free',  -- free, pro
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Services offered
CREATE TABLE services (
    id TEXT PRIMARY KEY,
    business_id TEXT REFERENCES businesses(id),
    name TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER,
    price_inr INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- Business hours
CREATE TABLE business_hours (
    id TEXT PRIMARY KEY,
    business_id TEXT REFERENCES businesses(id),
    day_of_week INTEGER,  -- 0=Monday, 6=Sunday
    open_time TEXT,
    close_time TEXT,
    is_closed BOOLEAN DEFAULT FALSE
);

-- Conversations
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    business_id TEXT REFERENCES businesses(id),
    customer_phone TEXT NOT NULL,
    customer_name TEXT,
    status TEXT DEFAULT 'active',  -- active, completed, abandoned
    current_intent TEXT,
    context_json TEXT,  -- JSON blob for conversation state
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id),
    direction TEXT NOT NULL,  -- inbound, outbound
    message_type TEXT DEFAULT 'text',  -- text, image, interactive, template
    content TEXT,
    twilio_sid TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings
CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    business_id TEXT REFERENCES businesses(id),
    conversation_id TEXT REFERENCES conversations(id),
    service_id TEXT REFERENCES services(id),
    customer_phone TEXT NOT NULL,
    customer_name TEXT,
    booking_date DATE NOT NULL,
    booking_time TEXT NOT NULL,
    status TEXT DEFAULT 'confirmed',  -- confirmed, cancelled, completed, no_show
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics (aggregated daily)
CREATE TABLE daily_analytics (
    id TEXT PRIMARY KEY,
    business_id TEXT REFERENCES businesses(id),
    date DATE NOT NULL,
    total_conversations INTEGER DEFAULT 0,
    new_conversations INTEGER DEFAULT 0,
    bookings_made INTEGER DEFAULT 0,
    bookings_cancelled INTEGER DEFAULT 0,
    avg_response_time_seconds INTEGER,
    top_intent TEXT,
    UNIQUE(business_id, date)
);
```

## API Endpoints

### Webhook (Twilio → Us)
- `POST /webhook/whatsapp` — Incoming WhatsApp messages
- `POST /webhook/whatsapp/status` — Message delivery status callbacks

### Business Owner Dashboard
- `GET /api/business/:id` — Get business config
- `PUT /api/business/:id` — Update business config
- `GET /api/business/:id/services` — List services
- `POST /api/business/:id/services` — Add service
- `GET /api/business/:id/conversations` — List conversations
- `GET /api/business/:id/analytics` — Get analytics
- `GET /api/business/:id/bookings` — List bookings

### Onboarding
- `POST /api/onboarding` — Create new business (generates config)
- `GET /api/onboarding/:id/status` — Check onboarding status

## Security
- Webhook signature verification (Twilio)
- API key authentication for dashboard
- Rate limiting (100 req/min per business)
- No PII in logs
- Environment variables for all secrets

## Decisions Log

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | WhatsApp Provider | Twilio → Meta Direct | Free trial, fast setup |
| 2 | Backend Framework | FastAPI | Async, Python, great for webhooks |
| 3 | Agent Pattern | Orchestrator + sub-agents | Matches Anthropic's recommended pattern |
| 4 | LLM Access | OpenRouter | Multi-model, cost-effective, single API |
| 5 | Database | SQLite → PostgreSQL | Zero config for MVP |
| 6 | State Management | JSON blob in DB | Simple, no Redis needed for MVP |
| 7 | Hosting | Railway | Free tier, Python-native, easy deploys |
| 8 | Frontend | Next.js + Tailwind | SEO-friendly, fast, free on Vercel |
