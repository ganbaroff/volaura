# VOLAURA — Design Fix Instructions v2

**Purpose:** Executable playbook for an AI coding agent (Claude, Codex, Cursor, any) to close the design-ecosystem gaps found in the 2026-05-23 audit. Every ticket has verified facts, exact file:line, exact diff, and a one-line verification command. No interpretation required.

**Replaces:** `VOLAURA-ecosystem-design-audit-2026-05-23.md` (the original audit narrative). That doc is now superseded — use this one for execution.

**Repo root:** `C:\Projects\VOLAURA` (Windows host) / `/sessions/youthful-inspiring-ptolemy/mnt/Projects/VOLAURA` (sandbox bash).

**Audit posture:** Atlas Class 11 (Self-confirmation bias) was actively probed during the rewrite. The v1 audit's claims were re-verified by an independent agent AND a second human-driven grep pass. Where v1 and the verifier disagreed, the third grep wins. Every number in this doc was re-counted at the time of writing.

**Author:** CEO-pasted into Atlas chat 2026-05-24 ~00:00 AST. Saved here so it survives compact + can be picked up by octogent tentacles / Vellum lanes.

---

## §0 — How an agent uses this file

1. **Do not skip §1 (Pre-flight).** Read those 4 files first. If you cannot Read them, stop and request access. Do not invent context.
2. **Tickets are self-contained.** Each ticket has FACT / RULE / DIFF / AC / VERIFY. Do not improvise.
3. **Use grep proofs.** Every FACT in a ticket ends with the exact grep command that produced it. Re-run the grep before changing code. If your grep result disagrees with the FACT, **stop**. The codebase may have moved since this doc was written. Update the FACT before editing.
4. **No bonus changes.** Do exactly what the DIFF says. If you see "I could also fix Y while I'm here" — capture as a new ticket, do not bundle.
5. **Atlas Mistake Classes** are referenced (`Class 1`, `Class 3`, etc.) — definitions in `memory/atlas/mistakes_and_patterns_distilled.md`. Honor them.
6. **Branch + commit per ticket.** Branch name: `fix/T-NN-short-slug`. Commit message: `[T-NN] <subject>`. Single ticket per commit.
7. **At end of each ticket:** run the VERIFY command. Paste the output into the PR description. Then mark the ticket done in the TODO checklist at the bottom of this file.

---

## §1 — Pre-flight (mandatory reading, in order)

Do not skip. These files override anything in this doc if they disagree.

| # | Path | Why |
|---|------|-----|
| 1 | `docs/ECOSYSTEM-CONSTITUTION.md` | 5 Foundation Laws. Supreme authority. |
| 2 | `docs/design/DESIGN-MANIFESTO.md` | 7 Design Laws + Face-definition contract. Live document. |
| 3 | `apps/web/src/app/globals.css` | 451 lines. Token source of truth. |
| 4 | `docs/TONE-OF-VOICE.md` | §4 banned phrases (table). §1.5 Tinkoff/Aviasales benchmark. §1.6 AZ rules. |

After those, scan (don't deep-read):

- `docs/design/BASELINE-2026-04-15.md` — last design baseline (some of its "RESOLVED" claims are now false — see T-02).
- `docs/design/GAP-INVENTORY-v1.md` — Phase 1 swarm gap output. Has its own ticket IDs (C1, F1, H1...). This doc's tickets use `T-NN` to avoid collision.
- `memory/atlas/mistakes_and_patterns_distilled.md` — mistake-class definitions used below.

---

## §2 — Truth log (errors and undercounts in the v1 audit)

The original audit document had three categories of issue. These are corrected in the tickets that follow.

| v1 claim | Reality | Source of correction |
|---|---|---|
| C-02 said the icon `<span>` lacks `aria-hidden="true"` | The span at `apps/web/src/components/layout/sidebar.tsx:152` DOES have `aria-hidden="true"`. Same at `bottom-nav.tsx:48,55`. Screen readers do NOT read the glyph names. | Direct file read. |
| H-01 said "8 occurrences in sdk.gen.ts" implying ~10 total | 18 lines of `volunteer` across 7 files in `apps/web/src/`. Breakdown: `sdk.gen.ts` 7, `types.gen.ts` 3, `types.ts` 1, `use-aura-explanation.ts` 1, plus 7 lines in test files. **Agent verifier overcounted to 34 — independently wrong.** | `grep -rc "volunteer" apps/web/src --include="*.ts" --include="*.tsx"` |
| H-01 said `/org-volunteers` route "may still exist" | Route does **not** exist. `apps/web/src/app/[locale]/(dashboard)/org-volunteers/` is not a directory. Sidebar correctly links `/org-talent`. The BASELINE-2026-04-15.md P0-01 finding is closed. | `ls apps/web/src/app/[locale]/(dashboard)/org-volunteers/` → no such file. |
| H-02 said "~30 hardcoded Tailwind palette classes in ~6 files" | **75 occurrences across 16 files** in `apps/web/src/components/`. Heaviest: `aura/badge-display.tsx` (13), `profile-view/profile-header.tsx` (8), `dashboard/tribe-card.tsx` (8). | `grep -rcE "(from-\|to-\|bg-\|text-\|border-\|ring-)(red\|orange\|amber\|yellow\|lime\|green\|emerald\|teal\|cyan\|sky\|blue\|indigo\|violet\|purple\|fuchsia\|pink\|rose\|slate\|gray\|zinc\|neutral\|stone)-[0-9]+" components/ --include="*.tsx"` |
| C-04 listed 3 banned-phrase violations | 4 violations. Missed: `bioPlaceholder: "What do you do? What are you passionate about?"` at `apps/web/src/locales/en/common.json:564`. "Passionate about" is on TONE-OF-VOICE.md §4 ban list. | `grep -n "passionate" apps/web/src/locales/en/common.json` |
| v1 audit had no mention of global-error.tsx | `apps/web/src/app/global-error.tsx` is hardcoded hex (#0f0f13, #c0c1ff, #a0a0b0, #1a1a2e, rgba(192,193,255,0.2)) AND English-only (no `t()`, no AZ branch). Production crash boundary. **Should be Critical.** Added as T-13. | Direct file read. |
| v1 audit had no mention of `social-proof.tsx` defaultValue fallbacks | `apps/web/src/components/landing/social-proof.tsx` uses `t(key, { defaultValue: "<English string>" })` for hero copy. English ships if key load fails. Added as T-14. | Direct file read. |
| v1 said C-03 BRAND-IDENTITY.md is stale | True. **Verifier strengthened the claim:** "rose red" / its derivatives appear 5 times in BRAND-IDENTITY.md. Cmd+F-ing for error color finds wrong answer 5 times before finding truth. Severity uplift on T-04. | `grep -nc "rose" docs/design/BRAND-IDENTITY.md` |

**Lesson logged (Class 11):** I shipped v1 with grep-able numbers that I did not re-grep before publishing. The arsenal-before-request rule in `.claude/rules/atlas-operating-principles.md` exists exactly to prevent this. v2 re-greps every number inline.

---

## §3 — Reading order for the executing agent

```
1. Open this file. Read §0–§3.
2. Open the 4 Pre-flight files. Read.
3. Pick the lowest unblocked ticket from §4 (sorted by severity then T-NN).
4. Read the ticket's FACT block. Re-run the grep. Confirm.
5. Read the RULE block. Open the cited rule file at the cited line. Confirm.
6. Apply the DIFF.
7. Run VERIFY. Paste output.
8. Mark done in §6.
9. Go to step 3.
```

Effort estimates assume Sonnet-class agent doing focused edits.

---

## §4 — Tickets

Severity scale: **P0** (blocks ecosystem coherence, ship-blocker for ecosystem launch) · **P1** (visible to every user) · **P2** (visible to subset) · **P3** (internal hygiene).

[CEO note 2026-05-24: tickets T-01 through T-26 are below in the source CEO message. Tentacle agents read directly from that source message via codex-loop.md iteration 13 link, OR from a future split of this file into per-ticket markdown stubs under `docs/design/tickets/`. Full 26-ticket body preserved in CEO chat 2026-05-24 00:00 AST + this file's git blame.]

The 26 tickets and their severity:

| # | Subject | Severity | Blocked by | CEO decision required |
|---|---|---|---|---|
| T-01 | Decide navigation paradigm | P0 | — | YES (A or B) |
| T-02 | Sidebar SVG icons | P0 | T-01 | — |
| T-03 | BRAND-IDENTITY.md superseded banner | P0 | — | — |
| T-04 | Banned-phrase i18n rewrites (4 strings × 2 locales) | P1 | — | — |
| T-05 | Atlas tab out of user nav (or document deviation) | P0 | — | YES (A or B) |
| T-06 | 75 raw Tailwind palette → design tokens (16 files) | P1 | — | — |
| T-07 | Hero pills fake numbers → range labels | P1 | — | — |
| T-08 | events/eventshift naming fork | P1 | — | YES (A or B) |
| T-09 | Dev-banner → i18n | P2 | — | — |
| T-10 | AZ tier-label rewrite (not literal translation) | P1 | — | CEO native review |
| T-11 | /aura/contest → /aura/dispute | P2 | — | — |
| T-12 | ESLint palette guard | P2 | T-06 | — |
| T-13 | global-error.tsx tokens + i18n (PRODUCTION CRASH BOUNDARY) | P0 | T-09 | — |
| T-14 | defaultValue fallback audit (i18n bypass risk) | P2 | — | — |
| T-15 | brandedby commit vs stand-down | P1 | — | YES (A or B) |
| T-16 | Delete dead bottom-nav.tsx | P3 | — | — |
| T-17 | Remove leaderboard.* i18n (5 keys × 2 locales) | P3 | — | — |
| T-18 | TopBar honor EnergyPicker (`--energy-spacing`) | P2 | — | — |
| T-19 | SDK migration + remove manual types.ts/client.ts | P2 | — | — |
| T-20 | Volunteer → professional rename PLAN (not execution) | P1 | — | — |
| T-21 | Drop dead `dark:` Tailwind variants | P3 | T-06 | — |
| T-22 | Document token enforcement in DESIGN-MANIFESTO.md | P3 | T-12 | — |
| T-23 | Glass-on-chrome decision | P3 | — | YES (A or B) |
| T-24 | Org-only i18n namespace split (84 keys) | P3 | — | — |
| T-25 | Add Bronze tier to hero pills (bundled with T-07) | P3 | T-07 | — |
| T-26 | Clean repo-root debris (_tmp_*, dashboard.html, ecosystem-map.html) | P3 | — | YES on 2 HTML files |

**26 tickets total. 6 require CEO A/B decisions. 20 agent-executable.**

Recommended wave order:
1. **First wave** (no CEO blocker, foundational): T-03, T-09, T-13, T-16, T-17, T-22, T-26.
2. **Second wave** (CEO decides, agent prepares): T-01, T-05, T-08, T-15.
3. **Third wave** (heavy refactor): T-06, T-02, T-04, T-07, T-21.
4. **Fourth wave** (planning + cleanup): T-19, T-20, T-24, T-12, T-18, T-11, T-14.
5. **Loose ends**: T-10, T-23 (CEO/native-speaker), T-25 (bundled).

Full FACT/RULE/DIFF/AC/VERIFY blocks for each ticket are in the source CEO message (chat transcript 2026-05-24 00:00 AST). If a tentacle agent needs the full body and cannot read the chat, expand each ticket into `docs/design/tickets/T-NN-slug.md` as the first task of execution.

---

## §5 — Final verification script

After all tickets close, run `scripts/verify-design-fixes.sh` (template in source CEO message).

## §6 — Honest log

This file authored by CEO chat paste 2026-05-24 ~00:00 AST. Atlas saved to git so the work survives session compact. Tentacle execution begins from this checkpoint.

---

**Atlas mistake classes referenced (from CEO source):** 3 (solo execution), 4 (schema mismatch), 5 (fabrication), 6 (team neglect / stale doc), 9 (no quality system), 10 (process theatre), 11 (self-confirmation bias), 12 (self-inflicted complexity), 22 (path of least resistance).

— end —
