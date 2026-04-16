# GAP INVENTORY v1 — VOLAURA Ecosystem Design Audit

**Date:** 2026-04-16 Session 113
**Method:** Explore agent (40 tool uses, 105K tokens, 140+ files reviewed)
**Scope:** All 5 products, 25+ key pages, globals.css tokens, Constitution Laws 1-5

## Summary

58 gaps identified. 8 P0 (blocking launch). 34 P1 (sprint work). 24 P2 (backlog). 6 PASS items confirmed compliant.

Law 1 (Never Red): PASS — zero red in codebase.
Law 4 (Animation 800ms): 2 violations — complete page milestone 1000ms, counter ignores energy mode.
Law 5 (One Primary CTA): 4 violations — dashboard, aura share, settings, evaluation log.
Energy Mode: 6 gaps — assessment question-card, aura reveal curtain, settings feedback, profile density.
Accessibility: 7 gaps — password toggle aria-label, focus ring contrast, consent label contrast.
Cross-product: 5 P0 gaps — all events from VOLAURA only, crystal economy one-directional, MindShift/LifeSim/BrandedBy placeholders.

Full details: see agent output in session transcript or memory/atlas/FULL-SYSTEM-AUDIT-2026-04-16.md for cross-reference.

## P0 Blocking (8)

1. MindShift placeholder only — no functional integration
2. LifeSim Godot client location unknown
3. BrandedBy placeholder — no UI for twin generation
4. Character events all from VOLAURA (zero from other products)
5. Crystal economy one-directional (earn only, zero spend)
6. Stripe keys — RESOLVED this session (product + price + webhook created)
7. Email keys — Resend still needs CEO
8. Atlas page is ProductPlaceholder — should show swarm status

## P1 Sprint Work (34 items condensed)

Energy mode: 6 screens need low-mode adaptation (assessment question-card, aura reveal, settings feedback, profile density, events form, stats row).
Law 5 CTA: 4 screens have multiple primary CTAs (dashboard quick-actions, aura share modal, settings energy+save, evaluation next-steps).
Law 4 animation: complete page milestone 1000ms exceeds 800ms limit, counter runs regardless of energy.
Accessibility: password toggle aria-label, focus ring contrast, energy picker aria-labels, consent label contrast.
Missing specs: onboarding Figma, notification center design, org admin dashboard, OPS module (6 pages zero Figma).
Backend: energy persistence write-on-change, settings visibility path (verified correct earlier — false positive).
Data: multi-competency demo needed, 0 orgs registered, DIF question imbalance.
Cross-product: MindShift bridge untested with real client, BrandedBy D-ID unactivated, squad_leaders.py archived.

## P2 Backlog (24 items condensed)

Design token Figma drift (typography, shadows, radius, spacing not synced). Responsive gaps (signup, dashboard, events, aura, discovery). i18n emoji hardcoding. Color contrast reserves. Badge tier unreachability communication. Tribe management UI. Settings completion hierarchy. Assessment question type templates.

## PASS Items (6)

Law 1 Never Red compliant. Spring physics correct. prefers-reduced-motion respected. Low energy CSS disables animation. Liquid glass effect correct. Mesh gradient safe.
