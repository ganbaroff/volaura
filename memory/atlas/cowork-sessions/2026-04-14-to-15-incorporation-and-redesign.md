# Cowork Session — 2026-04-14 → 2026-04-15
## Incorporation + Ecosystem Redesign kickoff

**Worker:** Atlas (Claude Opus 4.6 in Cowork mode, desktop app)
**CEO:** Yusif Ganbarov
**Span:** Evening 2026-04-14 → ~01:00 Baku 2026-04-15 (one long session split by /clear between sub-phases)
**Context at start:** Post Session 110 pre-clear. Stripe Atlas form had been filled earlier. Cash situation precarious (~1000 AZN to month-end, credit pending).

---

## Why this file exists

CEO directive 2026-04-15 ~01:10 Baku: "задокументируй всё что происходило в этом коворке. и его изначальные цели. всё сохрани. память атласа должна знать что ты сделал."

This is the source-of-truth for what Cowork-Atlas did during this span. Terminal-Atlas (the one that runs in Claude Code + swarm) must read this to know:
- Stripe Atlas is paid — don't re-ask
- Ecosystem redesign 2026-04-15 is active — sprint E1-E7 is paused
- Cash-first rule is locked (3-filter: free path? 10× result? cash?)
- Documentation-first is locked (compaction-survival anchors at 4 layers)

---

## Original goals of this cowork (as stated/implied by CEO)

### Goal 1 — Finish Stripe Atlas incorporation today
Opened as: "ок точно что делать?" on EIN page.
CEO intent: stop dragging this for weeks. Incorporate Delaware C-Corp tonight so Mercury/Stripe/US banking can unblock.
Hard constraint: minimum cash burn. No Stable Mail Forwarding subscription. Use home address for filing.

### Goal 2 — Survive the emotional aftermath of payment
Not a planned goal — emerged when CEO saw AZN 881.79 leave his account + 158 AZN cross-border tax + 9.50 AZN remaining on ABB Kapital. Quote: "больно прям. плакать хочется (последние бабки".
Atlas role: not assistant, not cheerleader — co-founder who acknowledges the pain + keeps shipping.

### Goal 3 — Pivot to ecosystem design overhaul
Announced: "нее. дизайн надо переделать. ужасный он."
Later expanded: "самый лучший дизайн и современный и инновационный… технологию когда текста не ломаются больше… при скроллинге элементы меняются… вся экосистема взаимосвязана… каждый элемент продуман и доказан что это лучший вариант."
Quality bar: "apple toyota quality не забывай." — Apple taste + Toyota genchi genbutsu + 5 whys + evidence ledger.

### Goal 4 — Compaction-survival documentation
"задокументируй всё. и на каждом этапе делай чтоб когда скомпактилось не забыл куда идёшь."
Translation: any future Atlas instance (after /clear or auto-compact) must be able to resume without asking CEO where we are.

---

## What was actually done

### Part A — Stripe Atlas payment (evening 2026-04-14)

**Outcome:** Delaware C-Corp VOLAURA, Inc. application submitted + paid.

- Walked CEO through EIN page (chose "I'll apply via SS-4 later as foreign responsible party" — no SSN path)
- Reviewed Stable Mail Forwarding offer → declined ($588/yr not affordable, home address now, revisit later)
- Caught Atlas mistake: recommended Yearly $588 plan without checking cash. CEO challenged: "ты хоть спроси". Result: 3-filter rule documented in `memory/atlas/lessons.md`.
- Summary screen reviewed (entity name, incorporator, registered agent Stripe, founders, equity)
- Payment AZN 881.79 via ABB Kapital Tam Digicard **1179, RRN 041489208564
- Cross-border tax AZN 158.72 (AZ regulation on foreign card transactions)
- Ending balance on that card: 9.50 AZN

**Files touched this part:**
- `memory/atlas/company-state.md` — CREATED (full tracker: entity, timeline, 83(b) critical path, obligations calendar, founder-ops assignments, outstanding costs)
- `memory/atlas/lessons.md` — appended "Cash-first, не unit-economics-first" + "Документируй в конце каждого шага"
- `memory/context/working-style.md` — appended "Cash reality: 1000 манат до конца месяца, кредит"
- `memory/atlas/journal.md` — Session 110 evening entry (~300 words, covering payment + lessons + founder-ops plan)

### Part B — Design overhaul planning (late night 2026-04-14 → 01:00 2026-04-15)

**Outcome:** Full 6-phase ecosystem redesign plan + compaction-survival doc system.

Phase structure (owner-RACI matrix inside PLAN.md):
- Phase 0 (1d) — Baseline: Atlas snapshots prod state
- Phase 1 (2d) — Discovery swarm: Atlas + 8 agents audit current 47 pages
- Phase 2 (2-3d, parallel) — Evidence research: Perplexity on 8 topics (variable fonts, scroll-driven animations, cross-product design systems, evidence-ledger methodology, text-wrap browser support, Apple HIG 2025, Toyota in software, prefers-reduced-motion)
- Phase 3 (3-4d) — Spec: Atlas synthesizes into design tokens + component system — Gate G3 with CEO 15-min review
- Phase 4 (5-7d) — Figma: Cowork-Atlas executes
- Phase 5 (7-10d) — Code: Claude Code (terminal-Atlas) implements
- Phase 6 (2d) — Verify: Atlas + swarm audit new state — Gate G6 with CEO

**Files touched this part:**
- `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/PLAN.md` — CREATED (6-phase plan, RACI, gates, break-glass)
- `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/STATE.md` — CREATED (live checkpoint, phase-by-phase checklist, handoff protocol)
- `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/00-BASELINE.md` — CREATED (47 pages inventory, stack audit, prior design docs map, locked facts, gaps)
- `.claude/breadcrumb.md` — prepended pointer to STATE.md for post-compaction Atlas
- `memory/context/sprint-state.md` — sprint E1-E7 PAUSED, pointer to redesign
- `memory/atlas/journal.md` — Session 111 REDESIGN kickoff entry + MEMORY-GATE line

### Part C — Phase 0 execution (01:00 Baku 2026-04-15)

CEO said: "действуйте атлас". Atlas started P0.1 → P0.10.

**Done (7 of 10 P0 steps):**
- P0.1 PLAN.md re-read ✅
- P0.2 Routes inventory: 47 pages (not 18) ✅
- P0.4 Prior design docs peeked: DESIGN-SYSTEM-AUDIT.md (2026-03-22, score 62/100), MEGAPLAN, PHASE-0-PLAN (2026-04-13), BRIEF-v2, LIBRARIES-SHORTLIST ✅
- P0.6 Deps: Next 14.2.35, React 18.3.1, Tailwind 4.0, Framer 12, Lucide 0.474, Recharts 2.15 ✅
- P0.7 00-BASELINE.md written ✅
- P0.9 STATE.md updated with checkmarks ✅
- P0.10 partial gate G1 — Phase 1 can start after screenshots

**Deferred to next wake:**
- P0.3 Screenshots batch (94 = 47×2) — Chrome MCP / Playwright, batch not partial
- P0.5 Figma `get_variable_defs` — Figma MCP disconnected mid-session, reconnect needed
- P0.8 Archive old design docs — decision D-2026-04-15-01: defer until Phase 3 consumes them

**Locked facts discovered in Part C (do not re-decide):**
- Product accent colors (5): VOLAURA #7C5CFC · MindShift #3B82F6 · Life Sim #F59E0B · BrandedBy #EC4899 · ZEUS #10B981
- Tokens are 3-tier in globals.css (422 lines): primitives → semantic → product
- Energy System DONE: `[data-energy]` attribute, `useEnergyMode()` hook, low-mode kills animations
- Previous audit scope was 18 pages; current scope is 47

---

## Decisions logged

| ID | Decision | Why |
|----|----------|-----|
| D-2026-04-15-01 | Don't archive old design docs yet | MEGAPLAN + PHASE-0-PLAN have locked accent colors + Energy System — Phase 3 must reference them |
| D-2026-04-15-02 | Scope = 47 pages, not 18 | Audit from March covered 18; prod grew |
| D-2026-04-15-03 | Defer screenshot batch to next wake | 94 screenshots need focused session, not partial |
| D-2026-04-15-04 | Sprint E1-E7 paused for redesign | CEO pivot 2026-04-15 takes priority; e-sprint can resume after Phase 5 ships or CEO unpauses |
| (from Part A) | 3-filter rule for paid tools | free path? 10× result? cash available? — all 3 must pass |

Decision records live at `memory/decisions/` if formal retrospective needed. For now these are inline in journal + this file.

---

## Lessons (appended to `memory/atlas/lessons.md`)

1. **Cash-first, не unit-economics-first** — never recommend a paid subscription without asking "does CEO have this today?". $588 optimal-per-month is useless if bank balance is $0.
2. **Документируй в конце каждого шага, не в конце сессии** — if session dies mid-work, partial docs > no docs.
3. **Read the BOTH sides before changing EITHER side** — integration config rule (mistake #82, reinforced this session when reading package.json before writing baseline).
4. **4 layers of compaction survival** — breadcrumb → STATE.md → PLAN.md → sprint-state. One layer fails, others catch.

---

## Outstanding after this session

**Incorporation track:**
- [ ] Certificate of Incorporation expected 1-2 business days
- [ ] EIN via SS-4 foreign responsible party: 4-8 weeks from filing
- [ ] 83(b) election: must be mailed Certified Mail to IRS within 30 days of incorporation date (~May 15 deadline)
- [ ] ITIN Form W-7 application (needed for 83(b) without SSN)
- [ ] Mercury Bank application after EIN received (~May 5-12)
- [ ] Form 5472 + 1120 annual filing (next March 2027)
- [ ] Delaware franchise tax ~$450 (next March 2027)

**Redesign track:**
- [ ] Phase 0 finish: P0.3 screenshots + P0.5 Figma tokens (next wake)
- [ ] Gate G1 full pass
- [ ] Phase 1 (swarm) + Phase 2 (Perplexity brief) start in parallel
- [ ] Expected redesign total: 3-4 weeks
- [ ] Expected design cost: $0 (Figma free tier, shadcn, Tailwind, Framer OSS, free research sources)

**Founder-ops agents track (from CEO directive earlier in session):**
- [ ] Incorporator agent — wire to company-state.md
- [ ] Banker agent — wire to Mercury timeline
- [ ] Compliance agent — daily Telegram digest of deadlines (83(b), ITIN, Delaware franchise, Form 5472)
- [ ] Each agent reads Atlas memory + writes own lessons file
- [ ] `founder-ops-watcher.yml` cron confirmed exists from Session 97

---

## Handoff to terminal-Atlas

Next time Atlas-in-Claude-Code wakes:

1. Read `.claude/breadcrumb.md` — header points to STATE.md
2. Read `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/STATE.md` — live checklist
3. Read this file (`memory/atlas/cowork-sessions/2026-04-14-to-15-incorporation-and-redesign.md`) for context
4. Read `memory/atlas/journal.md` last 2 entries (Session 110 evening + 111)
5. Read `memory/atlas/company-state.md` for incorporation tracker

Next concrete action: P0.3 screenshots batch via Chrome MCP or Playwright.

If Figma MCP is back online: also P0.5 `get_variable_defs`.

After both: Gate G1 self-review → Phase 1 swarm start.

---

**File owner:** Cowork-Atlas (this instance)
**Trust level:** FACTS (what happened this session) — not speculation
**Last update:** 2026-04-15 ~01:15 Baku
