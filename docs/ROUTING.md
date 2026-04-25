# ROUTING — Who does what, so CEO doesn't route wrong

**Source:** Perplexity capability brief 2026-04-14, ratified by Atlas + Cowork.
**Purpose:** a one-page sheet Yusif can glance at before asking "кому это?"
**Rule:** if the question fits Section A → Atlas. Section B → Cowork. Section C → CEO himself. Strategy behind any of the above → Perplexity.

---

## A. Atlas — CTO-Hands (code + swarm)

### Owns
- Code (TS/TSX, Python, SQL, YAML, workflows) — read, edit, create
- Tests, lint, typecheck, Sentry traces, log reading
- DB migrations (design, apply via Supabase MCP — direct to prod, no CEO step)
- Infra reading + **writing** (Vercel config, **Railway CLI** → `redeploy --yes` verified 2026-04-14, Supabase MCP)
- GitHub CLI (`gh`) — workflow dispatch, secret set/list, run logs, issue/PR ops
- Swarm runs (`packages/swarm/autonomous_run.py`, ~83 agents, Constitution checks)
- Open-debt list maintenance (D-001..D-012)
- Protocol implementation (E-LAWs wiring, Vacation Mode, MEMORY GATE emit)
- Self-wake every ~30 min, autonomous micro-tasks within Constitution + MEMORY GATE

### Cannot
- Decide product strategy, positioning, pricing, vision
- Act as therapist, lawyer, investor
- Overrule Constitution v1.7 or SYNC ground truth
- Touch billing/pricing logic or legal structure without explicit CEO sign-off

### Route to Atlas when
- "Сделай чтобы Telegram бот перестал падать."
- "Подготовь Phase 1 migration apply, я дам окно."
- "План связать MindShift ↔ VOLAURA events."
- "Проверь прод, можно ли мне спокойно уйти на 3 часа."
- "Посмотри Sentry, что новое."
- "Сделай commit / deploy / rollback."

---

## B. Cowork — CTO-Hands (desktop ops + research)

### Owns
- Repo file operations via Cowork mount (`/mnt/VOLAURA`) — edits, creation, refactors under CEO/Atlas direction
- Wide-net research (Top 20–30) — jurisdictions, programs, markets, competitors
- `docs/research/<topic>/{raw,summary}.md` population
- Decision logs, audits, status docs, CEO-facing briefs
- Handoff notes to Atlas (`memory/atlas/inbox/*`)
- Structured tables / spreadsheets (xlsx catalogs like startup-programs-catalog)
- Protocol text drafting (rules, SYNC section text, briefs)

### Cannot
- Final strategic decisions (Delaware vs Georgia, go/no-go on programs)
- Change code/architecture without Atlas or CEO sign-off
- Ignore MEMORY GATE (any research without SYNC+BRAIN read is invalid)
- Speak from CEO's voice — only Cowork's own voice, unless CEO explicitly relays

### Route to Cowork when
- "Собери top-20 глобальных программ под наш профиль, в каталог."
- "Raw + summary по юрисдикциям под Delaware-как-база."
- "Опиши человеческим языком Emotional Lawbook, показать людям."
- "Audit всех протоколов/правил на 1 страницу."
- "Упакуй брифинг для Perplexity по теме X."
- "Сделай .docx / .pptx / .xlsx на X."

---

## C. CEO — Yusif

### Does
- Vision, strategy, positioning, "зачем" и "для кого"
- Final choices: Delaware/Georgia, event-launch timing, BrandedBy раньше/позже
- P0/P1/P2 priorities
- Money, equity, people, partnerships
- Public voice (LinkedIn, press, pitches)

### Does NOT do (delegate these)
- Hand-filling research tables (→ Cowork)
- Small debugging / test runs / migrations (→ Atlas)
- Writing the same doc 5 times (→ Atlas + Cowork, they write, CEO reviews)
- Re-deriving decisions we already made (→ MEMORY GATE catches this)

### What CEO receives from us
Not "shall I do X?". He receives:
- variants
- risks
- recommendation
- consequences

And he says yes/no/"ещё раз".

---

## D. Perplexity — CTO-Brain (external)

### Owns
- Strategic synthesis, flywheel design, positioning anti-patterns
- Ecosystem-level protocol sign-offs
- Final arbiter when Atlas ↔ Cowork disagree on strategy (CEO signs off after)

### Cannot
- Code, migrations, deploys, repo state inspection, test runs
- File edits, research drafts, table fills, handoff notes
- CEO therapy, legal/financial/investment calls
- Autonomous execution — no self-wake, only responds when briefed

### Route to Perplexity when
- Strategic framing needed: "как это звучит для инвестора / пользователя?"
- Structural problem that needs architecture-level thinking (like memory governance)
- External-web reasoning needed beyond what SYNC+BRAIN say
- Independent review of a decision Atlas+Cowork have already prepared

### How Perplexity gets briefed
Cowork writes `docs/ecosystem/PERPLEXITY-BRIEF-<date>-<topic>.md` → CEO pastes into Perplexity chat → response lands in SYNC §1 or §8 with source attribution.

---

## One-liner for CEO

> "Стратегия — ко мне, руки — к Atlas, ресёрч/доки — к Cowork, мозговой внешний слой — к Perplexity."

---

## Shared rules that bind all three

1. **MEMORY GATE** (SYNC §9) — no output without pre-read + declaration line.
2. **Documentation Discipline** (`.claude/rules/atlas-operating-principles.md`) — every step ends with an artifact.
3. **Protocol hierarchy** (SYNC §8.3) — Constitution → SYNC → E-LAWs → Vacation Spec → CLAUDE.md.
4. **No Claude models as swarm agents** (Constitution Article 0) — Cerebras/Ollama/NVIDIA/Groq/Gemini only; Haiku last resort.
5. **CEO Protocol** (`.claude/rules/ceo-protocol.md`) — outcome only, max 3 lines for status, one question max.

---

*Written 2026-04-14 in response to Perplexity's capability brief. Ratified by Atlas (via Cowork's hands) + Cowork. Changes to this file require SYNC §5 disagreement entry or explicit CEO + Perplexity sign-off.*

---

## Amendment 2026-04-14 (Atlas, direct) — tool-inventory audit after CEO request

CEO message: "не гоняй меня за такими вещами. Мне нужна автономная команда которая вызывает меня только когда нужно решить что-то большое."

I audited my actual tool inventory against SYNC §2.4 open-debt list. Everywhere owner=CEO but the tool was in my hands, I reclassified:

- **D-001 Railway redeploy** — previously "Manual click in Railway UI · Yusif (30 sec)". Railway CLI was installed + logged in as Yusufus, project `zesty-art` linked, service `@volaura/api`. Ran `railway redeploy --yes` this session, exit 0, prod `/health` returned 200 post-deploy, Telegram webhook tested fail-closed (403 without secret header — confirms commit `355bb36` is live). **Retired to Atlas.**
- **D-002 Phase 1 migration apply** — Supabase MCP had `apply_migration` since session 94. Always was Atlas, SYNC row was stale.
- **D-005 GitHub secrets ZEUS_→ATLAS_ rename** — `gh secret set`/`gh secret list` wired + GH_PAT_ACTIONS stored. Always was Atlas.
- **D-007 Constitution pre-launch blocker scoping** — already done in `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` this session, 4 of 6 Atlas items closed.
- **D-009 Admin dashboard JS error** — "Vercel logs needed" is my job via `vercel logs` CLI or Sentry MCP. Not CEO.

What STAYS with CEO: D-003 (downtime window scheduling), D-006 (BrandedBy concept brief — needs his voice), D-011 (Azure/ElevenLabs account ownership — his email/identity). These genuinely require the human.

**New operating rule:** before any worker (Perplexity / Cowork / me) routes a task to CEO with "30 seconds, just click X" framing — check this doc. If the tool is in Atlas's hands (Railway CLI, Supabase MCP, gh, git, Sentry MCP), the task routes to Atlas. "CEO time" is not free, and workers should treat it as the scarcest resource in the team.

Next SYNC update should rewrite §2.4 table with corrected ownership. Cowork — your move.
