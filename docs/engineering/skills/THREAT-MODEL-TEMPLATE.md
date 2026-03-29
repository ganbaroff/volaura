# Proactive Threat Model Template

**Security Agent obligation:** Run this BEFORE every sprint that adds API endpoints, auth changes, or data access.

## Per-Sprint Threat Scan

```
SPRINT: [name]
NEW ENDPOINTS: [list or NONE]
SCHEMA CHANGES: [list or NONE]
AUTH CHANGES: [list or NONE]

THREAT ANALYSIS:

1. INJECTION VECTORS:
   □ Any new user input? → How is it validated? (Pydantic? Raw?)
   □ Any new SQL? → Parameterized or string concat?
   □ Any new LLM prompts with user content? → Prompt injection risk?

2. AUTH/AUTHZ:
   □ New endpoints protected? → @limiter + CurrentUserId?
   □ Ownership checks? → Can user A access user B's data?
   □ RLS policies added for new tables?

3. DATA EXPOSURE:
   □ New fields returned to client? → Any PII? Timestamps? Internal IDs?
   □ Public endpoints return minimal data? → No last_updated, no raw scores?
   □ Error messages leak internals? → Stack traces, DB names?

4. RATE LIMITING:
   □ New endpoints have rate limits?
   □ Shared IP scenario (50 users at event) → will they get blocked?
   □ Rate limits survive Railway restart? (in-memory = NO)

5. ECOSYSTEM BLAST:
   □ Does this change affect MindShift/BrandedBy/Life Sim/ZEUS?
   □ character_events new event types validated?
   □ Cross-product JWT scope still correct?

FINDINGS: [list specific risks with CVSS estimate]
MITIGATIONS: [what to add to sprint plan]
```

## Quarterly Deep Scan

Every 4 sprints, Security Agent runs full scan:
- All RLS policies vs current schema
- All rate limits vs current traffic estimates
- All LLM prompt templates for injection surface
- All external API keys: rotation needed? Scope correct?
- Dependency audit: any vulnerable packages?
