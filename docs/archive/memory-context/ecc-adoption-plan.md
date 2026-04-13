# Everything-Claude-Code — Adoption Plan
# Repo: https://github.com/affaan-m/everything-claude-code
# Analyzed: 2026-03-26
# AGENT VERDICT (3 agents, 2026-03-26): DEFER ALL until after Sprint 9 ships CSV + codegen
# Product score: 3/10 — "process over product, ship features first"

---

## VERDICT: NOT a replacement for our protocol. A peer system.
## ECC is more mature in: hook orchestration, verification loops, security scanning
## We are more mature in: agent coordination (roster.md, swarm), DSP, memory

---

## MUST HAVE — Adopt this sprint or next

### 1. Verification Loop (6-phase pre-PR gate)
- **What:** Build → Type check → Lint → Test → Security → Diff review
- **Our gap:** Hooks exist but no unified pre-PR checklist
- **Action:** Create `docs/engineering/skills/VERIFICATION-LOOP.md`
- **ECC source:** `.agents/skills/verification-loop/SKILL.md`

### 2. Strategic Compaction
- **What:** Explicit task boundaries for context management (not just token triggers)
- **Our gap:** Compaction timing is ad-hoc; we lose context mid-sprint
- **Action:** Add Step C.5 to CLAUDE.md Phase C: "COMPACTION CHECKPOINT"
- **ECC source:** `.agents/skills/strategic-compact/SKILL.md`

### 3. Deep Research (6-step methodology)
- **What:** Clarify → Plan → Source → Read → Synthesize → Deliver
- **Our gap:** research-first.md rule exists but no structured 6-step method
- **Action:** Expand `~/.claude/rules/research-first.md` with 6-step structure
- **ECC source:** `.agents/skills/deep-research/SKILL.md`

### 4. TDD Gate (80% coverage enforcement)
- **What:** Red→Green→Refactor with hard 80% coverage gate before merge
- **Our gap:** TDD mentioned in skills matrix but no enforcement
- **Action:** Add coverage gate to `docs/engineering/skills/TDD-WORKFLOW.md`
- **ECC source:** `.agents/skills/tdd-workflow/SKILL.md`

---

## NICE TO HAVE — Post-launch

### 5. Instinct Management
- **What:** Auto-update patterns.md from session outcomes (vs. manual)
- **ECC source:** `.claude/homunculus/instincts/`
- **Our version:** mistakes.md + patterns.md (manual). Upgrade later.

### 6. AgentShield (102 adversarial rules)
- **What:** Red-team/blue-team continuous security scanning
- **Our version:** security-review skill (manual). Upgrade for v2.

### 7. fileEdited Hook
- **What:** Auto-run lint + type-check on .ts/.py saves
- **ECC source:** `.kiro/hooks/`
- **Action:** Add to `.claude/hooks/` when hook v2 is designed

---

## ALREADY HAVE (confirmed by ECC analysis)

- Backend patterns (FastAPI, Supabase per-request) ✅
- API design (OpenAPI + @hey-api/openapi-ts) ✅
- Frontend patterns (shadcn, Zustand, TanStack Query) ✅
- Security review skill ✅
- Memory system (sprint-state, mistakes, patterns) ✅
- Agent coordination (roster.md, swarm, DSP) ✅ — MORE advanced than ECC

---

## NOT RELEVANT

- Market research / investor materials (not our stage)
- Twitter/X API crossposting (we use LinkedIn)
- Conventional commits enforcement (we commit manually)

---

## STATUS

- [ ] Verification Loop skill → create docs/engineering/skills/VERIFICATION-LOOP.md
- [ ] Strategic Compaction → add to CLAUDE.md Phase C
- [ ] Deep Research → expand research-first.md
- [ ] TDD Gate → add 80% coverage gate to TDD-WORKFLOW.md
