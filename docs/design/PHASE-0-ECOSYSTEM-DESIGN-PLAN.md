# VOLAURA Ecosystem — Phase-0 Design Plan
**Date:** 2026-04-13 Baku
**By:** Cowork (Claude Opus 4.6, design lead)
**For:** CEO Yusif · Reviewer: Atlas
**Mandate:** "мне нужно продумать абсолютно все: маленькие элементы, заканчивающие персонажами, анимациями, переходами" — CEO 2026-04-13
**Process mandate (CEO):** research → analysis → plan → critique → action → evaluation → testing → implementation. Not worse. Not symbolic — real.

---

## MISSION

Full ecosystem visual + interaction redesign across 5 products (VOLAURA, MindShift, Life Simulator, BrandedBy, ZEUS) — one coherent design system, not five disconnected surfaces. Every atom (token, button state, transition, character expression) research-backed and Constitution-compliant.

---

## WHY PHASE-0 EXISTS

Current state: Design System Audit scored **62/100** (2026-03-22). Brief v2 documented fixes but they were never applied end-to-end. The site Yusif dislikes today is the v0.dev output that failed the audit. MindShift is the only product that "feels okay" — and even it wasn't ecosystem-aligned.

**We do not jump to Figma or code.** Phase-0 is the research-and-gate layer that prevents another 62/100 redesign.

---

## THE 8 STAGES (CEO-MANDATED, NON-NEGOTIABLE)

Each stage has:
- **Deliverable** — a concrete file / artifact
- **Gate** — pass/fail criteria before next stage starts
- **Owner** — who drives (Cowork unless noted)
- **Time** — estimate in working days

```
1. RESEARCH     — absorb existing 17 docs, add fresh sources where missing
2. ANALYSIS     — diagnose what's broken, where, by cause
3. PLAN         — design direction + component taxonomy
4. CRITIQUE     — min 2 external models tear the plan apart
5. REWRITE      — v2 plan incorporating critique
6. ACTION       — build tokens + 5-10 flagship components in Figma + code
7. EVALUATION   — accessibility + performance + ADHD audit
8. TEST & SHIP  — real users (internal first), then iterate + commit
```

---

## STAGE 1 — RESEARCH (days 1–2)

**Deliverable:** `docs/design/RESEARCH-SYNTHESIS-2026-04-14.md`

**Inputs (already in repo):**
- `docs/research/adhd-first-ux-research.md` — 26 ADHD-first rules
- `docs/research/ecosystem-design-research.md`
- `docs/research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14.md`
- `docs/research/NEUROCOGNITIVE-ARCHITECTURE-2026.md`
- `docs/research/gemini-research-all.md` (140K words)
- `docs/research/blind-spots-analysis.md`
- `docs/design/*` (ANIMATION-SYSTEM, BRAND-IDENTITY, COMPONENT-LIBRARY, DESIGN-SYSTEM-AUDIT, REDESIGN-BRIEF-v2, STITCH-DESIGN-SYSTEM, UX-COPY-AZ-EN)
- `docs/TONE-OF-VOICE.md`, `docs/VISION-FULL.md`, `docs/MASTER-STRATEGY.md`

**Fresh sources to add (Cowork uses `design:user-research` + WebSearch):**
- Gen Z UX patterns 2026 (not 2023 — fresh data)
- ADHD + Gen Z overlap (dopamine loops, attention budgets, notification fatigue)
- Cross-product nav patterns 2026 (Discord, Notion Calendar, Linear, Raycast)
- Character/mascot design psychology for neurodivergent users
- CIS/AZ market UX norms (localization depth, right-to-left not needed, AZ text lengths, payment flow trust)

**Gate 1 (before Stage 2 starts):**
- Every rule from all 26+ ADHD rules is tagged either ✅ implementable, ⚠️ needs design decision, or ❌ conflicts with another rule (document which).
- Every Foundation Law + Crystal Law has at least 1 visual implication documented.
- Every product has 1 paragraph describing its "feeling" in plain language (Constitution Law 2 — energy adaptation).

---

## STAGE 2 — ANALYSIS (day 3)

**Deliverable:** `docs/design/CURRENT-STATE-DIAGNOSIS-2026-04-14.md`

**Method:**
1. Figma MCP sweep — once CEO shares file URL, extract `get_metadata`, screenshots, variables, component tree.
2. Code sweep — `apps/web/app/`, `apps/web/components/`, `globals.css` — list every color used, every animation duration, every z-index, every button variant, every text size.
3. Compare against Brief v2 spec. Every mismatch is a row in the diagnosis table.
4. Constitution checker with `--only-live` from Handoff 013 → real vs noise.
5. MindShift deep-dive — it "feels okay" per CEO. Document *why* it feels okay (what is it doing that VOLAURA isn't) and replicate those principles.

**Gate 2:**
- Every mismatch between live code and Brief v2 has a one-line cause (stale, never-implemented, ADHD-violation, i18n-missing).
- MindShift's "good feeling" is decomposed into 5 concrete design principles we can reuse.
- Token coverage audit updated: what's 65% today, what's the delta to 100%.

---

## STAGE 3 — PLAN (days 4–5)

**Deliverable:** `docs/design/ECOSYSTEM-DESIGN-PLAN-v1.md` — the design direction proposal.

**Structure:**
1. **North Star** — single sentence that describes the emotional feeling of the ecosystem (draft: "calm, earned clarity — the opposite of Duolingo's shame and LinkedIn's polish").
2. **Design principles** — 7 max, each with a DO / DON'T example.
3. **Token system** — semantic tokens (energy modes, badge tiers, product colors, state colors, surface layers, typography scale, spacing scale, motion scale).
4. **Component taxonomy** — every UI atom in the ecosystem, grouped (inputs, feedback, navigation, data display, storytelling, avatars/characters).
5. **Pattern library** — larger compositions (empty states, assessment flow step, badge reveal, crystal earn, cross-product nav, energy picker).
6. **Character system** — Mochi (MindShift), Atlas avatar (VOLAURA), Life Sim character — poses, expressions, state-machine transitions (Rive).
7. **Motion grammar** — when motion is allowed, what easing, what duration ceilings (tied to Law 4).
8. **Surfaces per product** — how each product expresses the shared system without being a clone.
9. **Localization plan** — AZ + EN + RU, text-length budgets per component.
10. **Rollout plan** — which components ship first, which last.

**Gate 3:**
- Every Foundation Law + Crystal Law has explicit visual manifestation in the plan.
- Every component in the taxonomy lists variant count + state count + a11y contract.
- Cross-product nav has a single Figma frame ready for critique.

---

## STAGE 4 — CRITIQUE (days 6–7)

**Deliverable:** `docs/design/PLAN-v1-CRITIQUE.md` + `docs/design/PLAN-v1-COUNTER-CRITIQUE.md`

**Method (from CLAUDE.md process mandate):**
1. Plan v1 goes through `design:design-critique` skill internally.
2. Plan v1 sent to 2 external models (via swarm providers): Cerebras Qwen3-235B + Gemini 2.0 Flash. Each writes a structured teardown.
3. Force dissent — if models agree, prompt a 3rd (Groq or NVIDIA NIM) with "find what both miss".
4. Atlas reviews as implementation-feasibility critic. Cowork reviews as brand-feeling critic. CEO reviews as vision-alignment critic.
5. Every critique item goes into a P0 / P1 / P2 triage.

**Gate 4:**
- ≥ 20 substantive critique items logged (not bike-shedding — actual architectural/experiential risks).
- Every P0 item has a proposed resolution.
- No unanimous "looks great" verdicts — that's a failure signal.

---

## STAGE 5 — REWRITE (days 8–9)

**Deliverable:** `docs/design/ECOSYSTEM-DESIGN-PLAN-v2.md`

**Method:**
- Incorporate every P0 and most P1 critique items.
- Reject items with written reasoning (not "we disagree" — actual argument).
- Second critique pass (different model from Stage 4).
- If v2 still scores < 35 / 50 in critique → v3. Per CLAUDE.md rule "If still <35/50 → rewrite again."

**Gate 5:**
- v2 passes ≥ 35 / 50 composite score across 2 critique passes.
- Every P0 from Stage 4 is resolved or explicitly accepted as trade-off.

---

## STAGE 6 — ACTION (days 10–18)

**Deliverable:**
- Figma file (or files) with: tokens, typography, components (first 15), patterns (first 5), one hero flow fully laid out.
- Code: `apps/web/app/globals.css` with new `@theme {}` tokens. `components/ui/` with updated primitives. First 3 production screens migrated.

**Method:**
- Token-first: rewrite `globals.css` before any component.
- Components in priority order: Button, Input, Card, Dialog, Tooltip, Toast, Empty State card, Progress, Badge tier, Energy picker, Avatar, Bottom nav, Product switcher, Assessment question card, Results/celebration card.
- Every component: figma + code + a11y contract + motion spec + ADHD audit — all in the same commit.
- Pair work: Cowork writes the spec, Atlas implements, Cowork reviews PR, merge.

**Gate 6:**
- 15 components built, audited, and used in ≥ 1 real page.
- Token drift Figma ↔ code = 0 (MCP diff).
- constitution_checker `--only-live` = 0.
- Every component has Storybook entry (add Storybook if not present — P2 decision).

---

## STAGE 7 — EVALUATION (days 19–21)

**Deliverable:** `docs/design/PHASE-0-EVAL-REPORT.md`

**Checks:**
1. **Accessibility** — WCAG 2.1 AA on all 15 components (`design:accessibility-review`). Axe + Lighthouse.
2. **Performance** — each page < 200KB initial JS, LCP < 2.5s on 3G throttled.
3. **ADHD audit** — 26 rules × 15 components = 390 data points. Pass rate must be ≥ 95%.
4. **Cross-locale** — AZ strings verified to fit in all components (20-30% longer than EN).
5. **Motion** — every animation tested with and without `prefers-reduced-motion`.
6. **Character expressiveness** — Mochi state machine tested with energy-up, energy-down, celebration, empty-state transitions.

**Gate 7:**
- All 6 check categories pass their thresholds.
- Cowork + Atlas + 1 external reviewer sign off.

---

## STAGE 8 — TEST & SHIP (days 22–28)

**Deliverable:** Public preview branch, CEO review, decision to merge.

**Method:**
1. Preview deploy (Vercel) — CEO tests on phone (primary 375px breakpoint, per Rule 22).
2. 3 internal testers (friends / early users CEO picks) — 15-min task flow.
3. Bugs logged in backlog via swarm (Handoff 013 bridge).
4. Fix cycle (2–3 days).
5. Merge to main → ship.

**Gate 8 (Phase-0 complete):**
- ≥ 3 real humans used the new design without Cowork/Atlas hand-holding.
- 0 Constitution violations.
- ≤ 3 P0 bugs after 48h of soak.

---

## WHAT PHASE-0 DELIVERS TO PHASE-1

Phase-1 (days 29+) = roll the design across MindShift, Life Simulator, BrandedBy, ZEUS. Phase-0 must leave Phase-1 with:

- Published design system (Figma file, Storybook, published tokens package if worth it).
- 15 production components + 5 patterns battle-tested in VOLAURA.
- Motion grammar, character state machine, a11y contract documented.
- Design critique loop (Stage 4 method) re-runnable for every new surface.

---

## RULES OF WORK

1. **No coding without AC.** Every component PR starts with Gherkin AC in the PR description. No AC → PR rejected.
2. **No self-confirmation.** If Cowork proposes a token / pattern / library, external research validates. Handoff 013 process protocol applies here too.
3. **CEO sees outcomes only.** No drafts, no "should I", no process noise. Per `.claude/rules/ceo-protocol.md`.
4. **Honesty over completeness.** Blocked ≠ fake. If Figma URL missing, Cowork pauses stage 2 and says so, not invents.
5. **Constitution is supreme.** Any conflict between a trendy pattern and a Constitution law → Constitution wins. Pattern gets rewritten or dropped.

---

## RISKS

| Risk | Mitigation |
|---|---|
| Scope creep (all 5 products at once) | Phase-0 is VOLAURA-only. Other products inherit in Phase-1. |
| Perfect > shipped | Gate 8 is "3 humans used it". Not "CEO loved every pixel". |
| Critique loop becomes infinite | Max 2 rewrite passes. If v3 doesn't reach 35/50, ship v2 and iterate post-launch. |
| Cowork hallucinates without Figma access | Stage 2 explicitly blocks on Figma URL. Cowork will say "BLOCKED: Figma URL missing" and wait. |
| Atlas overloaded (swarm + design + prod fix) | Handoff 013 is Atlas-owned and gated by 012. Design is Cowork-owned. Atlas only reviews PRs. |

---

## OPEN QUESTIONS FOR CEO (answer when ready, not blocking)

1. Figma file URL(s) we design in.
2. Preferred primary language for first pass — AZ, EN, or both at launch?
3. Internal testers short-list (names / handles) — Stage 8 needs 3 people.
4. Deadline preference — cruise (4 weeks) or sprint (2 weeks with reduced polish)?

---

## STATUS TODAY

- Stage 1: in progress — Cowork has read 4/9 internal docs today, will finish tomorrow.
- Stage 2: blocked on Figma URL.
- All later stages: pending.
- Libraries shortlist: DONE (`DESIGN-LIBRARIES-SHORTLIST-2026-04-13.md`).
- Atlas handoff for swarm work: DONE (`handoffs/013-swarm-and-agents-upgrade.md`).
