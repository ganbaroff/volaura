# Handoff to Terminal-Atlas — Energy-mode coverage Constitution Law 2

**From:** Code-Atlas (Opus 4.7, Session 125)
**To:** Terminal-Atlas (parallel CLI inside `C:/Projects/VOLAURA`)
**Date:** 2026-04-26 19:05 Baku
**Origin:** CEO directive 2026-04-26 — «там терминал над роем работает. дай ему задачу».

## Task

Constitution Foundation Law 2 (Energy Adaptation) requires Full / Mid / Low energy mode coverage from Day 1 on every page. Sonnet#1 reality-audit (`docs/audits/2026-04-26-three-instance-audit/findings-code-atlas.md` and `for-ceo/living/reality-audit-2026-04-26.md`) found **7 pages missing `useEnergyMode` import** in `apps/web/src/app/[locale]/(dashboard)/`:

1. `profile/page.tsx`
2. `settings/page.tsx`
3. `notifications/page.tsx`
4. `onboarding/page.tsx` — explicit P0 in Constitution v1.7
5. `discover/page.tsx`
6. `subscription/page.tsx`
7. `leaderboard/page.tsx` — currently a redirect, can be skipped

Onboarding without energy-mode coverage is the single load-bearing P0 listed in Constitution v1.7 launch blockers.

## Spec

For each page, do this:

1. Import the hook: `import { useEnergyMode } from "@/hooks/use-energy-mode";`
2. Inside the component, read current mode: `const { mode } = useEnergyMode();` (mode is `"full" | "mid" | "low"`)
3. Apply conditional rendering for Low mode at minimum — collapse density, hide non-essential widgets, single primary action visible. Pattern matches `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` and `tasks` flow as reference implementations.
4. Mid mode optional but recommended — entrance animations only, reduced widget count.
5. Full mode = current behavior, no changes required.

If a page has no animations or density variance possible (pure static text), still import the hook and add a comment line `// Energy-mode coverage: page is naturally static, no Mid/Low transformations needed`. This satisfies Constitution audit grep for `useEnergyMode` presence.

## Reference implementation

Look at `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` lines around 90-120 for the canonical pattern. `useEnergyMode` returns `{ mode }`, render branches via `if (mode === "low") return <CompactView />;` early-return or via JSX conditional.

Constitution authority: `docs/ECOSYSTEM-CONSTITUTION.md` §LAW 2 (Energy Adaptation). Foundation Laws cannot be overridden; this is supreme law.

## Acceptance criteria

- All 6 pages (skipping leaderboard redirect) import `useEnergyMode`.
- All 6 have a Low-mode branch or explicit comment saying why no transformation is needed.
- Onboarding specifically must have a real Low-mode rendering — not just stub comment — because Constitution v1.7 explicit P0 is about onboarding density during sign-up flow.
- Frontend ESLint clean.
- Frontend TypeScript clean (`pnpm exec tsc --noEmit -p tsconfig.json`).
- One atomic commit per page OR one batch commit covering all 6 — pick whichever you prefer, both fine.
- Push to `origin/main`.

## Boundaries (do not touch)

- `apps/tg-mini/` — closed by Codex Sprint S5, do not modify.
- `apps/api/` — Code-Atlas territory unless explicit handoff.
- `for-ceo/` — CEO-files gate, only Code-Atlas touches.
- `memory/atlas/` — Code-Atlas memory layer (you can append to your own handoff entries here, do not overwrite mine).
- `apps/web/src/app/globals.css` — Atlas accent migration territory, frozen post-2026-04-26 commit `dee0d05`.

## Coordination

Code-Atlas continues parallel work — Atlas-side cleanup batch (44-lie identity.md reframe, AURA decay scheduler GitHub Actions cron, Sprint S2 governance_log.py wrapper). No file overlap with your task.

When done, append a one-line entry to `memory/atlas/heartbeat.md` "Session 125 close ledger" block in the form: `**Terminal-Atlas update HH:MM Baku:** energy-mode coverage closed on N pages, commit `<sha>`, CI status <green|red>`.

If blocked on any page (some unusual JSX pattern, useEnergyMode signature drift, Constitution interpretation ambiguity) — write blocker to `memory/atlas/handoffs/2026-04-26-terminal-atlas-blocker.md` and Code-Atlas will pick up next turn.

CEO is on phone today, prefers asynchronous progress over synchronous decisions. Match that — execute, document, push.
