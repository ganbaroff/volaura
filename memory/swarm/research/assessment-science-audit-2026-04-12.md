# Assessment Science Agent Audit (2026-04-12)
# Provider: Groq llama-3.3-70b-versatile (first real activation of this agent)

## Critical findings

1. Guessed IRT parameters → SEM 2-5x higher than calibrated. Unacceptable for B2B.
2. Minimum calibration sample: 1000-2000 test-takers (not 300 as previously estimated).
3. DIF risk for AZ/RU/EN: translation errors, cultural bias, language proficiency effects.
4. 5 questions (low energy) NOT psychometrically defensible. Minimum 10-15 per ITC 2018.
5. Priority #1 before B2B: calibrate IRT parameters with real data via MML or Bayesian.

## References cited
- Ackerman 1994: misestimated params → 2-5x SEM increase
- APA 2014: Standards for educational/psychological testing
- De Ayala 2009: 500-1000 minimum for <200 items
- ITC 2018: 10-15 items minimum for reliable estimates
- Zumbo 2007: DIF in multilingual assessments

## Impact on VOLAURA
- Current AURA scores are UNRELIABLE for hiring decisions (B2B risk)
- Low energy mode (5q) should be raised to 10q minimum
- IRT calibration study is BLOCKING for B2B launch — not optional
- DIF analysis needed before expanding beyond AZ market

## Action items
1. Collect 1000+ assessment responses before claiming "verified" scores
2. Run MML calibration on collected data (R package: mirt)
3. Raise low energy minimum from 5 to 10 questions
4. Add DIF analysis for AZ vs EN responses
