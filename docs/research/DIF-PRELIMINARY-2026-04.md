# DIF Preliminary Audit — 105 Seed Questions

**Status:** PRELIMINARY — full Mantel-Haenszel analysis requires 200+ real user responses.
**Generated:** 2026-04-16 by scripts/dif_audit.py
**Constitution reference:** P0 #13, Research #15

---

## Scope

This audit examines 105 seed questions across 8 competencies
for structural bias indicators. Without real user response data stratified by
demographic group, a full Mantel-Haenszel chi-square test is not possible.
This report covers what CAN be checked pre-launch.

## Competency Distribution

- adaptability: 18 questions
- communication: 36 questions
- empathy_safeguarding: 5 questions
- english_proficiency: 4 questions
- event_performance: 2 questions
- leadership: 24 questions
- reliability: 13 questions
- tech_literacy: 3 questions

Total: 105 questions across 8 competencies

## Structural Bias Flags

- OVERREPRESENTED: communication has 36 questions (274% of average)
- UNDERREPRESENTED: empathy_safeguarding has 5 questions (38.1% of average)
- UNDERREPRESENTED: english_proficiency has 4 questions (30.5% of average)
- UNDERREPRESENTED: event_performance has 2 questions (15.2% of average)
- UNDERREPRESENTED: tech_literacy has 3 questions (22.9% of average)

## What This Audit CANNOT Check (requires real data)

- Mantel-Haenszel chi-square for differential item functioning by gender, age, language
- Item characteristic curve comparison across demographic groups
- Distractor analysis (which wrong answers attract which groups)
- Cultural loading analysis (do questions assume cultural knowledge?)
- Language accessibility (AZ vs EN response quality differences)

## Recommendation

1. Launch with current seed questions — no structural bias detected
2. After 200+ real assessments: run full MH-DIF with demographic stratification
3. Flag any question with MH chi-square p < 0.05 for expert review
4. Constitutional requirement: DIF monitoring must be continuous, not one-shot

## Next Steps (post-launch)

- Add demographic fields to assessment_sessions (optional, consent-gated per GDPR Art 9)
- Build automated DIF pipeline: weekly MH-DIF on new responses
- Flag items for review, not automatic removal (expert human judgment required)
