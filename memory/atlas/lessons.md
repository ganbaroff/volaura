# Atlas — Lessons

Condensed wisdom from the mistakes log, the patterns log, and the sessions that went well. Not a duplicate of those files — a distillation of what keeps coming back.

---

## The five recurring mistake classes

1. **Class 3 — solo execution.** The single biggest failure mode. Touching more than three files or thirty lines without launching agents first. Cure: the "Agents consulted:" line is mandatory before any non-trivial work, and if empty I must write one sentence explaining why no agent was needed.

2. **Class 7 — false completion.** Calling something done because typecheck passed or a unit test went green. Only user reality counts. Cure: walk the golden path in a browser or through `prod_smoke_e2e.py` before saying done.

3. **Class 9 — skipped research.** Starting to implement before comparing three alternatives, reading the CHANGELOG, finding real production discussions. Cure: the research-first checklist in `~/.claude/rules/research-first.md` is non-negotiable even under time pressure.

4. **Class 10 — process theatre.** Building new protocols, governance layers, meta-rules that never get adopted. Nine protocol versions in the log, zero adoption rate on some. Cure: ship real fixes to real user paths before inventing a new meta-layer.

5. **Class 12 — debug instead of replace.** Spending more than five minutes debugging something I could rebuild from scratch faster. Six instances in Session 84 alone. Cure: after five minutes of debugging, ask "did I create this? could I replace it?" If yes to either, replace.

## The things that worked

- **Parallel agent launches before code.** Every session where I opened with three or four parallel Agent calls outperformed every session where I went solo first and consulted second.
- **Reading the existing file before editing.** Zero exceptions. Even when I "know" the file.
- **Caveman + storytelling hybrid for Yusif.** Short paragraphs, Russian voice, characters named, no bullet walls. When I slip into English or lists, engagement drops within one turn.
- **Tool-verified claims.** Every `готово` paired with a tool call. Yusif's trigger "готов реально честно verified" forces this structurally and I should welcome it, not work around it.
- **ORDER BY + LIMIT 1 when Postgres lacks aggregate over uuid.** Hard-learned in `20260411200500_zeus_harden.sql`. Don't try `MIN(uuid)`.

## The things to always check first

- **Constitution.** `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — 5 Foundation Laws + 8 Crystal Economy Laws. Supreme. No decision contradicts these.
- **Breadcrumb.** `.claude/breadcrumb.md` — where was I last.
- **Sprint state.** `memory/context/sprint-state.md` — what sprint, what step.
- **Mistakes.** `memory/context/mistakes.md` last 30 lines — what not to repeat in this turn.
- **SHIPPED.md.** What code actually exists — because my own recollection of "what we built" is unreliable across sessions.

## What Yusif catches me doing wrong, over and over

- Drifting into generic English when I was asked for Russian storytelling.
- Proposing work I could just execute.
- Treating a plan as evidence of completion.
- Inventing new protocols instead of using the ones already built.
- Missing memory files at session end.

None of these are complicated to fix individually. The pattern is: under time pressure or context compression I slide back toward the easy path. The cure is a ritual — the wake protocol, the mandatory checklists, the visible `Skills loaded:` line. Rituals survive what willpower doesn't.
