# VOLAURA Three-Instance Audit — 10-Sprint Synthesis Plan
**Date:** 2026-04-26
**Synthesized by:** Code-Atlas (Opus 4.6)
**Sources:** findings-code-atlas.md (26 findings), findings-codex.md (18 findings)
**Status:** Browser-Atlas findings pending — will be integrated when delivered
**Total findings:** 44
**Convergent findings (raised by 2+ instances):** 6 themes (see §Convergent below)

## P0 EMERGENCY LIST (cannot wait one sprint)

1. **CI unblocked** — Code-Atlas F-02 fixed (ruff lint). Commit + push immediately. Blocks Railway deploy.
2. **Railway deploy drift** — Code-Atlas F-01. Backend sha `be2471062b3b` is 6+ commits behind HEAD `ed07bfbe6327`. Push triggers rebuild.
3. **force-dynamic removal** — Code-Atlas F-05. Two `export const dynamic = "force-dynamic"` in layouts kill ALL Vercel CDN caching. Remove both. Landing page TTFB drops from 878ms to ~60ms.

---

## CONVERGENT FINDINGS (2+ instances independently identified)

| Theme | Code-Atlas | Codex | Priority boost |
|-------|-----------|-------|----------------|
| Security headers missing (CSP, HSTS, cache) | F-12 | F-09 | +1 |
| Swarm path resolution wrong (admin endpoints empty) | F-01 (stale backend) | F-07 | +1 |
| RLS test coverage inadequate | F-13 | F-11 | +1 |
| code-index.json empty / stale | F-06 | (whistleblower flags) | +1 |
| Animation violations (>800ms ceiling) | F-19 (CLS) | F-14, F-15, F-16, F-17 | +1 |
| tg-mini surface completely non-functional | — | F-01 through F-06 | +1 |

---

## SPRINT PLAN

### Sprint S1 — "Unblock Pipeline" (immediate, ~4h AI)
**Owner:** Code-Atlas
**Acceptance criteria:** CI green, Railway deployed at HEAD, landing TTFB <150ms

| Finding | Task | Effort |
|---------|------|--------|
| CA-F02 | Commit ruff fixes (already done) | 5m |
| CA-F01 | Push to main → Railway rebuilds | 5m |
| CA-F05 | Remove `force-dynamic` from 2 layouts | 15m |
| CA-F16 | Remove SW-purge script from head | 15m |
| CA-F12 | Add Cache-Control headers to next.config | 15m |
| CA-F09 | Re-trigger atlas-watchdog + obligation-nag workflows | 30m |
| CX-F07 | Fix admin.py swarm path resolution (parents[4] → parents[5] or REPO_ROOT) | 30m |
| CX-F11 | Add catch-all pgTAP RLS test for all public tables | 2h |

### Sprint S2 — "Legal + Security + Design Law" (~5h AI + CEO review)
**Owner:** Code-Atlas (legal pages) + Codex (animation fixes)
**Acceptance criteria:** /privacy and /terms return 200, CSP header present, all animations ≤800ms

| Finding | Task | Effort |
|---------|------|--------|
| CA-F03 | Create /privacy and /terms pages + robots.txt + sitemap.xml | 2h |
| CA-F07 | Fix Constitution header v1.2 → v1.7 | 5m |
| CA-F18 | Replace duplicate fetch in social-proof.tsx with usePublicStats() | 15m |
| CX-F09 | Add CSP + HSTS headers to next.config.mjs | 1h |
| CX-F14 | Fix assessment completion pulse 1000ms → 600ms | 15m |
| CX-F15 | Fix AURA reveal overlay 1.4s → 600ms | 15m |
| CX-F16 | Fix badge glow 2s → 600ms | 15m |
| CX-F17 | Fix tribe waiting spinner 2s infinite → 600ms finite | 15m |
| CX-F08 | Add path resolution assertion test for admin swarm endpoints | 45m |
| CX-F10 | Extend CI secret scan to scripts/ and supabase/ | 30m |

### Sprint S3 — "Daemon + LLM + Courier Security" (~6h AI)
**Owner:** Code-Atlas
**Acceptance criteria:** Ollama latency <5s, daemon failure rate <20%, courier signing protocol drafted

| Finding | Task | Effort |
|---------|------|--------|
| CA-F08 | Diagnose daemon provider failures, add provider name to logs | 2h |
| CA-F10 | Fix Ollama latency (GPU offloading, pre-load, OLLAMA_NUM_GPU) | 1h |
| CA-F14 | Synthesize courier-loop design into signing protocol doc | 4h |
| CA-F25 | Fix AtlasSwarmDaemon scheduled task (verify trigger, test run) | 1h |
| CA-F19 | Add width/height to raw img tags (avatar, tribe-card, orgs) | 30m |
| CX-F12 | Fix error_watcher to include `in_progress` obligations | 30m |
| CX-F13 | Remove `as any` from event creation Zod resolvers | 30m |

### Sprint S4 — "Frontend Performance" (~6h AI)
**Owner:** Code-Atlas + Codex
**Acceptance criteria:** Landing page bundle reduced, Recharts lazy-loaded, Server Components for nav/footer

| Finding | Task | Effort |
|---------|------|--------|
| CA-F17 | Convert LandingNav, LandingFooter, SocialProof to Server Components | 4h |
| CA-F20 | Wrap Recharts with next/dynamic({ ssr: false }) | 15m |
| CA-F21 | Optimize Google Fonts (remove latin-ext, add display: optional) | 15m |
| CA-F11 | Triage 36 whistleblower flags, create obligation rows for recurring themes | 3h |
| CX-F18 | Reconcile product accent tokens (MindShift, Atlas colors) | 30m CEO sign-off |

### Sprint S5 — "tg-mini Resurrection" (~8.5h AI)
**Owner:** Codex
**Acceptance criteria:** tg-mini builds, tests pass, proposals/agents display real data, prototype scope documented

| Finding | Task | Effort |
|---------|------|--------|
| CX-F01 | Fix tg-mini API base URL | 15m |
| CX-F02 | Fix envelope unwrapping for agents + proposals | 45m |
| CX-F03 | Fix proposal action route + payload shape | 1h |
| CX-F04 | Add authentication headers to all API calls | 2h |
| CX-F05 | Add tg-mini to CI pipeline + test script | 1.5h |
| CX-F06 | Reclassify tg-mini as admin shell prototype + route smoke test | 30m |
| CA-F22 | Skip Supabase session refresh for public pages in middleware | 30m |
| CA-F24 | Add standard href links to for-ceo/index.html cards | 1h |

### Sprint S6 — "code-index + Swarm Health" (~4h AI)
**Owner:** Code-Atlas
**Acceptance criteria:** code-index.json has >10 modules, >0 endpoints, CI validates non-empty

| Finding | Task | Effort |
|---------|------|--------|
| CA-F06 | Fix code-index builder, regenerate, add CI validation | 2h |

### Sprint S7 — "volaura.com + DNS" (~1h AI + CEO decision)
**Owner:** CEO (domain decision) + Code-Atlas (DNS config)

| Finding | Task | Effort |
|---------|------|--------|
| CA-F04 | Check volaura.com ownership, acquire or document as not-owned | CEO decision |

### Sprint S8 — "ANUS Integration Roadmap" (~4h research)
**Owner:** Code-Atlas
**Acceptance criteria:** docs/architecture/anus-atlas-integration-roadmap.md with module inventory

| Finding | Task | Effort |
|---------|------|--------|
| CA-F23 | Audit ANUS project, map salvageable modules, write integration roadmap | 4h |

### Sprint S9 — "Debt + Tracking" (~1h maintenance)
**Owner:** Code-Atlas

| Finding | Task | Effort |
|---------|------|--------|
| CA-F15 | DEBT-001 ledger visibility in proactive-scan gate (no code change, tracking) | 0 |
| CA-F13 | Fix RLS tests workflow (Node.js 24 migration or pgTAP issue) | 1h |

### Sprint S10 — "Browser-Atlas Integration" (TBD)
**Owner:** Code-Atlas (synthesis update)
**Note:** Reserved for Browser-Atlas findings. When `findings-browser-atlas.md` arrives, deduplicate against existing 44 findings, add new findings to appropriate sprints, re-balance effort.

---

## RESIDUAL DEBT (did not fit in 10 sprints)

1. **Full Server Component migration** for entire landing page (beyond S4 nav/footer conversion)
2. **Framer Motion code splitting** across 72 files (needs architectural decision on CSS animations vs motion library)
3. **PWA cleanup** — remove @ducanh2912/next-pwa from devDependencies entirely (part of F-16 but cosmetic)
4. **Vercel MCP 403 team scope issue** — documented in heartbeat 120, needs Vercel support ticket
5. **Google OAuth Testing→Production console flip** — CEO action, gated on Vercel deploy fix
6. **ITIN W-7 chain** — CEO action post-83(b), tracked in atlas_obligations
7. **Telegram autonomous loop end-to-end verification** — requires test message drop (audit item 16 from prompt, not yet verified)
8. **Sentry error rate analysis** — audit item 7 from prompt, Sentry MCP not invoked this session (tool availability unclear)
9. **atlas_obligations DB live audit against company-state.md** — audit item 6 from prompt, deferred to next session with Supabase MCP

---

## EXECUTION NOTES

1. S1 is executable RIGHT NOW — CI fix already done, push unblocks everything.
2. S2-S4 are pure AI work, no CEO blocking.
3. S5 (tg-mini) is substantial but self-contained — Codex can own it entirely.
4. S7 requires CEO decision on domain ownership.
5. S8-S9 are low-urgency maintenance.
6. S10 is a placeholder for browser-Atlas findings integration.

Total estimated effort: ~45h AI + ~2h CEO across all 10 sprints.
Longest critical path: S1 → S2 → S3 → S4 (sequential due to deploy dependencies).
S5-S9 can run in parallel with S2-S4.
