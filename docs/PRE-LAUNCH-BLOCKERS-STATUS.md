# Pre-Launch Blockers — Status Audit (D-007)

**Authority:** Operational scope split for Constitution v1.7 pre-launch P0 blockers (19 items, originally logged in session 88 handoff). Sessions since then (89-108) closed several of them through various commits; this doc reconciles the list against the real repo state so WUF13 launch planning can work from ground truth.

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

### 7. DIF bias audit (Mantel-Haenszel) 🟥 ready to build
No audit script in repo. Needs: pull assessment_sessions + question responses grouped by demographic (gender, age band), run Mantel-Haenszel delta on item-level response rates, flag items with |ΔMH| > 1.5. ~200 lines of Python. No blocking dependency — the data schema already stores what's needed.

### 8. Voice data routing disclosure 🟡 partial
Voice path not in shipped flow, so no user-facing disclosure exists. When voice ships, disclosure copy needs to land. Not an active blocker for text-only MVP.

### 9. Formal grievance mechanism (ISO 10667-2) 🟥 ready to build
No endpoint exists. Minimum path: `/api/aura/grievance` POST → Supabase `grievances` table → admin review queue → response within 30 days. ~1 day of work including UI. Schema + email template.

### 10. ADHD language ban in AZ copy 🟡 partial
Spot-checked landing + assessment; no "ты не справляешься / ты медленный" copy found. But there's no CI-enforced regex check. Cowork could scan the whole AZ locale file vs a banned-terms list.

### 11. Community Signal widget (G44) 🟥 ready to build
No widget component. G44 requires showing "N professionals took this assessment today" without leaderboard framing. `/api/analytics/community-signal` endpoint + simple number display.

### 12. Landing sample AURA profile 🟥 ready to build
Landing hero does not currently show a fictional Leyla 74 Communication Silver profile. Sunk-Cost Registration pattern (from Constitution v1.7) — a visual AURA card demo without login gate.

### 13. Vulnerability Window content (Rule 29) 🟡 partial
Post-assessment page exists but the specific "what IS shown during 5-min vulnerability window" content may not match Rule 29 exactly. Needs review against current assessment complete page.

### 14. Ghosting Grace for pre-activation users (Rule 30) 🟥 ready to build
No 48h warm re-entry email or notification. Users who sign up but don't finish assessment should get one gentle nudge within 48h. Requires Resend + scheduled worker (already have pg_cron infrastructure). ~1 day including copy.

### 15. Open Badges 3.0 VC compliance 🟥 ready to build (large)
No DID issuer, no cryptographic proof generation, no revocation endpoint. Largest item on this list — 3-5 days of work. Can defer to post-launch if badges are shown as internal-only first.

### 16. MIRT assessment upgrade (8 independent → 1 multidimensional) 🟥 ready to build (large)
Engine still uses 8 per-competency 3PL models. Multidimensional IRT would unify into one model with competency loadings. Research task + algorithm rewrite. Defer post-launch — current 3PL works.

### 17. ASR routing (Soniox AZ, Deepgram EN) ⏸️ blocked-external
Depends on voice data DPA (#6). Not blocking text-only launch.

### 18. Credential display split (G43, public vs private) 🟡 partial
Public profile page at `/u/[username]` exists. Need to verify that it hides private fields (email, internal energy_level) and only shows public ones (AURA score, badge tier, selected competencies).

### 19. Old design on production 🟡 partial
Design System v2 is in Figma and mostly deployed. No item-by-item audit against the Figma tokens. Tail-end polish.

### Security items flagged in the same session 88 handoff

**S1. Telegram webhook no HMAC validation** — ✅ fixed session 108 commit `355bb36` + regression tests `d2b026f`.

**S2. Role self-selection gaming** — unverified. The `role_level` field in `assessment_sessions` CHECK constraint was extended (session 108 commit `20260416000000_role_level_add_professional`), but whether the API enforces that a user cannot claim `senior_manager` without evidence is a separate check. Needs audit.

---

## Scope split for WUF13

**Must-ship before WUF13 (P0):**
- #4 (Art. 9 consent) — legal review
- #5 (SADPP registration) — Yusif
- #9 (grievance mechanism) — Atlas ~1 day
- #11 (Community Signal widget) — Atlas ~0.5 day
- #12 (Landing sample profile) — Atlas ~0.5 day
- #14 (Ghosting Grace) — Atlas ~1 day
- #18 (Credential display split verify) — Atlas ~2h audit
- S2 (role_level gaming audit) — Atlas ~1h

Total Atlas work for P0 WUF13: ~4 days. Total CEO work: legal review + SADPP + Soniox DPA (if voice).

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

Atlas picks up the P0 WUF13 list above in priority order, one commit per item. #9, #11, #12, #14 are code-only, no legal dependency — they ship first. The `Must-ship` column estimates total ~4 days of focused Atlas work to clear the WUF13 gate.

CEO action: confirm legal timeline for #4, #5, and S2 audit.
