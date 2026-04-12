# Autonomous Mega-Plan — Session 95+

**Mandate:** CEO goes offline. Atlas + Cowork work without stopping until ecosystem is solid.
**Rule:** Do NOT ask CEO. Solve problems. Only report when done.

---

## TRACK 1: ATLAS (Code + Infrastructure)

### Iteration 1-3: Telegram Bot → Real Executor
- [ ] Research: can Telegram bot trigger GitHub Actions workflow_dispatch?
- [ ] Implement: /execute command → fires `gh workflow run` with task payload
- [ ] Bot receives CEO task → creates GitHub Issue → triggers Claude Code via webhook
- [ ] Test: CEO says "fix X" in Telegram → GitHub Action runs → result posted back

### Iteration 4-5: Self-Learning Pipeline
- [ ] Debug why ceo_inbox writes fail (Supabase client issue on Railway)
- [ ] Verify atlas_learnings populates after Groq extraction fix
- [ ] Test with real message, verify DB rows

### Iteration 6-7: Vertex AI
- [ ] Monitor billing propagation (may take hours)
- [ ] When working: switch bot primary to Vertex (better quality than Groq)
- [ ] Switch assessment LLM calls to Vertex too

### Iteration 8-10: volunteer_id DB Migration
- [ ] Create migration: add `professional_id` column alongside `volunteer_id`
- [ ] Copy data: UPDATE SET professional_id = volunteer_id
- [ ] Update RPC functions to accept both
- [ ] Update code to use professional_id
- [ ] Drop volunteer_id column (careful — needs downtime window)

### Iteration 11-13: Sentry + Monitoring
- [ ] Diagnose Sentry 0 events
- [ ] Verify DSN is correct project
- [ ] Add structured error logging
- [ ] Set up alerts for 5xx errors

### Iteration 14-15: CI + Tests
- [ ] Run full test suite, fix any failures from volunteer rename
- [ ] Add test for self-learning pipeline
- [ ] Add test for Telegram webhook routing

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
- [ ] All 5 Constitution Laws verified in code + design
- [ ] Crystal economy: at least 1 earn + 1 spend path implemented
- [ ] Telegram bot: executor, not chatbot
- [ ] Report to CEO: "ecosystem works, no problems"

---

**Working mode:** Atlas executes Track 1. Cowork gets Track 2 via CEO relay.
Each iteration = one focused task, commit, verify. No meta-discussion.
