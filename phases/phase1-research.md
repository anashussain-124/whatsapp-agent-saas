# Phase 1: Research Findings
**Date:** 2026-06-19
**Status:** Complete

## WhatsApp Business Platform (Cloud API)

### Key Facts
- **API Type:** Cloud API (hosted by Meta, no on-premise server needed)
- **Pricing Model:** Per-message basis (since July 1, 2025)
- **Free Messages:** ALL non-template messages within 24h customer service window
- **Free Entry Point:** 72-hour free window when customer initiates from ad/QR
- **India Marketing Template Rate:** ~₹0.115-0.135 per delivery
- **Utility Templates:** Free within service window
- **Message Types:** Text, image, video, audio, document, location, contacts, interactive (buttons, lists), templates

### Provider Options
1. **Direct (Meta):** Lowest cost, requires Facebook Business verification, more setup
2. **Twilio:** Free trial, simplifies onboarding, Conversations API for 2-way, SDK in Python/JS/Java/PHP/Ruby/C#
3. **Other BSPs:** Wati, Interakt, Gallabox (India-specific, higher cost but local support)

### Recommendation
**Start with Twilio** for MVP (free trial, fast onboarding, great docs). Migrate to direct Meta API at scale for cost optimization.

## Agentic Framework Landscape

### LangGraph (LangChain)
- **Status:** Production-grade, trusted by Klarna, LinkedIn, Uber, Coinbase, ServiceNow
- **Features:** State machine orchestration, human-in-the-loop, memory persistence, streaming
- **Best For:** Complex multi-step workflows requiring reliability and observability
- **Python:** `pip install langgraph`

### Anthropic's Agent Patterns (Dec 2024)
- **Key Insight:** Simplest composable patterns beat complex frameworks
- **Patterns:** Prompt chaining, routing, parallelization, orchestrator-workers
- **Recommendation:** Start with direct LLM API calls, add LangGraph only when complexity demands it

### Decision
**Start with direct LLM API (OpenRouter) + simple state machine.** Add LangGraph in Phase 2 if orchestration complexity grows.

## Indian SMB Market

### Key Stats
- 63 million MSMEs in India (2nd largest after China)
- WhatsApp penetration: 500M+ users in India (largest market)
- Digital adoption post-UPI: SMBs comfortable with WhatsApp for business
- Key verticals: Salons, clinics, tutors, repair services, restaurants, retail

### Competitive Landscape
- **Wati:** WhatsApp CRM for SMBs, $49/mo
- **Interakt:** WhatsApp commerce, ₹999/mo
- **Gallabox:** WhatsApp team inbox, ₹499/mo
- **Gap:** None offer true AI agentic orchestration — all are rule-based or simple chatbots

### Pricing Sweet Spot
- Indian SMBs willing to pay ₹499-999/mo ($6-12) for automation
- Free tier essential for adoption (WhatsApp non-template messages are free)

## Technical Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| WhatsApp Provider | Twilio (MVP) → Meta Direct (scale) | Free trial, fast setup |
| Backend | Python (FastAPI) | Async, great WhatsApp SDK support |
| Agent Framework | Direct LLM API + state machine | Simplicity first, add LangGraph later |
| LLM Provider | OpenRouter | Multi-model, cost-effective |
| Database | SQLite (MVP) → PostgreSQL (scale) | Zero config for prototype |
| Hosting | Railway/Render (MVP) | Free tier, easy Python deployment |
| Frontend (Landing) | Next.js + Tailwind | Fast, SEO-friendly, Vercel free tier |
| CI/CD | GitHub Actions | Free, integrated with GitHub |

## Cost Model (Per Business)

### MVP Costs (Twilio)
- Twilio WhatsApp: Free trial → ~$0.005/msg after
- OpenRouter LLM: ~$0.001-0.003 per request
- Hosting: Free (Railway/Render free tier)
- **Total per business/mo:** ~$2-5 at 1000 conversations

### Revenue Target
- Free tier: 100 conversations/mo
- Pro: ₹999/mo (~$12) — unlimited conversations
- **Break-even:** 50 Pro customers covers all infrastructure
