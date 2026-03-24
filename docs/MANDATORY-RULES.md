# Volaura — MANDATORY RULES v1.0

**Created:** 2026-03-25 | **Source:** Mega-retrospective (3 parallel agents + CTO synthesis)
**Authority:** CEO-approved. These rules CANNOT be overridden by any session, sprint, or agent.
**Violation:** Any violation must be logged in `docs/DECISIONS.md` with root cause.

---

## Rule 1: NO SOLO DECISIONS

**Every output > 10 lines affecting product, strategy, design, or content MUST pass agent review BEFORE creation.**

Check:
- [ ] Does this affect product/strategy/design/content? → agents review FIRST
- [ ] Did I get 3+ agent votes before writing? → yes required
- [ ] Is this an architecture decision? → MiroFish agents vote FIRST

**Enforcement:** If last sprint had a solo decision, next sprint's Step 0 must include acknowledgment.
**Source:** Feedback from Sessions 5, 10, 11, 14c, 15. CEO direct order after CTO scored 22/50.

---

## Rule 2: MEMORY RECOVERY IS VISIBLE

**Before ANY sprint work, print this exact block:**

```
▶ Session [N] resumed. Sprint [X], Step [Y]. Protocol v5.0 loaded.
Memory files read:
  ✓ sprint-state.md — [current position]
  ✓ mistakes.md — [N errors to avoid]
  ✓ patterns.md — [M patterns working]
Error classes to watch: [list top 3]
```

**Without this declaration — do NOT proceed to any work.**
**Source:** Sessions 1-14 showed 30-40% Step 0 compliance. Patterns repeated 4x (Mistakes #1, #6, #13, #14).

---

## Rule 3: TEST ON PRODUCTION URL

**Before closing a sprint, verify endpoints on the EXACT production URL you deployed to.**

```
POST-DEPLOY VERIFICATION
[ ] Deployed to: [exact URL from `railway status` or `vercel env ls`]
[ ] Tested against same URL: [curl output]
[ ] Endpoints tested: [minimum 3 — GET, POST, error case]
[ ] All passed? → close sprint
[ ] Any failed? → STOP. Fix before closing.
Written: "Tested against: [URL]. Endpoints: [N] passed."
```

**Production URLs (CANONICAL):**
- API: `https://modest-happiness-production.up.railway.app` (NOT volauraapi-production)
- Frontend: `https://volaura.app`

**Source:** 2+ hours wasted debugging wrong Railway endpoint. Session 14-15.

---

## Rule 4: SCHEMA VERIFICATION BEFORE DEPLOYMENT

**No new API endpoint ships without DB↔API field verification.**

```
SCHEMA VERIFICATION
[ ] Read: apps/api/app/schemas/[Model].py
[ ] Read: supabase/migrations/*.sql for table/function
[ ] Field names match: API field = DB column? (e.g., total_score ≠ overall_score)
[ ] Types match: string/int/timestamp/jsonb?
[ ] Written: "Schema verified against [files]. Mismatches: [none/list]."
```

**Source:** `overall_score` vs `total_score` caused 500. `is_verified` vs `verified_at` caused 500. Session 15.

---

## Rule 5: DELEGATE FIRST, DO LAST

**Before ANY task > 10 minutes, fill in:**

```
DELEGATION MAP
Task: [name]
Haiku agents: [what they'll do in parallel]
Research tool: [NotebookLM / Agent(Explore) / WebSearch]
CTO does: [only what agents cannot]
Model routing: [haiku for mechanical / sonnet for code / opus for architecture]
```

**If CTO is doing work that haiku can do → REDIRECT.**
**If research is needed → NotebookLM or Agent(Explore) FIRST, not CTO manually.**

**Source:** 2+ hours debugging solo instead of 3 parallel agents checking 4 URLs. Mega Feedback #1.

---

## Rule 6: SPRINT RETROSPECTIVE IS MANDATORY AND STRUCTURED

**After EVERY sprint, fill the template in `docs/SPRINT-REVIEW-TEMPLATE.md`.**

Minimum requirements:
- 5+ lines (not 3-line summaries)
- Specific outcomes vs DSP predictions
- Mistakes repeated: [list or "none"]
- New mistakes: [list or "none"]
- Model recommendation for next sprint

**"Sprint done" = code shipped + retrospective written. Not one without the other.**

**Source:** Agent #2 found 78% process compliance — retrospectives are the key gap.

---

## Rule 7: STATE PERSISTED DURING WORK (NOT AFTER)

**After EVERY deliverable, update memory IMMEDIATELY.**

```
Completed: [deliverable]
Updated: memory/context/sprint-state.md
Continuity: Next Claude can proceed because [state saved].
```

**Minimum frequency:** Every 30 minutes of active work.
**NEVER batch memory updates to "end of session."**

**Source:** Session 14b: 4+ hours, zero memory updates. Same bug as MiroFish pre-v4.

---

## How to Use This Document

1. **Session start:** Read this before CLAUDE.md
2. **Mid-sprint:** Check any rule that applies to current task
3. **Sprint end:** Verify all rules followed in retrospective
4. **New team member (agent):** Must read this as first file
5. **Rule violation:** Log in `docs/DECISIONS.md` with root cause + fix

---

## Changelog

| Version | Date | Change | Trigger |
|---------|------|--------|---------|
| v1.0 | 2026-03-25 | Initial 7 rules from mega-retrospective | CEO feedback + 3-agent RCA |
