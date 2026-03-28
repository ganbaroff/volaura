# Recursive Criticism — Standard Protocol

**Version:** 1.0 | **Added:** 2026-03-28 (Session 57)
**Why it exists:** Sprint Plan V2 was created this way (3 rounds) and found 10 critical failures that single-pass planning missed. CEO confirmed: "рекурсивная критика должна стать стандартом."

---

## What It Is

Recursive criticism is mandatory multi-round attack on any plan before execution. Each round produces a revised plan. The plan ships only when it survives a round without new critical findings.

**The core rule:** A plan that no one can break is a plan worth executing. A plan that breaks in review will break in production.

---

## When to Use

| Trigger | Rounds Required |
|---------|----------------|
| Sprint plan (new sprint) | 2 rounds minimum |
| Architecture decision (High/Critical) | 2 rounds minimum |
| Feature design (new user flow) | 1 round minimum |
| Pricing / B2B strategy | 2 rounds minimum |
| Security-affecting change | 1 round minimum (Security Agent) |

---

## Protocol (3 Rounds Max)

### Round 1 — Parallel Attack
- Launch ALL relevant personas/agents simultaneously
- Each persona attacks from their own perspective with SPECIFIC references (files, endpoints, user flows)
- Each persona: 3-5 concrete failure modes, not vague concerns
- No persona may say "looks good" — if they find nothing, they are not looking hard enough

### Round 2 — Synthesized Plan Under Attack
- CTO synthesizes Round 1 findings into a revised plan
- Launch Round 2 attack on the REVISED plan
- Focus: did the fixes create new problems? Were root causes addressed or just symptoms?

### Round 3 (only if Round 2 finds Critical issues)
- If Round 2 finds no Critical issues → plan approved
- If Round 2 finds Critical issues → revise + Round 3
- If Round 3 still finds Critical → escalate to CEO (plan is fundamentally broken)

---

## Persona Routing

| Plan type | Mandatory personas |
|-----------|-------------------|
| Sprint plan (any) | All 9 personas |
| B2B feature | Aynur + Sales Deal Strategist + Sales Discovery Coach |
| UX/onboarding | Leyla + Rauf + Behavioral Nudge Engine + Cultural Intelligence |
| Security | Attacker + Security Agent |
| Professional features | Kamal + Aynur + Rauf + LinkedIn Content Creator |
| Assessment | Leyla + Rauf + QA Engineer + Behavioral Nudge Engine |

---

## Output Format

Each round produces:
```
## Round [N] — [N] Critical, [N] High, [N] Medium found

| Finding | Persona | Severity | Specific Reference |
|---------|---------|----------|-------------------|
| [what breaks] | [who found it] | CRITICAL/HIGH/MED | [file/endpoint/flow] |

## Revised Plan After Round [N]
[what changed]
```

Round is complete when:
- No new Critical findings
- All High findings have a mitigation
- Medium findings are logged for future sprints

---

## Anti-Patterns

- "This looks fine" — not a valid response. Find something or you're not looking.
- Vague criticism ("UX could be better") — must reference specific flow/component
- Persona-hijacking (Security Agent commenting on UX copy) — stay in lane
- Round 1 findings ignored in Round 2 plan — must show what changed

---

## Integration with DSP

Recursive criticism IS the stress-test phase of DSP (Step 3). For any High/Critical decision:
1. Generate paths (DSP Step 2)
2. Run Recursive Criticism on winning path (this protocol)
3. Only proceed when plan survives

---

*Added to Skills Matrix in CLAUDE.md under: "Sprint planning, architecture decisions, B2B strategy"*
