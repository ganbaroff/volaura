# Acceptance Criteria Template

**Use:** Copy for every task BEFORE coding starts (Step 1.5).
**Rule:** No AC = task cannot enter batch.

---

## Task: [name]
**Level:** [L1-L5]
**Owner:** [agent/CTO]

### DONE WHEN:

1. [ ] [Specific testable condition — PASS/FAIL, no ambiguity]
2. [ ] [Second condition]
3. [ ] [Third condition]
4. [ ] [Fourth if needed]
5. [ ] [Fifth if needed]

### NOT IN SCOPE:
- [What this task does NOT include]

### VERIFICATION METHOD:
- [ ] Preview screenshot
- [ ] API curl test
- [ ] Unit test
- [ ] Manual walkthrough
- [ ] Agent review

---

## Example (good):

### Task: Add assessment verification page
**DONE WHEN:**
1. [ ] GET /api/assessment/verify/{session_id} returns 200 with score, badge, competency
2. [ ] Page renders at /u/{username}/verify/{sessionId} with badge color and score
3. [ ] 404 shows for invalid session_id
4. [ ] No auth required (public page)
5. [ ] i18n keys exist in both en.json and az.json

## Example (bad — too vague):

### Task: Add verification page
**DONE WHEN:**
1. [ ] Page works ← NOT TESTABLE
2. [ ] Looks good ← NOT MEASURABLE
3. [ ] API returns data ← WHAT DATA?
