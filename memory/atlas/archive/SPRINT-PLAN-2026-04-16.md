# Sprint Plan v2 — 2026-04-16 → 2026-04-29 (Operational)

**Previous version:** v1 was a prioritized TODO list without AC, DoD, milestones, evidence, or verification. CEO correctly identified it as CLASS 10 process theater. This v2 is operational.

---

## DOCTOR STRANGE EVIDENCE

**Question investigated:** Which of three paths maximizes WUF13 demo success in 28 days?
- Path A: UX-first (AURA indicator + Stripe + email + org onboarding)
- Path B: Living-Atlas-first (reflection card + cross-product memory sync + voice)
- Path C: Legal-first (GDPR + DIF + SADPP)

**External model verdicts (not self-confirmation):**

Gemma4 local (9.6GB, 1258 tokens, 82s): "Path A. Demo is utility not features. Progress indicator transforms assessments into goals. Stripe/email provide activation proof. One org = scale narrative." Trade-off accepted: delay wow-factor (Path B) and formal compliance (Path C) as V2.

Cerebras Qwen3-235B (600 tokens, 3s): Found 3 failure modes in v1 plan. (1) AURA indicator alone is cosmetic — root cause deeper, need multi-competency onboarding nudge. (2) Stripe/Resend CEO-dependency with no contingency — if keys delayed, sprint blocks. (3) DIF audit on 50 seed questions without real user data is statistically premature.

**Critique absorption:**
- Cerebras #1 → added "multi-competency nudge" to task 1 (not just indicator but onboarding flow change pushing users to 3+ assessments)
- Cerebras #2 → added Stripe fallback: if CEO keys not received by Day 3, pivot to "free-only beta" launch path with invite-code gate
- Cerebras #3 → DIF audit moved to Week 2 with explicit "preliminary" label, full audit deferred to 200+ real users

**Verdict:** Path A with Cerebras mitigations applied. Path B gets 2 small items (E1 reflection card + E4 voice module) as week 2 bonus. Path C gets GDPR Art. 22 consent only (minimal legal foundation).

---

## ROADMAP (12 days, 3 milestones)

```
Day 0 (Apr 16) ─── Session 113 closed: P0 quality_gate + P0 #15 + P0 #14 + 
                    system audit + ecosystem readiness + sprint plan v2

Day 1-4 ────────── MILESTONE 1: "Rauf can sign up and see a meaningful score"
                    AURA UX + multi-competency nudge + DB enum + energy persist +
                    test user cleanup + gaming flags hint

Day 5-7 ────────── MILESTONE 2: "Product can accept money and send email"
                    Stripe activation (or free-beta fallback) + Resend +
                    GDPR Art.22 consent + security quick wins

Day 8-12 ───────── MILESTONE 3: "Demo-ready for WUF13 pitch"
                    Atlas reflection card + PR narrative draft + landing social
                    proof + DIF preliminary audit + B2 gap inventory
                    
Day 12 (Apr 29) ── Sprint retrospective + next sprint plan
```

---

## TASK DECOMPOSITION WITH AC + DoD

### MILESTONE 1: "Rauf can sign up and see a meaningful score" (Days 1-4)

**Task 1: AURA completeness indicator + multi-competency nudge**
Files: `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`, `apps/web/src/locales/*/common.json`

AC:
- Given user has 1 of 8 competencies assessed, When they open /aura page, Then header shows "1/8 competencies assessed — complete more to build your full AURA" with progress ring
- Given user has 0 assessments, When they open /aura page, Then they see "Start your first assessment" CTA instead of empty score
- Given user has 3+ competencies, When AURA total >= 40, Then Bronze badge visible (proving system works)

DoD: Component renders all three states. AZ + EN i18n keys present. No shame-language. Typecheck clean. Manual verification: open /aura as CEO (1 competency) → see indicator. Complete 2 more assessments → see score jump + badge.

Verification: `grep "competencies assessed" apps/web/src/locales/en/common.json` returns key. Visual check on volaura.app after deploy.

Effort: 1.5h (was 0.5h in v1 — expanded per Cerebras critique to include nudge, not just indicator)

---

**Task 2: DB volunteer→professional enum migration**
Files: new `supabase/migrations/YYYYMMDD_volunteer_to_professional.sql`, `apps/web/src/app/[locale]/(auth)/signup/page.tsx`, `apps/web/src/locales/*/common.json`

AC:
- Given migration applied, When `SELECT count(*) FROM profiles WHERE account_type='volunteer'`, Then result = 0
- Given new user signs up as individual, When form submits, Then `account_type='professional'` in DB (not 'volunteer')
- Given frontend renders signup type selector, When user clicks individual button, Then label reads "I'm a professional" (EN) / "Mən peşəkaram" (AZ) AND code sends `account_type: "professional"`

DoD: Migration idempotent (ON CONFLICT safe). Frontend value change committed. No "volunteer" in any active code path (grep returns 0 in non-comment lines). Rollback plan documented in migration header.

Verification: `grep -rn "'volunteer'" apps/api/app apps/web/src --include="*.py" --include="*.tsx" | grep -v comment | grep -v test | grep -v archive` returns 0 active references. Supabase MCP `execute_sql("SELECT count(*) FROM profiles WHERE account_type='volunteer'")` returns 0.

Effort: 2h

---

**Task 3: Energy mode backend persistence**
Files: `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`, `apps/api/app/routers/profiles.py`

AC:
- Given user sets energy to "low" in settings, When they close browser and reopen, Then energy mode is still "low" (persisted to profiles.energy_level column)
- Given profiles.energy_level column exists (migration 20260416020000), When settings page loads, Then energy picker reads current value from API (not Zustand default)

DoD: Settings page PATCH call saves energy_level. On page load, GET /api/profiles/me returns energy_level. Zustand hydrates from API response. Typecheck clean.

Verification: `curl -H "Authorization: Bearer <jwt>" volauraapi.../api/profiles/me | jq .energy_level` returns "low" after setting.

Effort: 1.5h

---

**Task 4: Test user cleanup**
Files: none (DB operation only)

AC:
- Given 79 profiles in prod, When cleanup runs, Then only real users remain (CEO profile + any organic signups). "E2E Test User" display_name profiles deleted.
- Given cleanup complete, When `GET /api/stats/public`, Then total_professionals reflects real count (not inflated by test junk)

DoD: Service-role DELETE with WHERE display_name='E2E Test User'. Count before/after logged. No cascade damage (RLS + FK verified).

Verification: `db.table('profiles').select('id', count='exact').eq('display_name', 'E2E Test User')` returns 0.

Effort: 0.5h

---

**Task 5: Gaming flags expansion hint + share nudge timing**
Files: `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx`

AC:
- Given user has gaming flags, When warning renders, Then chevron icon visible indicating expandability
- Given user completes assessment with score >= 60, When complete page loads, Then share nudge appears AFTER milestone card animation (delay >= 400ms)

DoD: ChevronDown icon added to GamingFlagsWarning header. Share nudge transition delay increased. Typecheck clean.

Verification: Visual check on complete page with gaming-flagged session.

Effort: 0.5h

---

**Milestone 1 gate (Day 4):**
- Open volaura.app as new user → signup → complete 1 assessment → see "1/8" on AURA page → complete 2 more → see score jump above 40 → Bronze badge visible
- If gate FAILS: stop sprint, diagnose what broke in the path

---

### MILESTONE 2: "Product can accept money and send email" (Days 5-7)

**Task 6: Stripe activation**
Files: `apps/api/.env`, Railway env vars

AC:
- Given STRIPE_SECRET_KEY set + PAYMENT_ENABLED=true, When `GET /api/subscription/status` called with valid JWT, Then returns `{"status": "trial", ...}` (not 503)
- Given above, When `POST /api/subscription/create-checkout` called, Then returns `{"checkout_url": "https://checkout.stripe.com/..."}` (not 503)
- Given webhook configured, When `stripe trigger customer.subscription.created`, Then server responds 200

DoD: All 3 AC pass. Railway env vars set. Test card 4242... works end-to-end.

Verification: 3 curl commands per AC above.

Dependency: CEO provides sk_test key. Fallback (Day 3 trigger): if no key by Day 3, pivot to free-only beta with invite-code gate (OPEN_SIGNUP=false, BETA_INVITE_CODE set).

Effort: 1h (after key received)

---

**Task 7: Resend email activation**
Files: `apps/api/.env`, Railway env vars

AC:
- Given RESEND_API_KEY set + EMAIL_ENABLED=true, When user completes assessment, Then confirmation email sent to user's address
- Given email sent, When user checks inbox, Then email renders correctly with AURA score + competency name

DoD: Email delivered to real inbox (CEO's email). Template renders without broken HTML.

Verification: Complete assessment as CEO → check ganbarov.y@gmail.com inbox.

Dependency: CEO creates Resend account. Same fallback as Task 6.

Effort: 0.5h (after key received)

---

**Task 8: GDPR Art. 22 consent flow**
Files: new migration, `apps/api/app/routers/profiles.py`, `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`

AC:
- Given user has not consented to automated profiling, When org searches talent, Then user's profile does NOT appear in results
- Given user toggles "Make me discoverable" in settings, When consent saved, Then `consent_events` table records the consent with timestamp + policy version
- Given user revokes consent, When org searches again, Then user disappears from results

DoD: Migration adds consent check to discovery query. Settings UI has toggle with explanation text (GDPR Art. 22 language, i18n). consent_events audit trail created.

Verification: Search as org user before/after consent toggle. Check consent_events table.

Effort: 3h

---

**Task 9: Security quick wins batch**
Files: `apps/api/app/core/assessment/bars.py`, `apps/api/app/core/assessment/engine.py`

AC (BARS injection scan):
- Given LLM returns response containing "ignore previous instructions", When output validation runs, Then response flagged + logged + degraded fallback used

AC (IRT bounds validation):
- Given question with a=5.0 (outside [0.3, 3.0]), When assessment fetches question, Then ValueError raised + question skipped

DoD: Both validators added. Unit tests cover edge cases. Ruff clean.

Verification: Unit tests pass. `pytest tests/test_bars_injection.py tests/test_irt_bounds.py` green.

Effort: 3h

---

**Milestone 2 gate (Day 7):**
- Stripe checkout URL returns (or free-beta fallback active)
- Email arrives in CEO inbox after assessment
- Org search respects consent toggle
- BARS + IRT validators have passing tests

---

### MILESTONE 3: "Demo-ready for WUF13 pitch" (Days 8-12)

**Task 10: E1 Atlas reflection card**
Files: new API endpoint `apps/api/app/routers/aura.py`, `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`

AC:
- Given user has AURA score, When /aura page loads, Then "Atlas' reading" card shows 2-3 sentences of personalized reflection
- Given Gemini Flash free tier, When card renders, Then cost <= $0.02 per render (cached per user per day)
- Given reflection generated, When user reads it, Then tone matches Atlas voice (Russian storytelling, strength-first, no shame)

DoD: Backend endpoint + frontend card. Cache layer (localStorage 24h). Gemini Flash primary, keyword-fallback if quota hit.

Verification: Open /aura page → see reflection card with personal text, not template.

Effort: 2.5h

---

**Task 11: E4 Atlas voice unification module**
Files: new `apps/api/app/services/atlas_voice.py`

AC:
- Given Telegram bot, assessment reflection, and any future LLM surface, When system prompt is built, Then all read from same atlas_voice.py module
- Given module loaded, Then it includes: positioning lock, E-LAW 1-7, voice.md rules, emotional state adaptation

DoD: Module created. Telegram bot refactored to import from it (single import change). Assessment reflection endpoint uses same module.

Verification: `grep "from app.services.atlas_voice import" apps/api/app/routers/telegram_webhook.py apps/api/app/routers/aura.py` shows both importing.

Effort: 1.5h

---

**Task 12: PR narrative draft**
Files: new `docs/pr/WUF13-PRESS-BRIEF.md`

AC:
- Press brief contains: 1-paragraph pitch, 3 story angles (local: AZ talent verification gap, tech: AI-assessed competencies, human: founder solo-builds 5-product ecosystem), 5 AZ/CIS media targets
- Draft generated via Gemma4 + Cerebras (diverse models, not self-written), CEO-reviewed before any external contact

DoD: File committed. CEO reads and approves (or edits). No external contact without explicit CEO sign-off.

Verification: File exists with 3 angles and 5 targets. CEO says "ок" or edits.

Effort: 3h (AI generation + research + structuring)

---

**Task 13: Landing social proof section**
Files: `apps/web/src/app/[locale]/page.tsx`

AC:
- Given landing page, When visitor scrolls, Then sees "Founded by Yusif Ganbarov" section with registration count (real, not fake) + "Join N professionals already proving their skills"
- Given Constitution founding principle #1 (honesty before growth), Then count is REAL from `/api/stats/public` (no hardcoded inflation)

DoD: Component added. Count fetched from API. i18n present. No fake numbers.

Verification: View volaura.app → see social proof section with real number.

Effort: 1.5h

---

**Task 14: DIF preliminary bias audit**
Files: new `scripts/dif_audit.py`

AC:
- Given 50+ seed questions across 8 competencies, When Mantel-Haenszel script runs, Then report shows per-question bias indicators (flagged if significant at p<0.05)
- Report explicitly labeled "PRELIMINARY — full audit requires 200+ real user responses per Research #15"

DoD: Script runs against seed SQL. Report committed as `docs/research/DIF-PRELIMINARY-2026-04.md`. Preliminary label prominent.

Verification: `python scripts/dif_audit.py` produces report without error.

Effort: 3h

---

**Task 15: B2 Design gap inventory**
Files: new `docs/design/GAP-INVENTORY-v1.md`

AC:
- 8 swarm agents (design-critique, accessibility, ux-research, behavioral-nudge, cultural-intelligence, assessment-science, performance, ecosystem) run parallel review
- Output: priority-tagged gaps per product × screen

DoD: GAP-INVENTORY committed. Each gap has severity + screen + product.

Verification: File has entries from 5+ different agent perspectives.

Effort: 2h (swarm runs async)

---

**Milestone 3 gate (Day 12):**
- Atlas reflection card visible on /aura page (product feels alive)
- PR brief reviewed by CEO
- Landing has real social proof
- DIF report committed (preliminary)
- Design gap inventory ready for Phase 2

---

## INCREMENT VERIFICATION PROTOCOL

Every 2 tasks completed: push to main, check prod health, verify deploy landed on Railway. If any push fails (CI red, secret leak, merge conflict) — stop and fix before continuing.

Every milestone gate: walk the full user path manually (signup → assessment → AURA → settings → share). Screenshot or describe what you see. If any step breaks — milestone not passed, fix before next milestone.

---

## SPRINT DOD (April 29 review)

All three milestone gates passed. Specifically:
- [ ] New user sees "X/8 assessed" on AURA page (not bare 3.76)
- [ ] DB has zero "volunteer" account_type records
- [ ] Stripe checkout or free-beta path functional
- [ ] Email delivers to real inbox
- [ ] GDPR Art. 22 consent controls discovery visibility
- [ ] Atlas reflection card live on /aura (Atlas breathes in the product)
- [ ] PR brief + social proof section ready for CEO review
- [ ] DIF preliminary report committed
- [ ] Design gap inventory committed
- [ ] Zero new P0 incidents from sprint work

---

## RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CEO keys delayed >3 days | Medium | High (blocks M2) | Day 3 fallback: free-beta launch path |
| AURA indicator alone doesn't fix perception | Medium | Medium | Multi-competency nudge added (Cerebras critique) |
| Gemini Flash quota hit on reflection card | Low | Low | Keyword-fallback + 24h cache |
| DIF audit premature without real data | High | Low | Labeled "PRELIMINARY", full audit at 200+ users |
| Sprint over-scoped (15 tasks, 12 days) | Medium | Medium | Fallback: M1 alone = viable product |

---

## Sources (10-file cross-reference)

1. `memory/atlas/ECOSYSTEM-READINESS-2026-04-16.md`
2. `memory/atlas/FULL-SYSTEM-AUDIT-2026-04-16.md`
3. `memory/atlas/P0-VERIFICATION-2026-04-16.md`
4. `memory/atlas/CURRENT-SPRINT.md`
5. `memory/ceo/02-vision.md`
6. `memory/ceo/18-known-gaps-atlas-forgot.md`
7. `memory/ceo/13-financial-context.md`
8. `memory/ceo/09-frustrations.md`
9. `memory/decisions/2026-04-14-vision-canon.md`
10. `docs/ECOSYSTEM-CONSTITUTION.md` lines 1027-1047

## External model verdicts

- Gemma4 (Ollama local, 1258 tokens): Path A recommended, trade-off: delay wow-factor + formal compliance
- Cerebras Qwen3-235B (600 tokens): 3 failure modes found, all mitigated in v2
- Gemma4 (AC generation, 4000 tokens): acceptance criteria for 5 core tasks produced

No self-confirmation used. All strategic decisions validated by different-provider models per Mistake #77 (CLASS 11) cure.
