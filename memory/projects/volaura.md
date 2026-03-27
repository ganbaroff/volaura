# Volaura Project Context

## What It Is
Verified volunteer talent platform for Azerbaijan (CIS/MENA expansion later).
NOT a major event tool — platform FOR volunteers. Launch events are channels, not purpose.
AURA Score = credential system (like credit score for volunteering, weighted across 8 competencies).
Goal: collect BEST volunteers, create real professional credential. 200+ in pipeline.

## Business Context
- Budget: ~$50/mo (Vercel free, Railway $8, Supabase free tier)
- Timeline: 6 weeks total. Started 2026-03-23. Week 4 in progress.
- Yusif applies to Anthropic — Volaura is portfolio proof. Every session matters.
- 200+ volunteers in pipeline waiting for platform
- HR contacts (bouquet strategy) need working link to share
- B2B model: first 100 volunteers free, then $5 AZN per assessment for orgs

---

## Current Sprint Status (as of 2026-03-27 Session 50)

**Sprint 10 — IN PROGRESS | BrandedBy B1-B2-B3 COMPLETE ✅**

**BrandedBy Sprint B1-B2-B3 (Sessions 48-50) — ALL DONE:**
- brandedby.* Supabase schema: ai_twins + generations + RLS + triggers LIVE
- FastAPI: 8 routes for AI Twin CRUD + personality + video generation queue
- ZeusVideoSkill: portrait + script → Kokoro TTS → SadTalker → MP4 (~2 min, E2E verified)
- Async video worker: queued→processing→completed, stale-lock recovery, MAX_RETRIES=2
- Frontend: /brandedby (3-step setup) + /generations/[id] (video player + LinkedIn/TikTok share)
- volaura.app updated, FAL_API_KEY + GROQ_API_KEY on Railway
- brandedby.xyz: pending GoDaddy A record @ 76.76.21.21

**Sprint 10 — Activation Wave (Sessions 47+):**
- ✅ Groq fallback in bars.py (Gemini→Groq→OpenAI→keyword)
- ✅ Referral tracking migration (referral_code + utm_* + referral_stats VIEW)
- ✅ scenario_ru column on questions
- ✅ Org B2B dashboard (/me/dashboard + /me/volunteers)
- ✅ UTM capture at auth/callback — ProfileUpdate + UTMCapture component + callback PATCH
- ✅ Welcome page /welcome — post-onboarding activation screen with competency CTA
- ⏳ Badge share button on /aura (2h)
- ⏳ RU question translations x30 (2h)
- ⏳ CEO provides ~10 HR coordinator names for ref codes

---

## What's Done (Complete — do not re-do)

### Backend (51 routes — LIVE on Railway)
- FastAPI project: 60+ Python files, 512 tests passing
- Auth: register, login, refresh, logout (server-side JWT via admin.auth.get_user())
- Assessment engine: pure-Python IRT/CAT (3PL + EAP + MFI), zero external deps
- LLM evaluation: Gemini → OpenAI → keyword_fallback chain
  - DeCE Framework: per-concept {score, quote, confidence} (ISO 10667-2)
  - keyword_fallback flagged as evaluation_mode="degraded" (ADR-010)
  - 4 anti-gaming gates: min_length, stuffing_detection, coherence_heuristic, scenario_relevance
  - Async re-evaluation worker (reeval_worker.py): LLM re-scores degraded answers silently
- Per-competency decay half-lives: tech=730d, english=1095d, communication=1460d, leadership=1640d
- Quality gate: GRS metric + adversarial gate + 10-point checklist for questions
- Profile CRUD, Events CRUD, AURA score, Badge tiers
- Organizations, Invites (CSV bulk), Activity feed, Discovery, Leaderboard, Stats
- Referral system, Streak tracking, Leagues, AURA Coach
- Rate limiting (slowapi): auth 5/min, assessment start 3/hour, answer 60/hour
- Security: JWT fix (was CVSS 9.1), CORS, headers, Sentry monitoring, XSS protection
- Telegram webhook integration
- OpenAPI spec generation at /openapi.json
- **Production URL:** https://volauraapi-production.up.railway.app

### Database (30+ migrations — Supabase)
- All tables: profiles, assessments, competency_scores, events, event_registrations, organizations, org_members, invites, notifications, referrals, badge_history, activity_log, volunteer_leagues, evaluation_queue
- RLS on every table
- DB functions: match_volunteers (pgvector), upsert_aura_score, update_event_volunteer_count
- Seed data with GRS-validated question keywords (multi-word behavioral phrases, GRS=1.0)
- pgvector: 768 dimensions (Gemini text-embedding-004)
- **5 pending migrations:** HNSW, RLS fixes, assignment columns, evaluation_queue (000029), keyword redesign (000030)

### Frontend (LIVE on Vercel)
- Next.js 14 App Router, TypeScript strict, Tailwind CSS 4, shadcn/ui
- Supabase auth middleware chain: i18n → redirect → auth
- All pages: Landing, Dashboard, Profile, Assessment flow, Results + Radar chart, Organizations, Events, Leaderboard
- i18n: AZ primary, EN secondary, ~150+ keys
- PWA configured
- **Production URL:** https://volaura.app

### Infrastructure
- Vercel: frontend (free tier, custom domain)
- Railway: backend (~$8/mo, deployed)
- Supabase: database (free tier)
- GitHub Actions: swarm daily run at 09:00 Baku
- Sentry: error monitoring (backend)
- Telegram: Ambassador bot for CEO notifications

### Operating System (v4.0 — Swarm Architecture)
- CLAUDE.md: Operating Algorithm v4.0 (10 steps, 4 phases, swarm-based DSP)
- DSP: 10 parallel Agent(haiku) evaluators + 1 synthesis agent
- Skills Matrix: all sprint types mapped to required skills
- Memory system: 8 files (sprint-state, working-style, mistakes, patterns, deadlines, mcp-toolkit, volaura, swarm)
- Agent roster: memory/swarm/agent-roster.md
- Hooks: session-protocol.sh, auto-format.sh, session-end-check.sh

---

## Architecture (Reference)

```
volaura/                    <- Turborepo monorepo (pnpm)
├── apps/web/               <- Next.js 14 (Vercel)
│   ├── src/app/[locale]/   <- App Router, all pages
│   ├── src/components/     <- shadcn/ui + custom
│   ├── src/locales/        <- az/, en/ JSON translation files
│   └── middleware.ts       <- i18n + auth chain
├── apps/api/               <- FastAPI (Railway)
│   └── app/
│       ├── routers/        <- 15 routers (auth, assessment, aura, profiles, events, orgs, etc.)
│       ├── core/assessment/ <- engine.py (IRT/CAT), bars.py (BARS+DeCE), aura_calc.py, quality_gate.py
│       ├── services/       <- llm.py, reeval_worker.py, swarm_service.py
│       └── middleware/     <- rate_limit.py, security_headers.py
├── supabase/
│   ├── migrations/         <- 30+ SQL files
│   └── seed.sql            <- 8 competencies + GRS-validated questions
├── scripts/
│   └── audit_seed_questions.py <- GRS audit tool
└── memory/                 <- Claude's persistent context
    ├── context/            <- sprint-state, mistakes, patterns, deadlines
    ├── projects/           <- volaura.md (this file)
    └── swarm/              <- agent-roster, proposals, ceo-inbox
```

## Key Numbers
- AURA weights: communication 0.20, reliability 0.15, english 0.15, leadership 0.15, event_performance 0.10, tech_literacy 0.10, adaptability 0.10, empathy 0.05
- Badge tiers: Platinum >=90, Gold >=75, Silver >=60, Bronze >=40
- pgvector: 768 dimensions (Gemini text-embedding-004) — NEVER 1536 (OpenAI)
- Rate limits: auth 5/min, assessment start 3/hour, answer 60/hour
- Decay half-lives: tech/event 730d, english 1095d, communication/reliability/adaptability 1460d, leadership/empathy 1640d, weighted avg 1295.2d
- DeCE evaluation: per-concept {score, quote, confidence}, max_tokens=768
- GRS threshold: 0.6 (questions below this fail the quality gate)
- Anti-gaming gates: min_length(<30w)=cap 0.4, stuffing(>60%)=0.3x, coherence(<0.4 verb ratio)=0.55x, relevance(<15% overlap)=0.65x
- Verification multipliers: self=1.00, org=1.15, peer=1.25
- Sessions completed: 42

## What Is NOT Done (Next Phases)
- E2E test of Leyla's full journey (register -> assessment -> AURA -> badge)
- `pnpm generate:api` → replace 7 frontend TODO hooks with generated types
- Soniox ASR integration (AZ speech, WER 7.9% vs Whisper 19.5%) — needs API key
- 7-agent question generation pipeline (40s wall-clock, 4 stages, GRS gate)
- Flash-card micro-learning UI (while user waits for question generation)
- Regularized Bayesian calibration of IRT b-param from coordinator ratings
- Continuous DIF monitoring (Mantel-Haenszel every 500 responses)
- MIRT transition (Beta v2, requires n>5000)
- Resume flow UX (409 returns session_id but frontend shows error)
- Email lifecycle (React Email templates)
- Post 003 (LinkedIn series)
