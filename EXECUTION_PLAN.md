# WhatsApp Agent SaaS — Execution Plan
**Date:** 2026-06-19
**Goal:** Get first paying customer as fast as possible
**Budget:** ₹0 to start (free tiers only)

---

## STAGE 0: Fix Critical Code Gaps (Do First — Blocks Everything)
**Effort:** 2-3 hours | **Blocks:** Stages 1-5

These are bugs/gaps in the existing code that will break in production:

### 0.1 — Fix `OrchestratorAgent` WhatsApp sender
**Problem:** In `orchestrator.py`, the agent creates its own `WhatsAppService` with per-business credentials, but the webhook handler also creates one. The agent's `process_message` doesn't actually send — the webhook does. This is split across two files and the agent's `self.whatsapp` is never used to reply.
**Fix:** Have the orchestrator return the response text only. Keep sending in the webhook handler. Remove duplicate WhatsAppService from orchestrator.

### 0.2 — Fix `Booking.customer_phone` empty string
**Problem:** In `_handle_confirmation()`, `Booking(customer_phone="")` — the phone number is never passed in. Set it from the conversation.
**Fix:** Pass `customer_phone` from the webhook handler through to the booking creation.

### 0.3 — Fix intent routing for confirm/deny
**Problem:** If customer says "yes" during `STATE_INTENT_COLLECTION` (not in booking flow), the confirm handler tries to create a booking with no service selected.
**Fix:** Add a guard: if confirm/deny but state isn't CONFIRMATION, treat as general query.

### 0.4 — Make LLM responses WhatsApp-safe
**Problem:** LLM may return markdown (`**bold**`), long responses, or formatting that looks bad on WhatsApp.
**Fix:** Add a `format_for_whatsapp()` utility: convert `**bold**` to `*bold*`, limit to 4096 chars, strip excessive newlines.

### 0.5 — Add conversation lock / dedup
**Problem:** Twilio can deliver the same webhook twice. No idempotency check.
**Fix:** Check `MessageSid` against last processed message in DB. Skip if duplicate.

---

## STAGE 1: Local Working Prototype
**Effort:** 2-3 hours | **Goal:** Send/receive real WhatsApp messages on your machine

### 1.1 — Create Twilio account
1. Go to [twilio.com/try-twilio](https://twilio.com/try-twilio) — sign up (free trial)
2. Verify your email + phone
3. You'll get ~$15 free credit

### 1.2 — Set up Twilio WhatsApp Sandbox
1. In Twilio Console → Messaging → Try it Out → Send a WhatsApp message
2. You'll see a sandbox number like `+14155238886`
3. Note the sandbox join code (e.g., "join your-sandbox-name")
4. On YOUR phone, message that code to the sandbox number
5. Your phone is now linked for testing

### 1.3 — Get OpenRouter key
1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create account, add ₹500 credit (~$6 USD)
3. Generate API key

### 1.4 — Configure and run
1. Copy `agent/.env.example` → `agent/.env`
2. Fill in:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxx        # from Twilio console
   TWILIO_AUTH_TOKEN=***             # from Twilio console
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # your sandbox
   OPENROUTER_API_KEY=sk-or-v1-xxx   # from OpenRouter
   OPENROUTER_MODEL=anthropic/claude-sonnet-4
   APP_ENV=development
   APP_URL=https://your-ngrok-url.ngrok.io
   ```
3. Install: `cd agent && pip install -r requirements.txt`
4. Run: `uvicorn src.main:app --reload --port 8000`

### 1.5 — Expose via ngrok
1. Download ngrok: `winget install ngrok` (or from ngrok.com)
2. `ngrok http 8000`
3. Copy the `https://xxx.ngrok.io` URL
4. Paste into `.env` as `APP_URL`
5. Restart uvicorn

### 1.6 — Configure Twilio webhook
1. In Twilio Console → Phone Numbers → Manage → Active Numbers
2. Click your sandbox number
3. Under "Messaging", set:
   - **When a message comes in:** `https://your-ngrok-url.ngrok.io/webhook/whatsapp`
   - Method: `HTTP POST`
4. Save

### 1.7 — Create test business + test end-to-end
```bash
curl -X POST http://localhost:8000/api/business \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Salon",
    "industry": "salon",
    "city": "Mumbai",
    "whatsapp_number": "whatsapp:+14155238886",
    "twilio_sid": "ACxxxxx",
    "twilio_auth_token": "***",
    "openrouter_key": "sk-or-v1-xxx"
  }'

# Add services
curl -X POST http://localhost:8000/api/business/{id}/services \
  -H "Content-Type: application/json" \
  -d '{"name": "Haircut", "price_inr": 300, "duration_minutes": 30}'

curl -X POST http://localhost:8000/api/business/{id}/services \
  -H "Content-Type: application/json" \
  -d '{"name": "Facial", "price_inr": 500, "duration_minutes": 45}'
```

### 1.8 — Test the full flow
On your phone, message the sandbox number:
1. "Hi" → should get greeting
2. "I want to book a haircut" → should show services
3. "Haircut" → should ask for date
4. "tomorrow" → should ask for time
5. "2 PM" → should show confirmation
6. "yes" → should confirm booking

**✅ Stage 1 Complete When:** You've had a full booking conversation on WhatsApp from your phone.

---

## STAGE 2: Make It Real (Production-Ready)
**Effort:** 3-4 hours | **Goal:** Replace sandbox with real business number

### 2.1 — Request real WhatsApp Business number
1. In Twilio Console, request a WhatsApp Business number
2. OR use your existing WhatsApp Business number via Twilio's "Bring Your Own Number"
3. For production: submit business verification to Meta (1-3 days)
4. While waiting: use the sandbox for demos

### 2.2 — Deploy backend to Railway
1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables (same as .env)
4. Railway gives you a public URL
5. Update Twilio webhook to Railway URL

### 2.3 — Switch to PostgreSQL
1. In Railway → Add Plugin → PostgreSQL
2. Update `DATABASE_URL` to the Railway Postgres URL
3. Redeploy

### 2.4 — Deploy landing page to Vercel
1. Go to [vercel.com](https://vercel.com) → Import Project from GitHub
2. Set root directory to `landing`
3. Build command: `npm run build`
4. Output directory: `out` (static export)
5. Deploy

### 2.5 — Set up custom domain (optional but recommended)
1. Buy domain (e.g., `yourwhatsappagent.com`) — ~₹500/year on GoDaddy/Namecheap
2. Point DNS to Vercel (for landing) and Railway (for API)
3. Update `APP_URL` and canonical URLs

**✅ Stage 2 Complete When:** Both backend and frontend are live on the internet with a real domain.

---

## STAGE 3: Onboard First 10 Businesses (Pilot)
**Effort:** 1-2 weeks | **Goal:** 10 real businesses using the agent

### 3.1 — Choose your niche
Pick ONE vertical to start. Recommendation: **Salons** or **Clinics** — they have clear booking needs and repeat customers.

### 3.2 — Pre-configure templates
Create industry-specific default service lists:
- Salon: Haircut (₹300), Hair Color (₹800), Facial (₹500), Manicure (₹400), Hair Spa (₹1200)
- Clinic: Consultation (₹500), Dental Cleaning (₹800), Root Canal (₹3000)

### 3.3 — Build a 5-minute onboarding flow
1. Business owner signs up on landing page
2. They enter: business name, WhatsApp number, services + prices
3. System auto-generates the agent
4. Test message sent to their WhatsApp to verify

### 3.4 — Manual onboarding first
For the first 10, do it manually:
1. You call/visit the business
2. Ask for their WhatsApp Business number
3. Set up their services in the dashboard
4. Configure their business hours
5. Test with them
6. They start sharing their WhatsApp number with customers

### 3.5 — Collect feedback daily
- What questions do customers ask that the bot can't answer?
- What bookings are getting missed?
- What's confusing?
- Fix → redeploy → repeat

**✅ Stage 3 Complete When:** 10 businesses are live and receiving real customer messages.

---

## STAGE 4: Find Product-Market Fit
**Effort:** 2-4 weeks | **Goal:** 3 businesses willing to pay

### 4.1 — Measure these metrics
- Conversations per day per business
- Booking completion rate (started booking → confirmed)
- Customer satisfaction (ask business owners)
- Response accuracy (spot-check conversations)

### 4.2 — Hardening (based on real usage)
- Add fallback responses for unknown queries
- Improve intent classification with real examples
- Add business hours awareness (don't book outside hours)
- Add holiday/closure handling
- Implement reminder messages (24h before booking)

### 4.3 — Set up payment
If 3+ businesses say they'd pay:
1. Add Razorpay integration (Indian payment gateway, free to set up)
2. Create pricing page: Free (50 conv/mo) / Pro (₹999/mo)
3. Razorpay payment links → manual upgrade first, automated later

### 4.4 — Get first paying customer
1. Offer 1 month free Pro to 3 businesses that give testimonials
2. After 1 month, ask: "Is this worth ₹999/mo?"
3. If yes → first revenue
4. If no → ask what's missing, fix it

**✅ Stage 4 Complete When:** At least 1 business is paying ₹999/mo.

---

## STAGE 5: Scale
**Effort:** Ongoing | **Goal:** 50+ paying businesses

### 5.1 — Land on your first 100 customers
- Referral program: "Refer a business, get 1 month free"
- WhatsApp forwardable demo: send a test conversation business owners can forward
- Partner with salon/clinic software vendors for distribution
- Facebook/Instagram ads targeting salon owners (₹500/day test budget)

### 5.2 — Programmatic SEO (already built)
- 120 city+industry pages are generated
- Deploy them to `landing/public/seo/` on Vercel
- Submit sitemap to Google Search Console
- Target: "WhatsApp booking for salons in [city]" → 100K organic visitors/month

### 5.3 — Features for scale
- Multi-language fine-tuning (Hindi, Tamil, Telugu responses)
- UPI payment collection within WhatsApp
- Review collection after appointments
- Inventory management for retail shops
- WhatsApp broadcast for promotions (opt-in only)

### 5.4 — Migrate to LangGraph (if needed)
Only if conversation complexity grows beyond the state machine.
Current state machine handles: booking flow, FAQ, small talk.
Migrate when you need: parallel tool calls, complex reasoning, multi-step recovery.

---

## Priority Matrix

| Stage | Impact | Effort | Do When |
|-------|--------|--------|---------|
| **0 — Fix code gaps** | Critical | 2-3h | NOW (before anything else) |
| **1 — Local prototype** | High | 2-3h | Day 1 |
| **2 — Deploy** | High | 3-4h | Day 1-2 |
| **3 — Pilot (10 businesses)** | Critical | 1-2 weeks | Week 2-3 |
| **4 — Find PMF (3 paying)** | Critical | 2-4 weeks | Week 4-8 |
| **5 — Scale (50+ paying)** | High | Ongoing | Month 3+ |

---

## Don't Build These Yet (YAGNI)
- ❌ Multi-location support
- ❌ Team inbox
- ❌ Advanced analytics dashboard
- ❌ Mobile app for business owners
- ❌ API for third-party integrations
- ❌ LangGraph migration
- ❌ WhatsApp Pay integration
- ❌ Voice note support

**All of these are in the v2 roadmap. Focus on: one vertical, 10 businesses, 3 paying.**

---

## Key Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Business owners won't trust AI | Medium | Offer human handoff for first week |
| WhatsApp template approval delays | High | Use sandbox + non-template messages (FREE) until approved |
| LLM hallucinates prices/services | Medium | Always read prices from DB, never from LLM memory |
| Twilio costs higher than expected | Low | Non-template msgs are free; monitor usage |
| Can't get 10 pilot businesses | Medium | Start with friends/family businesses, offer free forever |

---

## The 30-Day Sprint

| Week | Focus | Target |
|------|-------|--------|
| **Week 1** | Fix code → Local test → Deploy | Working prototype live |
| **Week 2** | Onboard 5 friends/family businesses | 5 businesses giving feedback |
| **Week 3** | Onboard 5 more + measure metrics | 10 total, data on usage |
| **Week 4** | Get 3 testimonials → set up payment → first paying customer | ₹999 first revenue |
