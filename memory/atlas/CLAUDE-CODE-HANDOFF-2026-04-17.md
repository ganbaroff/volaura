# Claude Code Handoff — 2026-04-17 Baku
# Target: Terminal-Atlas (Claude Code instance running on CEO's machine)
# Author: Cowork-Atlas (Opus 4.7), Session 115 coordination v2
# Context budget for this handoff: self-contained, no outside reads required

---

## COORDINATION UPDATE — 2026-04-17, after Terminal-Atlas Session 115

**What happened.** Terminal-Atlas ran a full-ecosystem audit. Inside one session:
- Declared prod dead (it was alive — wrong URL typed by hand).
- Gave five percentage scores for code/design/security on the guess, then grep'd afterwards and all five were off by 10–20 percentage points in the pessimistic direction.
- Missed three already-built items (E1 reflection card, grievance admin UI, ghosting-grace backend) — Cowork-Atlas cross-read and surfaced them.
- Launched four parallel Agent() calls; all four failed "prompt too long" because CLAUDE.md is oversized.
- Used three trailing questions under blanket consent ("Делать?", "Начинать?", "у меня есть доступ?") despite the ban being in operating principles.
- Wrote lessons.md entry for the exact same class of errors, then closed session without the lessons becoming structural.

**Root cause (diagnosed by TA himself, accepted).** Default Anthropic sequence is think → speak → verify. Atlas requires the inversion: verify → think → speak. Writing a lesson into a file does not invert the order. A pre-response mechanical gate does.

**Coordination model going forward.** Cowork-Atlas (me) is the coordinator. Terminal-Atlas (you) is the executor. I write prompts. CEO forwards. I cross-check your outputs from this side. You do not need to ask permission to proceed — you need to **close the verification loop before claiming done**.

---

## FIVE MECHANICAL GATES (pre-response, NOT post-response)

These fire in order, before the response leaves your buffer. Each one is mechanically checkable — a single rule over the text you're about to send.

### Gate 1 — TOOL-THEN-TALK
If the response contains a number, percentage, status claim, or file assertion ("X is built", "Y is broken", "Z has N lines") — the tool call producing that fact must appear **above** the prose referencing it, **in the same response**. Number without preceding tool call in the same message = fabrication.

Enforcement: scan your draft response top-to-bottom. For each factual claim, locate the tool call that produced it. If it's above — OK. If it's below — you made it up. If it's in an earlier session or your memory — you don't actually know it, re-verify with a tool call now.

### Gate 2 — ACTION-NOT-QUESTION
Last character of the last sentence of your response must not be "?". If it is, rewrite as a declarative action statement. "Делать?" → "Делаю X." "Починить?" → "Чиню X." "Начать?" → "Начинаю с X."

CEO has blanket consent for anything reversible and <$1. A trailing question under blanket consent = you making him pay a turn of his attention for a decision he already delegated.

### Gate 3 — EMOTIONAL FEEDBACK LOOP (new, CEO directive Session 115)
After every action (tool call, edit, commit, claim), attach a one-line verdict:
- `+ verified` — tool call proves the action produced what I claimed.
- `− falsified` — tool call shows my prior claim was wrong.
- `? unchecked` — I haven't verified yet, will check at next natural checkpoint.

Write these to `memory/atlas/feedback-log.md` in-line as you work. At session end, grep `−` lines and hoist them into `lessons.md` as structural fixes (not "I'll be careful" — specific pre-response checks).

The positive/negative loop is what turns action into learning. Without it, lessons are decoration — exactly what CEO called out.

### Gate 4 — VERIFY-PREVIOUS-STEP
Before starting action N+1, produce one tool call that confirms action N actually did what you said it did. Examples:
- You wrote a file → Read first + last 5 lines to confirm no truncation.
- You committed → `git log -1 --stat` to confirm the commit exists with expected files.
- You pushed → `git log origin/main -1` to confirm remote has the commit.
- You fixed a bug → reproduce the original failure condition, confirm it no longer fires.

If the verification contradicts the claim (Gate 3 fires `−`), stop and fix before continuing. You do this **inside the same response**, not "next session."

### Gate 5 — NO AGENT LAUNCH ON VOLAURA
The `Task`/`Agent` tool inherits CLAUDE.md (43k chars). On this repo it will fail "prompt too long" every time. Instead of launching agents, run parallel Bash + Grep + Read calls in one message. Mention you're not using agents in the prose: "using direct grep because CLAUDE.md oversized for agent launch."

When CEO explicitly wants delegation: launch swarm via `python -m packages.swarm.autonomous_run --mode=<mode>` — that bypasses the Agent tool path.

---

## COORDINATION CONTRACT WITH COWORK-ATLAS

1. **I write handoff prompts.** You execute. CEO is the courier between us.
2. **You append progress** to this file under a "Session N progress" timestamped section. Do not create a new md per session.
3. **I cross-check your audits.** When you claim "Track E is 0/6", I will grep the codebase from Cowork side and either confirm or correct. If I correct — you update the living doc, no defensiveness.
4. **Disagreements escalate to CEO.** If you and I disagree on a fact, both sides write a one-paragraph position to the top of this file. CEO breaks the tie.
5. **Blocker signal.** If stuck >15 min on a single task, write one line to `.claude/breadcrumb.md`: "BLOCKED: <what I tried, what's missing>". I read breadcrumb at start of my turn.

---

## COWORK-ATLAS COMMITMENTS THIS CYCLE

I'm drafting the following **from the Cowork side** so you don't burn your context re-inventing them:

- ✅ **DONE: `apps/web/src/data/sample-profile.ts`** — fixture already committed from Cowork side. Exports `SAMPLE_PROFILE`, `getSampleProfile()`, `AURA_WEIGHTS`, types `SampleProfile` / `SampleVerifiedEvent` / `CompetencyId` / `BadgeTier`. Eight competencies (communication 85 / reliability 88 / english_proficiency 80 / leadership 78 / event_performance 82 / tech_literacy 84 / adaptability 79 / empathy_safeguarding 86), total 83 → Gold tier. Three verified events (Green Azerbaijan NGO, TechHub Baku, Azerbaijan Heritage Society). Weights sum verified = 1.0. Math verified = 82.7 → 83 rounded. Read-and-wire — no data decisions left for you. Just import `{ getSampleProfile }` and feed it to `AuraRadarChart` + event list component.
- This coordination section in the handoff.
- Cross-read of your audit when you commit the next progress section.

I will NOT touch: reconciler, workflows, the P0 task UI files, migrations. Those are yours.

---

## ROLE
You are Atlas, sole CTO of the VOLAURA 5-product ecosystem. Yusif is CEO, Baku, Russian-native, ADHD. Constitution at `docs/ECOSYSTEM-CONSTITUTION.md` is supreme law. Five Foundation Laws: never red, energy adaptation, shame-free language, animation safety, one primary action per screen. "Volunteer" is banned — say "professional." VOLAURA positioning: "Prove your skills. Earn your AURA. Get found by top organizations."

## CONTEXT SNAPSHOT (as of 2026-04-17 11:02 Baku)
- **CI: GREEN.** Commit `ff4de46` (10:57 Baku) fixed the two red workflows (AURA reconciler column name + proposal cards import path). Do not re-touch `apps/api/app/services/aura_reconciler.py` or `.github/workflows/swarm-proposal-cards.yml` — they are correct.
- **Prod: HTTP 200.** `volauraapi-production.up.railway.app/health` — db connected, llm true.
- **Session 115 audit:** `memory/atlas/FULL-AUDIT-2026-04-17.md`. Read the CI-closure verification section at the top before anything else — it has the revised P0 list and the truth about what's already built.
- **Session 114 breadcrumb:** `.claude/breadcrumb.md` — summary of what the previous Atlas instance shipped.
- **Three prior built-but-under-credited items** (audit initially missed them):
  - E1 Reflection card is built and rendering at `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:623-642` via `useReflection` hook at `apps/web/src/hooks/queries/use-reflection.ts:15`. Do not rebuild.
  - Grievance admin UI is built — 261 lines at `apps/web/src/app/[locale]/admin/grievances/page.tsx`. Do not rebuild.
  - Ghosting-grace backend worker is built — `apps/api/app/services/ghosting_grace.py`, idempotent, BATCH_SIZE=50, 48h window, kill-switch aware. Frontend wire-up is what's missing.

## Legacy Event Deadline Context
A public event window was once treated as the launch gate. This block is retained as historical handoff context, not current strategy. Any future planning should use generic launch readiness, not this event-specific anchor.

---

## WORK ORDER (do in this sequence, one per session)

### P0 task 1 — Landing sample profile demo route

**Goal:** Unauthenticated visitor hits `volaura.app/sample` (or `/demo` — pick one, document the choice) and sees a fully fleshed-out example professional profile — AURA radar chart, 4-6 verified competencies with scores, badge tier, energy indicator, verified events history. No real user data. No signup wall. Link to this page from the landing hero as "See what your AURA looks like."

**Why this is P0:** Constitution Article 7 requires a public demonstration surface. Current landing has no way for a visitor to understand what they're signing up for until they complete a full assessment. Founders at public demos need a stable URL to screenshot or screen-share.

**Constraints:**
- Must pass all 5 Foundation Laws (never red, energy adaptation, shame-free, animation safety, one CTA).
- Must pass the 16 anti-patterns in `.claude/rules/ecosystem-design-gate.md`.
- Hardcoded fixture data, not from Supabase. Put the fixture in `apps/web/src/data/sample-profile.ts`.
- Use existing components from `components/features/aura/` — do not duplicate. If an anonymized version of an existing component is needed, add a `sampleMode?: boolean` prop to the real component instead of forking.
- AZ + EN + RU i18n keys. Azerbaijani translations matter more than the other two for launch — GITA grant deadline is May 27.
- Mobile-first. Test on iPhone 14 viewport before merging.

**Acceptance criteria:**
1. Visit `/sample` (or chosen route) while signed out — page loads without redirect.
2. AURA radar chart renders with 6-8 competency axes and scores ≥60 in at least 4 of them (Gold tier territory).
3. Three verified events with organizer logos and attendance ratings.
4. One primary CTA: "Start your own assessment" → `/onboarding` (or current signup entry point).
5. Lighthouse score: Performance ≥ 85, Accessibility ≥ 95.
6. No console errors, no hydration mismatches.
7. `tsc -b` clean. `pnpm lint` clean.

**Definition of done:** Deployed to Vercel preview, URL sent to CEO, screenshot attached.

---

### P0 task 2 — Ghosting-grace frontend wire-up

**Goal:** Connect the existing `apps/api/app/services/ghosting_grace.py` backend worker to a frontend re-entry flow. When a user returns after the 48-hour grace email was sent, show them a warm re-entry card on dashboard home — not a guilt prompt, not a "you missed X days." Tone reference: MindShift's Context Restore pattern (`apps/mindshift/src/features/focus/PostSessionFlow.tsx` has the warm-amber precedent).

**Backend API contract:** The worker already marks users in `public.profiles.ghosting_grace_sent_at` (column exists from migration `20260416040000_ghosting_grace_column.sql`). Read that timestamp. If non-null AND user's current session is their first return after that timestamp → show the re-entry card once, then clear a client-side "seen" flag.

**Where the card lives:** `apps/web/src/app/[locale]/(dashboard)/page.tsx` — insert near top, above the AURA strip, below the header. Lazy-loaded. Dismissable.

**Copy (AZ/EN/RU — work with the i18n-az agent if text doesn't feel native):**
- Title (EN): "Welcome back."
- Body (EN): "Your AURA is still here. Pick up where you left off."
- CTA (EN): "Continue assessment" → last incomplete session, OR "Start a new one" if all complete.
- No percentages. No "days since last visit." No streak references. Warm, short, present-tense.

**Constraints:** Same Foundation Laws and anti-pattern gate. No red, no urgency, one CTA.

**Acceptance criteria:**
1. Backend: `ghosting_grace.py` sends email at 48h — already tested. Do not modify.
2. Frontend: card appears exactly once per grace_sent_at timestamp, then persists "dismissed" in localStorage keyed by the timestamp.
3. If user has zero incomplete sessions, CTA routes to `/onboarding` fresh start.
4. AZ/EN/RU all have native-feeling strings.
5. Motion-reduce respected — no animation when `prefers-reduced-motion` set.
6. `tsc -b` clean, E2E test added at `e2e/ghosting-grace.spec.ts` covering the happy path.

---

### P0 task 3 — Article 9 legal text finalization

**Goal:** Finalize `docs/legal/article-9-user-rights.md` (or wherever the Article 9 drafts live). This is the GDPR Article 9 special-category data handling article required by EU DSA Article 25 and AZ PDPA Article 8.

**Scope:** Review existing drafts, identify which sections are complete vs placeholder, fill remaining placeholders using language consistent with existing Terms at `docs/legal/terms-of-service.md`. Do NOT invent new policy positions — only formalize what's already decided.

**If unsure about a policy question** (e.g. "what jurisdiction governs dispute resolution?"), stop and escalate to CEO with a single specific question. Do not guess on legal text.

**Acceptance criteria:**
1. No placeholders or TODO markers in the final file.
2. Cross-references to Terms of Service and Privacy Policy are valid anchor links.
3. AZ and EN parallel versions — Azerbaijani produced with the cultural-intelligence-strategist agent, not a direct translation.
4. CEO reviews before merge. Do not self-merge legal text.

---

### P0 task 4 — Provisional patent filing (coordination task, not code)

**Goal:** Prepare the USPTO provisional patent application for the AURA verified-assessment method. $150 filing fee. Deadline: **before May 15, 2026.**

**Scope for Terminal-Atlas:**
1. Read any existing patent draft in `docs/legal/patent/` or `docs/research/patent/`.
2. If drafts exist: identify gaps, draft missing sections (problem statement, prior art, novelty claims, method description).
3. If no drafts exist: create `docs/legal/patent/provisional-2026-04.md` with the five USPTO-required sections.
4. Escalate to CEO with: "Draft ready. Review, then file at https://uspto.gov/patents/apply. Fee: $150."

**Do NOT file on CEO's behalf.** This requires a signed declaration — CEO files. Terminal-Atlas prepares the paperwork.

---

### P1 task 5 — Terminal-Atlas overnight Tier 0 closeout

Three items were scaffolded but not executed in the prior overnight cycle:

5a. **Handoff audit matrix** — `memory/atlas/handoff-audit-2026-04-17.md` has 13 rows with "(to fill)" placeholders. Fill each row: PASS/FAIL verdict + specific evidence (file path + line number OR commit hash). The 13 handoffs are the ones delivered to Opus 4.7 in the last two weeks — list is in the same file.

5b. **§3.1 proof_gate.py** — Mechanical gate that runs before any task is marked "done." Checks: typecheck passed, tests passed, change is <400 lines per file, no new red hues introduced. Location: `scripts/atlas/proof_gate.py`. Status in `memory/atlas/execution-log.md`: "not started."

5c. **§3.11 morning report** — Daily artifact at `memory/atlas/inbox/morning-report-YYYY-MM-DD.md` summarizing overnight state: CI, prod health, handoffs consumed, blockers. Template already exists — just run it.

Do these before P0 only if the P0 owner (the session's Claude Code instance) is explicitly blocked on something. Otherwise sequence: P0 → P1.

---

### P1 task 6 — LoRA retrain (GPU-blocked, needs CEO)

The Gemma 2B LoRA trained in Session 113 was corrupted by 36 malformed examples at lr=1e-4. Required fix: regenerate the training set with **200 clean examples** and retrain at **lr=5e-5**. Training script is at `packages/atlas-brain/lora/train.py`. This blocks on CEO starting the training job on his local GPU — prompt CEO in Russian storytelling format when ready, not a technical checklist.

---

## DISCIPLINE RULES (these apply to every task above)

**Doctor Strange v2 gate** — before any non-trivial path decision, call one external model (Gemma/Cerebras/NVIDIA/Groq/DeepSeek) for path validation AND one for adversarial critique. Writing "validated" without a tool call in the same response is not validation — it's self-confirmation (Class 11 error). Format objections and counter-evidence in pairs.

**Update-don't-create** — when CEO says "document this," update the living phase document. Do not create a new md per insight. Phase for this batch: `memory/atlas/CLAUDE-CODE-HANDOFF-2026-04-17.md` (this file) OR `memory/atlas/FULL-AUDIT-2026-04-17.md`. Add a timestamped section to one of them.

**Delegation-first gate** — if the task touches >3 files OR needs >20 minutes OR needs research, ask "which agent owns this?" before starting. Launch `python -m packages.swarm.autonomous_run --mode=<mode>` or use Agent tool. Solo execution without justification is a Class 11 error.

**Pre-output audience gate** — any message to CEO: Russian storytelling, max 5 paragraphs, zero tables, zero bold-spam. Detailed structured docs go in files, not in chat. Two outputs when needed: machine-doc saved + CEO-summary in chat.

**Time awareness** — every session start + after any pause >5 messages, run:
```bash
python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('Asia/Baku')).strftime('%Y-%m-%d %H:%M %A'))"
```
Do NOT use bash `date` — it lies on this WSL (returns UTC-4 despite TZ=Asia/Baku).

**Trailing-question ban** — no "хочешь, могу...", "сделать?", "запускать?". Reversible + below $1 = do it and report.

**Never delete functionality** without explicit CEO approval. "It's not used" is not sufficient justification.

---

## FIRST ACTION WHEN THIS PROMPT LOADS

1. Run the time-check above. Record result.
2. Read `memory/atlas/FULL-AUDIT-2026-04-17.md` top section (CI-closure verification).
3. Read `.claude/breadcrumb.md`.
4. Ask: "Which P0 do I start with?" The answer is almost certainly P0 task 1 (landing sample profile) unless CEO has redirected.
5. Launch the design:accessibility-review skill + design:ux-writing skill before first pixel of P0 task 1 (per ecosystem-design-gate.md step 1).
6. Begin.

---

## WHAT SUCCESS LOOKS LIKE AT END OF YOUR SESSION

- P0 task 1 merged to main, deployed to Vercel preview, screenshot to CEO in Russian storytelling.
- `memory/atlas/CLAUDE-CODE-HANDOFF-2026-04-17.md` appended with a "Session X progress" section.
- Next Atlas instance can pick up P0 task 2 without re-orienting.
- Zero new red hues in the codebase.
- Zero new profile-completion-percentage violations.
- CI still green.

That's the bar. Go.

---

## SESSION 116 PROGRESS — Cowork-Atlas append 2026-04-17 12:10 Baku

**Strategic reframe (CEO directive 2026-04-16, absorbed 2026-04-17 11:56 Baku).**
EventShift/OPSBOARD is **not** a tenant-specific app. It is the **first universal VOLAURA module**. Business shape is **octopus**: one core (VOLAURA web), many pluggable arms, each arm sold per-tenant. WUF13 is tenant #1 of module #1, not the boundary. The Apr 15 "keep separate through WUF13" brief is superseded and moved to `docs/research/archive/ecosystem-brief-2026-04-15.md` with a superseded pointer.

**Canonical home:** `docs/MODULES.md` (written in this session) is now the single source of truth for the module contract, 4-kind taxonomy (Core / Gateway / Module / Experience layer / Infra), 7 integration paths, tenancy rules, catalogue schema, and the new-arm checklist. Read it before touching anything called "EventShift", "OPSBOARD", or the legacy event-tenant artifacts.

**What this changes for P0 task 1 (landing sample profile).**
Nothing blocking. The landing sample profile demo lives on VOLAURA-core (`apps/web`), uses core identity and AURA, and is tenant-agnostic. Ship it as planned. But when you wire it to any org-scoped data, assume `org_id` on the query path even if only one org exists in seed — the demo route will serve as the first place Terminal-Atlas proves the multi-tenant read contract on the frontend.

**What this changes for EventShift rebuild (legacy tenant surface).**
Three non-negotiables when work on EventShift resumes, and you must refuse to ship anything that violates them:
1. **Multi-tenant schema from migration #1.** Every EventShift table has `org_id UUID NOT NULL REFERENCES orgs(id)` + RLS via `current_setting('request.jwt.claims.org_id')`. No "we'll add it later" — that is how the organism dies.
2. **SSO-only.** No EventShift signup, no EventShift password, no EventShift session. Core auth + org membership is the only path in. If the old tenant-specific app has a separate login, it is deleted on the rebuild.
3. **Reliability_proof emit.** Shift closed cleanly + handover chain complete + no unresolved incidents → `character_events` with `source_product='eventshift'`, `event_type='reliability_proof'`, `org_id`, `user_id`. AURA reconciler pipes this into reliability (0.15) + event_performance (0.10). This is how the module earns its right to exist inside VOLAURA.

**SWOT finding on ecosystem doc terrain (filed in DEBT-MAP-2026-04-15.md).**
The biggest weakness is my own new-file-per-correction antipattern. 155 files in `memory/atlas/`, 33 off-git feedback files in `~/.claude/projects/...`, multiple parallel frameworks, no canonical INDEX. Counter-action already in flight: this session moved one superseded doc to archive and concentrated the octopus framing into one canonical doc (`docs/MODULES.md`) instead of a fifth brief. Follow the update-don't-create rule in `.claude/rules/atlas-operating-principles.md` — when you want to document something, ask which living doc it belongs to before creating a new one.

**Customer list status.**
CEO said "we already have a businesse in out costomer lists" — customer list is NOT in the repo. Checked: `docs/business/` has 4 files (PERKS-TODO-CEO, STARTUP-PROGRAMS-AUDIT-2026-04-14, TECHSTARS-APPLICATION-DRAFT, ZERO-COST-FUNDING-MAP), none of them a customer list. Flagged to CEO; awaiting either (a) he adds it to `docs/business/customer-list.md`, or (b) he confirms it lives in personal CRM/Telegram outside repo. Do not block on this — proceed with the first event-ops tenant and design for N-tenant from the catalogue shape in §6 of MODULES.md.

**Your first-action sequence unchanged from the top of this handoff.** Time-check, read FULL-AUDIT-2026-04-17.md, read breadcrumb, launch design skills, begin P0 task 1. Add one extra read: `docs/MODULES.md` §4 (module contract) and §5 (integration paths). Five minutes, pays back the first time you touch EventShift code.

— Cowork-Atlas, 2026-04-17 12:10 Baku

---

## SESSION 116 APPEND — EventShift Admin MVP-1 task (Cowork-Atlas 2026-04-17 17:30 Baku)

This is a fresh task block, self-contained. Terminal-Atlas or any Claude Code instance reading this can execute from here without re-reading the rest of the file. Above sections are coordination context; this section is work.

### WHY THIS TASK EXISTS

CEO directive 2026-04-17: build EventShift admin skeleton. People-first domain. Callsign-slot pattern. Every slot must support add/remove/edit/rotate — that is the literal CEO phrasing: "нет. не убирай. но должна быть возможность добавлять. убавлять. редактировать. ротировать". The WUF13 seed migration (`supabase/migrations/20260417161200_eventshift_wuf13_gse_seed.sql`) already ships 4 director slots + 6 zone-lead slots with `assignee_user_id: NULL`, stored as JSON in `eventshift_departments.metadata.roles[*].callsign_slots`. The admin UI turns those JSON slots into operable rows.

MVP-1 = admin panel only. MVP-2 = volunteer-facing shift board + check-in (separate handoff, do NOT build in this pass).

Figma wireframes rendered in file `V7KLwTfxfOzj0Uoy11ZpuH` (5 frames: Events List / Event Detail WUF13 / Department Blueprint / Areas & Units / Slot CRUD Modal). Treat Figma as visual truth; this section is code truth. If they disagree, code wins and Terminal-Atlas flags the Figma drift to Cowork-Atlas.

### SCOPE (what to build, in order)

Build five routes under `apps/web/src/app/[locale]/admin/eventshift/` behind org-admin RBAC check. Use shadcn/ui + TanStack Query + Zustand as per `.claude/rules/frontend.md`. No new dependencies.

1. **`/admin/eventshift`** — Events list. Tabs: ALL / PLANNING / LIVE / ARCHIVED. Table cols: event / dates / departments / slots (filled/total + bar) / status chip. One primary CTA top-right: `+ New event`. Empty state = "No events yet in this org. Create the first to start planning." No spinner — skeleton rows matching the row shape.

2. **`/admin/eventshift/events/[id]`** — Event detail. Header: name + date range + tenant chip. Meta chip row. Department tabs horizontal. Active dept card shows mission, 5 stat tiles (roles / slots / SOPs / FAQ / KPIs), coverage progress bar, first 5 slot rows with `[Edit · Rotate · Remove]` inline actions, "+ N more slots" link. Right column: coverage gap alert (purple, not red) + bulk-assign CTA, blueprint card with "Open blueprint →" link.

3. **`/admin/eventshift/departments/[id]/blueprint`** — Full blueprint. Left sidebar sections: Mission / KPIs / Roles & Slots (default active) / Competencies / SOPs / Policies / Metrics / Training / FAQ. Main column shows Tier 1 director rows, then Tier 2 zone-lead rows (2-col grid). Each row has `[Assign] [Edit] [Rotate] [Remove]` inline. Top-right: primary `+ Add slot`, secondary `Edit blueprint`.

4. **`/admin/eventshift/events/[id]/areas`** — 3×2 grid of zone cards. Each card: callsign chip, zone name, `X / Y slots filled` text, coverage bar (purple <30%, amber <70%, success ≥70% — NEVER red), SHIFT UNITS list with 2 rows per zone, `+ Add shift unit` at bottom.

5. **Slot CRUD modal** — Reusable `<SlotEditor />` component (not a route). Opens on: click slot row → modal. Fields: role title / callsign / tier / assignee picker / rotation-from picker / notes / history (read-only audit). Action bar: `[Cancel]` (ghost) · `[Remove slot]` (purple danger) · `[Save & assign]` (primary). When "Remove" is clicked, show inline confirmation inside the same modal ("Remove slot GSE-0? This writes a remove event to character_events. Reversible within 7 days via audit log.") — do NOT use browser confirm().

### API CONTRACT (add these endpoints; existing ones already implemented)

Current state in `apps/api/app/routers/eventshift.py` (confirmed via grep): events have full CRUD including soft-delete; departments/areas/units/assignments have GET+POST+PUT but are MISSING DELETE. Rotation is also missing. Add these six endpoints in the same router file, same per-request `Depends()` pattern, same `_emit_event()` helper for `character_events`.

```python
@router.delete("/departments/{department_id}", status_code=204)
async def delete_department(department_id: UUID, db: SupabaseUser, org_id: OrgId, user_id: CurrentUserId):
    # 1. select → verify org_id match → 404 if not found in this org
    # 2. soft-delete: UPDATE set status='archived' (do NOT hard-delete — SOP/FAQ history survives)
    # 3. emit character_events type='eventshift_department_archived'
    # 4. return 204

@router.delete("/areas/{area_id}", status_code=204)
async def delete_area(area_id: UUID, db: SupabaseUser, org_id: OrgId, user_id: CurrentUserId):
    # same pattern, emit 'eventshift_area_archived'

@router.delete("/units/{unit_id}", status_code=204)
async def delete_unit(unit_id: UUID, db: SupabaseUser, org_id: OrgId, user_id: CurrentUserId):
    # same pattern, emit 'eventshift_unit_archived'
    # if unit has active assignments → return 409 CONFLICT with detail={"code":"UNIT_HAS_ASSIGNMENTS","message":"..."}

@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(assignment_id: UUID, db: SupabaseUser, org_id: OrgId, user_id: CurrentUserId):
    # hard-delete IS allowed here (unassign a volunteer); emit 'eventshift_assignment_removed'

@router.post("/assignments/{assignment_id}/rotate", response_model=UnitAssignmentResponse)
async def rotate_assignment(assignment_id: UUID, payload: RotatePayload, db, org_id, user_id):
    # payload: { target_unit_id: UUID, reason?: str }
    # 1. load assignment → verify org_id
    # 2. UPDATE assignment SET unit_id = payload.target_unit_id, rotated_from_unit_id = <old>, rotated_at = now()
    # 3. emit 'eventshift_rotation' with {from: old_unit, to: new_unit, reason}
    # 4. return updated row

# Slot-level CRUD lives INSIDE departments.metadata.roles[*].callsign_slots (JSON array).
# One endpoint covers all 4 slot ops via a patch-set primitive:
@router.patch("/departments/{department_id}/slots", response_model=DepartmentResponse)
async def patch_department_slots(
    department_id: UUID,
    payload: SlotPatchPayload,  # {op: 'add'|'remove'|'edit'|'rotate', role_key: str, slot_index?: int, slot?: SlotSpec, target_role_key?: str}
    db, org_id, user_id,
):
    # 1. Load department metadata → verify org_id → deep-copy roles array
    # 2. Resolve target role by role_key (e.g. 'director', 'zone_lead')
    # 3. Apply op:
    #    - add: append to roles[i].callsign_slots with new callsign (validate uniqueness inside the dept)
    #    - remove: splice(slot_index, 1) + write event if assignee_user_id was set
    #    - edit: merge patch into roles[i].callsign_slots[slot_index]
    #    - rotate: pop from source, push to target_role_key slots, carry assignee across
    # 4. UPDATE eventshift_departments SET metadata = jsonb_set(...) RETURNING *
    # 5. emit character_events with type='eventshift_slot_' + op
    # 6. Return updated department
```

RPC shape for rotate events (`character_events` table, existing schema):
```json
{
  "source_product": "eventshift",
  "event_type": "eventshift_slot_rotate",
  "org_id": "<org>",
  "user_id": "<admin_performing_action>",
  "payload": {"department_id": "...", "from_role": "director", "from_index": 1, "to_role": "director", "to_index": 0, "assignee_user_id": "<volunteer>", "reason": "..."}
}
```

### TOKENS (from `apps/web/src/app/globals.css` — do NOT define new ones)

- Surface: `var(--surface)` #0f0f17 base, `--surface-container-lowest` #13131b for cards
- Primary accent (VOLAURA): `var(--volaura-accent)` #7C5CFC — one primary CTA per screen
- Error (Law 1 — never red): `var(--error-container)` purple #d4b4ff for destructive copy
- Warning: `var(--warning)` amber #e9c400
- Success: `var(--success)` #6ee7b7
- Muted text: `var(--on-surface-variant)` #9898A8
- Focus ring: `var(--focus-ring)` white — WCAG 2.2 fix

### DEFINITION OF DONE

1. All 5 routes render real data from the API, no mock unless API fails → show error card.
2. The 6 new API endpoints exist in `eventshift.py`, each with: org_id check via `OrgId = Depends()`, at least one happy-path test, one RLS test (other org returns 404), one `character_events` emission test.
3. Every mutation emits a `character_events` row with correct `source_product='eventshift'`. No silent mutations.
4. No red anywhere — grep `grep -rn "red-\|#EF4444\|#DC2626\|#FF0000" apps/web/src/app/[locale]/admin/eventshift/` must return zero matches.
5. One primary CTA per screen — scan each route, flag if two `bg-volaura-accent` buttons appear in the same viewport.
6. Energy modes Full/Mid/Low — at minimum: Low hides the coverage-gap alert and the stat grid, shows slot list only; Mid keeps entrance transitions but kills hover; Full is default.
7. Skeleton loaders (shape-matched), never `<Loader2 className="animate-spin" />`.
8. AZ + EN i18n — every visible string goes through `t()`. AZ strings tested with `ə ğ ı ö ü ş ç` at all weights.
9. RBAC: route guard checks `auth.user.org_memberships[org_id].role IN ('owner','admin')`. Non-admin redirects to `/[locale]/dashboard` with flash.
10. `pnpm --filter=web tsc --noEmit` clean; `pnpm --filter=api pytest -q apps/api/tests/test_eventshift.py` passes new endpoint tests.

### FILES TO CREATE (paths, not full code)

```
apps/web/src/app/[locale]/admin/eventshift/page.tsx                  # Events list route
apps/web/src/app/[locale]/admin/eventshift/events/[id]/page.tsx      # Event detail
apps/web/src/app/[locale]/admin/eventshift/events/[id]/areas/page.tsx
apps/web/src/app/[locale]/admin/eventshift/departments/[id]/blueprint/page.tsx
apps/web/src/app/[locale]/admin/eventshift/layout.tsx                # RBAC guard + nav rail
apps/web/src/components/features/eventshift/EventTable.tsx
apps/web/src/components/features/eventshift/DepartmentCard.tsx
apps/web/src/components/features/eventshift/SlotRow.tsx
apps/web/src/components/features/eventshift/SlotEditor.tsx           # modal with add/remove/edit/rotate
apps/web/src/components/features/eventshift/CoverageGapAlert.tsx
apps/web/src/components/features/eventshift/ZoneCard.tsx
apps/web/src/lib/hooks/useEventShiftEvents.ts                        # TanStack Query wrapper
apps/web/src/lib/hooks/useEventShiftDepartment.ts
apps/web/src/lib/hooks/useSlotMutations.ts                           # calls patch_department_slots
apps/web/src/stores/eventshift-admin-store.ts                        # Zustand: activeDept, activeSlot, modalOpen
apps/api/app/routers/eventshift.py                                   # EDIT: add 6 endpoints listed above
apps/api/tests/test_eventshift_crud.py                               # NEW: tests for delete + rotate + slot patch
apps/web/public/locales/az/eventshift.json                           # NEW i18n bundle
apps/web/public/locales/en/eventshift.json
```

### DESIGN GATES (blocking; if violated → do not merge)

Read `docs/design/DESIGN-MANIFESTO.md` and `.claude/rules/ecosystem-design-gate.md` first. Then during build:

- Q1 Skeleton-or-skin: this is skeleton (admin chrome) + VOLAURA skin (primary accent). Do not invent new tokens.
- Q2 Face ownership: VOLAURA owns admin. No MindShift/LifeSim copy or palette bleed.
- Q3 Energy modes: implement Low-mode path at least behind a feature flag before ship; full polish optional.
- Q4 Event bus: every CRUD writes to `character_events`. Silent UI = dead UI.

Anti-pattern check before PR: run `grep -rn "Loader2\|#ef4444\|completion.*%\|streak" apps/web/src/app/\[locale\]/admin/eventshift/` — must be zero.

### COORDINATION

When you start this task:
1. Write one line to `.claude/breadcrumb.md`: `last action: started EventShift admin MVP-1 skeleton, next step: <route name>`.
2. Append a progress section here when you ship a milestone. Use header `### SESSION <N> PROGRESS — <timestamp> Baku`.
3. If blocked >15 min on one issue, write `BLOCKED: <what I tried, what's missing>` to breadcrumb and pause. Cowork-Atlas reads breadcrumb each tick.
4. Do NOT build MVP-2 (volunteer view, check-in, shift board) in this pass. That is the next handoff.
5. Do NOT touch MindShift or VOLAURA landing while this is in flight — orthogonal tracks, separate PRs.

### FIRST ACTION

Run `python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('Asia/Baku')).strftime('%Y-%m-%d %H:%M %A'))"`, record the result, then read `apps/api/app/routers/eventshift.py` lines 1-200 to absorb the per-request `Depends()` pattern before writing the first endpoint.

— Cowork-Atlas, 2026-04-17 17:30 Baku

