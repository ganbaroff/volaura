# Best Practices — Volaura Team

**Created:** 2026-03-25
**Purpose:** What works, what doesn't. Read before any plan or sprint.
**Source:** Agent reviews, CEO feedback, CTO mistakes.

---

## Planning Best Practices

### 1. User value from step 1
Before designing any feature, ask: "Does the user get value from the FIRST action?"
- BAD: User takes test → result hidden → user clicks share → recruiter sees it (3 steps to value)
- GOOD: User takes test → recruiter sees badge immediately (1 step to value)
- Rule: If user needs >1 action to get value, redesign.

### 2. Data lifecycle before schema
Before adding any table/column, answer: "Where does the initial data come from?"
- BAD: `role_percentile_curves` table exists but is empty at launch → scoring breaks
- GOOD: Bootstrap with theoretical values, label "Estimated", replace with real data at N=50
- Rule: Empty table = broken feature. Plan the seed.

### 3. Inter-actor flows before API design
Don't design endpoints for actors in isolation. Map: "Actor A does X → Actor B sees Y → Actor B does Z."
- BAD: "Volunteer shares score" + "Org sees score" designed separately → no consent model between them
- GOOD: Map the handshake: volunteer grants access → org receives → org acknowledges → volunteer can revoke
- Rule: If two actors interact with the same data, there's a permission flow. Design it.

### 4. Back-of-envelope math before JSONB
Before storing rich data (logs, eval results), calculate: rows/year × size/row = total storage. Compare to budget.
- BAD: "Store full LLM rationale per answer" sounds good. 1.5KB × 30 answers × 100K users = 4.5GB/year.
- GOOD: Archive to R2 after 30 days, keep summary (200B) in DB.
- Rule: Any JSONB column needs a napkin calculation before design.

### 5. Add 50% buffer to time estimates
CTO consistently underestimates by 30-50%. Every estimate needs explicit buffer for: edge cases, testing, migrations, debugging.
- BAD: "7 sessions" → reality is 11
- GOOD: Calculate base estimate → multiply by 1.5 → present THAT number
- Rule: The estimate you're confident about is 66% of reality.

### 6. Cost modeling at 10x and 100x
Before shipping, calculate monthly cost at 10x and 100x current users. If budget breaks → add archival/cleanup before launch.
- BAD: "Free Supabase tier is enough" → breaks at 3K users ($25/mo) without archival
- GOOD: Table showing cost per user tier, with action items at each breakpoint

---

## Product Best Practices

### 7. Public by default for value-generating data
If the product's value IS visibility (badges, scores, credentials), hiding by default kills adoption.
- Privacy by default = good for medical data
- Privacy by default = death for credential platforms
- Rule: Default = maximum value. Offer hide option for exceptions.

### 8. Same ruler for everyone, role reports as supplement
Users and orgs need ONE comparable score across all roles + role-specific context.
- BAD: "Coordinator 85 ≠ Manager 85" → nobody trusts the number
- GOOD: Global score (85 = 85 for everyone) + "As a coordinator, you're in top 15% of coordinators"
- Rule: Dual scoring. Global for comparison, role-specific for context.

### 9. Org-assigned roles, not self-selected
Self-selection = gaming. Org assigns role at invite time. User can request change with explanation.
- Exception: Solo users (not invited by org) self-select.
- Rule: Whoever has authority assigns the role.

### 10. No black boxes — explain every score
"Why this score?" is not optional. It's the brand.
- Per-competency breakdown minimum. Per-answer breakdown in v1.1.
- Methodology references required (ISO, BARS, Heckman).
- User can add comments if they disagree — not ignored, logged.

### 11. k-anonymity for small groups
Org with <5 members: hide aggregate stats entirely.
Tier counts <3: merge with adjacent tier.
Never let aggregate data identify individuals.

---

## Engineering Best Practices

### 12. Archive before accumulate
Any data that grows linearly with users (logs, evaluations, history) needs an archival strategy BEFORE it ships.
- Hot storage: last 30 days (DB)
- Cold storage: older than 30 days (R2/S3)
- Retention: 12 months max for non-essential data

### 13. RLS is not enough — test the boundaries
Write explicit tests: "User A cannot see User B's data." "Org admin cannot see non-opted-in scores."
- Every RLS policy needs a corresponding test
- Every new table needs RLS enabled before any data enters

### 14. Retake flows need specification
Every assessment system needs answers for:
- Can user retake immediately? (No: 24h cooldown)
- Which score shows on leaderboard? (Latest)
- What happens to old scores? (Superseded, visible in history)
- What if new score is lower? (Show variance context, not red numbers)

### 15. Security mitigations before launch, not after
Attacker found 2 CRITICAL vulnerabilities in 60 seconds of reading the plan. Always run attacker review on design, not just on code.

---

## Process Best Practices

### 16. Agent review BEFORE presenting to CEO
Plans >10 lines → agents critique FIRST → fix → then present. Not: present → agents later → oops.

### 17. "Запомнил" without file write = lie
Any lesson, pattern, or decision exists only if it's in a file. Context compacts. Chat disappears. Memory files are the only truth.

### 18. Honest assessment > flattery
No superlatives unless backed by comparative data. "Strong" with evidence. "Weak" with evidence. No sugar.

### 19. Ideas in chat → IDEAS-BACKLOG.md within 5 minutes
CEO shares strategic insight → save to backlog immediately. Don't write 500 words in chat and ask "what's next?"

### 20. Evaluate people by THEIR role
Vision leaders → vision metrics. Technicians → tech metrics. Never penalize someone for not having skills outside their role.

### 21. CTO acts, CEO gets results
If plan is approved and no blockers exist → START. Don't ask CEO "should I begin?" That's your job.
- CEO sees: "Phase 1 done. Here's what changed. Here's what's next."
- CEO does NOT see: "Should I start Phase 1 or Phase 2?" / "Do you want to discuss first?"
- Rule: Report outcomes, not options. Technical decisions are CTO's job.
