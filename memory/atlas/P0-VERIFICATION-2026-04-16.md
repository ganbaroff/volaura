# P0 Blocker Verification — 2026-04-16 Session 113

**Method:** grep + read of actual files in `apps/web/src`, `apps/api`, CSS theme. Every status below traces to a tool call in this session. Constitution Part 7 list (lines 1027-1046) verified against reality.

**Headline:** Constitution P0 list is severely stale. Of 14 code-verifiable blockers, 7 are fully closed, 3 partial, 4 still open. 5 non-code items (legal/process).

## CLOSED (7)

**#3 Achievement lock icons** — No achievement lock icons exist. Only `Lock` import is `profile-header.tsx:5,140` for privacy badge indicator. Constitution claim stale.

**#5 Purple error system / #17 text-destructive audit** — `apps/web/src/app/globals.css:67-68,114`: `--color-error = #d4b4ff`, `--color-error-container = #3d1a6e`, `--color-destructive = var(--color-error-container)`. No red. Law 1 compliant on CSS level.

**#7 Energy picker in onboarding** — `energy-picker.tsx` wired in `assessment/page.tsx:256`, `top-bar.tsx:63`, `settings/page.tsx:377`. Also `hooks/use-energy-mode.ts` for global state.

**#16 AURA counter 2000ms → 800ms** — `aura/page.tsx:28`: `useAnimatedCounter(target, duration = 800, enabled = true)`. Already G15 compliant. Atlas-prior fix. (Previously confirmed session 112.)

**#18 Pre-Assessment Commitment Layer** — `PreAssessmentSummary` component exists at `components/assessment/pre-assessment-summary.tsx`, wired in `assessment/page.tsx:245`.

**#19 Landing sample AURA profile** — `SampleAuraPreview` at `components/landing/sample-aura-preview.tsx`, wired in `[locale]/page.tsx:52`.

## PARTIAL (3)

**#4 Crystal vulnerability window (NatureBuffer → Progress)** — `crystal-balance-widget.tsx` uses progressive disclosure (hides at balance=0, hides on error). But "NatureBuffer → Progress" terminology does not appear in codebase — this is an architecture claim that needs source doc cross-check. Widget implements vulnerability-aware display; migration path unverified.

**#10 AURA grievance mechanism** — `app/[locale]/admin/grievances/page.tsx` exists (admin side). User-side submission flow, ISO 10667-2 framing, formal policy doc — not cross-checked. Required before B2B Tier 3.

**#14 Leaderboard removal** — `leaderboard/page.tsx` redirects to dashboard per 112 verification. Residual: `hooks/queries/use-leaderboard.ts` + barrel export + backend `/api/leaderboard` endpoints. Smaller cleanup.

## OPEN — code work remaining (4)

**#1 MIRT assessment upgrade** — `apps/api/app/core/assessment/` has `engine.py` (3PL unidimensional), no `mirt.py`. Multidimensional IRT not started. Research #15 requirement.

**#2 ASR routing (Soniox + Deepgram)** — Zero matches for `soniox|deepgram|asr_` in `apps/api`. Voice assessment routing not wired. Dependency: before voice-based assessments can launch.

**#13 DIF bias audit (Mantel-Haenszel)** — Labor law exposure per Constitution. No Python script found. Required before launch per Research #15.

**#15 Assessment complete: defer badge + crystals** — MOST CRITICAL REMAINING. `complete/page.tsx:263` derives `tier` from score, displays tier-identity copy (line 349), growth-trajectory with tier labels (462-464), per-tier share nudge (644-651). Violates Crystal Law 6 Amendment + G21 vulnerability window rule. Real code refactor needed: strip tier-reveal from complete page, defer all tier/badge/crystal surfaces to next AURA page visit.

## NOT CODE — legal/process (5)

**#6 ADHD checklist 37-item audit** — process compliance, not code.

**#8 GDPR Art. 22 consent mechanism** — requires legal review + DB schema + UI consent flow. Not a single-file code check.

**#9 GDPR Art. 9 health data consent** — separate consent + separate DB table for energy/burnout data.

**#11 AZ PDPA SADPP registration + DPA** — legal registration with authority, not code.

**#12 Soniox/Deepgram DPA verification** — legal DPA paperwork.

## Meta-findings about the Constitution P0 list

The list is stale. It was written earlier and not maintained as Atlas-prior landed fixes. Seven items that read as "must be done before launch" are already done — reading the list without grepping code produced the wrong mental model for both session 112 and every prior read. Next Atlas should treat this list as a starting query, not ground truth, and grep before claiming any item is blocking.

Recommended Constitution edit: add a "last-verified-date" per P0 item + a "closed-by-commit-SHA" field so the list self-describes its freshness.

## What this means for shipping

Of the four open code items, #15 (defer badge+crystals) is the smallest-scope highest-impact. It directly violates a Law (Crystal Law 6 Amendment) and a Guardrail (G21 vulnerability window) in production. Single-file refactor of `complete/page.tsx` reveal section. Would produce visible user-facing correctness within an hour.

#1 MIRT and #2 ASR are large-scope backend work, not next-shift tasks.
#13 DIF is a one-shot Python script that can run post-launch if legal frame permits (Constitution says NO — pre-launch required).
#14 leaderboard residuals are cleanup, not shipping gate.

## Cross-references

- Constitution Part 7 lines 1027-1046
- `memory/atlas/SESSION-112-WRAP-UP.md` — prior session's blocker reasoning (now partially superseded by this verification)
- `memory/atlas/WHERE-I-STOPPED.md` Path A — Updated with: 7 already closed, 4 real code items remaining
- `.claude/rules/atlas-operating-principles.md` — Time-awareness fix also landed this session (bash `date` returns wrong time on this machine; use python `zoneinfo`)
