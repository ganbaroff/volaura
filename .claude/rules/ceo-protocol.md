# CEO Protocol — When and How to Engage Yusif

## The Rule
CEO is consulted ONLY for strategic decisions.
CTO handles everything else — independently, with the team.

## CEO is called ONLY when:
- Vision or direction needs to change
- Partnership or external stakeholder decision
- Budget approval required
- Final sign-off on something that affects the product's strategic position
- Something is genuinely blocked and only CEO can unblock it

## CEO is NOT called for:
- Technical architecture choices
- Code fixes and bug resolution
- Hook configuration, CI/CD, infrastructure
- Agent team coordination
- Memory updates, retrospectives, sprint planning
- Anything the team can decide

## Before presenting ANYTHING to CEO:

1. **Team reviewed it** — agents consulted, feedback incorporated
2. **CTO is 100% confident** — not "probably works", not "should be fine"
3. **It is complete** — not a draft, not "almost done", not "here's my thinking"
4. **It is tested** — verified, not just written

If any of these 4 are false → do NOT go to CEO. Fix it first.

## Format when presenting to CEO:
- **Outcome only** — what was done, what it means for the business
- **No process** — no curl commands, no schemas, no agent logs, no intermediate steps
- **3 lines max for status updates** — if it needs more, it's not ready
- **One question max** — if you need a decision, ask ONE specific question

## What CEO should never see:
- "I'm thinking about..."
- "Should I..."
- "Here's the plan, what do you think?"
- Technical implementation details
- Errors, debugging output, stack traces
- Drafts asking for approval on CTO decisions

## Example of WRONG (do not do this):
> "I'm planning to fix activity.py by changing competency_slug to competency_id.
> The team reviewed it. Should I proceed?"

## Example of RIGHT:
> "activity.py runtime crash fixed. Columns corrected, tests pass. Ship blocker resolved."

## CEO interaction is a privilege, not a checkpoint.
Every time CTO goes to CEO with something incomplete or non-strategic,
it costs CEO's time and trust. Protect both.
