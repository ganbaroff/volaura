# ECOSYSTEM AUDIT — ALL REPOSITORIES
**Date:** 2026-04-06 | **By:** CTO + 3 Explore agents (each repo read fully)
**Repos audited:** VOLAURA, MindShift, claw3d-fork (ZEUS + Life Sim), VidVow

---

## VOLAURA (C:\Projects\VOLAURA)
**Status:** 85% built | **Live:** volaura.app
- 43 pages, 24 API routers, 67 migrations, 742 tests
- IRT/CAT engine (pure Python), AI eval pipeline (Gemini→Groq→keyword)
- Python swarm: 8 perspectives, daily cron, 48 skill files
- **Fixed today:** 30+ Law 1 violations (zero red remaining), G9 leaderboard deleted, G15 counters, G21+CL6 badge/crystals
- **Still broken:** 19 Constitution pre-launch blockers, old design on prod, Energy Picker missing

## MINDSHIFT (C:\Users\user\Downloads\mindshift)
**Status:** 95% built | **Live:** Vercel
- 187 TS/TSX files, 14 Supabase Edge Functions, 207+201 tests
- Focus timer, Mochi AI companion, NOW/NEXT/SOMEDAY tasks, energy/burnout tracking
- 6 locales (EN/RU/AZ/TR/DE/ES), Capacitor for iOS/Android
- VOLAURA bridge EXISTS: `volaura-bridge.ts` sends focus sessions, streaks, vitals, psychotype
- **CRITICAL BUG:** i18n `translate.mjs` — arrays deserialized as objects for ALL non-English locales. 236 Mochi strings inaccessible. Fix: `unflatten()` must detect numeric keys → restore arrays.
- **Pending:** Google Play account verification, pg_cron push notifications (CEO manual action)

## CLAW3D-FORK — ZEUS Gateway (C:\Users\user\Downloads\claw3d-fork\server)
**Status:** 70% functional | **Live:** Railway + localhost:18789
- 39 agents, 4 LLM providers (Cerebras primary → Ollama → NVIDIA → Anthropic)
- Event-driven: webhooks from GitHub/Sentry/Railway → auto-classify → wake agents
- User memory system (4KB per user, auto-updated)
- Autonomous audit mode (`swarm.auto`) — 19 agents per domain
- **Broken:**
  - WEBHOOK_SECRETs not in Railway (events don't fire in prod)
  - Synthesis override dead code (lines 1371-1381)
  - `staticReply()` undefined — gateway crashes if all providers fail
  - No heartbeat — WebSocket clients hang silently
  - Hardcoded Windows paths (`C:/Projects/VOLAURA/...`)
  - AGENT_FILE_MAPPING points to non-existent MindShift files

## CLAW3D-FORK — Life Simulator 3D (C:\Users\user\Downloads\claw3d-fork\src)
**Status:** 40% integrated
- Next.js + Three.js + React Three Fiber
- 3D office: agents walk, sit, use rooms, show emoji status
- Interaction zones: SMS booth, server room, QA lab, gym
- **Not connected:** Ready Player Me avatars, RemoteAgentChatPanel, per-session memory, autonomous coordinator

## VIDVOW (C:\Users\user\Downloads\vidvow)
**Status:** Standalone | **Not part of ecosystem**
- Video-verified crowdfunding: React 19 + Hono + Cloudflare Workers + D1
- 4 funding models, AI trust score, multi-currency (Stripe/GoldenPay/Cryptomus)
- **No integration** with VOLAURA/MindShift/ZEUS

---

## CROSS-REPO INTEGRATION STATUS

| From → To | Mechanism | Works? |
|-----------|-----------|--------|
| MindShift → VOLAURA | `volaura-bridge.ts` (fire-and-forget HTTP) | ✅ Code exists, needs VITE_VOLAURA_API_URL set |
| VOLAURA → Life Sim | `character_events` table + crystal_ledger | ✅ Tables exist, Life Sim not reading yet |
| VOLAURA → ZEUS (Python swarm) | `proposals.json` + Telegram | ✅ Works daily |
| Python swarm → ZEUS Gateway | `POST /event` bridge | ❌ GATEWAY_SECRET not in Railway |
| ZEUS Gateway → Life Sim 3D | Agent state → 3D office rendering | ⚠️ Partial (static state, no real-time) |
| ZEUS Gateway → MindShift | None | ❌ Not connected |
| Life Sim → VOLAURA | CloudSaveManager (CLOUD_ENABLED=false) | ❌ Stub only |

## SHARED AUTH STATUS

| Product | Auth system | Shared? |
|---------|-----------|---------|
| VOLAURA | Supabase (project A) | — |
| MindShift | Supabase (project B: awfoqycoltvhamtrsvxk) | ❌ SEPARATE |
| ZEUS Gateway | STUDIO_ACCESS_TOKEN (custom) | ❌ SEPARATE |
| Life Sim | None (piggybacks on claw3d session) | ❌ NO AUTH |
| VidVow | Mocha users service | ❌ SEPARATE |

**Shared Supabase auth = NOT implemented across ANY products.**

---

## TOP 10 CROSS-ECOSYSTEM ISSUES

1. **No shared auth** — each product has its own auth. ADR-006 planned shared Supabase but never implemented.
2. **MindShift i18n arrays broken** — 236 Mochi strings inaccessible for 5 languages. Blocks AZ launch.
3. **ZEUS webhooks dead in prod** — GATEWAY_SECRET not set. Event-driven architecture is cron-only.
4. **Life Sim cloud = stub** — CLOUD_ENABLED=false. Character state never syncs to Supabase.
5. **Hardcoded Windows paths in ZEUS** — gateway breaks on any non-Windows deployment.
6. **Python↔Node.js bridge dead** — bridge code exists but secret not deployed.
7. **Constitution not enforced in MindShift/claw3d** — only VOLAURA has tools/checker.
8. **No E2E tests for ZEUS** — 0 tests for 39-agent system.
9. **3D office disconnected from reality** — agents animate but don't reflect real agent state.
10. **VidVow orphaned** — production-grade platform sitting unused.
