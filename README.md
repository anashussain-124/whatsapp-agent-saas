# WhatsApp Agent SaaS v0.2.0

**Zero-cost WhatsApp AI booking agent for Indian local businesses**

## Quick Start

### Backend
```bash
cd agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
python -m uvicorn src.main:app --reload --port 8000
```

### Frontend
```bash
cd landing
npm install
npm run dev
```

## Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for the full zero-cost deployment guide.

## Tech Stack
- **Backend:** Python 3.12 + FastAPI
- **Database:** SQLite (default) → PostgreSQL (Supabase free tier)
- **LLM:** OpenRouter (OWL Alpha model — free)
- **Messaging:** Meta WhatsApp Cloud API (direct)
- **Frontend:** Next.js 14 + Tailwind CSS
- **Hosting:** Render (backend) + Vercel (frontend)

## Cost: ₹0/month
All components use free tiers. Only cost is LLM tokens (~₹100-500/mo at pilot volume).
