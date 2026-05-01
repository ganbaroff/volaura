# False Positive Registry

Disproven claims. If agent repeats without NEW evidence → weight penalty.

| Date | Agent | Claim | Disproof | Evidence |
|------|-------|-------|----------|----------|
| 2026-05-01 | Ecosystem Auditor | Law 2 Energy Adaptation broken 4/5 products | 116 files with energy, EnergyPicker in assessment+dashboard | grep -rl useEnergyMode = 10+ files |
| 2026-05-01 | Security Auditor | Missing rate limit on /assessment/start | @limiter.limit(RATE_ASSESSMENT_START) line 181 | grep -n limiter assessment.py |
| 2026-05-01 | Scaling Engineer | Unbounded query /assessment/next | .limit(1) on lines 239,346,393. /next endpoint doesn't exist | grep -n limit assessment.py |
| 2026-05-01 | DevOps Engineer | Missing input validation for role_level | Pydantic Literal["professional","volunteer"] line 70 | grep -n role_level schemas/assessment.py |
| 2026-05-01 | Cultural Intelligence | Animation 2000ms in globals.css | Not found in globals.css | grep -n 2000 globals.css = empty |
| 2026-05-01 | Product Strategist | Score counter 2000ms violating Law 4 | Not found in globals.css | grep -n score.*counter globals.css = empty |
| 2026-04-30 | Multiple | Code-index builder broken | build_index() works, 1064 files indexed | python3 -c build_index |
