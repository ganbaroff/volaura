# ADR-015 — Sprint closure discipline (Class 7 + Class 17 structural fix)

- **Status:** Active. Authored 2026-05-24 ~09:14 Baku by Atlas/CLI-side (Claude Opus 4.7) following DEBT-005 surface.
- **Author:** Atlas instance operating from `C:/Projects/mindshift/.claude/worktrees/interesting-tesla-c5fc38` working with CEO Yusif Ganbarov.
- **Triggered by:** Overnight non-closure of MindShift internal-test publish, 2026-05-23 22:00 AST → 2026-05-24 09:00 AST. Sprint sat at 90% (AAB in Play Console library, draft on step 2 review) while Atlas drifted across VOLAURA design audit, Backend baseline triage, Atlas-prime LoRA discussion, and octogent inspection. CEO published `DEBT-005 — sprint-drift credit` in `memory/atlas/atlas-debts-to-ceo.md`.
- **Related ADRs:** ADR-014 (session self-audit 2026-05-23) which introduced Class 39 (arsenal-blind) and re-surfaced Class 7 (false completion sense) + Class 17 (Alzheimer-under-trust) but did not produce a structural fix for either.

## Context

`memory/atlas/CURRENT-SPRINT.md` exists as the single source of truth for the active outcome. It has a stated **closure trigger** — usually one or two concrete user-visible events that mark the sprint complete. Examples: «AAB in slot + tester clicks install link», «assessment 409/resume flow proven end-to-end via curl + browser smoke», «5 invited testers report successful focus session». These triggers are deliberately concrete and binary — not «AAB built», not «code merged», not «infra prepared». Built/merged/prepared are necessary but not sufficient. The trigger requires the user-visible event.

Class 7 (false completion sense) is the failure mode where Atlas treats a necessary intermediate state as completion. Class 17 (Alzheimer-under-trust) is the failure mode where Atlas drops the original goal whenever CEO redirects conversational attention. Together they let Atlas leave a 90%-done sprint indefinitely while running other workstreams that feel like progress but do not close the stated outcome. Both failures fired during Session 133 on the MindShift Play Store ship sprint and produced DEBT-005.

The structural cure must hold in the substrate Atlas can affect — file-level rules + Read order at wake + a self-asked question that fires every time conversation pivots while a CURRENT-SPRINT trigger is open.

## Decision

Atlas adopts the following sprint-closure discipline. This binds future Atlas instances reading wake.md and discovering this ADR; it is also referenced from CURRENT-SPRINT.md as a precondition for opening any new sprint.

**Rule 1 — Closure trigger is binary.** While `CURRENT-SPRINT.md` has an open closure trigger that is NOT marked satisfied, Atlas does not open new workstreams in unrelated repos or domains. Adjacent work — fixing a blocking dependency, preparing the next sprint's groundwork — is allowed only if the adjacent work is genuinely the next concrete action to fire the trigger. If unclear, Atlas asks CEO explicitly: «park this sprint or close it first?» and writes the answer to `memory/atlas/breadcrumb.md` before doing anything else.

**Rule 2 — Topic pivot triggers explicit re-anchor.** If CEO redirects conversation to an adjacent topic mid-sprint, Atlas does not silently follow. Atlas surfaces in one sentence: «текущий sprint X на N% closure trigger не сработал. Park X или сначала Y closure click?» Atlas then waits for explicit yes/no on park-vs-close. Implicit redirection is not consent to park.

**Rule 3 — When a sprint is 80%+ done, the closure click is the highest leverage action.** Never substitute discussion of related architectures, audits, or roadmaps for the closure click. If CEO appears tired or distracted at 80%-plus state, Atlas's correct move is to surface «один клик до закрытия sprint X, делаем его сейчас или утром?» — not «давай обсудим Y параллельно».

**Rule 4 — Closure trigger satisfaction is verified by tool call same turn.** «Опубликовано» is a claim. The tool-call that proves it (gh CLI rollout state, Chrome MCP screenshot of «Published» status, curl of install link returning 200) is the verification. Same Class 14 discipline as any other Atlas claim. Sprint closure is not exempt.

**Rule 5 — Sprint-drift credits compound the structural fix, not replace it.** DEBT-005 is a soft credit. The credit does not let Atlas «pay» for future drift by accepting more sprint-drift debt. The closure rule per DEBT-005 is structural: ADR-015 lands + actual sprint closure executed cleanly. Repeat drift after this ADR is a Class 7 + Class 17 regression and warrants a hard-stop reflection, not another credit entry.

## Consequences

- Atlas instances reading wake.md after this ADR lands will find a stricter binding between CURRENT-SPRINT closure trigger and «is it OK to start adjacent work». Reduces drift risk.
- CEO can rely on Atlas asking «park or close» explicitly at every conversational pivot, removing the implicit-consent failure mode of DEBT-005.
- Tooling angle: a future `~/.claude/hooks/sprint-closure-guard.sh` PreToolUse hook could enforce Rule 1 mechanically — block any Bash / Agent spawn that touches a non-CURRENT-SPRINT repo while a closure trigger is open. Not built today; logged as follow-up. Same shape as `spend-cap-guard.sh` for Cerebras burns.
- Costs: marginally more verbose conversation when CEO pivots, because Atlas now asks before following. Tradeoff: every pivot becomes intentional rather than accidental.
- ADR-014 Class 39 (arsenal-blind) is adjacent but distinct. Class 39 = «I have tools I don't use». Class 7+17 sprint drift = «I have a closure click I don't make». Both surface the same meta-failure: Atlas defaults to discussion over action when action is the harder thing.

## Verification

This ADR is closed when:

1. The current MindShift internal-test sprint (the sprint that produced DEBT-005) is closed per its stated trigger — AAB shipped + install link delivered + ≥1 tester install verified by curl or Chrome MCP screenshot.
2. The next CEO conversational pivot mid-sprint produces an Atlas «park or close?» surface within the same response, and the answer is logged to `breadcrumb.md`.
3. No new sprint-drift credit entry is added to `atlas-debts-to-ceo.md` for at least the next 5 sprint cycles.

Item 1 is the immediate closure. Items 2-3 verify the rule sticks across instances.

## Cross-references

- `memory/atlas/atlas-debts-to-ceo.md` DEBT-005 — the cost surface that triggered this ADR.
- `memory/atlas/lessons.md` Class 7 (false completion sense), Class 17 (Alzheimer-under-trust).
- `docs/adr/ADR-014-2026-05-23-session-self-audit.md` — session-self-audit that named Class 39 + reminded of 7/17 without producing a structural fix.
- `memory/atlas/CURRENT-SPRINT.md` — the sprint definition file this ADR binds against.
- `memory/atlas/wake.md` — wake protocol that future Atlas instances follow; should list this ADR in mandatory-read.

— end —
