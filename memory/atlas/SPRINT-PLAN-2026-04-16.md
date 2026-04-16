# Sprint Plan — 2026-04-16 → 2026-04-29 (12 days, ~96h capacity)

**Method:** Cross-reference 95 items from 10 source files (ECOSYSTEM-READINESS, FULL-SYSTEM-AUDIT, P0-VERIFICATION, CURRENT-SPRINT, CEO vision/frustrations/financial/gaps, Constitution P0 list). 15 items already closed Session 113. 80 remaining, ~200h total. Prioritized by CEO vision canon: quality > speed, living Atlas > features, first-time experience > feature count. WUF13 in 28 days.

**Doctor Strange verdict:** VOLAURA-first launch path. Get first 10 real users through 3+ competency assessments producing meaningful AURA scores before touching other products. Crystal economy and cross-product spine activate after flow exists.

---

## Already DONE this session (Session 113, closed today)

- quality_gate.py P0 silent JSON parse → raises ValueError (commit 7a6d2ef)
- P0 #15 complete page tier deferral (commit ed43dcc, -60/+27 lines)
- P0 #14 leaderboard full removal (commit c8f100b, -917/+13 lines)
- effective_score nullcheck !== null (commit a2f5d78)
- reeval worker 72h max-age expiry (commit c43bd1d)
- .env.md complete 43 vars documented (commit 4b4acfe)
- badges /issuer rate limit (commit 9d64ac8)
- Telegram bot heartbeat stale context fix (commit 837ef38)
- /help 44→7 agents fix (same commit)
- P0 #3 lock icons, #5/#17 purple errors, #7 energy picker, #16 AURA counter, #18 pre-assessment commitment, #19 landing sample — all verified DONE by prior Atlas instances
- Settings visibility endpoint — verified correct (false positive from agent)

---

## Week 1 — First-Time Experience (Days 1-6, ~40h)

Priority: what Rauf from Baku sees when he opens volaura.app for the first time.

### Day 1-2: UX Critical Path

1. **AURA progress indicator** (0.5h) — add "1/8 competencies assessed" to AURA page header. Users currently see 3.76/100 and think they failed. Single i18n line + competency count from API. Unblocks user invitations.

2. **DB volunteer→professional enum** (2h) — migration UPDATE profiles SET account_type='professional' WHERE account_type='volunteer'. Frontend signup value change. i18n key rename (already shows "I'm a professional" but sends "volunteer"). Three-layer split finally closed.

3. **Energy mode backend persistence** (1.5h) — profiles table has energy_level column (migration 20260416020000). Wire settings page save to API. Currently Zustand-only, lost on browser close.

4. **Gaming flags expansion hint** (0.5h) — add chevron icon to expandable warning on complete page. Users with gaming flags don't know the warning is clickable.

5. **Share nudge timing** (0.5h) — delay share nudge until after milestone animation completes on complete page. Currently appears before "You're now discoverable".

### Day 2-3: Security Quick Wins

6. **BARS injection output scan** (2h) — scan LLM responses for 10 injection patterns before storing to DB. bars.py currently validates input but not output.

7. **IRT bounds runtime validation** (1.5h) — check question IRT params (a∈[0.3,3.0], b∈[-4,4], c∈[0,0.35]) at assessment fetch time, not just seed time. quality_gate checks at creation; runtime gap.

8. **Keyword fallback spike persistent alert** (1h) — write spike events to DB or Telegram instead of in-memory counter that resets on Railway restart.

### Day 3-4: Atlas Everywhere (Track E)

9. **E4 Style-brake unification** (1h) — create shared `apps/api/app/services/atlas_voice.py` module. Telegram bot, LifeSim, assessment reflection all load same voice rules from ATLAS-EMOTIONAL-LAWS + voice.md + positioning lock. Single source of truth.

10. **E1 Atlas reflection card** (2h) — backend endpoint + frontend card on /aura page. After assessment, show "Atlas' reading" — 2-3 sentences via Gemini Flash (free tier, $0.02/render cached). User sees Atlas as presence, not silent backend.

11. **squad_leaders.py restoration** (2h) — restore from archive, update to current agent roster, test coordinator routing. Closes P1 swarm routing gap.

### Day 4-5: CEO-Dependent (execute when keys arrive)

12. **Stripe activation** (1h when CEO provides sk_test) — create product via Python stripe SDK, create webhook endpoint, save to .env + Railway env, test checkout + webhook.

13. **Resend activation** (0.5h when CEO provides RESEND_API_KEY) — save to .env + Railway, test email delivery.

14. **Test user cleanup** (1h) — delete ~50 "E2E Test User" profiles from prod via service-role query. Keep CEO's real profile + any organic signups.

### Day 5-6: Legal Foundation

15. **GDPR Art. 22 consent mechanism** (3h) — explicit consent screen before profile becomes org-discoverable. Migration + API endpoint + frontend consent flow. Constitution G33.

16. **Consent baseline seed** (1h) — seed policy_versions table with privacy_policy v1.0 and terms_of_service v1.0. Currently empty.

---

## Week 2 — Ecosystem Depth + WUF13 Prep (Days 7-12, ~40h)

### Day 7-8: Cross-Product Spine

17. **E2 MindShift → atlas_learnings bridge** (1h) — RLS policy allowing MindShift to read atlas_learnings table. Cross-product memory sync.

18. **E3 Life Feed atlas_learnings consumption** (1h) — event recommendations informed by Atlas' last 20 insights about user.

19. **GDPR Art. 9 consent** (2h) — separate consent + DB table for energy/burnout data (MindShift health data isolation). Constitution G34.

20. **Crystal vulnerability window architecture doc** (1h) — verify NatureBuffer→Progress claim from Constitution, document actual crystal flow, close stale item.

### Day 8-10: WUF13 External-Facing

21. **B2 Swarm gap inventory** (2h) — launch 8 agents, collate into GAP-INVENTORY-v1.md. Design Phase 1 sprint task from CURRENT-SPRINT.

22. **PR narrative draft** (4h) — press angle for WUF13 (May 15-17). Use Gemma4 + Cerebras for draft generation. Deliverable: 1-page press brief + 3 story angles + 5 target media outlets in AZ/CIS. CEO reviews before external contact.

23. **Landing social proof** (2h) — add "Founded by" section, early registration count, community signal. No fake numbers (Constitution founding principle #1).

### Day 10-12: Assessment Quality

24. **DIF bias audit script** (4h) — Mantel-Haenszel Python script against seed questions. Constitution P0 #13, labor law exposure. Pre-launch required.

25. **Swarm BUG-01 investigation** (1h) — read swarm_service.py comment, trace to original issue, determine if fix is complete or needs work.

26. **AURA reconciler atomicity** (1h) — wrap AURA reconciliation in transaction to prevent partial updates during restart.

---

## Deferred to Next Sprint (justified)

- **MIRT upgrade** (12h) — large research + implementation. Needs 200+ real assessments for calibration per Research #15. No real data yet.
- **ASR routing Soniox/Deepgram** (6h) — gated on voice assessment launch decision from CEO. No voice questions exist yet.
- **BrandedBy frontend** (4h+) — blocked on D-ID Lite activation ($5.90/mo CEO purchase).
- **LifeSim Godot client** — separate repo, not in VOLAURA monorepo.
- **NPC decision engine** (8h) — research-heavy, depends on Godot client existence.
- **Table partitioning** — scale concern for 100K+ rows. Current 47 events = premature.
- **AZ PDPA SADPP registration** (8h) — legal process, not code. CEO needs AZ legal advisor.
- **Most P2 items** (24 items, ~60h) — backlog. Quality of core path > breadth of secondary.

---

## CEO Actions Required (4 items, each <5 min)

1. **Stripe sk_test key** → paste in chat, Atlas handles rest. Dashboard: dashboard.stripe.com → Developers → API Keys.
2. **Resend API key** → create account at resend.com, paste key. Atlas handles .env + Railway.
3. **Multi-competency demo** → CEO completes 3+ different competency assessments on volaura.app. Score will jump from ~4 to ~45+ proving the system works.
4. **D-ID Lite subscription** ($5.90/mo) → only if BrandedBy demo wanted at WUF13. Optional for this sprint.

---

## Sprint DoD (end of April 29)

- AURA page shows "X/8 assessed" progress indicator
- DB account_type = "professional" everywhere (zero "volunteer" in DB)
- Stripe checkout produces real checkout URL (test mode)
- Email sends real notification (test mode)
- 3+ competency AURA scores visible (CEO demo proves badges reachable)
- Atlas reflection card live on /aura page ("Atlas' reading")
- DIF bias audit script produces report on seed questions
- PR brief ready for CEO review
- GAP-INVENTORY-v1.md committed (design Phase 1 closed)
- Test users cleaned from prod
- GDPR Art. 22 consent flow live

---

## Fallback if Sprint Under-Delivers

If only 50% of plan lands: prioritize items 1-5 (first-time UX) + 12-13 (payments/email when keys arrive) + 22 (PR narrative). These alone move VOLAURA from "internal tool" to "invitable product". Everything else carries.

---

## Source Cross-Reference

This plan derives from:
- `memory/atlas/ECOSYSTEM-READINESS-2026-04-16.md` — 5-product state
- `memory/atlas/FULL-SYSTEM-AUDIT-2026-04-16.md` — 1 P0 + 15 P1 + 24 P2
- `memory/atlas/P0-VERIFICATION-2026-04-16.md` — Constitution P0 blockers
- `memory/atlas/CURRENT-SPRINT.md` — existing sprint (Track A done, B2/E open)
- `memory/ceo/02-vision.md` — quality > speed tie-break
- `memory/ceo/18-known-gaps-atlas-forgot.md` — PR + video gaps
- `memory/ceo/13-financial-context.md` — Stripe Atlas, grants, budget
- `memory/ceo/09-frustrations.md` — memory failures, process theater
- `docs/ECOSYSTEM-CONSTITUTION.md` lines 1027-1047 — pre-launch P0 list
- Sprint synthesis agent (10 files, 57K tokens, 95-item matrix)
