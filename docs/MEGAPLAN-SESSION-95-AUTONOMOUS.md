# Autonomous Mega-Plan — Session 95+

**Mandate:** CEO goes offline. Atlas + Cowork work without stopping until ecosystem is solid.
**Rule:** Do NOT ask CEO. Solve problems. Only report when done.

**Cross-references:** [[research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14]] | [[LIFE-SIMULATOR-GAME-DESIGN]] | [[ECOSYSTEM-CONSTITUTION]] | [[CONSTITUTION_AI_SWARM]] | [[ECOSYSTEM-MAP]] | [[SPRINT-ATLAS-AUTONOMY-2026-04-12]]

---

## TRACK 1: ATLAS (Code + Infrastructure)

### Iteration 1-3: Telegram Bot → Real Executor
- [x] Research: can Telegram bot trigger GitHub Actions workflow_dispatch? (Session 105: YES, httpx POST to dispatches API)
- [x] Implement: /execute command → fires `gh workflow run` with task payload (Session 105: telegram_ambassador.py + telegram-execute.yml)
- [x] Bot receives CEO task → creates GitHub Issue → triggers Claude Code via webhook (Session 105: Issue creation + workflow_dispatch)
- [x] Test: CEO says "fix X" in Telegram → GitHub Action runs → result posted back (Session 105+: GH_PAT_ACTIONS set, E2E workflow triggered via `gh workflow run`, run #24366724526)

### Iteration 4-5: Self-Learning Pipeline
- [x] Debug why ceo_inbox writes fail — root cause: _handle_atlas never called _save_message (Session 95)
- [ ] Verify atlas_learnings populates after Groq extraction fix (needs real CEO message)
- [ ] Test with real message, verify DB rows

### Iteration 6-7: Vertex AI
- [ ] Monitor billing propagation (may take hours)
- [ ] When working: switch bot primary to Vertex (better quality than Groq)
- [ ] Switch assessment LLM calls to Vertex too

### Iteration 8-10: volunteer_id DB Migration
- [x] Create migration: add `professional_id` column alongside `volunteer_id` (20260415100000)
- [x] Views: professional_badges, professional_behavior_signals, professional_embeddings
- [x] Update RPC functions to accept both (Session 105: 20260415120000_rpc_accept_professional_id.sql)
- [x] Update code to use professional_id — Phase 1: schemas + 4 routers (aura, discovery, organizations, events). Phase 2: badges, profiles, events, verification. 126 remaining are DB column refs (correct, stay until column rename). 758 tests pass.
- [ ] Drop volunteer_id column (careful — needs downtime window, Phase 3)

### Iteration 11-13: Sentry + Monitoring
- [x] Diagnose Sentry 0 events — DSN configured, no errors = good
- [x] Verify DSN is correct project (e4751e368a48dc9e)
- [x] Enhanced Sentry init: attach_stacktrace, no PII, release tag
- [ ] Set up alerts for 5xx errors (Sentry MCP lacks alert creation — use web UI)

### Iteration 14-15: CI + Tests
- [x] Verified no zeus_gateway references in tests (clean)
- [x] All Python files parse OK (ast check)
- [x] Full test suite run — 749 passed, 0 fail (Session 105)
- [x] Add test for self-learning pipeline (Session 105: 9 tests in test_atlas_self_learning.py)

## TRACK 2: COWORK (Design + Research)

### Iteration 1-5: Phase A Foundation
- [ ] Build 3-tier token system in Figma (primitive → semantic → component)
- [ ] Map Constitution Law 1 (NEVER RED) to Figma error tokens
- [ ] Map Constitution Law 2 (Energy) to 3 visual states
- [ ] Export tokens → Tailwind @theme format

### Iteration 6-10: Component Library
- [ ] Energy Picker redesign (if needed — current one is good)
- [ ] Bottom Tab with Character Avatar (5th tab, app switcher)
- [ ] Button System (primary/secondary/ghost, 3 sizes, ADHD-safe)
- [ ] AURA Radar with Liquid Glass
- [ ] Assessment Question Card

### Iteration 11-15: Full Screens
- [ ] Dashboard (identity-first, AURA widget, activity feed)
- [ ] Assessment flow (energy picker → questions → results)
- [ ] Profile (public + private views)
- [ ] Landing page

## TRACK 3: SHARED (Both)

### After all iterations:
- [ ] E2E test: full user journey on prod
- [ ] Design-code sync: Figma tokens = globals.css tokens
- [x] Constitution Laws verified: Law 1 (purple ✅), Law 3 (shame-free ✅ — "Complete"→"Set up"), Law 4 (reduced-motion ✅), Law 5 (one primary ✅). Law 2 (energy modes) = feature work, needs Cowork design.
- [x] Crystal economy: 6 VOLAURA events with crystal earn/spend + sync every 5 game-years
- [ ] Telegram bot: executor, not chatbot
- [ ] Report to CEO: "ecosystem works, no problems"

---

**Working mode:** Atlas executes Track 1. Cowork gets Track 2 via CEO relay.
Each iteration = one focused task, commit, verify. No meta-discussion.
