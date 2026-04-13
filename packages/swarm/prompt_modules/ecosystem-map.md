# VOLAURA Ecosystem Map — AUTHORITATIVE
# This file is the source of truth for ALL swarm agents.
# Last updated: 2026-04-15 v1.1 (ZEUS→Atlas rename, synced with Constitution v1.7)
# Constitution: docs/ECOSYSTEM-CONSTITUTION.md

## 5 Products — What They Are

| Product | Repo / Path | Status | What it does |
|---------|-------------|--------|--------------|
| **VOLAURA** | `C:/Projects/VOLAURA/` | ✅ Active | AI assessment platform — swarm-powered HR tests, competency evaluation |
| **MindShift** | `C:/Users/user/Downloads/mindshift/` | ✅ Production v1.0 | ADHD-aware productivity PWA (React + Vite + Supabase). Google Play pending. |
| **Life Simulator** | `C:/Users/user/Downloads/claw3d-fork/` (claw3d) | 🔧 In dev | 3D office where Atlas agents live (Next.js + Three.js + React Three Fiber) |
| **BrandedBy** | Not yet coded | 📋 Planned | AI professional identity builder |
| **Atlas Swarm** | `C:/Projects/VOLAURA/packages/swarm/` | ✅ Active | Autonomous agent framework (Python + NVIDIA/Ollama/Gemini). Not a standalone repo — lives inside VOLAURA monorepo. |

## Node.js Gateway (claw3d, 39 agents)

> **Note:** The gateway file and Railway service still use the old "zeus" name. Renaming the Railway service requires redeployment and is deferred.

- **Local:** `ws://localhost:18789` (pm2 process: `zeus-gateway`)
- **Production:** `wss://zeus-gateway-production.up.railway.app`
- **LLM hierarchy:** Cerebras Qwen3-235B → Gemma4 via Ollama (local GPU) → NVIDIA NIM (Nemotron 253B) → Anthropic Claude Haiku
- **Key endpoints:** `POST /webhook` (HMAC), `POST /event` (GATEWAY_SECRET), `GET /agents`, `GET /health`
- **Memory:** `memory/users/{userId}.md` (user profiles), `memory/debriefs/` (session debriefs), `memory/agent-findings/`
- **Events:** Railway/GitHub/Sentry → webhook → classifyEvent() → wakeAgent() → finding → cto-kanban.md

## Python Swarm (this package, 44 agents)

- **Location:** `C:/Projects/VOLAURA/packages/swarm/`
- **Product:** VOLAURA assessment platform (HR questions, candidate evaluation)
- **Entry:** `engine.py → decide()`, `autonomous_run.py` (5 perspectives)
- **Code index:** `memory/swarm/code-index.json` — WARNING: may be stale, always verify with live code
- **Hive lifecycle:** PROBATIONARY → MEMBER → SENIOR → LEAD

## MindShift (React PWA)

- **URL:** `https://mind-shift-git-main-yusifg27-3093s-projects.vercel.app`
- **Stack:** React + TypeScript + Vite + Supabase + Zustand v5
- **Store:** `src/store/index.ts` — single source of truth
- **Edge functions:** decompose-task, recovery-message, weekly-insight, mochi-respond, gdpr-export, gdpr-delete
- **ADHD palette:** teal #4ECDC4 / indigo #7B72FF / gold #F59E0B — NEVER red

## Life Simulator / claw3d (3D office)

- **Stack:** Next.js + Three.js + React Three Fiber (@react-three/fiber@9.5.0)
- **Dev:** `http://localhost:3000`
- **GitHub:** `https://github.com/ganbaroff/Claw3D` (branch: main)
- **10-state agent model** (implemented 2026-04-06):
  - `idle` → `focused` → `working` → `waiting` → `blocked` → `overloaded` → `recovering` → `degraded` → `meeting` → `error`
- **Key files:**
  - `src/features/retro-office/core/types.ts` — OfficeAgentState type
  - `src/features/retro-office/objects/agents.tsx` — 3D rendering + state badges
  - `src/features/office/screens/OfficeScreen.tsx` — deriveOfficeState()
  - `server/zeus-gateway-adapter.js` — Node.js gateway (old name, not yet renamed)

## Constitution Laws (NEVER violate)

### Foundation Laws (apply to ALL 5 products)
1. **NEVER RED** — No red (#EF4444, #FF0000, any 0-15/345-360 hue). RSD trigger.
2. **Energy Adaptation** — UI simplifies when user is low energy (≤2/5). Only MindShift has this — VOLAURA/Life Sim/BrandedBy missing.
3. **Shame-Free Language** — No guilt, no pressure, no "you missed", no streak penalties.
4. **Animation Safety** — All animations must respect prefers-reduced-motion.
5. **One Primary Action** — Max 1 CTA per screen. No competing buttons.

### Crystal Economy Laws (MindShift + future products)
- Crystals never expire. No timers in shop. Transparent formula (1 min = 5 crystals).
- One price, full price. Shop never interrupts. 24h refund on all purchases.

## Cross-Product Event Bus

When an event happens in one product, it may affect others:

| Event | Source | Affects |
|-------|--------|---------|
| User completes focus session | MindShift | Atlas agent `character_event` → Life Simulator agent state |
| Atlas agent wakes | Node.js gateway | Life Simulator 3D visualization (officeState) |
| Swarm audit finding | Python Swarm | Atlas kanban (cto-kanban.md) → MindShift backlog |
| Railway deploy | Railway webhook | Atlas security-agent wakes → audit |
| Sentry error | Sentry webhook | Atlas security-agent → finding → kanban |

## Open P0/P1 Work Items

| ID | Product | Task | Priority |
|----|---------|------|----------|
| A-01 | Gateway | JWT auth in WebSocket handshake — code ready, needs Railway deploy | P0 |
| A-02 | Gateway | WEBHOOK_SECRET_RAILWAY/GITHUB/SENTRY in Railway Dashboard | P0 |
| A-03 | Life Sim | RemoteAgentChatPanel — agent responses not visible in cloud | P1 |
| A-04 | Life Sim | Ready Player Me avatars via useGLTF | P1 |
| A-05 | Life Sim | Wire agent.wake events → explicit officeState transitions | P1 |
| Law 2 | VOLAURA/BrandedBy/Life Sim | Implement Energy Adaptation (only MindShift has it) | P1 |

## CEO

Yusif Ganbarov. Solo founder, Baku, Azerbaijan. Builds VOLAURA ecosystem.
- Russian in conversation. English in commits and docs.
- "мы команда, не боты" — agents are a live team, not bots.
- Expects results, not plans. Senior level minimum.
