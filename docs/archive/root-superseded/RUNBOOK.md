# RUNBOOK — VOLAURA Operations

## Prerequisites

- Node.js 20+, pnpm 10+
- Python 3.11+
- Docker (optional — Supabase local)

## Local Setup

```bash
git clone https://github.com/ganbaroff/volaura
cd volaura
pnpm install

# Copy env files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local

# Start frontend
pnpm dev

# Start backend (separate terminal)
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

## Required ENV vars (apps/api/.env)

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | `https://dwdgzfusjsobnixgyzjk.supabase.co` |
| `SUPABASE_SERVICE_KEY` | ✅ prod | Admin key — never expose |
| `GEMINI_API_KEY` | ✅ | Primary LLM evaluator |
| `GROQ_API_KEY` | recommended | Fallback LLM (free tier) |
| `GATEWAY_SECRET` | ✅ | ZEUS bridge auth token |
| `TELEGRAM_BOT_TOKEN` | optional | CEO notifications |
| `TELEGRAM_CEO_CHAT_ID` | optional | CEO chat ID |
| `EXTERNAL_BRIDGE_SECRET` | optional | MindShift bridge |

## Deploy

**Frontend → Vercel** (auto-deploy on push to main)

**Backend → Railway:**
```bash
railway up --service volaura-api
```

**MindShift edge function:**
```bash
cd /path/to/mindshift
npx supabase functions deploy volaura-bridge-proxy --project-ref awfoqycoltvhamtrsvxk
```

## Production Health Check

```bash
curl https://volauraapi-production.up.railway.app/health | python3 -m json.tool
```

Expected: `{"status":"ok","database":"connected","llm_configured":true}`

## Smoke Test

```bash
VOLAURA_PROD_URL=https://volauraapi-production.up.railway.app \
VOLAURA_TEST_EMAIL=your@email.com \
VOLAURA_TEST_PASS=yourpass \
python scripts/prod_smoke_test.py
```

## Swarm (AI agents)

```bash
# Run manually
python -m packages.swarm.autonomous_run

# GitHub Actions: .github/workflows/swarm-daily.yml
# Runs daily at 05:00 UTC (09:00 Baku)
```

## Database Migrations

```bash
npx supabase db push --project-ref dwdgzfusjsobnixgyzjk
```

## Logs

- **Backend:** Railway dashboard → volaura-api → Deployments → Logs
- **Frontend:** Vercel dashboard → volaura-web → Functions
- **Errors:** Sentry (DSN in Railway env)
