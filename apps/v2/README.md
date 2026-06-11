# VOLAURA v2 — ground-up rebuild

Started 2026-06-11 on direct CEO directive: *"переосмысли всё — дизайн, структуру,
идею, архитектуру. Это твой проект, ты должен его создать с нуля, а не исправлять
то что есть. Возьми отсюда модули, создай с нуля этот проект."*

## What this is

A NEW product built from zero, not a refactor. The old app (`apps/web`) keeps
running while v2 grows; modules are imported from the old world only when they
have earned it.

**Idea (rethought):** VOLAURA is not a talent marketplace. It is a verification
instrument sold to employers. The candidate side exists as the exhaust of every
B2B sale. See `for-ceo/briefs/2026-06-11-refounding-volaura.md`.

**Design language — "Ledger":** the old site was a dark consumer app; v2 is a
verification document. Warm paper (#FAF9F6), ink typography (Space Grotesk +
Inter), one violet seal (#5B2EE5), hairline rules, tabular numbers, hard
shadows like stamped paper. Constitution survives: no red, shame-free copy,
one primary CTA per screen, reduced-motion respected.

**Architecture:**
- `apps/v2` — fresh Next.js 14 + Tailwind v4, zero legacy CSS, zero legacy components.
- Backend module REUSED as-is: FastAPI on Railway (assessment engine, campaigns API).
  v2 talks to it via `/api` rewrite — the IRT/CAT + LLM evaluation engine is the
  crown jewel of the old project and migrates by reference, not rewrite.
- Auth bridge: v2 links to the legacy app's auth flow until v2 grows its own
  (`/screening/[token]` CTA → volaura.app join flow).

## Run

```bash
pnpm install --filter volaura-v2
cd apps/v2 && pnpm dev   # port 3001
```

Pages live now:
- `/` — B2B landing (employer pitch, report demo, 8 competencies)
- `/screening/[token]` — candidate invite landing, server-rendered from the
  LIVE production API (try `pilot-c9ddfe3a56b14e573ec7`)

## Build order (v2 roadmap)

1. ✅ Foundation: design tokens, landing, screening landing (live data)
2. Org console: create campaign → copy link → ranked report (reuse campaigns API)
3. v2 auth (Supabase) + candidate assessment runner in Ledger design
4. Candidate verified profile page (the shareable certificate)
5. Cut volaura.app DNS over to v2 when the loop closes end-to-end; legacy app retires
