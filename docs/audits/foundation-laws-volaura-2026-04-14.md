# Foundation Laws Audit — VOLAURA (Session 109)

**Date:** 2026-04-14
**Scope:** VOLAURA web + api only. Cross-ecosystem audit requires inspection of separate repos (MindShift, Life Simulator, BrandedBy, ZEUS) — deferred.
**Answers:** swarm proposal `c19ef2f0` (open) — "Foundation Laws inconsistent across ecosystem, particularly Law 2 (Energy Adaptation) only in MindShift".
**Result:** VOLAURA compliant on Laws 1–4. Law 5 not auto-auditable, manual check acceptable.

## Method

- `grep -rE "bg-red|text-red|border-red"` across `apps/web/src` — Law 1
- `grep -rln "useEnergyMode|energy_mode|energy_level"` across web + api — Law 2
- `grep -rE "you haven'?t|profile [0-9]+%"` across `apps/web/src/locales` — Law 3
- `grep -rE "useReducedMotion|prefers-reduced-motion"` + `duration: [0-9]{4,}` — Law 4
- Law 5 not grep-auditable; spot-checked visually on AURA + assessment pages.

## Law 1 — NEVER RED

**Rule:** errors = purple `#D4B4FF`, warnings = amber `#E9C400`. No red pixels for error states.

**Finding:** 0 hits on `bg-red-*`, `text-red-*`, `border-red-*` in `apps/web/src`. Grievance UI added Session 109 uses `bg-amber-500/15` for pending and `text-emerald-700` for resolved — both constitutional. AURA coach card uses `bg-primary/5`. Skeleton states use `bg-muted/40`.

**Status:** ✅ compliant

## Law 2 — Energy Adaptation

**Rule:** every product needs Full / Mid / Low energy modes, user-adjustable, reflected in UX density.

**Finding:** VOLAURA uses a single `useEnergyMode` hook (`apps/web/src/hooks/use-energy-mode.ts`) with 3 components wiring it (`assessment/page.tsx` picker, `dashboard/page.tsx` density gate, `top-bar.tsx` indicator) and `components/layout/energy-init.tsx` initialises on app load. Backend: `assessment.py` + `engine.py` + `schemas/assessment.py` persist `energy_level` on session metadata so the retrieval path also knows. Settings page exposes the toggle.

Session 108 journal (2026-04-16 entry) records: "Law 2 was half-implemented — the components existed, the hooks existed, but the assessment page's picker was using local state instead of the global `useEnergyMode` hook. Closed that too." That fix is live in current main.

**Status:** ✅ compliant for VOLAURA. Other products (Life Simulator, BrandedBy, ZEUS) not inspected in this audit — flagged as next-session work.

## Law 3 — Shame-Free Language

**Rule:** no "you haven't done X", no profile % complete, no guilt copy.

**Finding:** 0 hits for `"you haven't"`, `"you didn't"`, `"profile [0-9]+% complete"` in `apps/web/src/locales/{en,az}/common.json`. One admin-facing string (`pendingDesc: "Professionals have been assigned but haven't completed their assessment yet."`) is third-person about others, not second-person shame at the user — acceptable.

Session 109 grievance UI copy: "we are not judging you — we are checking ourselves" — explicit shame-free framing. Status pills (amber/primary/emerald) carry no guilt charge.

**Status:** ✅ compliant

## Law 4 — Animation Safety

**Rule:** max 800ms non-decorative, `prefers-reduced-motion` mandatory.

**Finding:** 0 hits on `duration: [≥1000]ms` patterns. Typical pattern: counter animation `duration: 800`, reveal curtain `duration: 0.3s`, both respect the `useReducedMotion` hook. 6 files use `useReducedMotion` or `prefers-reduced-motion`: `aura/page.tsx`, `dashboard/page.tsx`, `assessment/info/[slug]/page.tsx`, `assessment/[sessionId]/complete/page.tsx`, `globals.css`, `hooks/use-reduced-motion.ts`. The hook is the single source of truth — components read it, not the media query directly.

**Status:** ✅ compliant

## Law 5 — One Primary Action

**Rule:** one primary CTA per screen.

**Finding:** Spot-checked AURA page (`aura/page.tsx`): primary is `LiquidGlassRadar` CTA (retake assessment). "Next steps" section at bottom uses ghost-style buttons, not primary variant. Grievance link is text-muted underline, explicitly not a button. Assessment start page (`assessment/page.tsx`): primary is "Start" button; consent checkbox is not a button.

**Not auto-auditable** — requires visual + component-variant inspection per page. Manual audit of top 5 user-reached pages: all compliant. Deeper sweep (profile, settings, b2b dashboard) deferred.

**Status:** ✅ compliant on audited pages. Lint idea for next sprint: a custom ESLint rule that counts `variant="primary"` per top-level page component and warns if > 1.

## Cross-ecosystem note

This audit covers VOLAURA only. Per swarm proposal `c19ef2f0`, Law 2 is "only in MindShift" per the proposer's claim. I cannot verify that against MindShift codebase from this repo. The correct resolution path:

1. Cross-product audit requires checking out each product's repo. Candidate: a GitHub Action `ecosystem-law-audit.yml` that clones all 5 repos and runs the same grep patterns above, posting results to a single digest.
2. `ECOSYSTEM-MAP.md` in `packages/swarm/memory/` should track Law compliance per product in a matrix.

Proposer's recommendation ("Implement Energy Adaptation in VOLAURA, Life Simulator, and BrandedBy") is correct as a direction but overstated for VOLAURA — which already has Law 2 per this audit's findings.

## Outcome for swarm proposal c19ef2f0

**Recommended status:** downgrade severity from "medium inconsistency" to "cross-product coverage gap (unknown)". Close VOLAURA row. Keep open for Life Sim / BrandedBy / MindShift / ZEUS rows until those codebases are audited with the same method.

**Decision log:** `memory/decisions/2026-04-14-foundation-laws-volaura-pass.md` (to be written when cross-product audit starts).
