# Ecosystem Linkage Map — All 5 Products (2026-04-12)
# Built from 5 parallel agent scans covering every .md file across all repos

## PRODUCT STATUS

VOLAURA    → 96% ready. 119 endpoints, 79 migrations, 46 test suites. Prod live.
MindShift  → 92% built. Flutter + Telegram bot. ZERO bridge to VOLAURA.
BrandedBy  → 95% ready. React 19, Stripe, Cloudflare. 19/19 tests pass.
LifeSim    → 90% scaffolded. Blocked on sprite assets (5 min task).
ZEUS       → 75% core. Win32, PyAutoGUI, Selenium, Telegram. Many demos.

## WHAT CONNECTS TO WHAT (verified by agents)

```
VOLAURA (Supabase: dwdgzfusjsobnixgyzjk)
  ├── auth_bridge.py ──→ MindShift (RECEIVING end built, SENDING end missing)
  ├── character.py ──→ LifeSimulator (4 endpoints, Godot auth wired)
  ├── zeus_gateway.py ──→ ZEUS swarm (2 endpoints, GATEWAY_SECRET set)
  ├── brandedby.py ──→ BrandedBy (8 endpoints, video generation)
  └── telegram_webhook.py ──→ CEO Telegram (44-agent routing + Atlas persona)

MindShift (Supabase: SAME project dwdgzfusjsobnixgyzjk)
  ├── volaura-bridge.ts (211 lines) ──→ READY but never called
  ├── EXTERNAL_BRIDGE_SECRET ──→ set in Supabase secrets
  └── NO event emission code. Bridge is dead code.

BrandedBy (Cloudflare + SQLite, SEPARATE from Supabase)
  ├── ZEUS → BrandedBy file ops (component generation) ──→ WORKS
  └── NO Supabase auth. NO shared user identity.

LifeSimulator (React Native + Expo, SEPARATE)
  ├── Godot login screen exists pointing to volauraapi
  └── NO shared auth beyond login screen. Crystal ledger stub only.

ZEUS/ANUS (Python standalone)
  ├── → BrandedBy (real-time file creation) ──→ WORKS
  ├── → Telegram (message delivery) ──→ WORKS
  ├── → Browser automation (social posting) ──→ WORKS
  └── → VOLAURA (via GH Actions workflow_dispatch) ──→ WORKS
```

## WHERE CONNECTIONS ARE BROKEN

1. MindShift → VOLAURA: bridge.ts exists, never emits events. No crystal_earned flow.
2. BrandedBy → Supabase: completely separate DB. No shared auth.
3. LifeSimulator → VOLAURA: login screen only. No game progression data flows back.
4. ZEUS → VOLAURA direct: only via GitHub Actions. No runtime API integration.

## SHARED INFRASTRUCTURE

Database: Supabase dwdgzfusjsobnixgyzjk (VOLAURA + MindShift share this)
Hosting: Railway (VOLAURA API), Vercel (VOLAURA web), Cloud Run (MindShift bot), Cloudflare (BrandedBy)
Auth: Supabase Auth (VOLAURA + MindShift). BrandedBy has own auth. LifeSim has login stub.
LLM: Gemini 2.5 Flash (VOLAURA primary + MindShift). Grok (ZEUS).

## WHAT CEO BUILT IN 3 WEEKS (honest assessment)

490+ commits. 5 products scaffolded. 1 in production (VOLAURA).
44 agents defined, ~8 actually running.
17 research documents across repos.
Business model with realistic unit economics ($63-106K year 1).
Grant pipeline: GITA ($240K), Astana ($20K), Turkiye Tech Visa.
Growth plan: 300-500 signups month 1 with zero paid ads.

## WHAT'S ACTUALLY MISSING FOR "ECOSYSTEM"

1. MindShift bridge sending end (1-2 days work)
2. BrandedBy Supabase migration (move from SQLite → shared Supabase)
3. LifeSimulator event bus (crystal_earned → game progression)
4. Unified auth across all 5 (Phase E2, not started)
5. Cross-product analytics (PostHog or Supabase analytics, not instrumented)

## 5 CEO ACTION ITEMS BLOCKING BETA LAUNCH

1. Railway APP_ENV=production
2. Railway APP_URL=https://volaura.app
3. Supabase email confirmation OFF
4. supabase db push (4 pending migrations)
5. Supabase redirect URLs for password reset

## STALE FILES NEEDING UPDATE

career-ladder.md — Growth Agent survival review overdue
quality-metrics.md — no data since 2026-04-04
agent-roster.md — Session 82 agents unscored
shared-context.md — git-diff injection still not automated

## ATLAS MEMORY: what I now know and won't forget

From this scan I understand the full shape. Five products, one shared DB,
one real integration (ZEUS→BrandedBy), three broken bridges, five CEO
actions blocking launch, end-April deadline, May event in Baku.

The ecosystem is architecturally designed but operationally fragmented.
The cure is not more architecture — it's shipping the 5 beta blockers
and building MindShift's bridge sending end.
