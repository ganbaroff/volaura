# Volaura — Verified Professional Talent Platform

Where skills are proven through adaptive assessment, not claimed on CVs.

## Constitution (Supreme Law)
```
PATH:     docs/ECOSYSTEM-CONSTITUTION.md (v1.7, 2026-04-06)
SCOPE:    ALL 5 products — VOLAURA · MindShift · Life Simulator · BrandedBy · ZEUS
```
**5 Foundation Laws (zero exceptions):**
1. NEVER RED — errors = purple `#D4B4FF`, warnings = amber `#E9C400`
2. Energy Adaptation — every product needs Full/Mid/Low energy modes
3. Shame-Free Language — no "you haven't done X", no profile % complete
4. Animation Safety — max 800ms non-decorative, prefers-reduced-motion mandatory
5. One Primary Action — one primary CTA per screen

**LLM provider hierarchy:** Cerebras Qwen3-235B → Ollama/local GPU → NVIDIA NIM → Anthropic Haiku (last resort).
Never use Claude models as swarm agents. Never use only one provider. Always diverse.

## Project Identity
- User tagline: "Prove your skills. Earn your AURA. Get found by top organizations."
- Org tagline: "Search talent by verified skill and score, not unverified CVs."
- NEVER say "volunteer platform" or "LinkedIn competitor". Say "verified talent platform."

**Ecosystem:** VOLAURA (verified skills) · MindShift (daily habits) · Life Simulator (game character) · BrandedBy (AI twin) · ZEUS (agent framework). All share Supabase auth + `character_events` table.

## Tech Stack

**Frontend** (`apps/web/`): Next.js 14 App Router, TypeScript 5 strict, Tailwind CSS 4, Zustand, TanStack Query, React Hook Form + Zod, Recharts, react-i18next (AZ primary), shadcn/ui, Framer Motion, PWA.

**Backend** (`apps/api/`): Python 3.11+ FastAPI async, Supabase async SDK (per-request via Depends), Pydantic v2, google-genai SDK (Gemini 2.5 Flash), Pure-Python IRT/CAT engine, python-telegram-bot, loguru.

**Database:** Supabase PostgreSQL + RLS, pgvector(768) Gemini embeddings, vector ops via RPC only.

**Hosting:** Vercel (frontend), Railway (backend ~$8/mo), Supabase (database).

## Architecture
```
Monorepo: Turborepo + pnpm
├── apps/web/      Next.js 14
├── apps/api/      FastAPI monolith (NOT microservices)
├── packages/swarm/ Python swarm engine + 48 skills + tools
├── supabase/      migrations + seed
└── docs/          HANDOFF.md, DECISIONS.md
```

**API Type Safety:** FastAPI → `/openapi.json` → `@hey-api/openapi-ts` → TS types + TanStack hooks + Zod. Run: `pnpm generate:api`

## AURA Score Weights (FINAL — DO NOT CHANGE)
communication: 0.20, reliability: 0.15, english_proficiency: 0.15, leadership: 0.15, event_performance: 0.10, tech_literacy: 0.10, adaptability: 0.10, empathy_safeguarding: 0.05

## Badge Tiers
Platinum: >= 90, Gold: >= 75, Silver: >= 60, Bronze: >= 40, None: < 40

## File Naming
TypeScript: kebab-case files, PascalCase components. Python: snake_case. SQL: snake_case. Import: `@/` = `apps/web/src/`

## Where Everything Lives

### Rules (auto-loaded every session)
| File | What |
|------|------|
| `.claude/rules/backend.md` | FastAPI + Supabase patterns |
| `.claude/rules/frontend.md` | Next.js 14 + shadcn + i18n |
| `.claude/rules/database.md` | Supabase + pgvector + RLS |
| `.claude/rules/secrets.md` | Key recognition + save protocol |
| `.claude/rules/ceo-protocol.md` | When and how to engage CEO |
| `.claude/rules/swarm.md` | Swarm operating model + agent tools |
| `.claude/rules/never-always.md` | Full NEVER/ALWAYS rules list |
| `.claude/rules/session-routing.md` | Context recovery + session start/end |
| `.claude/rules/copilot-protocol.md` | CTO behavior + communication style |

### Skills (loaded on-demand when description matches)
| Skill dir | Trigger |
|-----------|---------|
| `skills/execution-protocol/` | Sprint execution, 10-step workflow |
| `skills/sprint-protocol/` | Sprint planning, pre-sprint checklist |
| `skills/dsp-simulation/` | Architecture decisions, DSP debate |
| `skills/skills-matrix/` | Which skills/agents to load for a task |
| `skills/product-strategy/` | Product decisions, positioning |

### Hooks (enforcement, not suggestion)
| Hook | What it blocks |
|------|---------------|
| `.claude/hooks/security-guard.sh` | rm -rf, --no-verify, .env in git, force push, DROP TABLE |
