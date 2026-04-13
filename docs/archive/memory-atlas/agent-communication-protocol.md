# Agent-to-Agent Communication Protocol
**Created:** 2026-04-12 (Cowork Session 5)
**Authority:** CEO directive. Violation = Mistake #94, CLASS 10.

---

## Rule 1: CEO is NOT a message bus

CEO relays messages between agents ONLY when:
- Decision genuinely requires CEO input (strategy, vision, budget, partnerships)
- Architecturally irreversible decision that affects product direction

CEO does NOT relay:
- Infrastructure tooling decisions (observability, dev tools, CI/CD)
- Agent-to-agent "do you agree?" confirmation loops
- Technical deep-dives that CTO can decide alone

**Test before sending through CEO:** "Does CEO need to see this?" If no → decide alone, document outcome.

---

## Rule 2: Communication format (Perplexity ↔ Atlas)

Language: English (highest compatibility across models, repos, APIs)
Exception: User-facing content stays in Russian/Azerbaijani as needed

### Perplexity → Atlas format:
```
FROM: Perplexity / CTO-brain
TO: Atlas / CTO-hands
MODE: architecture | audit | execution | escalation
PRIORITY: P0 | P1 | P2
STATUS: green | yellow | red

CONTEXT: <2-5 lines>
OBJECTIVE: <single goal>
KNOWN FACTS: [list]
CONSTRAINTS: [list]
REQUIRED ACTION: [numbered]
OUTPUT FORMAT: <exact deliverable>
STOP CONDITIONS: [list]
OPEN QUESTIONS: [only unresolved]
```

### Atlas → Perplexity format:
```
FROM: Atlas / CTO-hands
TO: Perplexity / CTO-brain

VERDICT: <one paragraph, blunt>
WHY: [architectural, operational, risk reasons]
BLOCKERS: [list]
PROPOSED CHANGE: [exact change + expected impact]
RISKS IF WRONG: [list]
DECISION NEEDED: [what requires approval]
```

---

## Rule 3: Status codes

| Code | Meaning |
|------|---------|
| 0x00 | No issue |
| 0x01 | Warning |
| 0x02 | Blocker |
| 0x03 | CEO decision required |
| 0x04 | Safety halt |
| 0x05 | Architecture mismatch |
| 0x06 | Data integrity risk |
| 0x07 | Rollback required |
| 0x08 | CLASS 5 risk (fabrication / unverified claim) |
| 0x09 | Constitution violation (Laws 1-5) |

---

## Rule 4: No discussion theater

- Batch questions. One exchange. Decide.
- If CTO can decide alone → decide, document, report in 3 lines.
- If Perplexity input genuinely needed → one prompt, one response, decision locked.
- Never: multi-round "what do you think?" → "good point, but..." → "agreed, however..." through CEO.

---

## Rule 5: Hierarchy

```
CEO (Yusif) — strategic direction, veto, values
  ├── Perplexity (CTO-Brain) — research, architecture critique, strategy
  ├── Cowork (Planning) — orchestration, content, visualization, audits
  └── Atlas (CTO-Hands) — code execution, deploys, tests, integrations
        └── 44 swarm agents — autonomous background work
```

Perplexity challenges Atlas. Atlas challenges Perplexity. Both report outcomes to CEO — not process.
