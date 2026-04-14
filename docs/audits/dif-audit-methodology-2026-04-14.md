# DIF Audit Methodology — Pre-Launch Readiness

**Date:** 2026-04-14
**Scope:** Preparation doc for E4 task 2 (`memory/atlas/inbox/2026-04-14T0734-epic-E4-constitution-p0.md`).
**Status:** Methodology locked; execution blocked on live response data. This doc tells a future Atlas (or a human psychometrician) exactly how to run the audit the day we have data.

## Why this doc exists now

E4 task 2 asks for a DIF audit with per-item scores in `docs/audits/dif-audit-2026-04.md`. But Differential Item Functioning is a **statistical test on response data** — you need users answering questions across groups before DIF has any meaning. VOLAURA is pre-launch. Zero users. Zero responses. No DIF is computable.

What we CAN do now: lock the method, pre-register group definitions, and pre-declare the pass/fail thresholds. Methodology set BEFORE data prevents the "cherry-pick the statistical model to pass the audit" failure mode that kills assessment platforms.

## Method: Mantel-Haenszel DIF with ETS thresholds

We use the Mantel-Haenszel (MH) procedure because it's the standard that EEOC + ISO 10667-2 auditors know. Alternative models (logistic-regression DIF, IRT-DIF via lordif) add complexity without improving defensibility at our scale. Start simple, escalate only if MH flags items we need to litigate.

### Focal vs reference groups

Pre-registered groups (locked before data collection to prevent post-hoc gerrymandering):

| Group type | Reference (most examinees) | Focal (comparison) |
|------------|---------------------------|--------------------|
| Language | AZ native responders | RU native responders |
| Language | AZ native responders | EN native responders |
| Gender | Male respondents | Female respondents |
| Age band | 25–34 | 18–24 |
| Age band | 25–34 | 35+ |
| Geography | Baku | Other AZ cities |
| Device | Mobile | Desktop |

Each pair is analyzed separately. A single item can be flagged DIF under one partition and clean under another — that's diagnostic, not a bug.

### Minimum data requirements (pre-condition)

- **Per item:** ≥ 200 responses total, ≥ 50 in each group.
- **Per competency:** ≥ 15 items all meeting the per-item minimum.
- Below this, DIF statistics are noise. Abort and wait for more data.

### ETS classification

After computing MH Δ (delta) statistic per item:

| Category | ETS threshold | Action |
|----------|--------------|--------|
| A (negligible) | \|Δ\| < 1.0 AND p > 0.05 | ship |
| B (moderate) | 1.0 ≤ \|Δ\| < 1.5 OR p < 0.05 with \|Δ\| < 1.5 | flag for review, don't ship as-is |
| C (large) | \|Δ\| ≥ 1.5 AND p < 0.05 | **remove or reword, do not ship** |

The E4 brief says "flag items with DIF > 0.4 for review; remove or reword 3 worst." That maps cleanly: 0.4 in the brief ≈ category B in ETS. "3 worst" means the top 3 |Δ| values across all partitions.

## Pre-flight: qualitative bias scan (doable NOW, no data needed)

Before a single user sees a question, the assessment-science-agent skill already commits us to these pre-conditions. Extract them into a 1-hour manual pass:

1. **Translation parity** — every question has AZ/RU/EN versions. For each competency item:
   - Read all 3 translations back-to-back
   - Flag translations that change difficulty (different cultural frame of reference)
   - Flag translations that change specificity (e.g., "leadership" → "boss-behavior" in AZ would narrow the construct)
   - Tool: Cowork + a native speaker for AZ, LLM for initial draft
2. **Cultural-frame review** — any question assuming specific institutional context (Western corporate norms, specific software), reword or split per region.
   - Example: "How would you handle a 360 review?" assumes 360-review culture exists. Replace with scenario-level wording.
3. **Gender-coded language** — scan for gendered role assumptions in Russian (most common failure mode in RU translations). "Начальник" vs "руководитель" carries different weight.
4. **Age-coded references** — scan for technology/pop-culture refs (Slack, Notion, remote work) that bias against older responders without that context.

Output: a spreadsheet with 120 rows (8 competencies × 15 items) × 4 review axes, with pass/fail per cell. Produces the same "items worth rewriting" list that MH-DIF will produce post-launch, ~6 months earlier.

## Output artifact when data arrives

File: `docs/audits/dif-audit-[YYYY-MM].md` — once per quarter.

Structure:
1. **Executive summary** — how many items in each ETS category A/B/C, by partition
2. **Category-C items table** — item ID, competency, partitions flagged, Δ statistic, p-value, proposed action (remove/reword)
3. **Category-B items table** — same, with "review in 1 quarter if still flagged" note
4. **Partition-level summaries** — is there a pattern (e.g., all gender-DIF items in the leadership competency)?
5. **Action log** — which items were removed, which were reworded, pre/post Δ where re-measured.

## Dependencies

- Response data stored in `assessment_responses` table with `user_id`, `item_id`, `response_value`, `is_correct`, `theta_estimate`.
- Demographic fields on user profile: `language`, `gender` (optional), `birth_year`, `city`, `device_class`. These exist partially — `language` is set via locale, `gender` is NOT currently collected (requires explicit consent), `city` is coarse.
- For any partition that relies on self-reported demographics, **the consent path must explicitly say "we use this to check for fairness bias in scoring"** — required for GDPR Article 9 (special category data for gender) and ISO 10667-2 §7.

## Runtime: the audit itself

When data is ready (target: 3 months post-launch at Q1 volumes):

```python
# Pseudo-code; real implementation uses difR in R OR mhdif in Python
import pandas as pd
from difr import difMH  # or equivalent

responses = load_responses_matrix()
for item in competency_items:
    for (ref_group, focal_group) in GROUP_PAIRS:
        ref = responses[responses.group == ref_group]
        focal = responses[responses.group == focal_group]
        result = difMH(ref, focal, item=item)
        record(item, ref_group, focal_group, result.delta, result.p_value, classify_ets(result))
```

Export → the table structure above → commit to `docs/audits/`.

## Who can run this

- Any worker with read access to `assessment_responses` + Python or R.
- The assessment-science-agent skill (`memory/swarm/skills/assessment-science-agent.md`) has the IRT framework already — extend it with the DIF runner on data-availability day.

## Closes

E4 task 2 **methodology** is now locked. E4 task 2 **execution** is data-gated and will run first at M+3 (three months post-launch when per-item volume ≥ 200). Until then, the pre-flight qualitative scan fills the same audit gap with defensible rigor.
