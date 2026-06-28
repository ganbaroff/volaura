# Legal Engagement Brief — VOLAURA — 2026-06-07

## Executive summary

VOLAURA is **not** blocked by known user-blocking code bugs from the current audit. The launch gate is still **external**: legal/compliance, controller/processor sign-off, and owner approval.

The repo already contains draft privacy/ToS materials and compliance research, but the unresolved questions are now legal, not technical:
- Does AZ privacy law treat any of our assessment inputs as sensitive health data?
- Is SADPP filing required now, and what exact proof is needed?
- Are the current cross-border transfer / processor / consent clauses sufficient for launch?
- For EU launch, does the AURA flow trigger GDPR Art. 22 and/or AI Act high-risk obligations, and what exact controls must be in place first?

This brief is for licensed counsel. It is not a code review and not a request for a new architecture.

## What is already in the repo

- Draft privacy policy and ToS already exist:
  - `docs/legal/Privacy-Policy-draft.md`
  - `docs/legal/ToS-draft.md`
- The repo already has compliance implementation notes for:
  - Art. 20 portability
  - Art. 22 human review
  - retention enforcement
  - see `docs/COMPLIANCE-OPERATIONS-RUNBOOK.md`
- Repo research already flags GDPR Art. 22 / AI Act risk around AURA scoring:
  - `docs/research/gdpr-article-22/summary.md`
- The entity-change diff already exists and maps the future Delaware C-Corp controller story:
  - `docs/legal/PRIVACY-POLICY-DE-CCORP-DIFF.md`
- A cross-border counsel shortlist already exists for US/AZ tax and legal support:
  - `docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md`

## Counsel #1: Azerbaijan privacy / cross-border / SADPP

Please answer these concretely:

1. Is `energy_level` or any other assessment input treated as health data / special-category data under AZ law?
   - If yes, what exact consent / notice / storage controls are required before launch?
2. Is SADPP filing or notification required before launch?
   - If yes, what exact filing is needed and what proof should we keep?
3. Are the current cross-border transfer statements in the privacy draft sufficient for AZ PDPA?
   - If not, what exact transfer mechanism or wording is required?
4. Do the current draft controller/operator statements and contact details need to change before launch?
5. Do the privacy / ToS drafts need any AZ-specific language about professional verification, discovery, or reputation risk?
6. Is the current deletion / retention language acceptable under AZ law, or do we need a different retention basis?

## Counsel #2: EU GDPR / AI Act

Please answer these concretely:

1. Does the AURA scoring + org discovery flow qualify as GDPR Art. 22 automated decision-making for our use case?
2. Does the same flow fall under EU AI Act high-risk recruitment/candidate evaluation obligations?
3. If yes, what must be in place before any EU user can be scored or discovered?
   - explicit opt-in
   - human review
   - explanation text
   - logging / audit trail
   - DPIA / FRIA
   - representative / controller details
4. Are the current draft privacy / ToS clauses sufficient for:
   - processing basis
   - processor disclosures
   - cross-border transfers
   - human review rights
   - objection / withdrawal rights
5. Do we need an EU representative before any EU signup?
6. Which items are launch-blocking now, and which can wait until after launch?

## What to review

Please review these files as the core packet:

- `docs/legal/Privacy-Policy-draft.md`
- `docs/legal/ToS-draft.md`
- `docs/legal/PRIVACY-POLICY-DE-CCORP-DIFF.md`
- `docs/COMPLIANCE-OPERATIONS-RUNBOOK.md`
- `docs/research/gdpr-article-22/summary.md`
- `docs/PRE-LAUNCH-BLOCKERS-STATUS.md`

Optional supporting context:

- `docs/legal/US-AZ-TAX-LAWYERS-SHORTLIST.md`
- `docs/privacy-policy.md`
- `docs/INDEX.md`

## Scope and cost guidance

Please give a written answer, not just a verbal opinion.

Suggested engagement shape:
- AZ privacy / cross-border counsel: 60-90 minute review or fixed-fee memo.
- EU GDPR / AI Act counsel: 60-90 minute strategic review with marked-up issues list.

If you can estimate cost, please give:
- a quick consult range
- a redline / memo range
- anything that would require a separate follow-up engagement

## Output requested

Please return:
1. A short verdict: what is the real launch blocker now?
2. A red/amber/green list of the unresolved legal items.
3. The exact questions I should ask each lawyer on the first call.
4. The exact docs or evidence I should send them.
5. Anything in the repo that should be corrected before legal review, if any.

## Non-goals

- No new architecture.
- No code changes.
- No user launch.
- No assumption that stale planning docs are current truth.

