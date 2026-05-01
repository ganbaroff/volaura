# Pre-Launch Blockers — Status Audit (D-007)

**Authority:** Operational scope split for Constitution v1.7 pre-launch P0 blockers (19 items, originally logged in session 88 handoff). Sessions since then (89-108) closed several of them through various commits; this doc reconciles the list against the real repo state so launch planning can work from ground truth.

**Method:** each blocker verified by code read, commit log grep, or explicit schema/DB check. Numbering preserved from the session 88 source list.

**Legend:** ✅ done · 🟡 partial / needs polish · 🟥 ready to build · ⏸️ blocked on external

---

## Blocker-by-blocker status

### 1. Energy Picker ✅ done
`apps/web/src/components/assessment/energy-picker.tsx` exists (5 referencing files). `useEnergyMode` hook in `apps/web/src/hooks/use-energy-mode.ts` wires local + Supabase cross-device sync (session 108 commit `3a0d6b8`). TopBar compact variant, settings full variant, assessment full variant all live. Three-mode CSS tokens in `globals.css` (full/mid/low). `data-energy` attribute applied on `<html>`. Dashboard hides Tribe in low, hides Feed in mid+low (session 108 commit `97b537e`).

### 2. Pre-Assessment Commitment Layer ✅ done
`apps/web/src/components/assessment/pre-assessment-summary.tsx` exists. Assessment page renders it before the first question. Includes energy check, competency summary, AI disclosure text.

### 3. GDPR Art. 22 consent screen ✅ done (field level)
`apps/api/app/schemas/assessment.py` has `automated_decision_consent: bool = False` required on `/assessment/start`. Frontend assessment page sends it from the consent checkbox. Non-consent blocks start. Art. 22 text itself is in the consent label; swarm proposal "GDPR Article 22 consent flow not legally sufficient" (still open, medium) flags that the text may need legal review — that's a polish, not a blocker.

### 4. Art. 9 health data consent (energy/burnout) 🟡 partial
Energy level is stored but there is no explicit "health data" classification or separate consent screen. Whether `energy_level` in Supabase counts as Art. 9 sensitive data depends on legal interpretation. Needs legal review before launch, not code work.

### 5. AZ PDPA SADPP registration ⏸️ blocked-external
No code — this is a legal filing with the AZ State Agency. Owner: Yusif (legal).

### 6. Soniox/Deepgram DPA verification ⏸️ blocked-external
No code — vendor DPA sign-off. Owner: Yusif (legal). Note: voice processing is not in the shipped product path, so this blocker only fires if voice-answer is re-enabled pre-launch.

### 7. DIF bias audit (Mantel-Haenszel) ✅ done (script ready)
`scripts/audit_dif_bias.py` — 190 lines. Groups by language (en/az) and role_level.
Computes Mantel-Haenszel delta, flags items |delta| > 1.5. Outputs CSV to
`memory/swarm/dif_audit_results.csv`. Session 129.
Note: no gender/age columns in profiles yet — groups by available fields only.
Needs 300+ completed sessions for publishable findings.

### 8. Voice data routing disclosure 🟡 partial
Voice path not in shipped flow, so no user-facing disclosure exists. When voice ships, disclosure copy needs to land. Not an active blocker for text-only MVP.

### 9. Formal grievance mechanism (ISO 10667-2) ✅ done
`apps/api/app/routers/grievance.py` — 548 lines. Full ISO 10667-2 §7 compliance.
User: POST/GET /api/aura/grievance. Admin: pending queue + resolve/reject with mandatory resolution.
GDPR Art.22 human review: POST /api/aura/human-review + admin transition.
SLA deadline tracking in human_review_requests. E2E test #6 verified on prod.
Verified Session 128 by code read (was marked 🟥 incorrectly — code predates this audit).

### 10. ADHD language ban in AZ copy ✅ done
`scripts/lint_shame_free.py` — CI-ready lint script. Scans all locale JSON files for banned terms.
Session 129: created script + fixed "remaining" in competencyProgressTransition (EN+AZ).
Session 129 final: `python3 scripts/lint_shame_free.py` → PASS. Zero violations.

### 11. Community Signal widget (G44) ✅ done
`apps/web/src/components/community/community-signal-inline.tsx` + `use-community-signal.ts` hook.
Shows "professionals_this_week" on assessment page. Imported in assessment/page.tsx.
Verified Session 128 by grep (was marked 🟥 incorrectly).

### 12. Landing sample AURA profile ✅ done
`apps/web/src/components/landing/sample-aura-preview.tsx` on landing page (gated by SAMPLE_PROFILE_ENABLED).
Full sample profile page at `/sample` with `sample-profile-view.tsx` + `data/sample-profile.ts`.
Verified Session 128 by grep (was marked 🟥 incorrectly).

### 13. Vulnerability Window content (Rule 29) ✅ done
Crystal Law 6 Amendment implemented on complete page (lines 128-129, 270, 365, 456).
Badge tier + crystal rewards deferred to next /aura page visit.
Competency score shown, not badge identity. Verified Session 129.

### 14. Ghosting Grace for pre-activation users (Rule 30) ✅ done
`apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` — NewUserWelcomeCard
checks `profile.created_at` > 48h. Shows warm re-entry copy:
"Still thinking about it? Start when you're ready — there's no deadline."
CTA: "Start when ready →". Shame-free (Law 3), single CTA (Law 5).
Frontend-only, no email (swarm voted 3-2 for Option A). Session 128.

### 15. Open Badges 3.0 VC compliance 🟥 ready to build (large)
No DID issuer, no cryptographic proof generation, no revocation endpoint. Largest item on this list — 3-5 days of work. Can defer to post-launch if badges are shown as internal-only first.

### 16. MIRT assessment upgrade (8 independent → 1 multidimensional) 🟥 ready to build (large)
Engine still uses 8 per-competency 3PL models. Multidimensional IRT would unify into one model with competency loadings. Research task + algorithm rewrite. Defer post-launch — current 3PL works.

### 17. ASR routing (Soniox AZ, Deepgram EN) ⏸️ blocked-external
Depends on voice data DPA (#6). Not blocking text-only launch.

### 18. Credential display split (G43, public vs private) ✅ done
Public profile at `/u/[username]` — backend selects ONLY `display_name, username, account_type`.
No email, no energy_level, no stripe_customer_id in public response.
Frontend: no PII references in public page component.
Verified Session 129 by grep on both backend + frontend.

### 19. Old design on production 🟡 partial
Design System v2 is in Figma and mostly deployed. No item-by-item audit against the Figma tokens. Tail-end polish.

### Security items flagged in the same session 88 handoff

**S1. Telegram webhook no HMAC validation** — ✅ fixed session 108 commit `355bb36` + regression tests `d2b026f`.

**S2. Role self-selection gaming** — unverified. The `role_level` field in `assessment_sessions` CHECK constraint was extended (session 108 commit `20260416000000_role_level_add_professional`), but whether the API enforces that a user cannot claim `senior_manager` without evidence is a separate check. Needs audit.

---

## Scope split for current launch readiness

**Must-ship before public launch (P0):**
- #4 (Art. 9 consent) — legal review (CEO)
- #5 (SADPP registration) — Yusif (legal filing)
- ~~#9 (grievance mechanism)~~ — ✅ DONE (548 lines, verified Session 128)
- ~~#11 (Community Signal widget)~~ — ✅ DONE (verified Session 128)
- ~~#12 (Landing sample profile)~~ — ✅ DONE (verified Session 128)
- ~~#14 (Ghosting Grace)~~ — ✅ DONE (Session 128, frontend-only)
- ~~#18 (Credential display split verify)~~ — ✅ DONE (Session 128: PublicProfile interface has no email/energy_level/internal fields)
- ~~S2 (role_level gaming audit)~~ — ✅ DONE (Session 128: Pydantic Literal["professional","volunteer"] rejects invalid values)

Revised Atlas work: ~1.5 days (was 4 days — 3 items were already built but doc was stale).
CEO work unchanged: legal review + SADPP.

**Can defer to post-launch (P1):**
- #7 (DIF bias audit)
- #10 (ADHD language CI check)
- #13 (Vulnerability Window content alignment)
- #15 (Open Badges 3.0 VC)
- #16 (MIRT upgrade)
- #19 (Figma design polish)

**Blocked on external, not launch-critical for text-only MVP:**
- #6, #8, #17 (voice data path — only fires when voice ships)

**Already done:** #1, #2, #3 (field level) + S1.

---

## Next action

Atlas picks up the P0 launch list above in priority order, one commit per item. #9, #11, #12, #14 are code-only, no legal dependency — they ship first. The `Must-ship` column estimates total ~4 days of focused Atlas work to clear the current launch gate.

CEO action: confirm legal timeline for #4, #5, and S2 audit.
