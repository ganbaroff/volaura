# ADR-001: System Architecture

**Status:** Accepted
**Date:** 2026-03-22
**Deciders:** Yusif (product owner), Claude (architecture)
**Related:** [[ADR-002-database-schema]], [[ADR-003-auth-verification]], [[ADR-004-assessment-engine]], [[ADR-005-aura-scoring]], [[ADR-006-ecosystem-architecture]]
**Governed by:** [[../ECOSYSTEM-CONSTITUTION]]

## Context

Volaura is a verified professional talent platform launching in Azerbaijan. The system must handle adaptive assessments, AURA score computation, public profile sharing, event matching, and organization search. Target: 200+ assessed users at launch, scaling to 10,000+ within 6 months. Development speed is 100x via AI-augmented tooling.

### Requirements

**Functional:**
- User authentication (magic link + Google OAuth)
- Adaptive assessment engine (8 competencies, 3 question types)
- AURA composite score calculation with badge tiers
- Public shareable profiles with OG image generation
- Event listing with AURA-based eligibility
- Organization portal (search volunteers, request volunteers)
- Real-time leaderboard
- Multi-language (AZ primary, EN secondary, RU/TR planned)
- Share cards (LinkedIn, Story, Square formats)
- Referral/invite system
- Email lifecycle (welcome, score ready, events, re-engagement)

**Non-Functional:**
- Public profiles: TTFB < 100ms (SEO critical, journalist-scannable QR)
- Assessment: works on unstable WiFi (major event venue, 5000 people)
- PWA: installable, offline assessment capability
- WCAG 2.1 AA accessibility
- GDPR-adjacent data privacy (Azerbaijan data protection law)

**Constraints:**
- Solo developer + AI tooling (100x speed)
- Budget: minimal (free tiers where possible, ~$50/mo max)
- Stack already chosen: Next.js 14, FastAPI, Supabase

## Decision

### Architecture: Supabase-First with Edge Computing

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENTS                                │
│  Next.js PWA (Web)  ·  Telegram Bot  ·  Org API consumers   │
└──────────┬───────────────────┬───────────────────┬───────────┘
           │                   │                   │
           ▼                   ▼                   ▼
┌──────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   Vercel Edge    │ │  Supabase BaaS  │ │   Railway (API)     │
│                  │ │                 │ │                     │
│ • Next.js SSR    │ │ • PostgreSQL    │ │ • FastAPI           │
│ • ISR pages      │ │ • Auth          │ │ • Assessment Engine │
│ • OG Image gen   │ │ • Storage       │ │ • AURA Calculator   │
│ • Middleware      │ │ • Realtime      │ │ • LLM Evaluator     │
│   (auth check,   │ │ • Edge Funcs    │ │ • Email triggers    │
│    i18n routing)  │ │ • RLS policies  │ │ • Org API (v1)      │
│ • Static assets   │ │ • pg_cron       │ │                     │
│ • Analytics       │ │ • pgvector      │ │ Gemini 2.5 Flash    │
└──────────────────┘ └─────────────────┘ └─────────────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Supabase DB       │
                    │   PostgreSQL 15     │
                    │                     │
                    │ • users             │
                    │ • assessments       │
                    │ • aura_scores       │
                    │ • events            │
                    │ • organizations     │
                    │ • questions         │
                    │ • referrals         │
                    │ • notifications     │
                    │ • embeddings (768d) │
                    └─────────────────────┘
```

### Why This Split (not pure Supabase, not pure FastAPI)

**Supabase handles:** Auth, database, storage, realtime subscriptions, simple CRUD (profiles, events, registrations). Direct client access via RLS = zero backend for reads.

**FastAPI handles:** Complex business logic that can't live in RLS or Edge Functions:
- Assessment engine (question selection algorithm, theta estimation)
- AURA score calculation (weighted composite across competencies + reliability + event performance)
- LLM evaluation of open-text answers (Gemini API calls)
- Certificate/PDF generation
- Organization API (rate-limited, API key auth)

**Vercel Edge handles:** SSR, ISR for public profiles, OG image generation (Satori), i18n routing middleware, auth cookie validation.

## Options Considered

### Option A: Pure Supabase (Edge Functions for all logic)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | ~$0 (free tier) |
| Scalability | High (auto-scaling) |
| Team familiarity | Medium |

**Pros:** Simplest possible stack. Everything in one platform. No Railway cost.
**Cons:** Edge Functions have 150ms cold start. Complex scoring logic is painful in Deno. No Python = no adaptivetesting library. LLM calls from Edge Functions have timeout issues. Debugging is harder.

### Option B: Supabase + FastAPI on Railway (CHOSEN)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost | ~$8/mo (Railway) + $0 (Supabase free) + $0 (Vercel free) |
| Scalability | High (Railway auto-scale + Supabase) |
| Team familiarity | High (Python backend, existing code) |

**Pros:** Python ecosystem (adaptivetesting, google-genai, Pillow). FastAPI generates OpenAPI → type-safe frontend. Complex business logic in proper language. Easy to test. Existing backend code.
**Cons:** Two deployment targets. Need to manage Railway separately. ~$8/mo cost.

### Option C: Full Next.js API Routes (no separate backend)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low-Medium |
| Cost | $0 (Vercel free tier) |
| Scalability | Medium (Vercel serverless limits) |
| Team familiarity | High |

**Pros:** Single deployment. No Railway. All TypeScript.
**Cons:** No Python = lose adaptivetesting, google-genai SDK advantages. Serverless cold starts for assessment engine. 10s timeout on Vercel free tier = LLM calls may fail. Can't run background jobs.

## Trade-off Analysis

Option B wins because:
1. **Python is essential** for assessment engine (adaptivetesting library is Python-only)
2. **$8/mo is negligible** vs the complexity savings
3. **OpenAPI → type-safe frontend** is a massive DX win
4. **Existing code** — backend already has routers, schemas, services

The key trade-off: we accept operational complexity (2 deploy targets) for development speed and capability.

## Data Flow Patterns

### Pattern 1: Direct Read (most common)
```
Browser → Supabase Client (with RLS) → PostgreSQL
```
Used for: profiles, events list, leaderboard, notifications.
No backend round-trip. Instant. Protected by RLS.

### Pattern 2: Authenticated Write via API
```
Browser → FastAPI (Bearer token) → Supabase Admin → PostgreSQL
```
Used for: submit assessment answer, update profile, register for event.
FastAPI validates business logic, then writes via admin client.

### Pattern 3: Computed Read
```
Browser → FastAPI → compute → return
```
Used for: AURA score calculation, next question selection, LLM evaluation.
Computation happens in Python, result cached in DB.

### Pattern 4: Edge-Rendered
```
Browser → Vercel Edge → ISR cache / Supabase → HTML
```
Used for: public profiles (/u/[username]), OG images.
ISR revalidates every 60s. Edge runtime = global CDN = <100ms TTFB.

### Pattern 5: Realtime
```
Browser → Supabase Realtime subscription → PostgreSQL changes
```
Used for: leaderboard live updates, notification count badge.

## Consequences

**What becomes easier:**
- Direct Supabase reads = instant data with zero backend
- Python scoring engine = clean, testable business logic
- ISR public profiles = SEO + speed
- OpenAPI codegen = type-safe frontend-backend contract

**What becomes harder:**
- Two deployment targets to manage
- Auth token must work across Supabase + FastAPI (solved: Supabase JWT verified in FastAPI)
- Need to define clear boundary: what goes to Supabase direct vs FastAPI

**Boundary rule:**
> If it's a simple CRUD and RLS can protect it → Supabase direct.
> If it needs computation, LLM, or cross-table business logic → FastAPI.

## Offline Strategy (Event WiFi concern)

```
Service Worker (Workbox) + IndexedDB (Dexie.js):

1. Assessment questions pre-fetched when starting assessment
2. Answers stored in IndexedDB as user progresses
3. On submit: try API call
   → Success: clear local, show score
   → Fail (offline): queue in IndexedDB, show "Saved, will sync"
4. Background Sync API retries when online
5. UI indicator: "Offline mode — answers saved locally ✓"
```

## Monitoring & Error Handling

- **Sentry** (free tier): error tracking, frontend + backend
- **Vercel Analytics**: Core Web Vitals, page performance
- **Loguru** (backend): structured JSON logging
- **Supabase Dashboard**: DB metrics, auth metrics
- **Health endpoint**: `GET /api/health` returns DB, LLM, storage status

## Action Items

1. [x] Choose architecture (Option B)
2. [ ] Deploy Supabase project, configure Auth providers → [[ADR-003-auth-verification]]
3. [ ] Design database schema → [[ADR-002-database-schema]]
4. [ ] Define API contracts → [[engineering/API-CONTRACTS]]
5. [ ] Configure Vercel deployment with environment variables
6. [ ] Set up Railway for FastAPI
7. [ ] Configure Sentry for both frontend and backend
8. [ ] Set up Workbox for offline PWA capability

