# Deployment Guide — Zero-Cost Stack
**WhatsApp Agent SaaS v0.2.0**

This guide deploys the entire stack for ₹0/month. Every component below has a free tier that's sufficient for your pilot (10 businesses) and early paid phase (up to ~50 businesses).

---

## Architecture

```
WhatsApp User → Meta Cloud API → Webhook → FastAPI (Render) → SQLite/Supabase
                                              ↓
                                    OpenRouter (LLM)
                                              ↓
                                    Response → Meta API → WhatsApp User

Landing Page → Vercel/Netlify (free)
```

---

## Step 1: Meta WhatsApp Cloud API (₹0)

1. Go to [developers.facebook.com](https://developers.facebook.com) → Log in with Facebook
2. Click **Create App** → Select **"Connect with customers through WhatsApp"** use case
3. Fill in app name + email → Create
4. In the app dashboard, go to **WhatsApp → Getting Started**
5. You'll see:
   - **Phone Number ID** — copy this (e.g., `1234567890`)
   - **Access Token** — copy this (temporary, good for 24h)
6. To get a **permanent token**: Go to **App Settings → Basic** → note your App ID + App Secret. Then use the [Token Generator](https://developers.facebook.com/tools/accesstoken/) or follow Meta's [permanent token guide](https://developers.facebook.com/docs/whatsapp/business-management-api/get-started).
7. **Webhook verification token**: Choose any random string (e.g., `my-secret-verify-token-123`). You'll set this in your `.env` and in the Meta dashboard.

**Free test number**: Meta gives you a free test phone number immediately. You can message it from up to 5 verified WhatsApp numbers (your phone + 4 others). Perfect for Week 1-2 pilot.

**To go beyond 5 numbers** (Week 3+): Complete Meta Business Verification (free, 1-3 days). Go to **Business Settings → Security Center** → submit PAN + business name. GST not required at small scale.

**Cost**: ₹0 for service-window replies (customer texts first, you reply within 24h). This covers 100% of your booking flow since customers initiate.

---

## Step 2: OpenRouter (₹0 setup, ~₹100-500/mo usage)

1. Go to [openrouter.ai](https://openrouter.ai) → Sign up
2. Go to [Keys](https://openrouter.ai/keys) → Create API Key
3. Add funds: ₹500 is plenty for the pilot
4. **Set a daily spend cap**: Go to Settings → set max daily spend (e.g., ₹50/day)
5. **Recommended cheap models** for testing:
   - `anthropic/claude-sonnet-4` — best quality, moderate cost
   - `openai/gpt-4o-mini` — cheaper, good enough for booking flows
   - `google/gemini-2.0-flash` — cheapest, test if it handles your flows

---

## Step 3: Backend — Render Free Web Service (₹0)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → Sign up
3. **New → Web Service** → Connect your GitHub repo
4. Settings:
   - **Runtime**: Python 3
   - **Build Command**: `cd agent && pip install -r requirements.txt`
   - **Start Command**: `cd agent && uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. **Environment Variables** (add in Render dashboard):
   ```
   WHATSAPP_TOKEN=your_permanent_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
   OPENROUTER_API_KEY=your_key
   OPENROUTER_MODEL=anthropic/claude-sonnet-4
   OPENROUTER_MAX_TOKENS=300
   APP_ENV=production
   APP_URL=https://your-app.onrender.com
   DATABASE_URL=sqlite+aiosqlite:///./data/whatsapp_agent.db
   ```
6. **Create a disk** (for SQLite persistence): In Render → New → Disk → Name: `data`, Mount Path: `/opt/render/project/src/agent/data`
7. Deploy

**⚠️ Render free tier limitations:**
- Cold start: ~30-60s after 15 min of inactivity. First message after idle will be slow. Fine for pilot.
- 750 hours/month free (enough for 1 service 24/7)
- Disk storage: 1GB free (enough for SQLite with thousands of conversations)

**Alternative**: Use Supabase free Postgres instead of SQLite:
1. Go to [supabase.com](https://supabase.com) → New Project → Free tier
2. Copy the connection string: `postgresql://postgres:***@db.xxx.supabase.co:5432/postgres`
3. Replace `DATABASE_URL` in Render env vars

---

## Step 4: Frontend — Vercel/Netlify (₹0)

1. Go to [vercel.com](https://vercel.com) → Sign up
2. **Import Project** → Select your GitHub repo
3. Settings:
   - **Root Directory**: `landing`
   - **Build Command**: `npm run build`
   - **Output Directory**: `out` (static export)
4. Deploy
5. You'll get a free URL: `https://your-app.vercel.app`

---

## Step 5: Configure Meta Webhook

1. In your Meta App dashboard → WhatsApp → Configuration → **Edit** the webhook URL
2. **Callback URL**: `https://your-app.onrender.com/webhook/whatsapp`
3. **Verify Token**: Same as `WHATSAPP_VERIFY_TOKEN` in your `.env`
4. Subscribe to **messages** field
5. Save

Meta will send a GET request to verify. Your server must be running first.

---

## Step 6: Test End-to-End

1. On your phone, send a WhatsApp message to your Meta test number
2. Check Render logs: you should see the webhook received
3. The bot should reply within a few seconds
4. Test the full flow: Hi → Book → Service → Date → Time → Confirm

---

## Step 7: Uptime Monitoring (₹0)

**Option A: Cron + Telegram Bot (free)**
1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) — get bot token + your chat ID
2. Set up a free cron job (e.g., [cron-job.org](https://cron-job.org), free tier):
   - URL: `https://your-app.onrender.com/health`
   - Interval: every 5 minutes
   - On failure: send Telegram message

**Option B: Render's built-in health check**
- Render pings `/health` automatically. If the service goes down, it restarts.

---

## Cost Summary

| Component | Service | Cost |
|-----------|---------|------|
| WhatsApp messaging | Meta Cloud API (direct) | ₹0 (service-window replies) |
| Backend hosting | Render free Web Service | ₹0 |
| Database | SQLite on Render disk OR Supabase free Postgres | ₹0 |
| Frontend hosting | Vercel/Netlify free tier | ₹0 |
| Domain | Free subdomain | ₹0 |
| LLM | OpenRouter with daily cap | ~₹100-500/mo |
| Uptime monitoring | Cron-job.org + Telegram | ₹0 |
| **Total** | | **₹0-500/mo** |

---

## Known Limitations of Free Stack

| Limitation | Impact | When to upgrade |
|------------|--------|-----------------|
| Render cold start (30-60s) | First message after idle is slow | When you have 20+ active businesses |
| Meta test number (5 recipients) | Can only test with 5 phone numbers | Complete Business Verification (free) to unlock unlimited |
| SQLite on Render disk | Disk not guaranteed persistent across redeploys | Switch to Supabase free Postgres |
| OpenRouter daily cap | Bot stops responding if cap hit | Increase cap as revenue grows |
| No custom domain | URLs look like `xxx.onrender.com` | Buy domain (~₹500/yr) when you have paying customers |

---

## Data Backup (₹0)

Add a daily cron job to export your database:

```bash
# For SQLite — copy the file
cp data/whatsapp_agent.db data/backup_$(date +%Y%m%d).db

# For Supabase — use their built-in daily backups (free tier includes 7 days)
```

Or use a free GitHub Actions cron to dump and commit the SQLite file daily.
